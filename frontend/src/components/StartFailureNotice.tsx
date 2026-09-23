import { useLayoutEffect, useRef } from "react";

/** A failed new round remains visible until the player retries or resumes a game. */
export function StartFailureNotice({ failed, reserveSpace = false }: {
  failed?: boolean;
  reserveSpace?: boolean;
}) {
  const noticeRef = useRef<HTMLParagraphElement>(null);
  useLayoutEffect(() => {
    // Reveal the whole persistent message within its scroller, including when a
    // transient toast above the game later disappears. Keep the player's focus.
    if (failed) noticeRef.current?.scrollIntoView({ block: "nearest", inline: "nearest", behavior: "instant" });
  }, [failed]);

  if (!failed && !reserveSpace) return null;
  return (
    <p
      ref={noticeRef}
      className="card start-failure-notice"
      role={failed ? "alert" : undefined}
      aria-hidden={!failed || undefined}
      style={{ padding: 14, margin: 0, visibility: failed ? "visible" : "hidden" }}
    >
      Nu am putut porni jocul. Am păstrat opțiunile alese. Poți încerca din nou.
    </p>
  );
}
