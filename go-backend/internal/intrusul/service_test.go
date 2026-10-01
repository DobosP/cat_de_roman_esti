package intrusul

import (
	"encoding/json"
	"fmt"
	"math/big"
	"reflect"
	"strings"
	"sync"
	"testing"
	"time"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/pyrandom"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/session"
)

func testService(t *testing.T) *Service {
	t.Helper()
	data := &content.Content{Labels: map[string]string{"a": "Țară", "b": "Școală", "c": "Carte", "d": "Intrus"}, CategoryLabels: map[string]string{"cultura": "Cultură", "empty": "Fără table"}}
	for i := 0; i < 7; i++ {
		data.Boards = append(data.Boards, content.Board{Game: GameKey, CatalogID: fmt.Sprintf("catalog-%d", i), SourceID: fmt.Sprintf("source-%d", i), Category: "cultura", Difficulty: "usor", OverallScore: 90, StarterScore: 90, OverallRank: i + 1, StarterSafe: true, Payload: map[string]any{"members": []string{"a", "b", "c"}, "intruder": "d", "group_label": "Grupul privat"}})
	}
	return New(data)
}

func createGame(t *testing.T, service *Service, seed int64) (string, map[string]any) {
	t.Helper()
	body, err := service.Create(big.NewInt(seed), "", "", "", false)
	if err != nil {
		t.Fatal(err)
	}
	return body["game_id"].(string), body
}

func checkError(t *testing.T, err *Error, status int, detail string) {
	t.Helper()
	if err == nil || err.Status != status || err.Detail != detail {
		t.Fatalf("want %d %q, got %#v", status, detail, err)
	}
}

func checkNoPrivateState(t *testing.T, body map[string]any) {
	t.Helper()
	serialized, err := json.Marshal(body)
	if err != nil {
		t.Fatal(err)
	}
	for _, key := range []string{"solution", "intruder", "members", "group", "group_label", "source_id", "source_ring", "catalog_id", "rank", "standard_rank", "starter_rank", "standard_score", "starter_score", "selection_weight", "score", "share"} {
		if strings.Contains(string(serialized), `"`+key+`":`) {
			t.Fatalf("private field %s in %s", key, serialized)
		}
	}
	if strings.Contains(string(serialized), "Grupul privat") || strings.Contains(string(serialized), "source-") || strings.Contains(string(serialized), "catalog-") {
		t.Fatalf("private values in %s", serialized)
	}
}

func TestCreationPrivacyAndSeededStability(t *testing.T) {
	service := testService(t)
	first, initial := createGame(t, service, 17)
	_, again := createGame(t, service, 17)
	if !reflect.DeepEqual(initial["tiles"], again["tiles"]) {
		t.Fatal("seeded shuffle changed")
	}
	checkNoPrivateState(t, initial)
	for _, key := range []string{"attempts", "mistakes", "hints_used"} {
		if initial[key] != 0 {
			t.Errorf("%s = %v", key, initial[key])
		}
	}
	if initial["remaining_mistakes"] != 3 || initial["hint_available"] != false || initial["won"] != false || initial["lost"] != false {
		t.Fatal("incorrect initial state")
	}
	if _, exists := initial["board_category"]; exists {
		t.Fatal("unrequested provenance category")
	}
	if len(initial["wrong_ids"].([]string)) != 0 {
		t.Fatal("initial wrong ids nonempty")
	}
	fetched, err := service.Get(first)
	if err != nil {
		t.Fatal(err)
	}
	checkNoPrivateState(t, fetched)
	if !reflect.DeepEqual(initial, fetched) {
		t.Fatal("get differs from creation")
	}
}

