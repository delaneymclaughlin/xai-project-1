/** State helpers for the shared Chip / Toggle controls and a roving-tabindex listbox. */

/** Chip: aria-pressed on/off. */
export function setPressed(btn: HTMLElement, on: boolean): void {
  btn.setAttribute("aria-pressed", on ? "true" : "false");
}
export const isPressed = (btn: HTMLElement) => btn.getAttribute("aria-pressed") === "true";

/** Toggle (role="switch"): aria-checked plus its visible "On"/"Off" state line. */
export function setSwitch(btn: HTMLElement, on: boolean): void {
  btn.setAttribute("aria-checked", on ? "true" : "false");
  const state = btn.querySelector("[data-toggle-state]");
  if (state) state.textContent = on ? "On" : "Off";
}
export const isOn = (btn: HTMLElement) => btn.getAttribute("aria-checked") === "true";

export interface ListboxOptions {
  orientation?: "horizontal" | "vertical";
  /** Called on Enter/Space/click. Focus stays where it is. */
  onSelect: (option: HTMLElement, index: number) => void;
}

/**
 * Roving-tabindex listbox (design.md 8.1, 8.2). `root` has role="listbox";
 * options are [role="option"] children. Options with aria-disabled="true" are
 * skipped by arrow keys. Arrow keys move focus; Enter/Space/click select.
 * Returns a function to programmatically move the tab stop.
 */
export function initListbox(root: HTMLElement, opts: ListboxOptions): { focusIndex: (i: number) => void } {
  const options = () => Array.from(root.querySelectorAll<HTMLElement>('[role="option"]'));
  const enabled = () => options().filter((o) => o.getAttribute("aria-disabled") !== "true");
  const setStop = (target: HTMLElement) => {
    for (const o of options()) o.tabIndex = o === target ? 0 : -1;
  };
  const initial = options().find((o) => o.getAttribute("aria-selected") === "true") ?? enabled()[0];
  if (initial) setStop(initial);

  const prev = opts.orientation === "horizontal" ? "ArrowLeft" : "ArrowUp";
  const next = opts.orientation === "horizontal" ? "ArrowRight" : "ArrowDown";

  root.addEventListener("keydown", (e) => {
    const list = enabled();
    const current = document.activeElement as HTMLElement | null;
    const i = current ? list.indexOf(current) : -1;
    let target: HTMLElement | undefined;
    if (e.key === next) target = list[Math.min(list.length - 1, i + 1)];
    else if (e.key === prev) target = list[Math.max(0, i - 1)];
    else if (e.key === "Home") target = list[0];
    else if (e.key === "End") target = list[list.length - 1];
    else if ((e.key === "Enter" || e.key === " ") && current && i >= 0) {
      e.preventDefault();
      opts.onSelect(current, options().indexOf(current));
      return;
    }
    if (target) {
      e.preventDefault();
      setStop(target);
      target.focus();
    }
  });
  root.addEventListener("click", (e) => {
    const opt = (e.target as HTMLElement).closest<HTMLElement>('[role="option"]');
    if (!opt || !root.contains(opt) || opt.getAttribute("aria-disabled") === "true") return;
    setStop(opt);
    opts.onSelect(opt, options().indexOf(opt));
  });
  return {
    focusIndex(i: number) {
      const o = options()[i];
      if (o) setStop(o);
    },
  };
}
