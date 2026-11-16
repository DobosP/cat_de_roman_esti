import { useCallback, useState } from "preact/hooks";

export function useCoachMessage(initial: string | null = null) {
  const [[message, revision], setMessage] = useState<[string | null, number]>([initial, 0]);
  const announce = useCallback((text: string | null) => setMessage(([, next]) => [text, next + 1]), []);
  return [message, announce, revision] as const;
}
