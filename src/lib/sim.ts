/**
 * Adapter for the precomputed simulation (S28). Nothing here recomputes the
 * model: it only reshapes demo.json / sim.json for display, and checks that
 * the derived shares match the published figures.
 */
import demo from "../data/demo.json";
import sim from "../data/sim.json";

export type Feature = keyof typeof demo.feature_labels;
export const featureLabels = demo.feature_labels as Record<Feature, string>;
export const FEATURES = Object.keys(featureLabels) as Feature[];

/** The signal the platform-style reason describes, and the one it leaves out. */
export const TOLD: Feature = "topic_history";
export const HIDDEN_TOP = demo.completeness.shap_top_reason as Feature;

export interface Post {
  name: string;
  id: string;
  title: string;
  distress: boolean;
  rank: number;
  cfRank: number;
  score: number;
  base: number;
  shap: { f: Feature; v: number }[];
}

const shapAll = demo.shap.per_post as Record<string, Record<Feature, number>>;
const cfRanks = new Map(demo.counterfactuals.design_side.new_feed.map((p) => [p.name, p.rank]));

export const posts: Post[] = demo.feed.map((p) => {
  const s = shapAll[p.name];
  const sum = FEATURES.reduce((a, f) => a + s[f], 0);
  return {
    name: p.name,
    id: p.name.replace(/\s+/g, "-").toLowerCase(),
    title: p.title,
    distress: p.distress_related,
    rank: p.rank,
    cfRank: cfRanks.get(p.name) ?? p.rank,
    score: p.score,
    base: p.score - sum,
    shap: FEATURES.map((f) => ({ f, v: s[f] })).sort((a, b) => Math.abs(b.v) - Math.abs(a.v)),
  };
});

/** Largest absolute attribution across all posts, for one shared bar scale. */
export const shapMax = Math.max(...posts.flatMap((p) => p.shap.map((x) => Math.abs(x.v))));

export const topPost = posts.find((p) => p.name === demo.top_post)!;

/** Each signal's share of the top post's total absolute attribution. */
const absTotal = topPost.shap.reduce((a, x) => a + Math.abs(x.v), 0);
export const topShares = topPost.shap.map((x) => ({ f: x.f, pct: (Math.abs(x.v) / absTotal) * 100 }));

const toldPct = topShares.find((x) => x.f === TOLD)!.pct;
if (Math.abs(toldPct - demo.completeness.platform_style_reason_share_pct) > 0.05) {
  throw new Error(`Told share ${toldPct} does not match ${demo.completeness.platform_style_reason_share_pct}`);
}

export const stats = {
  impressions: sim.n_impressions.display,
  age: sim.persona_age.display,
  shareAll: sim.distress_share_all_pct.display,
  shareTop: sim.distress_share_top_decile_pct.display,
  shareTopNoIntensity: sim.distress_share_top_decile_no_intensity_pct.display,
  toldPct: demo.completeness.platform_style_reason_share_pct.toFixed(1),
  untoldPct: demo.completeness.left_out_of_platform_reason_pct.toFixed(1),
  platformReason: demo.completeness.platform_style_reason,
};
