/**
 * Shared citation popover (design.md 8.6). Imported by Cite.astro and
 * Simulated.astro; Astro bundles it once per page.
 *
 * Markers are <a href="#src-S29" data-cite="S29" data-claims="2 5"> (no-JS
 * fallback: plain links). Simulated markers are <a data-sim-marker>.
 * One shared <div id="cite-pop" popover="auto"> lives in Layout.astro, and
 * the data comes from <script type="application/json" id="cite-data">.
 */
interface CiteData {
  sim: string;
  simSentence: string;
  sources: Record<string, { n: number; title: string; url: string | null; domain: string | null }>;
  claims: Record<string, { verdict: string; check: string }>;
}

let data: CiteData | null = null;
let trigger: HTMLElement | null = null;
let skipReturn = false;

function getData(): CiteData | null {
  if (data) return data;
  const el = document.getElementById("cite-data");
  if (!el?.textContent) return null;
  data = JSON.parse(el.textContent) as CiteData;
  return data;
}

function el<K extends keyof HTMLElementTagNameMap>(tag: K, cls?: string, text?: string): HTMLElementTagNameMap[K] {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text) e.textContent = text;
  return e;
}

function claimLines(pop: HTMLElement, d: CiteData, claimsAttr: string | undefined) {
  const ids = (claimsAttr ?? "").split(/\s+/).filter(Boolean);
  for (const id of ids) {
    const c = d.claims[id];
    const row = el("p", "cite-pop-claim");
    const a = el("a", undefined, `Claim ${id} in the ledger`);
    a.href = `#claim-${id}`;
    a.addEventListener("click", () => {
      skipReturn = true;
      pop.hidePopover();
    });
    row.append(a);
    if (c) row.append(el("span", "cite-pop-status", ` · ${c.verdict}`));
    pop.append(row);
  }
}

function fill(pop: HTMLElement, t: HTMLElement, d: CiteData) {
  pop.replaceChildren();
  const isSimMarker = t.hasAttribute("data-sim-marker");
  const srcId = t.dataset.cite;
  if (isSimMarker || srcId === d.sim) {
    const src = d.sources[d.sim];
    pop.append(el("p", "cite-pop-title", isSimMarker ? "Simulated" : `Source ${src?.n ?? ""}: ${src?.title ?? ""}`));
    pop.append(el("p", "cite-pop-body", d.simSentence));
  } else if (srcId) {
    const src = d.sources[srcId];
    if (!src) return;
    pop.append(el("p", "cite-pop-title", `Source ${src.n}: ${src.title}`));
    if (src.url) {
      const p = el("p", "cite-pop-body");
      const a = el("a", undefined, "Open source");
      a.href = src.url;
      a.target = "_blank";
      a.rel = "noopener";
      if (src.domain) a.append(el("span", "cite-pop-domain", ` ${src.domain}`));
      p.append(a);
      pop.append(p);
    } else {
      pop.append(el("p", "cite-pop-body", "No public link for this source; see the source list."));
    }
  }
  claimLines(pop, d, t.dataset.claims);
  const ground = t.closest("[data-ground]")?.getAttribute("data-ground");
  pop.dataset.ground = ground === "night" ? "night" : "day";
}

function position(pop: HTMLElement, t: HTMLElement) {
  const sheet = window.matchMedia("(width < 40rem)").matches;
  pop.classList.toggle("is-sheet", sheet);
  if (sheet) {
    pop.style.left = "";
    pop.style.top = "";
    return;
  }
  const r = t.getBoundingClientRect();
  const pw = pop.offsetWidth;
  const ph = pop.offsetHeight;
  const m = 16;
  const left = Math.min(Math.max(m, r.left - 12), window.innerWidth - pw - m);
  let top = r.bottom + 8;
  if (top + ph > window.innerHeight - m) top = Math.max(m, r.top - ph - 8);
  pop.style.left = `${left}px`;
  pop.style.top = `${top}px`;
}

function open(t: HTMLElement) {
  const pop = document.getElementById("cite-pop");
  const d = getData();
  if (!pop || !d || typeof pop.showPopover !== "function") return false;
  if (trigger === t && pop.matches(":popover-open")) {
    pop.hidePopover();
    return true;
  }
  fill(pop, t, d);
  trigger = t;
  pop.showPopover();
  t.setAttribute("aria-expanded", "true");
  position(pop, t);
  pop.querySelector<HTMLElement>("a")?.focus({ preventScroll: true }) ?? pop.focus({ preventScroll: true });
  return true;
}

function init() {
  const pop = document.getElementById("cite-pop");
  if (!pop || typeof pop.showPopover !== "function") return; // no Popover API: markers stay links

  for (const m of document.querySelectorAll<HTMLElement>("[data-cite], [data-sim-marker]")) {
    m.setAttribute("role", "button");
    m.setAttribute("aria-haspopup", "dialog");
    m.setAttribute("aria-expanded", "false");
    m.setAttribute("aria-controls", "cite-pop");
  }

  document.addEventListener("click", (e) => {
    const t = (e.target as Element).closest<HTMLElement>("[data-cite], [data-sim-marker]");
    if (!t) return;
    if (open(t)) e.preventDefault();
  });
  document.addEventListener("keydown", (e) => {
    if (e.key !== " ") return;
    const t = (e.target as Element).closest?.<HTMLElement>("[data-cite], [data-sim-marker]");
    if (t && open(t)) e.preventDefault();
  });
  pop.addEventListener("toggle", (e) => {
    if ((e as ToggleEvent).newState === "closed" && trigger) {
      trigger.setAttribute("aria-expanded", "false");
      const t = trigger;
      trigger = null;
      // return focus to the marker, unless the reader followed a ledger link
      if (!skipReturn) t.focus({ preventScroll: true });
      skipReturn = false;
    }
  });
  window.addEventListener("resize", () => {
    if (trigger && pop.matches(":popover-open")) position(pop, trigger);
  });
}

if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init, { once: true });
else init();
