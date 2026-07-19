// Ranking — the public online leaderboard (one view per game). Anyone can view it; a line
// only appears here for players who signed in and opted into the ranking. The signed-in
// viewer sees their own rank highlighted.

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getRanking, type RankingResponse } from "../api/auth";
import { GAMES, type GameKey } from "../games";

export default function Ranking() {
  const navigate = useNavigate();
  const [game, setGame] = useState<GameKey>("alchimie");
  const [data, setData] = useState<RankingResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    setError(null);
    getRanking(game, 50)
      .then((r) => alive && setData(r))
      .catch(() => alive && setError("Nu am putut încărca clasamentul."))
      .finally(() => alive && setLoading(false));
    return () => {
      alive = false;
    };
  }, [game]);

  const entries = data?.entries ?? [];
  const meRank = data?.me?.rank ?? null;

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

        {loading && <div className="card center muted" style={{ minHeight: 82 }}>Se încarcă…</div>}
        {error && <div className="card center account-error" style={{ minHeight: 82 }}>{error}</div>}

        {!loading && !error && entries.length === 0 && (
          <div className="card center muted" style={{ minHeight: 100, padding: 18 }}>
            Încă nimeni în clasament la acest joc. Intră cu Google și fii primul!
          </div>
        )}

        {!loading && !error && entries.length > 0 && (
          <div className="col" style={{ gap: 6 }}>
            {entries.map((row) => (
              <div
                key={`${row.rank}-${row.name}`}
                className={`card row spread rank-row${meRank === row.rank ? " rank-row--me" : ""}`}
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
                <strong style={{ fontVariantNumeric: "tabular-nums" }}>{row.score}</strong>
              </div>
            ))}
          </div>
        )}

        {data && !data.me && !loading && (
          <p className="faint" style={{ fontSize: "0.85rem" }}>
            Intră cu Google (dreapta sus) ca să apari și tu în clasament.
          </p>
        )}
      </div>
    </div>
  );
}
