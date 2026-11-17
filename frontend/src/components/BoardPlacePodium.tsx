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
export function BoardPlacePodium({ round, replay, gameTitle, canBePerfect = true }: {
  round: Pick<RoundCounters, "place"> & { daily?: string; won: boolean };
  replay: boolean;
  gameTitle: string;
  canBePerfect?: boolean;
}) {
  const { daily, place, won } = round;
  if (!won || !daily || replay || !place) return null;

  const availableTiers = canBePerfect ? tiers : tiers.filter(({ key }) => key !== "perfect");
  const tier = availableTiers.find(({ key }) => key === place.tier);
  if (!tier) return null;

  const today = daily === localDay();
  const boardDate = today ? "de azi" : `din ${formatDayKey(daily)}`;
  const legend = availableTiers.map(({ label }) => label).join(", ");
  return (
    <div className="board-place">
      <div className="board-place-intro">
        <h3>{tier.label}{today && " azi"}</h3>
        <p className="board-place-count">
          la {gameTitle}, din {countFormat.format(place.rounds)} {roNoun(place.rounds, "rundă", "runde")} încheiate
        </p>
      </div>
      <div className={canBePerfect ? "board-place-chart" : "board-place-chart board-place-chart--three"} role="img" aria-label={`Podium cu treptele ${legend}. Treapta ta este ${tier.label}.`}>
        {availableTiers.map(({ key, label }) => (
          <div className="board-place-column" key={key} aria-hidden="true" data-tier={key} data-current={key === tier.key || undefined}>
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
