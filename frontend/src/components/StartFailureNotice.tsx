/** A failed new round remains visible until the player retries or resumes a game. */
export function StartFailureNotice({ failed, reserveSpace = false }: {
  failed?: boolean;
  reserveSpace?: boolean;
}) {
  if (!failed && !reserveSpace) return null;
  return (
    <p
      className="card start-failure-notice"
      role={failed ? "alert" : undefined}
      aria-hidden={!failed || undefined}
      style={{ padding: 14, margin: 0, visibility: failed ? "visible" : "hidden" }}
    >
      Nu am putut porni jocul. Am păstrat opțiunile alese. Poți încerca din nou.
    </p>
  );
}
