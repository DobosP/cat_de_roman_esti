import type { Ref } from "preact";

export function HintBar({ remaining, disabled, onHint, buttonRef }: {
  remaining: number;
  disabled?: boolean;
  onHint: () => void;
  buttonRef?: Ref<HTMLButtonElement>;
}) {
  return (
    <div className="hint-bar">
      <button type="button" className="btn hint-bar-button" ref={buttonRef}
        onClick={onHint} disabled={disabled || remaining === 0}>
        <span aria-hidden="true">💡</span> {remaining > 0 ? "Indiciu" : "Fără indicii"}
      </button>
      <span>{remaining > 0 ? "Costă un pas." : "Ai folosit toate indiciile."}</span>
    </div>
  );
}
