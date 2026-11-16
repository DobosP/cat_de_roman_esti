import type { BoardPlaceTier, RoundCounters } from "../api/round";
import { localDay } from "../entry";
import { formatDayKey, roNoun } from "../share";

const tiers: readonly { key: BoardPlaceTier; label: string }[] = [
  { key: "perfect", label: "Perfect" },
  { key: "top_10", label: "Top 10%" },
  { key: "top_half", label: "Prima jumătate" },
  { key: "completed", label: "Ai reușit" },
];

const countFormat = new Intl.NumberFormat("ro-RO");
const legend = tiers.map(({ label }) => label).join(", ");

export function BoardPlacePodium({ round, replay, gameTitle }: {
  round: Pick<RoundCounters, "place"> & { daily?: string; won: boolean };
  replay: boolean;
  gameTitle: string;
}) {
  const { daily, place, won } = round;
  if (!won || !daily || replay || !place) return null;

  const tier = tiers.find(({ key }) => key === place.tier);
  if (!tier) return null;

  const today = daily === localDay();
  const boardDate = today ? "de azi" : `din ${formatDayKey(daily)}`;
  return (
    <div className="board-place">
      <div className="board-place-intro">
        <h3>{tier.label}{today && " azi"}</h3>
        <p className="board-place-count">
          la {gameTitle}, din {countFormat.format(place.rounds)} {roNoun(place.rounds, "rundă", "runde")} încheiate
        </p>
      </div>
      <div className="board-place-chart" role="img" aria-label={`Podium cu treptele ${legend}. Treapta ta este ${tier.label}.`}>
        {tiers.map(({ key, label }) => (
          <div className="board-place-column" key={key} aria-hidden="true" data-current={key === tier.key || undefined}>
            {key === tier.key && <span className="board-place-marker">Tu</span>}
            <span className="board-place-bar" />
            <span className="board-place-label">{label}</span>
          </div>
        ))}
      </div>
      <p>
        Mai bine decât <strong>{place.better_than_pct}%</strong> dintre rundele încheiate pe tabla {boardDate}.
      </p>
    </div>
  );
}
