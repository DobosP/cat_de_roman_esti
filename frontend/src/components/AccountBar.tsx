// AccountBar — the fixed top-right cluster: Donează (if configured), Clasament link
// (when accounts are on), and the account affordance (Sign in with Google → RO age-16
// consent gate → signed-in chip). Renders one useAuth() for the whole bar.
//
// Anonymous/offline play is never gated: you only need an account to APPEAR on the ranking.
// When accounts are disabled the bar shows just the Donează button (if a URL is set).

import { useState } from "react";
import { Link } from "react-router-dom";
import {
  type AuthUser,
  deleteAccount,
  loginWithGoogle,
  logout,
  submitConsent,
  updateProfile,
} from "../api/auth";
import { useAuth } from "../hooks/useAuth";

const CURRENT_YEAR = new Date().getFullYear();

export default function AccountBar() {
  const { me, loading, refresh } = useAuth();
  if (loading || !me) return null;

  const donate = me.donate_url ? (
    <a
      className="account-btn account-btn--donate"
      href={me.donate_url}
      target="_blank"
      rel="noreferrer"
    >
      ♥ Donează
    </a>
  ) : null;

  const ranking = me.accounts_enabled ? (
    <Link className="account-btn" to="/clasament">
      🏆 Clasament
    </Link>
  ) : null;

  return (
    <div className="account-bar">
      {donate}
      {ranking}
      {me.accounts_enabled && <AccountSection me={me} refresh={refresh} />}
    </div>
  );
}

function AccountSection({
  me,
  refresh,
}: {
  me: { authenticated: boolean; user: AuthUser | null; min_self_consent_age?: number };
  refresh: () => Promise<void>;
}) {
  if (!me.authenticated || !me.user) {
    return (
      <button type="button" className="account-btn account-btn--google" onClick={loginWithGoogle}>
        Intră cu Google
      </button>
    );
  }
  const user = me.user;
  if (!user.consent_completed) {
    if (user.parental_consent_required) return <RestrictedNotice onLogout={refresh} />;
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
          un cont. Poți juca în continuare fără cont — nu apari însă în clasament.
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
  const [handle, setHandle] = useState("");
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
      await submitConsent(year, true, handle.trim());
    } finally {
      setBusy(false);
      await onResolved();
    }
  };

  return (
    <div className="account-overlay">
      <div className="account-card">
        <h2>Un pas rapid</h2>
        <p>Ca să apari în clasament, confirmă vârsta, alege un nume și acceptă regulile.</p>
        <label className="account-field">
          <span>Numele din clasament (poți folosi o poreclă)</span>
          <input
            type="text"
            maxLength={80}
            value={handle}
            onChange={(e) => setHandle(e.target.value)}
            placeholder="ex. VulpeaIsteata"
          />
        </label>
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
          <input type="checkbox" checked={accepted} onChange={(e) => setAccepted(e.target.checked)} />
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
        <p className="account-muted">Copiii sub {minAge} ani au nevoie de acordul unui părinte.</p>
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
  const initial = (user.ranking_name || user.name || "?").slice(0, 1).toUpperCase();

  const editName = async () => {
    const next = window.prompt("Numele afișat în clasament:", user.ranking_name);
    if (next === null || !next.trim()) return;
    await updateProfile({ display_name: next.trim() });
    await onChanged();
  };

  const toggleRanking = async () => {
    await updateProfile({ show_on_ranking: !user.show_on_ranking });
    await onChanged();
  };

  return (
    <div className="account-anchor">
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
        <span className="account-name">{user.ranking_name}</span>
      </button>
      {open && (
        <div className="account-menu" role="menu">
          <button type="button" role="menuitem" onClick={editName}>
            Editează numele
          </button>
          <button type="button" role="menuitem" onClick={toggleRanking}>
            {user.show_on_ranking ? "Ascunde-mă din clasament" : "Apari în clasament"}
          </button>
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
