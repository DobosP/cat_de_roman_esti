// AccountBar — the top-right account affordance for the arcade (accounts ON only).
//
// Renders nothing when accounts are disabled or still loading, so the anonymous/offline
// arcade is visually unchanged. Otherwise: a "Sign in with Google" button, the RO age-16
// consent gate for freshly-signed-in users, a restricted notice for under-age accounts, or
// the signed-in chip (name/avatar + logout + delete-my-data).

import { useState } from "react";
import {
  type AuthUser,
  deleteAccount,
  loginWithGoogle,
  logout,
  submitConsent,
} from "../api/auth";
import { useAuth } from "../hooks/useAuth";

const CURRENT_YEAR = new Date().getFullYear();

export default function AccountBar() {
  const { me, loading, refresh } = useAuth();
  if (loading || !me || !me.accounts_enabled) return null;

  if (!me.authenticated || !me.user) {
    return (
      <div className="account-bar">
        <button type="button" className="account-btn account-btn--google" onClick={loginWithGoogle}>
          Intră cu Google
        </button>
      </div>
    );
  }

  const user = me.user;
  if (!user.consent_completed) {
    if (user.parental_consent_required) {
      return <RestrictedNotice onLogout={refresh} />;
    }
    return <ConsentGate minAge={me.min_self_consent_age ?? 16} onResolved={refresh} />;
  }

  return <UserChip user={user} onChanged={refresh} />;
}

function RestrictedNotice({ onLogout }: { onLogout: () => Promise<void> }) {
  return (
    <div className="account-overlay">
      <div className="account-card">
        <h2>Cont restricționat</h2>
        <p>
          Conform legii, copiii sub 16 ani au nevoie de acordul unui părinte pentru a-și crea
          un cont. Poți juca în continuare fără cont — progresul se salvează pe acest
          dispozitiv.
        </p>
        <p className="account-muted">
          Un flux de consimțământ al părintelui va fi disponibil în curând.
        </p>
        <div className="account-actions">
          <button
            type="button"
            className="account-btn"
            onClick={async () => {
              await logout();
              await onLogout();
            }}
          >
            Închide contul
          </button>
        </div>
      </div>
    </div>
  );
}

function ConsentGate({ minAge, onResolved }: { minAge: number; onResolved: () => Promise<void> }) {
  const [birthYear, setBirthYear] = useState("");
  const [accepted, setAccepted] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async () => {
    const year = Number(birthYear);
    if (!Number.isInteger(year) || year < 1900 || year > CURRENT_YEAR) {
      setError("Introdu un an de naștere valid.");
      return;
    }
    if (!accepted) {
      setError("Trebuie să accepți politica și termenii.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await submitConsent(year, true);
    } finally {
      setBusy(false);
      await onResolved();
    }
  };

  return (
    <div className="account-overlay">
      <div className="account-card">
        <h2>Un pas rapid</h2>
        <p>Pentru a-ți salva progresul în cont, confirmă vârsta și acceptă regulile.</p>
        <label className="account-field">
          <span>Anul nașterii</span>
          <input
            type="number"
            inputMode="numeric"
            min={1900}
            max={CURRENT_YEAR}
            value={birthYear}
            onChange={(e) => setBirthYear(e.target.value)}
            placeholder="ex. 2005"
          />
        </label>
        <label className="account-check">
          <input
            type="checkbox"
            checked={accepted}
            onChange={(e) => setAccepted(e.target.checked)}
          />
          <span>
            Am citit și accept{" "}
            <a href="/legal/privacy" target="_blank" rel="noreferrer">
              Politica de confidențialitate
            </a>{" "}
            și{" "}
            <a href="/legal/terms" target="_blank" rel="noreferrer">
              Termenii
            </a>
            .
          </span>
        </label>
        <p className="account-muted">
          Copiii sub {minAge} ani au nevoie de acordul unui părinte.
        </p>
        {error && <p className="account-error">{error}</p>}
        <div className="account-actions">
          <button
            type="button"
            className="account-btn"
            onClick={async () => {
              await logout();
              await onResolved();
            }}
          >
            Renunță
          </button>
          <button
            type="button"
            className="account-btn account-btn--primary"
            onClick={submit}
            disabled={busy}
          >
            {busy ? "Se salvează…" : "Continuă"}
          </button>
        </div>
      </div>
    </div>
  );
}

function UserChip({ user, onChanged }: { user: AuthUser; onChanged: () => Promise<void> }) {
  const [open, setOpen] = useState(false);
  const initial = (user.name || user.email || "?").slice(0, 1).toUpperCase();

  return (
    <div className="account-bar">
      <button
        type="button"
        className="account-chip"
        onClick={() => setOpen((v) => !v)}
        aria-haspopup="menu"
        aria-expanded={open}
      >
        {user.avatar ? (
          <img className="account-avatar" src={user.avatar} alt="" />
        ) : (
          <span className="account-avatar account-avatar--letter">{initial}</span>
        )}
        <span className="account-name">{user.name}</span>
      </button>
      {open && (
        <div className="account-menu" role="menu">
          <a href="/legal/privacy" target="_blank" rel="noreferrer" role="menuitem">
            Confidențialitate
          </a>
          <a href="/legal/terms" target="_blank" rel="noreferrer" role="menuitem">
            Termeni
          </a>
          <button
            type="button"
            role="menuitem"
            onClick={async () => {
              await logout();
              await onChanged();
            }}
          >
            Ieși din cont
          </button>
          <button
            type="button"
            role="menuitem"
            className="account-menu__danger"
            onClick={async () => {
              if (!window.confirm("Ștergi definitiv contul și tot progresul salvat?")) return;
              await deleteAccount();
              await onChanged();
            }}
          >
            Șterge contul și datele
          </button>
        </div>
      )}
    </div>
  );
}
