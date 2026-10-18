/**
 * Cold open: the field of points (design.md 6.1).
 * One point per post Molly saved, liked or shared; a subset are lit, chosen by a
 * seeded shuffle so every visit shows the same field. Drawn once per container
 * width (no count-up, no twinkle). Counts come from build-time data.
 */
import { readJson, $ } from "./lib/dom";

interface FieldData {
  total: number;
  lit: number;
  label: string;
}

/** Small deterministic PRNG (mulberry32). */
function mulberry32(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** Seeded Fisher-Yates over indices; the first `lit` are the lit points. */
function pickLit(total: number, lit: number, seed: number): Uint8Array {
  const rand = mulberry32(seed);
  const idx = new Uint32Array(total);
  for (let i = 0; i < total; i++) idx[i] = i;
  for (let i = total - 1; i > 0; i--) {
    const j = Math.floor(rand() * (i + 1));
    const t = idx[i];
    idx[i] = idx[j];
    idx[j] = t;
  }
  const mask = new Uint8Array(total);
  for (let i = 0; i < Math.min(lit, total); i++) mask[idx[i]] = 1;
  return mask;
}

function init() {
  const canvas = document.getElementById("molly-field") as HTMLCanvasElement | null;
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  if (!ctx) return;
  const data = readJson<FieldData>("cold-open-data");
  const mask = pickLit(data.total, data.lit, 20171121);

  canvas.setAttribute("role", "img");
  canvas.setAttribute("aria-label", data.label);

  const wrap = canvas.parentElement as HTMLElement;
  const css = getComputedStyle(document.documentElement);
  const dotColor = css.getPropertyValue("--color-dot").trim() || "#8792A8";
  const litColor = css.getPropertyValue("--color-moon").trim() || "#DCE3F0";
  let lastKey = "";

  function draw() {
    const width = Math.floor(wrap.clientWidth);
    if (width < 1) return;
    const dpr = Math.max(1, window.devicePixelRatio || 1);
    // 2px dots with 2px gaps on desktop; 1px and 1px below 640px.
    const small = window.innerWidth < 640;
    const dot = small ? 1 : 2;
    const cell = dot * 2;
    const cols = Math.max(1, Math.floor(width / cell));
    const rows = Math.ceil(data.total / cols);
    const height = rows * cell;
    const key = `${width}|${dpr}|${dot}`;
    if (key === lastKey) return;
    lastKey = key;

    canvas!.width = Math.round(width * dpr);
    canvas!.height = Math.round(height * dpr);
    canvas!.style.width = `${width}px`;
    canvas!.style.height = `${height}px`;
    const c = ctx!;
    c.clearRect(0, 0, canvas!.width, canvas!.height);

    // Centre the grid horizontally in the leftover width.
    const offset = Math.floor((width - cols * cell + (cell - dot)) / 2);
    const px = Math.max(1, Math.round(dot * dpr));
    const place = (i: number) => {
      const col = i % cols;
      const row = Math.floor(i / cols);
      return [Math.round((offset + col * cell) * dpr), Math.round(row * cell * dpr)] as const;
    };

    c.globalAlpha = 0.35;
    c.fillStyle = dotColor;
    for (let i = 0; i < data.total; i++) {
      if (mask[i]) continue;
      const [x, y] = place(i);
      c.fillRect(x, y, px, px);
    }
    c.globalAlpha = 1;
    c.fillStyle = litColor;
    for (let i = 0; i < data.total; i++) {
      if (!mask[i]) continue;
      const [x, y] = place(i);
      c.fillRect(x, y, px, px);
    }
  }

  draw();
  let raf = 0;
  new ResizeObserver(() => {
    cancelAnimationFrame(raf);
    raf = requestAnimationFrame(draw);
  }).observe(wrap);
}

// Make sure the element exists before running (script is deferred as a module).
$("#cold-open");
init();
