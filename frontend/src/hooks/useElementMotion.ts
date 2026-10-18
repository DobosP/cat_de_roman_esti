import type { RefObject } from "preact";
import { useLayoutEffect } from "preact/hooks";
import { animate } from "motion/mini";
import { spring } from "motion";
import { motionAllowed, type PresenceKeyframes, type PresenceTransition } from "@roedu/ui/motion";

/** Own one actual-element WAAPI animation; no layout or presence implementation. */
export function useElementMotion<T extends HTMLElement>(ref: RefObject<T | null>, frames: PresenceKeyframes | false,
  transition: PresenceTransition, dependencies: readonly unknown[]) {
  useLayoutEffect(() => {
    const element = ref.current;
    if (!element || !frames) return;
    const allowed = motionAllowed(element);
    const options = !allowed ? { duration: 0 } : "spring" in transition
      ? { type: spring, ...transition.spring } : { duration: transition.durationMs / 1000 };
    const previous = Object.keys(frames).map((key) => ({ key, value: element.style.getPropertyValue(key), priority: element.style.getPropertyPriority(key) }));
    const control = animate(element, frames, options);
    const finish = () => { if (!motionAllowed(element)) control.complete(); };
    const media = matchMedia("(prefers-reduced-motion: reduce)");
    media.addEventListener("change", finish);
    const observer = new MutationObserver(finish);
    observer.observe(document.documentElement, { attributes: true, subtree: true, attributeFilter: ["data-motion"] });
    let released = false;
    const dispose = () => {
      if (released) return;
      released = true; media.removeEventListener("change", finish); observer.disconnect();
      // Return completed tracks to authored CSS, so a later depleted/disabled
      // class cannot be overridden by a committed inline opacity or transform.
      for (const item of previous) {
        if (item.value) element.style.setProperty(item.key, item.value, item.priority);
        else element.style.removeProperty(item.key);
      }
    };
    void control.then(dispose);
    return () => { control.cancel(); dispose(); };
  }, dependencies);
}