func TestWrongRepeatHintScoredWinAndSnapshotOwnership(t *testing.T) {
	service := testService(t)
	id, _ := createGame(t, service, 17)
	_, err := service.Hint(id)
	checkError(t, err, 400, "Indiciul apare după prima încercare.")
	first, err := service.Guess(id, " a ")
	if err != nil {
		t.Fatal(err)
	}
	if first["correct"] != false || first["already_tried"] != false || first["attempts"] != 1 || first["mistakes"] != 1 || first["hint_available"] != true {
		t.Fatalf("bad wrong state: %#v", first)
	}
	checkNoPrivateState(t, first)
	first["wrong_ids"].([]string)[0] = "tampered"
	first["tiles"].([]map[string]string)[0]["label"] = "tampered"
	repeated, err := service.Guess(id, "a")
	if err != nil {
		t.Fatal(err)
	}
	if repeated["already_tried"] != true || repeated["attempts"] != 1 || repeated["mistakes"] != 1 || !reflect.DeepEqual(repeated["wrong_ids"], []string{"a"}) {
		t.Fatal("repeated guess cost or response alias")
	}
	hinted, err := service.Hint(id)
	if err != nil {
		t.Fatal(err)
	}
	if hinted["hints_used"] != 1 || hinted["hint_available"] != false || hinted["clue"].(map[string]string)["message"] != "Trei cuvinte țin de: Grupul privat." {
		t.Fatalf("bad hint: %#v", hinted)
	}
	if _, exists := hinted["solution"]; exists {
		t.Fatal("hint exposed answer")
	}
	_, err = service.Hint(id)
	checkError(t, err, 400, "Indiciul a fost deja folosit")
	won, err := service.Guess(id, "d")
	if err != nil {
		t.Fatal(err)
	}
	if won["correct"] != true || won["won"] != true || won["lost"] != false || won["attempts"] != 2 || won["score"] != 650 {
		t.Fatalf("bad win: %#v", won)
	}
	if won["share"] != "cat_de_roman_esti · Intrusul\n🟩 2 încercări · indiciu" {
		t.Fatalf("bad share: %v", won["share"])
	}
	solution := won["solution"].(map[string]any)
	if solution["intruder"].(map[string]string)["id"] != "d" || solution["group"].(map[string]any)["label"] != "Grupul privat" {
		t.Fatal("bad terminal solution")
	}
	_, err = service.Guess(id, "d")
	checkError(t, err, 400, "Jocul s-a terminat")
	_, err = service.Hint(id)
	checkError(t, err, 400, "Jocul s-a terminat")
}

func TestFirstTryScoreAndThirdWrongLoss(t *testing.T) {
	service := testService(t)
	id, _ := createGame(t, service, 51)
	won, err := service.Guess(id, "d")
	if err != nil {
		t.Fatal(err)
	}
	if won["score"] != 1000 || won["share"] != "cat_de_roman_esti · Intrusul\n🟩 1 încercare" {
		t.Fatalf("first-try score: %#v", won)
	}
	lostID, _ := createGame(t, service, 52)
	for i, wrong := range []string{"a", "b", "c"} {
		body, err := service.Guess(lostID, wrong)
		if err != nil {
			t.Fatal(err)
		}
		if body["lost"] != (i == 2) || body["mistakes"] != i+1 {
			t.Fatalf("wrong loss progression: %#v", body)
		}
		if i == 2 && (body["score"] != 0 || body["remaining_mistakes"] != 0 || body["share"] != "cat_de_roman_esti · Intrusul\n🟥 3 încercări") {
			t.Fatal("bad loss score/share")
		}
	}
}

func TestDailyIgnoresSeedStarterAndPrevious(t *testing.T) {
	service := testService(t)
	previous, _ := createGame(t, service, 10)
	first, err := service.Create(big.NewInt(1), "2026-10-01", "cultura", "", false)
	if err != nil {
		t.Fatal(err)
	}
	second, err := service.Create(big.NewInt(999), "2026-10-01", "cultura", previous, true)
	if err != nil {
		t.Fatal(err)
	}
	if !reflect.DeepEqual(first["tiles"], second["tiles"]) || first["daily"] != "2026-10-01" || first["board_category"] != "cultura" {
		t.Fatal("daily forks")
	}
	service.store.Transaction(second["game_id"].(string), func(game *gameSession) error {
		if !reflect.DeepEqual(game.sourceRing, []string{game.sourceID}) {
			t.Error("daily retained previous ring")
		}
		return nil
	})
	won, err := service.Guess(second["game_id"].(string), "d")
	if err != nil {
		t.Fatal(err)
	}
	if won["share"] != "cat_de_roman_esti · Intrusul · Cultură\n🟩 1 încercare\n2026-10-01" {
		t.Fatalf("themed daily share: %v", won["share"])
	}
}

