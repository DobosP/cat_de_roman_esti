package httpgolden

import (
	"context"
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/browserplan"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"sort"
	"sync"
	"time"
)

type BenchmarkConfig struct {
	Flows       int
	Warmup      int
	Concurrency int
	Workload    string
}
type Latency struct {
	Count int     `json:"count"`
	P50   float64 `json:"p50_ms"`
	P95   float64 `json:"p95_ms"`
	P99   float64 `json:"p99_ms"`
	Max   float64 `json:"max_ms"`
}
type BenchmarkReport struct {
	OK             bool    `json:"ok"`
	Workload       string  `json:"workload"`
	Flows          int     `json:"flows"`
	Warmup         int     `json:"warmup_flows"`
	Concurrency    int     `json:"concurrency"`
	Requests       int     `json:"requests"`
	ElapsedSeconds float64 `json:"elapsed_seconds"`
	FlowsPerSecond float64 `json:"flows_per_second"`
	Latency        Latency `json:"request_latency"`
	StateSHA256    string  `json:"state_sha256"`
	Scope          string  `json:"scope"`
}

func percentile(v []float64, n int) float64 {
	if len(v) == 0 {
		return 0
	}
	index := (len(v)*n+99)/100 - 1
	if index < 0 {
		index = 0
	}
	return v[index]
}
func Benchmark(ctx context.Context, client *Client, data *content.Content, cfg BenchmarkConfig) (BenchmarkReport, error) {
	report := BenchmarkReport{Workload: cfg.Workload, Flows: cfg.Flows, Warmup: cfg.Warmup, Concurrency: cfg.Concurrency, Scope: "bounded fixed seeded HTTP workload; client-observed timings only, no saturation or production capacity claim"}
	if cfg.Flows < 1 || cfg.Flows > 900 || cfg.Warmup < 0 || cfg.Warmup > 100 || cfg.Concurrency < 1 || cfg.Concurrency > 64 || cfg.Workload != "journeys" && cfg.Workload != "creates" {
		return report, fmt.Errorf("benchmark bounds: flows 1..900, warmup 0..100, concurrency 1..64, workload creates|journeys")
	}
	plans := map[string]*browserplan.Plan{}
	for _, game := range browserplan.Games {
		p, err := browserplan.Solution(data, game, "", "")
		if err != nil {
			return report, err
		}
		plans[game] = p
	}
	type sample struct {
		index     int
		latencies []float64
		digest    string
		err       error
	}
	flow := func(index int) sample {
		result := sample{index: index}
		game := browserplan.Games[index%len(browserplan.Games)]
		plan := plans[game]
		base := "/api/wordgames/" + game + "/games"
		hash := sha256.New()
		request := func(method, path string, payload any) (map[string]any, error) {
			res, err := checked(ctx, client, JSONRequest(method, path, payload), 200, true)
			if err != nil {
				return nil, err
			}
			result.latencies = append(result.latencies, float64(res.Duration)/float64(time.Millisecond))
			body, err := res.Object()
			if err != nil {
				return nil, err
			}
			snapshot := normalized(body, map[string]string{}).(map[string]any)
			if _, ok := snapshot["game_id"]; ok {
				snapshot["game_id"] = "<session>"
			}
			raw, _ := json.Marshal(snapshot)
			hash.Write(raw)
			return body, nil
		}
		state, err := request("POST", base+"?"+queryFor(game), nil)
		if err != nil {
			result.err = err
			return result
		}
		snapshot := map[string]any{}
		for k, v := range state {
			if k != "game_id" {
				snapshot[k] = v
			}
		}
		if !same(snapshot, plan.Initial) {
			result.err = fmt.Errorf("benchmark initial semantic drift")
			return result
		}
		if cfg.Workload == "journeys" {
			path := base + "/" + state["game_id"].(string)
			if _, err = request("GET", path, nil); err != nil {
				result.err = err
				return result
			}
			for _, step := range plan.Steps {
				state, err = request("POST", path+"/"+step.Action, step.Payload)
				if err != nil {
					result.err = err
					return result
				}
			}
			if err = final(state); err != nil {
				result.err = err
				return result
			}
			terminal, err := request("GET", path, nil)
			if err != nil || terminal["won"] != true || !same(terminal["score"], state["score"]) || !same(terminal["share"], state["share"]) {
				if err == nil {
					err = fmt.Errorf("benchmark terminal won/score/share resume drift")
				}
				result.err = err
				return result
			}
		}
		result.digest = fmt.Sprintf("%x", hash.Sum(nil))
		return result
	}
	for i := 0; i < cfg.Warmup; i++ {
		if result := flow(i); result.err != nil {
			return report, result.err
		}
	}
	start := time.Now()
	jobs := make(chan int, cfg.Concurrency)
	results := make(chan sample, cfg.Flows)
	var workers sync.WaitGroup
	for i := 0; i < cfg.Concurrency; i++ {
		workers.Add(1)
		go func() {
			defer workers.Done()
			for index := range jobs {
				results <- flow(index)
			}
		}()
	}
	go func() {
		for i := 0; i < cfg.Flows; i++ {
			jobs <- i
		}
		close(jobs)
		workers.Wait()
		close(results)
	}()
	samples := make([]sample, cfg.Flows)
	var first error
	for sample := range results {
		if sample.err != nil && first == nil {
			first = sample.err
		}
		samples[sample.index] = sample
	}
	if first != nil {
		return report, first
	}
	latencies := []float64{}
	hash := sha256.New()
	for _, sample := range samples {
		latencies = append(latencies, sample.latencies...)
		hash.Write([]byte(sample.digest))
	}
	sort.Float64s(latencies)
	report.OK = true
	report.Requests = client.Count()
	report.ElapsedSeconds = time.Since(start).Seconds()
	report.FlowsPerSecond = float64(cfg.Flows) / report.ElapsedSeconds
	report.StateSHA256 = fmt.Sprintf("%x", hash.Sum(nil))
	report.Latency = Latency{len(latencies), percentile(latencies, 50), percentile(latencies, 95), percentile(latencies, 99), latencies[len(latencies)-1]}
	return report, nil
}
