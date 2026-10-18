// Parity check: the browser logic in src/lib/model.ts must reproduce the Python
// scores (xgboost .predict) and SHAP values (shap.TreeExplainer, interventional)
// within 1e-6. Run from the repo root:  node analysis/parity.mjs
// (Node >= 22.18 strips TypeScript types natively.)
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { predict, shapley, backgroundFor } from "../src/lib/model.ts";

const here = dirname(fileURLToPath(import.meta.url));
const bundle = JSON.parse(readFileSync(join(here, "..", "src", "data", "model.json"), "utf8"));
const fx = JSON.parse(readFileSync(join(here, "out", "parity_fixture.json"), "utf8"));
const demo = JSON.parse(readFileSync(join(here, "..", "src", "data", "demo.json"), "utf8"));
const TOL = 1e-6;
let worst = 0;
let failures = 0;

function check(label, got, want) {
  const d = Math.abs(got - want);
  worst = Math.max(worst, d);
  if (!(d <= TOL)) {
    failures++;
    if (failures <= 10) console.error(`FAIL ${label}: ts=${got} py=${want} |d|=${d}`);
  }
}

const t0 = performance.now();
for (const which of ["full", "ablation"]) {
  const model = bundle[which];
  const bg = backgroundFor(model, bundle);
  const idx = model.features.map((f) => bundle.background.features.indexOf(f));
  const ref = fx[which];
  fx.rows.forEach((row, k) => {
    const x = idx.map((i) => row[i]);
    check(`${which} score row ${k}`, predict(model, x), ref.scores[k]);
    const s = shapley(model, x, bg);
    check(`${which} base row ${k}`, s.base, ref.base);
    model.features.forEach((f, j) => check(`${which} shap row ${k} ${f}`, s.phi[f], ref.shap[k][j]));
    // Additivity against an independent evaluation of the trees, not against
    // the coalition value v(full) that the Shapley sum is built from.
    const add = s.base + Object.values(s.phi).reduce((a, b) => a + b, 0);
    check(`${which} additivity row ${k}`, add, predict(model, x));
  });
}
// demo.json consistency (its scores are rounded to 4 dp for display)
const full = bundle.full;
const bgFull = backgroundFor(full, bundle);
for (const p of demo.feed) {
  const x = full.features.map((f) => p.features[f]);
  const sc = predict(full, x);
  if (Math.abs(sc - p.score) > 5e-5) { failures++; console.error(`FAIL demo score ${p.name}: ${sc} vs ${p.score}`); }
  const s = shapley(full, x, bgFull);
  for (const f of full.features) check(`demo shap ${p.name} ${f}`, s.phi[f], demo.shap.per_post[p.name][f]);
}
const ms = performance.now() - t0;
const nRows = fx.rows.length;
console.log(`parity: ${nRows} rows x 2 models + ${demo.feed.length} demo posts; max |ts - py| = ${worst.toExponential(2)}; tol ${TOL}; ${ms.toFixed(0)} ms`);
if (failures) {
  console.error(`parity FAILED (${failures} mismatches)`);
  process.exit(1);
}
console.log("parity OK");
