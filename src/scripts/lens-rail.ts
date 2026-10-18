/** Lens rail: marks the lens section containing the 40% viewport line, drives the mobile name bar. */
import { $$ } from "./lib/dom";

function init(): void {
  const root = document.querySelector<HTMLElement>("[data-lens-rail]");
  if (!root) return;
  const ids = (root.dataset.ids ?? "").split(" ").filter(Boolean);
  const sections = ids.map((id) => document.getElementById(id)).filter((e): e is HTMLElement => !!e);
  if (!sections.length) return;

  const links = $$<HTMLAnchorElement>("[data-lens-link]", root);
  const bar = document.querySelector<HTMLElement>("[data-lens-bar]");
  const barName = bar?.querySelector<HTMLElement>("[data-lens-bar-name]") ?? null;
  const thesis = document.getElementById("thesis");

  let active: string | null = null;
  let thesisGone = false;

  const render = (): void => {
    for (const a of links) {
      if (a.dataset.lensLink === active) a.setAttribute("aria-current", "true");
      else a.removeAttribute("aria-current");
    }
    if (bar && barName) {
      const link = links.find((a) => a.dataset.lensLink === active);
      barName.textContent = link?.textContent ?? "";
      bar.dataset.show = String(thesisGone && !!active);
    }
  };

  // A thin band at the 40% line: the section intersecting it is the active one.
  const inLine = new Set<string>();
  const lineObs = new IntersectionObserver(
    (entries) => {
      for (const e of entries) {
        if (e.isIntersecting) inLine.add(e.target.id);
        else inLine.delete(e.target.id);
      }
      active = ids.find((id) => inLine.has(id)) ?? null;
      render();
    },
    { rootMargin: "-40% 0px -60% 0px", threshold: 0 },
  );
  sections.forEach((s) => lineObs.observe(s));

  if (thesis) {
    new IntersectionObserver(
      ([e]) => {
        thesisGone = !e.isIntersecting && e.boundingClientRect.bottom <= 0;
        render();
      },
      { threshold: 0 },
    ).observe(thesis);
  }
  render();
}

init();