func TestSourceRotationDistinctBoundedRingAndExpiredPrevious(t *testing.T) {
	service := testService(t)
	previous := ""
	seen := []string{}
	for i := 0; i < 12; i++ {
		body, err := service.Create(big.NewInt(31), "", "", previous, false)
		if err != nil {
			t.Fatal(err)
		}
		id := body["game_id"].(string)
		service.store.Transaction(id, func(game *gameSession) error {
			if contains(seen, game.sourceID) {
				t.Error("repeated source despite alternatives")
			}
			seen = append(seen, game.sourceID)
			if len(seen) > SourceRingLimit {
				seen = seen[len(seen)-SourceRingLimit:]
			}
			if !reflect.DeepEqual(game.sourceRing, seen) {
				t.Errorf("ring %v != %v", game.sourceRing, seen)
			}
			return nil
		})
		previous = id
	}
	body, err := service.Create(big.NewInt(31), "", "", "expired-id", false)
	if err != nil {
		t.Fatal(err)
	}
	service.store.Transaction(body["game_id"].(string), func(game *gameSession) error {
		if !reflect.DeepEqual(game.sourceRing, []string{game.sourceID}) {
			t.Error("missing previous inherited history")
		}
		return nil
	})
}

func TestForcedRepeatMovesSourceToTail(t *testing.T) {
	service := testService(t)
	board := &service.content.Boards[0]
	game, err := build(board, pyrandom.New(big.NewInt(1)), "", "", []string{"source-a", board.SourceID, "source-c", "source-d"})
	if err != nil {
		t.Fatal(err)
	}
	if !reflect.DeepEqual(game.sourceRing, []string{"source-a", "source-c", "source-d", board.SourceID}) {
		t.Fatalf("repeat shrank memory: %v", game.sourceRing)
	}
}

func TestStarterSafeFallbackAndSelectionErrors(t *testing.T) {
	service := testService(t)
	for i := range service.content.Boards {
		service.content.Boards[i].StarterSafe = false
	}
	// The catalog owns immutable board copies; create a service after changing input.
	service = New(service.content)
	if _, err := service.Create(big.NewInt(7), "", "", "", true); err != nil {
		t.Fatalf("starter failed to widen safe catalog: %v", err)
	}
	_, err := service.Create(big.NewInt(1), "", "missing", "", false)
	checkError(t, err, 400, "Categorie necunoscută.")
	_, err = service.Create(big.NewInt(1), "", "empty", "", false)
	checkError(t, err, 503, "Nu există încă jocuri sigure pentru această categorie.")
	id, _ := createGame(t, service, 1)
	_, err = service.Guess(id, "not-on-board")
	checkError(t, err, 400, "Concept care nu este pe tablă")
	_, err = service.Get("missing")
	checkError(t, err, 404, "Joc inexistent")
	_, err = service.Guess("missing", "a")
	checkError(t, err, 404, "Joc inexistent")
	_, err = service.Hint("missing")
	checkError(t, err, 404, "Joc inexistent")
}

func TestConcurrentRepeatedWrongHintAndWin(t *testing.T) {
	service := testService(t)
	id, _ := createGame(t, service, 61)
	const workers = 32
	var wg sync.WaitGroup
	results := make(chan map[string]any, workers)
	for i := 0; i < workers; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			body, err := service.Guess(id, "a")
			if err != nil {
				t.Error(err)
				return
			}
			results <- body
		}()
	}
	wg.Wait()
	close(results)
	charged := 0
	for body := range results {
		if body["already_tried"] == false {
			charged++
		}
		if body["attempts"] != 1 || body["mistakes"] != 1 {
			t.Error("duplicate cost")
		}
	}
	if charged != 1 {
		t.Fatalf("charged %d times", charged)
	}
	var successMu sync.Mutex
	hints := 0
	for i := 0; i < workers; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			_, err := service.Hint(id)
			if err == nil {
				successMu.Lock()
				hints++
				successMu.Unlock()
			} else if err.Detail != "Indiciul a fost deja folosit" {
				t.Error(err)
			}
		}()
	}
	wg.Wait()
	if hints != 1 {
		t.Fatalf("hint charged %d times", hints)
	}
	wins := 0
	for i := 0; i < workers; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			body, err := service.Guess(id, "d")
			if err == nil {
				successMu.Lock()
				wins++
				successMu.Unlock()
				if body["score"] != 650 {
					t.Error("wrong score")
				}
			} else if err.Detail != "Jocul s-a terminat" {
				t.Error(err)
			}
		}()
	}
	wg.Wait()
	if wins != 1 {
		t.Fatalf("won %d times", wins)
	}
}

