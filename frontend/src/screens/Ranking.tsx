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
    <div className="screen-pad fill" style={{ overflowY: "auto" }}>
      <div className="container col" style={{ gap: 20, paddingBlock: 16 }}>
        <div className="row spread" style={{ alignItems: "center" }}>
          <h1 style={{ margin: 0 }}>🏆 Clasament</h1>
          <button type="button" className="account-btn" onClick={() => navigate("/")}>
            ← Acasă
          </button>
        </div>

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

        <p className="muted" style={{ margin: 0, fontSize: "0.9rem" }}>
          Recorduri verificate de joc · maximum 1000 de puncte.
        </p>

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
          <div className="card center muted" style={{ minHeight: 100, padding: 18 }}>
            Încă nimeni în clasament la acest joc. Intră cu Google și fii primul!
          </div>
        )}

        {!loading && !error && entries.length > 0 && (
          <div className="col" style={{ gap: 6 }}>
            {entries.map((row, index) => (
              <div
                key={`${row.rank}-${row.name}-${index}`}
                className={`card row spread rank-row${row.is_me ? " rank-row--me" : ""}`}
                style={{ padding: "10px 14px", alignItems: "center" }}
              >
                <div className="row" style={{ gap: 12, minWidth: 0, alignItems: "center" }}>
                  <span className={`rank-num rank-num--${row.rank <= 3 ? row.rank : "n"}`}>
                    {row.rank}
                  </span>
                  <strong style={{ overflow: "hidden", textOverflow: "ellipsis" }}>
                    {row.name}
                  </strong>
                </div>
                <strong style={{ fontVariantNumeric: "tabular-nums" }}>{row.score} pct</strong>
              </div>
            ))}
          </div>
        )}

        {data?.me && !loading && !error && !meIsVisible && (
          <div className="card row spread rank-row rank-row--me" style={{ padding: "12px 14px" }}>
            <strong>Locul tău: #{data.me.rank}</strong>
            <strong style={{ fontVariantNumeric: "tabular-nums" }}>{data.me.score} pct</strong>
          </div>
        )}

        {data && !data.me && !loading && (
          <p className="faint" style={{ fontSize: "0.85rem" }}>
            Pentru a apărea, intră în cont și activează clasamentul din meniul profilului.
          </p>
        )}
      </div>
    </div>
  );
}
