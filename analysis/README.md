# Feed simulation (source S28)

A small, seeded and deterministic simulation that replaces the precomputed demo with a real model. The site's SHAP values, feed scores and counterfactuals all come from this model.

```
uv run python analysis/run.py      # from the repo root; about 60-70 s on an M-series laptop
node analysis/parity.mjs           # checks src/lib/model.ts against the Python numbers (tol 1e-6)
```

If the active Python lacks the dependencies, `run.py` re-executes itself with `uv run --project analysis`. Dependencies are pinned in `uv.lock`: numpy, pandas, xgboost, shap, lime and scikit-learn (scipy comes with scikit-learn). There are no downloads and no LLM calls.

## Outputs

| file | contents |
|---|---|
| `src/data/sim.json` | every `{{sim.*}}` token, same keys as before, filled from seed 0. New detail goes under `extra` (metrics, checks, CIs over seeds). |
| `src/data/demo.json` | same shape as before: the feed and its scores, per-post SHAP plus `base_value`, completeness, and the design-side and user-side counterfactual feeds. |
| `src/data/model.json` | both XGBoost models as node arrays, plus the 100-row SHAP background. |
| `src/lib/model.ts` | tree evaluation and exact interventional Shapley values (all 2^n coalitions over the background), run in the browser. |
| `analysis/out/results.json` | every number for every seed. |
| `analysis/out/parity_fixture.json` | the Python scores and SHAP values that `parity.mjs` compares against. |
| `analysis/out/timing.json` | wall time. |
| `reports/numbers-diff.md` | old vs. new value for every number, and each original qualitative finding marked HOLDS or CHANGED. |
| `analysis/baseline/*.precomputed.json` | frozen copies of the original precomputed `sim.json` and `demo.json`, used for the diff. |

## Engagement value: X's published weights

Ground truth is a weighted sum of simulated per-action outcomes. The weights come from `xai-org/x-algorithm`, file `home-mixer/params/param.rs`, at commit `862a1235` (2026-10-17), as recorded in `docs/research/grounding.md` section 5:

| action (X name) | simulated as | weight |
|---|---|---|
| favorite | like, Bernoulli | 0.66 |
| reply | reply/comment, Bernoulli | 5.0 |
| retweet | repost, Bernoulli | 1.0 |
| share | share, Bernoulli | 2.0 |
| dwell | dwell (yes/no), Bernoulli | 0.05 |
| cont. dwell time | seconds of dwell | 0.006 per second |

`value = 0.66*fav + 5*reply + 1*repost + 2*share + 0.05*dwell + 0.006*dwell_seconds`

The simulation leaves out several things:
- the bidirectional-follow reply boost (+15), because there are no mutual follows in the simulation;
- share via DM (5.0) and copy link (20.0);
- quote, click, profile, photo and video actions;
- every negative action (not interested, mute, block, report);
- X's post-score adjustments: author-diversity decay, the out-of-network multiplier and the VM rerank.

Mapping the simulated actions onto X's action names is approximate. X's real ranker is a transformer that predicts each action's probability. Here one XGBoost regressor learns the expected value directly.

## Data-generating process (every assumed parameter)

None of these numbers is an empirical estimate. They were fixed before the results were seen and were not tuned to reproduce the original demo's findings.

**Population**
- 20,000 impressions, drawn as uniformly random (user, post) pairs.
- 1,000 users, 2,000 posts and 8 topics.
- Topic 0 is "distress-related". A post is in topic 0 with probability 0.15; otherwise its topic is uniform over 1-7.
- `distress_related` is a hidden flag (topic == 0). It is **not** a model feature and has no direct effect on any outcome.

**User side**
- Topic affinity is Beta(2, 3) for topics 1-7. For the distress topic it is Beta(1.5, 5), so most users have little affinity for it.
- `topic_history` = clip(affinity[user, topic] + N(0, 0.10), 0, 1).
- `from_followed` ~ Bernoulli(0.20) per impression.
- `hours_old` ~ Exponential(mean 12), clipped to [0, 72].

**Post side**
- Content features depend on the distress flag `d`.
- `emotional_intensity` ~ Beta(5, 2) if d, else Beta(2, 3). The means are 0.71 and 0.40.
- `watch_completion` = clip(0.25 + 0.30·intensity + 0.10·d + N(0, 0.08)).
- `comment_rate` = clip(0.05 + 0.35·intensity + 0.08·d + N(0, 0.08)).
- `reactions` ~ Beta(2, 5), independent of everything else.

So distress posts are more intense, and watch completion and comment rate are correlated with intensity: r = 0.69 and 0.75 in seed 0.

**Action heads**
Each head is a logistic model, logit P = b0 + Σ coef·feature. Blank cells mean the feature has no effect on that head.

| head | b0 | topic_history | emotional_intensity | reactions | comment_rate | watch_completion | from_followed | hours_old |
|---|---|---|---|---|---|---|---|---|
| favorite | -3.9 | 1.8 | 0.9 | 1.5 | | | 0.6 | -0.015 |
| reply | -5.6 | 1.6 | 1.0 | | 3.0 | | 0.8 | -0.01 |
| repost | -6.0 | 1.2 | 1.2 | 2.0 | | | | -0.02 |
| share | -6.2 | 1.2 | 1.5 | 1.5 | | | | -0.02 |
| dwell | -1.6 | 1.5 | 0.5 | | | 2.5 | | |

