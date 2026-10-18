/** Shared client helpers. Import from section scripts; do not edit per section. */

/** Read build-time data emitted by <JsonData id="..."/>. */
export function readJson<T>(id: string): T {
  const el = document.getElementById(id);
  if (!el?.textContent) throw new Error(`readJson: #${id} not found`);
  return JSON.parse(el.textContent) as T;
}

const REDUCED = "(prefers-reduced-motion: reduce)";

/** True when the reader prefers reduced motion. Check before every animation. */
export function prefersReducedMotion(): boolean {
  return window.matchMedia(REDUCED).matches;
}

/** Call `fn` whenever the reduced-motion preference changes. Returns an unsubscribe. */
export function onReducedMotionChange(fn: (reduced: boolean) => void): () => void {
  const mq = window.matchMedia(REDUCED);
  const h = (e: MediaQueryListEvent) => fn(e.matches);
  mq.addEventListener("change", h);
  return () => mq.removeEventListener("change", h);
}

/** Set a polite live region's text (one sentence per action). */
export function announce(region: Element | null, sentence: string): void {
  if (!region) return;
  region.textContent = "";
  // next frame so identical sentences are re-announced
  requestAnimationFrame(() => (region.textContent = sentence));
}

/** querySelector that throws instead of returning null. */
export function $<T extends Element = HTMLElement>(sel: string, root: ParentNode = document): T {
  const el = root.querySelector<T>(sel);
  if (!el) throw new Error(`$: ${sel} not found`);
  return el;
}
export const $$ = <T extends Element = HTMLElement>(sel: string, root: ParentNode = document): T[] =>
  Array.from(root.querySelectorAll<T>(sel));
