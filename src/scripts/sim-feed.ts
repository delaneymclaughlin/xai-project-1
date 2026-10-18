/**
 * Simulated feed interactive (design.md 8.2, 8.3).
 * Selects among precomputed states only: nothing is recomputed here. All
 * strings, bar geometry and counterfactual orders arrive from build-time
 * JSON (#sim-feed-data, #sim-cf-data).
 */
import { readJson, prefersReducedMotion, announce, $, $$ } from "./lib/dom";
import { initListbox, setSwitch, isOn } from "./lib/controls";

interface RowState {
  l: number;
  w: number;
  neg: boolean;
  tl: number;
  t: string;
}
interface PostState {
  heading: string;
  scoreLine: string | null;
  baseLine: string | null;
  rows: Record<string, RowState>;
  order: Record<string, number>;
  her: string;
  design: string;
  total: string;
  announce: string;
}
interface FeedData {
  posts: Record<string, PostState>;
  origRanks: Record<string, number>;
  defaultName: string;
}
interface Meter {
  pct: number;
  text: string;
}
interface Cf {
  id: string;
  order: string[];
  ranks: Record<string, number>;
  sentence: string;
  meter: Meter | null;
  posts: Record<string, PostState> | null;
}
interface CfData {
  off: { sentence: string; meter: Meter };
  cfs: Cf[];
}

const EASE = "cubic-bezier(.2,.7,.2,1)";
const FLIP_MS = 400;
const OUTLINE_MS = 1000;

function init(root: HTMLElement) {
  const feed = readJson<FeedData>("sim-feed-data");
  const cfData = readJson<CfData>("sim-cf-data");

  const list = $<HTMLElement>("[data-feed-list]", root);
  const opts = () => $$<HTMLElement>('[role="option"]', list);
  const byName = new Map(opts().map((o) => [o.dataset.name as string, o]));
  const pane = $<HTMLElement>("[data-attr-pane]", root);
  const live = $<HTMLElement>("[data-feed-live]", root);
  const heading = $("[data-heading]", pane);
  const scoreline = $("[data-scoreline]", pane);
  const baseline = $("[data-baseline]", pane);
  const baseSep = $("[data-base-sep]", pane);
  const dimNote = $("[data-dim-note]", pane);
  const rows = new Map($$<HTMLElement>("[data-feature]", pane).map((r) => [r.dataset.feature as string, r]));
  const herEl = $("[data-her]", pane);
  const designEl = $("[data-design]", pane);
  const totalEl = $("[data-total]", pane);

  const resultEl = $("[data-cf-result]", root);
  const meterFill = $("[data-meter-fill]", root);
  const meterTop = $("[data-meter-top]", root);
  const switches = $$<HTMLElement>("[data-cf]", root);

  let selected = feed.defaultName;
  let active: Cf | null = null;
  let currentRanks: Record<string, number> = { ...feed.origRanks };

  /* ---- Attribution pane ---- */
  function renderPane() {
    const src = active?.posts ?? feed.posts;
    const st = src[selected] ?? feed.posts[selected];
    heading.textContent = st.heading;
    const hasScore = st.scoreLine !== null;
    scoreline.textContent = st.scoreLine ?? "";
    baseline.textContent = st.baseLine ?? "";
    baseSep.hidden = !hasScore;
    for (const [f, el] of rows) {
      const r = st.rows[f];
      if (!r) continue;
      el.style.order = String(st.order[f]);
      const bar = el.querySelector<HTMLElement>("[data-bar]");
      const val = el.querySelector<HTMLElement>("[data-val]");
      if (bar) {
        bar.style.left = `${r.l}%`;
        bar.style.width = `${r.w}%`;
        bar.toggleAttribute("data-neg", r.neg);
      }
      if (val) {
        val.style.left = `calc(${r.tl}% + 6px)`;
        val.textContent = r.t;
      }
    }
    herEl.textContent = st.her;
    designEl.textContent = st.design;
    totalEl.textContent = st.total;
    const dim = !!active && !active.posts;
    pane.toggleAttribute("data-dim", dim);
    dimNote.hidden = !dim;
  }

  function select(name: string, user: boolean) {
    selected = name;
    for (const [n, o] of byName) o.setAttribute("aria-selected", n === name ? "true" : "false");
    renderPane();
    if (!user) return;
    const st = (active?.posts ?? feed.posts)[name] ?? feed.posts[name];
    announce(live, st.announce);
    // Stacked layout: bring the attribution header into view only if it is off-screen.
    if (window.matchMedia("(max-width: 63.999rem)").matches) {
      heading.scrollIntoView({ block: "nearest", behavior: prefersReducedMotion() ? "auto" : "smooth" });
    }
  }

  initListbox(list, {
    orientation: "vertical",
    onSelect: (opt) => select(opt.dataset.name as string, true),
  });

  /* ---- Reorder (FLIP) ---- */
  function applyRanks(ranks: Record<string, number>, order: string[]) {
    const reduced = prefersReducedMotion();
    const hadFocus = list.contains(document.activeElement) ? (document.activeElement as HTMLElement) : null;
    const first = new Map(opts().map((o) => [o, o.getBoundingClientRect().top]));
    const prev = currentRanks;
    currentRanks = ranks;

    for (const name of order) {
      const o = byName.get(name);
      if (o) list.appendChild(o);
    }
    if (hadFocus && document.activeElement !== hadFocus) hadFocus.focus({ preventScroll: true });

    const showScores = order.every((n, i) => feed.origRanks[n] === i + 1);
    for (const [name, o] of byName) {
      const rank = ranks[name];
      $("[data-rank]", o).textContent = String(rank);
      const was = $("[data-was]", o);
      const orig = feed.origRanks[name];
      was.hidden = rank === orig;
      was.textContent = rank === orig ? "" : `was #${orig}`;
      $("[data-score]", o).hidden = !showScores;
    }

    for (const o of opts()) {
      const name = o.dataset.name as string;
      const moved = prev[name] !== ranks[name];
      if (!moved) continue;
      if (reduced) {
        o.setAttribute("data-changed", "");
        window.setTimeout(() => o.removeAttribute("data-changed"), OUTLINE_MS);
      } else {
        const dy = (first.get(o) ?? 0) - o.getBoundingClientRect().top;
        if (dy !== 0) o.animate([{ transform: `translateY(${dy}px)` }, { transform: "none" }], { duration: FLIP_MS, easing: EASE });
      }
    }
  }

  function setMeter(m: Meter) {
    meterFill.style.width = `${m.pct}%`;
    meterTop.textContent = m.text;
  }

  function setCf(next: Cf | null) {
    active = next;
    for (const b of switches) setSwitch(b, !!next && b.dataset.cf === next.id);
    if (next) {
      applyRanks(next.ranks, next.order);
      setMeter(next.meter ?? cfData.off.meter);
      resultEl.textContent = next.sentence;
    } else {
      const order = Object.entries(feed.origRanks)
        .sort((a, b) => a[1] - b[1])
        .map(([n]) => n);
      applyRanks(feed.origRanks, order);
      setMeter(cfData.off.meter);
      resultEl.textContent = cfData.off.sentence;
    }
    renderPane();
  }

  for (const b of switches) {
    b.addEventListener("click", () => {
      const cf = cfData.cfs.find((c) => c.id === b.dataset.cf) ?? null;
      setCf(isOn(b) ? null : cf);
    });
  }

  renderPane();
}

const root = document.querySelector<HTMLElement>("[data-sim-feed]");
if (root) init(root);