func TestSessionExpiryAndPinnedCapacityArePublicErrors(t *testing.T) {
	service := testService(t)
	now := time.Unix(0, 0)
	service.store, _ = session.NewWithOptions[*gameSession](time.Second, 1, func() time.Time { return now })
	id, _ := createGame(t, service, 1)
	now = now.Add(2 * time.Second)
	_, err := service.Get(id)
	checkError(t, err, 404, "Joc inexistent")
	id, _ = createGame(t, service, 1)
	service.store.Transaction(id, func(*gameSession) error {
		_, err := service.Create(big.NewInt(2), "", "", "", false)
		checkError(t, err, 503, "Prea multe jocuri active. Încearcă din nou.")
		return nil
	})
}

func TestMalformedPrivateBoardFailsClosed(t *testing.T) {
	service := testService(t)
	board := service.content.Boards[0]
	for _, payload := range []map[string]any{{"members": []string{"a", "b"}, "intruder": "d", "group_label": "x"}, {"members": []string{"a", "b", "c"}, "intruder": "a", "group_label": "x"}} {
		board.Payload = payload
		_, err := build(&board, pyrandom.New(big.NewInt(1)), "", "", nil)
		checkError(t, err, 503, "Tabla aleasă nu mai este validă.")
	}
}

func TestGuessInputPinsValidationAndPreservesErrorPrecedence(t *testing.T) {
	service := testService(t)
	service.store, _ = session.NewWithOptions[*gameSession](time.Hour, 1, time.Now)
	id, _ := createGame(t, service, 1)
	validationError := &Error{Status: 422, Detail: []any{map[string]any{"loc": []string{"id"}, "msg": "Field required"}}}
	_, err := service.GuessInput(id, func() (string, *Error) {
		if service.store.Delete(id) {
			t.Error("validation did not pin the session")
		}
		_, capacityError := service.Create(big.NewInt(2), "", "", "", false)
		checkError(t, capacityError, 503, "Prea multe jocuri active. Încearcă din nou.")
		return "", validationError
	})
	if err != validationError {
		t.Fatalf("validation error lost: %v", err)
	}
	body, err := service.Get(id)
	if err != nil || body["attempts"] != 0 {
		t.Fatal("validation mutated state")
	}
	_, err = service.Guess(id, "d")
	if err != nil {
		t.Fatal(err)
	}
	_, err = service.GuessInput(id, func() (string, *Error) { return "", validationError })
	if err != validationError {
		t.Fatal("terminal check preceded malformed body validation")
	}
	_, err = service.GuessInput("missing", func() (string, *Error) { t.Error("missing-session body validator called"); return "", validationError })
	checkError(t, err, 404, "Joc inexistent")
}

func TestBundledReviewedContentWorksWithoutPython(t *testing.T) {
	data, loadErr := content.Load()
	if loadErr != nil {
		t.Fatal(loadErr)
	}
	service := New(data)
	for _, seed := range []int64{0, 17, 91, -1, 999} {
		id, body := createGame(t, service, seed)
		if len(body["tiles"].([]map[string]string)) != 4 {
			t.Fatal("invalid reviewed board")
		}
		var answer string
		service.store.Transaction(id, func(game *gameSession) error { answer = game.intruder; return nil })
		won, err := service.Guess(id, answer)
		if err != nil || won["score"] != 1000 {
			t.Fatalf("bundled gameplay: %#v %v", won, err)
		}
	}
}
