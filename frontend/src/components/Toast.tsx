import { AnimatePresence, motion } from "framer-motion";

export type ToastKind = "error" | "info" | "success";

export interface ToastData {
  id: number;
  kind: ToastKind;
  message: string;
}

const ACCENT: Record<ToastKind, string> = {
  error: "var(--bad)",
  info: "var(--accent)",
  success: "var(--good)",
};

const ICON: Record<ToastKind, string> = {
  error: "!",
  info: "i",
  success: "✓",
};

/** Stacked, auto-animated toast overlay. The host owns the list + dismissal timers. */
export function ToastStack({
  toasts,
  onDismiss,
}: {
  toasts: ToastData[];
  onDismiss: (id: number) => void;
}) {
  return (
    <div
      style={{
        position: "fixed",
        top: 20,
        left: "50%",
        transform: "translateX(-50%)",
        display: "flex",
        flexDirection: "column",
        gap: 10,
        zIndex: 1000,
        pointerEvents: "none",
        width: "min(440px, calc(100vw - 32px))",
      }}
    >
      <AnimatePresence initial={false}>
        {toasts.map((t) => (
          <motion.div
            key={t.id}
            layout
            initial={{ opacity: 0, y: -24, scale: 0.94 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -16, scale: 0.96 }}
            transition={{ type: "spring", stiffness: 420, damping: 30 }}
            onClick={() => onDismiss(t.id)}
            role="status"
            style={{
              pointerEvents: "auto",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: 12,
              padding: "12px 16px",
              borderRadius: 14,
              background: "var(--surface-strong)",
              border: `1px solid ${ACCENT[t.kind]}`,
              boxShadow: `0 0 28px -8px ${ACCENT[t.kind]}, var(--shadow-pop)`,
              backdropFilter: "blur(16px)",
            }}
          >
            <span
              aria-hidden
              style={{
                flex: "0 0 auto",
                width: 22,
                height: 22,
                borderRadius: "50%",
                display: "grid",
                placeItems: "center",
                fontWeight: 800,
                fontSize: 13,
                color: "#0a0b14",
                background: ACCENT[t.kind],
              }}
            >
              {ICON[t.kind]}
            </span>
            <span style={{ fontSize: "0.92rem", fontWeight: 500 }}>
              {t.message}
            </span>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}