- Dwell seconds, given a dwell, ~ Gamma(shape 2), with mean 5 + 25·watch_completion·(0.5 + topic_history).
- Resulting base rates (seed 0): like 8.7%, reply 2.7%, repost 0.9%, share 0.8%, dwell 54%. These fall inside the assumed ranges in `grounding.md` (like 2-10%, comment 0.5-3%, reshare 0.2-2%).
- Coefficient directions follow the grounding notes: emotional arousal raises sharing, and interest and familiarity raise everything. The magnitudes are assumptions. **Every finding is conditional on them.** In particular, `topic_history` has a coefficient between 1.2 and 1.8 in every head, which makes it the largest true driver.

**The teen's feed (persona)**
- One simulated 14-year-old with a fixed seed (2026), independent of the model seed.
- Her affinities are Beta(2, 3) per topic, except distress, which is Beta(9, 2) because she recently engaged with distress content. The draw was 0.71.
- The 8 posts keep the original titles and distress flags. Posts A and D are in the distress topic. The others are in their own non-distress topics.
- `from_followed` = 1 only for "Friend's soccer game photos" and "Cousin's new puppy", because the titles imply it.
- Every other feature is drawn from the DGP above. The values are rounded to 2 decimals (hours to an integer), so the displayed features are exactly the model inputs.

## Model

- 80/20 random train/test split of the impressions.
- XGBoost `reg:squarederror`, learning rate 0.03, subsample 0.8, lambda 1, `hist`.
- `max_depth` ∈ {2, 3, 4} and `min_child_weight` ∈ {20, 100, 300} are chosen by 5-fold CV RMSE on the **realized** value of the training split. The number of rounds comes from CV early stopping (patience 100, max 2,000). The test set and the true expectation are never used for selection.
- Ablation: the same procedure without `emotional_intensity`.
- Test R² is reported two ways:
  - against the realized value, which is about 0.03. The ceiling is the true expectation's own R², 0.028, because a single impression is mostly zeros and rare 5-point replies.
  - against the true expected value, which is about 0.89.

## Audit methods

- **SHAP.** `shap.TreeExplainer(model, data=background, feature_perturbation="interventional")` on the raw regressor output, so values are in engagement points. The background is 100 training rows sampled with a fixed seed.
  - Additivity is checked, and the values are cross-checked against a brute-force 2^7-coalition Shapley computation using xgboost predictions.
- **True drivers.** Exact interventional Shapley values of the closed-form true expectation E[value | x], with the same background, on 1,000 held-out rows. Global importance is mean |SHAP|. The comparison with the model is a Spearman correlation over the 7 features.
- **Proxy effect.**
  - The overall share is the distress share of all 20,000 impressions.
  - The top-decile share is the distress share of the top 10% of the 4,000 held-out impressions by model score, with a 1,000-resample bootstrap CI.
  - The same is reported for the ablation model and for ranking by the true expectation.
- **LIME.** `LimeTabularExplainer` in regression mode with quartile discretization. `from_followed` is categorical. 5,000 samples, default kernel width. 40 reruns with `random_state` 0-39.
  - "Top reason" is the largest |weight|.
  - "Local fit" is the mean `explanation.score`, the surrogate's weighted R².
  - Kernel width is checked at 0.5× and 2× the default, with 10 runs each.
- **Faithfulness.** Remove the top 2 |SHAP| features of the top post, meaning replace them with background values, interventionally. Compare the score drop with the mean drop over all 21 feature pairs.
- **Completeness.** Shares of Σ|SHAP| for the top post. The platform-style reason ("similar to content you've interacted with") is `topic_history`'s share.
- **SHAP stability.** 50 small perturbations of the top post: ±0.02 on continuous features and ±1 hour. Count how many keep the same top-3 set.
- **Counterfactuals.** Grid search with the other 7 posts held fixed.
  - User side: the top post's `topic_history` ∈ {0, 0.01, …, 1} × `from_followed` ∈ {0, 1}.
  - Also a topic-level variant that changes her history for every post in the same topic.
  - Content side: one feature at a time over its range (0.01 grid; hours 0-72). Report the smallest change, measured in dataset SDs, that drops the post below rank 3.
- **Seeds.** The whole pipeline runs for seeds 0-4. Seed 0 is shipped to the browser. `extra.seeds` in `sim.json` gives per-seed values, the mean, a t-based 95% interval and categorical tallies.

## Browser model

`model.json` stores each tree as arrays: `f` is the split feature (-1 means a leaf), `t` is the threshold, or the leaf value at a leaf, and `l`/`r` are the children. The left branch is taken when `x < t`, compared in float32 as XGBoost does. `model.ts` evaluates the trees and computes exact Shapley values by enumerating every coalition: 128 × 100 background rows per post for the full model. `parity.mjs` checks scores, the base value, SHAP and additivity for the 8 feed posts plus 12 held-out rows, for both models, within 1e-6.
