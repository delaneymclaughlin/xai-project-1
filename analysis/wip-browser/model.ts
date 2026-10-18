/**
 * In-browser evaluation of the simulation's XGBoost regressors and EXACT
 * interventional Shapley values.
 *
 * Data: src/data/model.json, written by analysis/run.py. Each tree is stored as
 * parallel node arrays: f = split feature index (-1 = leaf), t = threshold (go
 * left if x < t) or, at a leaf, the leaf value; l/r = child node indices.
 * XGBoost compares in float32, so inputs and thresholds go through Math.fround.
 *
 * Shapley values: for a model with n features, v(S) = mean over the background
 * rows b of f(x_S, b_~S), computed for all 2^n coalitions, then
 * phi_i = sum over S not containing i of |S|!(n-|S|-1)!/n! * (v(S+i) - v(S)).
 * This is the same quantity shap.TreeExplainer computes with
 * feature_perturbation="interventional"; analysis/parity.mjs checks agreement.
 *
 * Erasable TypeScript only (no enums/namespaces), so Node can run it directly.
 */

export interface Tree {
  f: number[];
  t: number[];
  l: number[];
  r: number[];
}

export interface TreeModel {
  features: string[];
  base_score: number;
  trees: Tree[];
  removed?: string;
}

export interface ModelBundle {
  about: string;
  seed: number;
  units: string;
  full: TreeModel;
  ablation: TreeModel;
  background: { features: string[]; rows: number[][] };
}

interface Compiled {
  features: string[];
  base: number;
  trees: { f: Int32Array; t: Float64Array; l: Int32Array; r: Int32Array }[];
}

const cache = new WeakMap<TreeModel, Compiled>();

function compile(m: TreeModel): Compiled {
  let c = cache.get(m);
  if (!c) {
    c = {
      features: m.features,
      base: Math.fround(m.base_score),
      trees: m.trees.map((tr) => ({
        f: Int32Array.from(tr.f),
        t: Float64Array.from(tr.t, (v) => Math.fround(v)),
        l: Int32Array.from(tr.l),
        r: Int32Array.from(tr.r),
      })),
    };
    cache.set(m, c);
  }
  return c;
}

function evalCompiled(c: Compiled, x: ArrayLike<number>): number {
  let s = c.base;
  for (const tr of c.trees) {
    let n = 0;
    while (tr.f[n] !== -1) n = Math.fround(x[tr.f[n]]) < tr.t[n] ? tr.l[n] : tr.r[n];
    s += tr.t[n];
  }
  return s;
}

/** Model output for one row given in the model's own feature order. */
export function predict(model: TreeModel, x: ArrayLike<number>): number {
  return evalCompiled(compile(model), x);
}

/** Build a row in the model's feature order from a {feature: value} record. */
export function rowFor(model: TreeModel, rec: Record<string, number>): number[] {
  return model.features.map((f) => {
    const v = rec[f];
    if (typeof v !== "number") throw new Error(`model.ts: missing feature ${f}`);
    return v;
  });
}

/** Background rows projected onto the model's features. */
export function backgroundFor(model: TreeModel, bundle: Pick<ModelBundle, "background">): number[][] {
  const idx = model.features.map((f) => bundle.background.features.indexOf(f));
  if (idx.some((i) => i < 0)) throw new Error("model.ts: background lacks a model feature");
  return bundle.background.rows.map((row) => idx.map((i) => row[i]));
}

/** v(S) for every coalition mask S (bit i = feature i present). */
export function coalitionValues(model: TreeModel, x: ArrayLike<number>, background: number[][]): Float64Array {
  const c = compile(model);
  const n = c.features.length;
  const size = 1 << n;
  const v = new Float64Array(size);
  const z = new Float64Array(n);
  for (let mask = 0; mask < size; mask++) {
    let sum = 0;
    for (const b of background) {
      for (let i = 0; i < n; i++) z[i] = mask & (1 << i) ? x[i] : b[i];
      sum += evalCompiled(c, z);
    }
    v[mask] = sum / background.length;
  }
  return v;
}

export interface ShapResult {
  /** E[f(b)] over the background: the "average prediction". */
  base: number;
  /** f(x). Equals base + sum(phi) exactly (up to float rounding). */
  value: number;
  phi: Record<string, number>;
}

/** Exact interventional Shapley values over all 2^n coalitions. */
export function shapley(model: TreeModel, x: ArrayLike<number>, background: number[][]): ShapResult {
  const n = model.features.length;
  const v = coalitionValues(model, x, background);
  const fact = [1];
  for (let k = 1; k <= n; k++) fact[k] = fact[k - 1] * k;
  const phi = new Float64Array(n);
  for (let mask = 0; mask < 1 << n; mask++) {
    let s = 0;
    for (let m = mask; m; m &= m - 1) s++;
    const w = (fact[s] * fact[n - s - 1]) / fact[n];
    for (let i = 0; i < n; i++) if (!(mask & (1 << i))) phi[i] += w * (v[mask | (1 << i)] - v[mask]);
  }
  const out: Record<string, number> = {};
  model.features.forEach((f, i) => (out[f] = phi[i]));
  return { base: v[0], value: v[(1 << n) - 1], phi: out };
}

/** Rank (1 = top) of each row's score; ties keep input order. */
export function rankScores(scores: number[]): number[] {
  const order = scores.map((s, i) => [s, i] as const).sort((a, b) => b[0] - a[0] || a[1] - b[1]);
  const ranks = new Array<number>(scores.length);
  order.forEach(([, i], k) => (ranks[i] = k + 1));
  return ranks;
}
