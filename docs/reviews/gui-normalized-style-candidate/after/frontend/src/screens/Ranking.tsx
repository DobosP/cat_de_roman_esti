import { Csp } from "../components/CspStyle";
// Ranking — the public online leaderboard (one view per game). Anyone can view it; a line
// only appears here for players who signed in and opted into the ranking. The signed-in
// viewer sees their own rank highlighted.

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AuthError, getRanking, type RankingResponse } from "../api/auth";
import { GAMES, type GameKey } from "../games";

type RankingError = "unavailable" | "failed";

export default function Ranking() {
  const navigate = useNavigate();
  const [game, setGame] = useState<GameKey>("alchimie");
  const [data, setData] = useState<RankingResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<RankingError | null>(null);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    setError(null);
    setData(null);
    getRanking(game, 50)
      .then((r) => alive && setData(r))
      .catch((reason: unknown) => {
        if (!alive) return;
        setError(reason instanceof AuthError && reason.status === 404 ? "unavailable" : "failed");
      })
      .finally(() => alive && setLoading(false));
    return () => {
      alive = false;
    };
  }, [game, attempt]);

  const entries = data?.entries ?? [];
  const meIsVisible = entries.some((row) => row.is_me);

  return (
    <Csp.div className="screen-pad fill" css={{ overflowY: "auto" }}>
      <Csp.div className="container col" css={{ gap: "20px", paddingBlock: "16px" }}>
        <Csp.div className="row spread" css={{ alignItems: "center" }}>
          <Csp.h1 css={{ margin: "0px" }}>🏆 Clasament</Csp.h1>
          <button type="button" className="account-btn" onClick={() => navigate("/")}>
            ← Acasă
          </button>
        </Csp.div>

        <label className="ranking-game-select">
          <span>Alege jocul</span>
          <select
            className="field"
            value={game}
            onChange={(event) => setGame(event.target.value as GameKey)}
          >
            {GAMES.map((g) => (
              <option key={g.key} value={g.key}>
                {g.title}
              </option>
            ))}
          </select>
        </label>

        <div className="segment ranking-game-tabs" role="group" aria-label="Alege jocul">
          {GAMES.map((g) => (
            <button
              key={g.key}
              type="button"
              className="segment-item"
              aria-pressed={game === g.key}
              onClick={() => setGame(g.key)}
            >
              {g.title}
            </button>
          ))}
        </div>

        <Csp.p className="muted" css={{ margin: "0px", fontSize: "0.9rem" }}>
          Recorduri verificate de joc · maximum 1000 de puncte.
        </Csp.p>

        {loading && (
          <div
            className="card ranking-state muted"
            role="status"
            aria-live="polite"
            aria-busy="true"
          >
            Se încarcă…
          </div>
        )}

        {!loading && error && (
          <div className="card ranking-state">
            <p className="account-error" role="alert">
              {error === "unavailable"
                ? "Clasamentul nu este activ aici."
                : "Nu am putut încărca clasamentul."}
            </p>
            {error === "unavailable" ? (
              <button type="button" className="account-btn" onClick={() => navigate("/")}>
                Acasă →
              </button>
            ) : (
              <button
                type="button"
                className="account-btn"
                onClick={() => setAttempt((value) => value + 1)}
              >
                Reîncearcă
              </button>
            )}
          </div>
        )}

        {!loading && !error && entries.length === 0 && (
          <Csp.div className="card center muted" css={{ minHeight: "100px", padding: "18px" }}>
            Încă nimeni în clasament la acest joc. Intră cu Google și fii primul!
          </Csp.div>
        )}

        {!loading && !error && entries.length > 0 && (
          <Csp.div className="col" css={{ gap: "6px" }}>
            {entries.map((row, index) => (
              <Csp.div
                key={`${row.rank}-${row.name}-${index}`}
                className={`card row spread rank-row${row.is_me ? " rank-row--me" : ""}`}
                css={{ padding: "10px 14px", alignItems: "center" }}
              >
                <Csp.div className="row" css={{ gap: "12px", minWidth: "0px", alignItems: "center" }}>
                  <span className={`rank-num rank-num--${row.rank <= 3 ? row.rank : "n"}`}>
                    {row.rank}
                  </span>
                  <Csp.strong css={{ overflow: "hidden", textOverflow: "ellipsis" }}>
                    {row.name}
                  </Csp.strong>
                </Csp.div>
                <Csp.strong css={{ fontVariantNumeric: "tabular-nums" }}>{row.score} pct</Csp.strong>
              </Csp.div>
            ))}
          </Csp.div>
        )}

        {data?.me && !loading && !error && !meIsVisible && (
          <Csp.div className="card row spread rank-row rank-row--me" css={{ padding: "12px 14px" }}>
            <strong>Locul tău: #{data.me.rank}</strong>
            <Csp.strong css={{ fontVariantNumeric: "tabular-nums" }}>{data.me.score} pct</Csp.strong>
          </Csp.div>
        )}

        {data && !data.me && !loading && (
          <Csp.p className="faint" css={{ fontSize: "0.85rem" }}>
            Pentru a apărea, intră în cont și activează clasamentul din meniul profilului.
          </Csp.p>
        )}
      </Csp.div>
    </Csp.div>
  );
}
