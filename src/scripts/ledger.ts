/**
 * Claims ledger (design.md 8.7). Search (debounced 120ms), section and check
 * chips, live count, "Show all N claims", and #claim-N arrival (expand, scroll,
 * highlight). Everything is progressive: without JS every row is visible.
 */
import { announce, prefersReducedMotion } from "./lib/dom";
import { isPressed, setPressed } from "./lib/controls";

function init(root: HTMLElement): void {
  const controls = root.querySelector<HTMLElement>("[data-ledger-controls]");
  const search = root.querySelector<HTMLInputElement>("[data-ledger-search]");
  const countEl = root.querySelector<HTMLElement>("[data-ledger-count]");
  const clearBtn = root.querySelector<HTMLButtonElement>("[data-ledger-clear]");
  const emptyEl = root.querySelector<HTMLElement>("[data-ledger-empty]");
  const moreWrap = root.querySelector<HTMLElement>("[data-ledger-more]");
  const moreBtn = root.querySelector<HTMLButtonElement>("[data-ledger-showall]");
  const rows = Array.from(root.querySelectorAll<HTMLTableRowElement>("tbody tr[data-claim]"));
  const chips = Array.from(root.querySelectorAll<HTMLButtonElement>("button[data-filter]"));
  if (!controls || !search || !countEl || !moreWrap || !moreBtn || !rows.length) return;

  const PREVIEW = Number(root.dataset.preview) || 12;
  const total = rows.length;
  let expanded = false;
  let timer = 0;
  let targetRow: HTMLElement | null = null;
  let targetTimer = 0;

  controls.hidden = false;

  const selected = (kind: string) =>
    new Set(chips.filter((c) => c.dataset.filter === kind && isPressed(c)).map((c) => c.dataset.value ?? ""));

  const clearTarget = () => {
    window.clearTimeout(targetTimer);
    targetRow?.classList.remove("is-target");
    targetRow = null;
  };

  /** Matching rows for the current query and chips. */
  function matches(): HTMLTableRowElement[] {
    const q = search!.value.trim().toLowerCase();
    const terms = q.split(/\s+/).filter(Boolean);
    const secs = selected("section");
    const checks = selected("check");
    return rows.filter((r) => {
      if (secs.size && !secs.has(r.dataset.section ?? "")) return false;
      if (checks.size && !checks.has(r.dataset.check ?? "")) return false;
      const hay = r.dataset.search ?? "";
      return terms.every((t) => hay.includes(t));
    });
  }

  const filtersActive = () => search!.value.trim() !== "" || chips.some(isPressed);

  function apply(opts: { announceCount?: boolean } = {}): void {
    const hit = matches();
    const limit = expanded ? Infinity : PREVIEW;
    const shown = new Set(hit.slice(0, limit));
    for (const r of rows) r.hidden = !shown.has(r);

    const active = filtersActive();
    const more = hit.length > shown.size;
    moreWrap!.hidden = !more;
    moreBtn!.textContent = active ? `Show all ${hit.length} matching claims` : `Show all ${total} claims`;
    if (emptyEl) emptyEl.hidden = hit.length > 0;
    if (clearBtn) clearBtn.hidden = !active;

    const sentence = shown.size === total
      ? `Showing all ${total} claims`
      : `Showing ${shown.size} of ${total} claims${active ? `, ${hit.length} match` : ""}`;
    if (opts.announceCount) announce(countEl, sentence);
    else countEl!.textContent = sentence;
  }

  function expand(): void {
    expanded = true;
    moreBtn!.setAttribute("aria-expanded", "true");
  }

  function resetFilters(): void {
    search!.value = "";
    for (const c of chips) setPressed(c, false);
  }

  /* Controls */
  search.addEventListener("input", () => {
    window.clearTimeout(timer);
    timer = window.setTimeout(() => {
      clearTarget();
      apply({ announceCount: true });
    }, 120);
  });
  search.addEventListener("keydown", (e) => {
    if (e.key === "Enter") e.preventDefault();
  });
  for (const chip of chips) {
    chip.addEventListener("click", () => {
      clearTarget();
      setPressed(chip, !isPressed(chip));
      apply({ announceCount: true });
    });
  }
  moreBtn.addEventListener("click", () => {
    clearTarget();
    expand();
    apply({ announceCount: true });
    moreBtn.setAttribute("aria-expanded", "true");
  });
  clearBtn?.addEventListener("click", () => {
    clearTarget();
    resetFilters();
    apply({ announceCount: true });
    search.focus();
  });

  /* Arrival by hash */
  function reveal(row: HTMLTableRowElement): void {
    clearTarget();
    // A row hidden by search or chips would never be found: drop them.
    if (!matches().includes(row)) resetFilters();
    expand();
    apply();
    targetRow = row;
    row.classList.add("is-target");
    requestAnimationFrame(() => {
      row.scrollIntoView({ block: "center", behavior: prefersReducedMotion() ? "auto" : "smooth" });
    });
    // 2s highlight; under reduced motion it stays until the next interaction.
    if (!prefersReducedMotion()) {
      targetTimer = window.setTimeout(() => {
        row.classList.remove("is-target");
        if (targetRow === row) targetRow = null;
      }, 2000);
    }
  }

  function fromHash(): void {
    const m = /^#claim-(\d+)$/.exec(window.location.hash);
    if (!m) return;
    const row = root.querySelector<HTMLTableRowElement>(`tbody tr[data-claim="${m[1]}"]`);
    if (row) reveal(row);
  }

  // Links to the same hash do not fire hashchange; handle clicks on claim links too.
  document.addEventListener("click", (e) => {
    const a = (e.target as Element | null)?.closest<HTMLAnchorElement>('a[href^="#claim-"]');
    if (!a) return;
    const row = root.querySelector<HTMLTableRowElement>(`tbody tr[data-claim="${a.getAttribute("href")!.slice(7)}"]`);
    if (row && window.location.hash === a.getAttribute("href")) {
      e.preventDefault();
      reveal(row);
    }
  });
  window.addEventListener("hashchange", fromHash);

  apply();
  if (/^#claim-\d+$/.test(window.location.hash)) {
    // after layout settles so the scroll lands correctly
    requestAnimationFrame(fromHash);
  }
}

document.querySelectorAll<HTMLElement>("[data-ledger]").forEach(init);
