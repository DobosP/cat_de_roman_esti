import { useMemo } from "preact/hooks";

function eventValue<T>(initial: T) {
  let value = initial;
  return {
    read: () => value,
    write: (next: T) => { value = next; },
  };
}

/** Callback-owned data with a stable identity. Presentation reads component state. */
export function useEventValue<T>(initial: T) {
  return useMemo(() => eventValue(initial), [initial]);
}
