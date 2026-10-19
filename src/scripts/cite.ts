// One shared tooltip for all citation markers: shows the source title on
// hover or keyboard focus, clamped to the viewport.
const tip = document.createElement("div");
tip.id = "cite-tip";
tip.hidden = true;
tip.setAttribute("aria-hidden", "true");
document.body.append(tip);

let current: HTMLElement | null = null;

function show(a: HTMLElement) {
  current = a;
  const n = a.textContent ?? "";
  tip.innerHTML = "";
  const b = document.createElement("b");
  b.textContent = `Source ${n}`;
  tip.append(b, document.createTextNode(a.dataset.cite ?? ""));
  tip.hidden = false;
  const r = a.getBoundingClientRect();
  const w = tip.offsetWidth;
  const h = tip.offsetHeight;
  let left = r.left + r.width / 2 - w / 2;
  left = Math.max(16, Math.min(left, window.innerWidth - w - 16));
  let top = r.top - h - 10;
  if (top < 12) top = r.bottom + 10;
  tip.style.left = `${left}px`;
  tip.style.top = `${top}px`;
}
function hide() {
  current = null;
  tip.hidden = true;
}

const isCite = (t: EventTarget | null) =>
  t instanceof Element ? (t.closest("a[data-cite]") as HTMLElement | null) : null;

document.addEventListener("pointerover", (e) => {
  const a = isCite(e.target);
  if (a && a !== current) show(a);
  else if (!a && current) hide();
});
document.addEventListener("focusin", (e) => {
  const a = isCite(e.target);
  if (a) show(a);
  else hide();
});
document.addEventListener("focusout", hide);
document.addEventListener("keydown", (e) => { if (e.key === "Escape") hide(); });
window.addEventListener("scroll", () => current && hide(), { passive: true });
