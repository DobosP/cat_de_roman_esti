import type { TargetedEvent } from "preact";
import { useLayoutEffect, useRef, useState } from "preact/hooks";
import { Button, type ToastKind } from "@roedu/ui";
import { GAMES } from "../games";
import { exportScores, importScores } from "../scores/history";
import { recentScores } from "../scores/read";
import { formatDayKey, roNoun } from "../share";

type Props = { onClose: () => void; onToast: (message: string, kind?: ToastKind) => void };

function completedRounds() {
  return recentScores(undefined, 300)
    .flatMap((row) => {
      const game = GAMES.find(({ key }) => row.game === key);
      return game && row.steps !== undefined ? [{ ...row, title: game.title, steps: row.steps }] : [];
    })
    .slice(0, 30);
}

export default function ResultsHistory({ onClose, onToast }: Props) {
  const dialog = useRef<HTMLDialogElement>(null);
  const input = useRef<HTMLInputElement>(null);
  const [rounds, setRounds] = useState(completedRounds);

  useLayoutEffect(() => {
    const node = dialog.current!;
    node.showModal();
    return () => node.close();
  }, []);

  const download = () => {
    const url = URL.createObjectURL(new Blob([exportScores()], { type: "application/json" }));
    const link = document.createElement("a");
    link.href = url;
    link.download = "rezultatele-mele.json";
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  };

  const upload = async (event: TargetedEvent<HTMLInputElement>) => {
    const file = event.currentTarget.files?.[0];
    event.currentTarget.value = "";
    if (!file) return;
    try {
      if (file.size > 1024 * 1024) throw new Error("Fișier prea mare.");
      importScores(await file.text());
      setRounds(completedRounds());
      onToast("Istoricul a fost importat.", "success");
    } catch {
      onToast("Fișierul ales nu este un export de istoric valid.", "error");
    }
  };

  return (
    <dialog ref={dialog} className="results-history" aria-labelledby="results-history-title" onClose={onClose}>
      <header className="row spread">
        <h2 id="results-history-title">Rezultatele mele</h2>
        <Button variant="secondary" onClick={() => dialog.current?.close()}>Închide</Button>
      </header>
      {rounds.length ? <ol>
        {rounds.map((row, index) => <li key={`${row.game}-${row.at}-${index}`}>
          <strong>{row.title}</strong>
          <span>{row.steps} {roNoun(row.steps, "pas", "pași")}</span>
          <time>
            {row.daily ? formatDayKey(row.daily) : new Date(row.at).toLocaleDateString("ro-RO")}
          </time>
        </li>)}
      </ol> : <p>Nicio rundă terminată încă.</p>}
      <div className="row wrap">
        <Button variant="secondary" onClick={download}>Exportă istoricul</Button>
        <Button variant="secondary" onClick={() => input.current?.click()}>Importă istoricul</Button>
        <input ref={input} type="file" accept=".json,application/json" hidden onChange={upload} />
      </div>
    </dialog>
  );
}
