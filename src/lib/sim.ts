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
  limeRuns: sim.lime_top_reason_runs.display,
  limeReruns: sim.lime_reruns.display,
  limeFit: sim.lime_local_fit_pct.display,
  faithTop: sim.faith_drop_topk.display,
  faithRandom: sim.faith_drop_random.display,
  top3Pct: sim.shap_top3_share_pct.display,
  cfRankNoHistory: sim.cf_rank_no_history.display,
  cfIntensityFrom: sim.cf_intensity_from.display,
  cfIntensityTo: sim.cf_intensity_to.display,
};

/** Rounded "N in 100" forms; the exact figure is always shown next to them. */
export const per100 = (pct: string) => Math.round(Number(pct));

/** Plain-language phrases for each signal, for generated sentences. */
export const plainLabels: Record<Feature, string> = {
  topic_history: "her past engagement with this topic",
  emotional_intensity: "how emotionally intense the post is",
  reactions: "how many reactions it has",
  comment_rate: "how often people comment",
  watch_completion: "how much of it people watch",
  from_followed: "whether she follows the account",
  hours_old: "how long ago it was posted",
};

/** The model's average score (SHAP base value). Scores are stored to 3 d.p.,
 * so per-post derivations differ by <0.001; show their mean. */
export const baseline = posts.reduce((a, p) => a + p.base, 0) / posts.length;
