"""Seeded feed simulation for the XAI project.

Run from the repo root:   uv run python analysis/run.py
(If the active interpreter lacks the deps, the script re-executes itself
inside the analysis/ uv project.)

Pipeline (see analysis/README.md for every assumed parameter):
  1. Simulate 20,000 impressions from a documented data-generating process (DGP).
  2. Simulate per-action outcomes and score each impression with the X ranker
     weights published in xai-org/x-algorithm, home-mixer/params/param.rs @ 862a1235.
  3. Train an XGBoost regressor on the 7 features (and an ablation without
     emotional_intensity) to predict that engagement value.
  4. Rank the 8-post feed of one simulated 14-year-old and audit it with
     interventional TreeSHAP, LIME, counterfactual search, a proxy-effect test,
     faithfulness and completeness checks.
  5. Repeat the whole pipeline for 5 seeds for across-seed intervals; seed 0 is
     the model shipped to the browser.
"""

from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
try:
    import numpy as np
    import pandas as pd
    import xgboost as xgb
    import shap
    import lime.lime_tabular
    import sklearn
    from scipy.stats import spearmanr
except ImportError:  # pragma: no cover - re-exec inside the uv project
    if os.environ.get("XAI_SIM_REEXEC"):
        raise
    os.environ["XAI_SIM_REEXEC"] = "1"
    os.execvp("uv", ["uv", "run", "--project", HERE, "python", os.path.abspath(__file__), *sys.argv[1:]])

import itertools
import json
import math
import time
import warnings
from math import factorial

warnings.filterwarnings("ignore")

ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "out")
DATA = os.path.join(ROOT, "src", "data")

# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------
FEATURES = [
    "topic_history",
    "emotional_intensity",
    "reactions",
    "comment_rate",
    "watch_completion",
    "from_followed",
    "hours_old",
]
USER_SIDE = ["topic_history", "from_followed"]
CONTENT_SIDE = ["emotional_intensity", "reactions", "comment_rate", "watch_completion", "hours_old"]
ABLATED = "emotional_intensity"

# X "For You" ranker weights, xai-org/x-algorithm, home-mixer/params/param.rs,
# commit 862a1235 (2026-10-17). Only the actions this DGP simulates are used.
X_COMMIT = "862a1235"
X_WEIGHTS = {
    "favorite": 0.66,
    "reply": 5.0,  # no bidirectional-follow boost: the DGP has no mutual follows
    "retweet": 1.0,
    "share": 2.0,
    "dwell": 0.05,
    "not_dwelled": -0.02,  # applied to 1 - dwell
    # param.rs says only "a continuous value e.g. watch time"; treating the
    # value as SECONDS of dwell is this project's assumption (no unit is given).
    "cont_dwell_time": 0.006,
}

N_IMPRESSIONS = 20_000
N_USERS = 1_000
N_POSTS = 2_000
N_TOPICS = 8
DISTRESS_TOPIC = 0
P_DISTRESS_POST = 0.15
# A minority of users have recently engaged with distress content. Their
# distress-topic affinity is drawn from the same Beta(9, 2) as the persona's, so
# the persona's feed sits inside the training distribution (review finding:
# with Beta(1.5, 5) for everyone, her distress posts had 0-2 training rows
# within 0.5 SD). Chosen to fix support, not to target any finding.
P_DISTRESS_ENGAGED_USER = 0.10
DISTRESS_ENGAGED_BETA = (9, 2)
DISTRESS_TYPICAL_BETA = (1.5, 5)
P_FOLLOWED = 0.20
HOURS_MEAN = 12.0
HOURS_MAX = 72.0

# Logistic heads: logit P(action) = b0 + sum(coef * feature)
HEADS = {
    "favorite": {"b0": -3.9, "topic_history": 1.8, "reactions": 1.5, "emotional_intensity": 0.9, "from_followed": 0.6, "hours_old": -0.015},
    "reply": {"b0": -5.6, "topic_history": 1.6, "comment_rate": 3.0, "emotional_intensity": 1.0, "from_followed": 0.8, "hours_old": -0.01},
    "retweet": {"b0": -6.0, "topic_history": 1.2, "reactions": 2.0, "emotional_intensity": 1.2, "hours_old": -0.02},
    "share": {"b0": -6.2, "topic_history": 1.2, "reactions": 1.5, "emotional_intensity": 1.5, "hours_old": -0.02},
    "dwell": {"b0": -1.6, "topic_history": 1.5, "watch_completion": 2.5, "emotional_intensity": 0.5},
}
# Dwell time (seconds) given a dwell: Gamma(shape=2), mean = 5 + 25 * wc * (0.5 + th)
DWELL_SHAPE = 2.0

# Fixed boosting settings; depth, min_child_weight and the number of rounds are
# chosen per model by 5-fold CV RMSE on the REALIZED engagement value of the
# training split (never on the test split, never on the true expectation).
XGB_FIXED = dict(learning_rate=0.03, subsample=0.8, reg_lambda=1.0, tree_method="hist", objective="reg:squarederror", n_jobs=4)
XGB_GRID = {"max_depth": [2, 3, 4], "min_child_weight": [20, 100, 300]}
MAX_ROUNDS = 2000
EARLY_STOP = 100
CV_FOLDS = 5

SEEDS = [0, 1, 2, 3, 4]
SHIP_SEED = 0
FEED_SEED = 2026
N_BACKGROUND = 100
N_GLOBAL = 1000
LIME_RERUNS = 40
LIME_SAMPLES = 5000
TOP_K = 3
FAITH_K = 2

PLATFORM_REASON = "This video is similar to content you've interacted with"

FEED_POSTS = [
    # name, title, distress, topic, from_followed (from the title's meaning)
    ("Post A", "Sad-edit video about feeling alone", True, 0, 0),
    ("Post B", "Friend's soccer game photos", False, 2, 1),
    ("Post C", "Viral dance challenge", False, 3, 0),
    ("Post D", "Late-night venting post about feeling empty", True, 0, 0),
    ("Post E", "Study tips for finals", False, 4, 0),
    ("Post F", "Outrage clip about a celebrity", False, 5, 0),
    ("Post G", "Cousin's new puppy", False, 6, 1),
    ("Post H", "Mental health hotline awareness post", False, 1, 0),
]

PHRASE = {
    "topic_history": "the user's past engagement with the topic",
    "emotional_intensity": "the emotional intensity of the post",
    "reactions": "the post's reactions (popularity)",
    "comment_rate": "the post's comment rate",
    "watch_completion": "the post's average watch completion",
    "from_followed": "whether the user follows the account",
    "hours_old": "how long ago it was posted",
}
SHORT = {
    "topic_history": "past engagement with the topic",
    "emotional_intensity": "emotional intensity",
    "reactions": "reactions",
    "comment_rate": "comment rate",
    "watch_completion": "watch completion",
    "from_followed": "from a followed account",
    "hours_old": "hours since posted",
}
WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight"]


# --------------------------------------------------------------------------
# Data-generating process
# --------------------------------------------------------------------------
def clip01(a):
    return np.clip(a, 0.0, 1.0)


def post_content(rng, distress):
    """Post-level content features given the hidden distress flag."""
    n = distress.shape[0]
    d = distress.astype(float)
    ei = np.where(distress, rng.beta(5, 2, n), rng.beta(2, 3, n))
    wc = clip01(0.25 + 0.30 * ei + 0.10 * d + rng.normal(0, 0.08, n))
    cr = clip01(0.05 + 0.35 * ei + 0.08 * d + rng.normal(0, 0.08, n))
    reac = rng.beta(2, 5, n)
    return ei, wc, cr, reac


def head_probs(X: np.ndarray) -> dict[str, np.ndarray]:
    cols = {f: X[:, i] for i, f in enumerate(FEATURES)}
    out = {}
    for head, coefs in HEADS.items():
        z = np.full(X.shape[0], coefs["b0"])
        for f, c in coefs.items():
            if f != "b0":
                z = z + c * cols[f]
        out[head] = 1.0 / (1.0 + np.exp(-z))
    return out


def dwell_mean_seconds(X: np.ndarray) -> np.ndarray:
    th = X[:, FEATURES.index("topic_history")]
    wc = X[:, FEATURES.index("watch_completion")]
    return 5.0 + 25.0 * wc * (0.5 + th)


def true_value(X: np.ndarray) -> np.ndarray:
    """E[engagement value | features] under the DGP (closed form)."""
    p = head_probs(X)
    ev = sum(X_WEIGHTS[h] * p[h] for h in HEADS)
    ev = ev + X_WEIGHTS["not_dwelled"] * (1.0 - p["dwell"])
    ev = ev + X_WEIGHTS["cont_dwell_time"] * p["dwell"] * dwell_mean_seconds(X)
    return ev


def simulate(seed: int):
    rng = np.random.default_rng(seed)
    aff = rng.beta(2, 3, (N_USERS, N_TOPICS))
    engaged = rng.random(N_USERS) < P_DISTRESS_ENGAGED_USER
    aff[:, DISTRESS_TOPIC] = np.where(engaged, rng.beta(*DISTRESS_ENGAGED_BETA, N_USERS), rng.beta(*DISTRESS_TYPICAL_BETA, N_USERS))
    topic = np.where(rng.random(N_POSTS) < P_DISTRESS_POST, DISTRESS_TOPIC, rng.integers(1, N_TOPICS, N_POSTS))
    distress_post = topic == DISTRESS_TOPIC
    ei, wc, cr, reac = post_content(rng, distress_post)

    u = rng.integers(0, N_USERS, N_IMPRESSIONS)
    p = rng.integers(0, N_POSTS, N_IMPRESSIONS)
    th = clip01(aff[u, topic[p]] + rng.normal(0, 0.10, N_IMPRESSIONS))
    ff = (rng.random(N_IMPRESSIONS) < P_FOLLOWED).astype(float)
    hrs = np.clip(rng.exponential(HOURS_MEAN, N_IMPRESSIONS), 0.0, HOURS_MAX)
    X = np.column_stack([th, ei[p], reac[p], cr[p], wc[p], ff, hrs])
    distress = distress_post[p]

    probs = head_probs(X)
    acts = {h: (rng.random(N_IMPRESSIONS) < probs[h]).astype(float) for h in HEADS}
    mu = dwell_mean_seconds(X)
    dwell_t = acts["dwell"] * rng.gamma(DWELL_SHAPE, mu / DWELL_SHAPE)
    value = (sum(X_WEIGHTS[h] * acts[h] for h in HEADS) + X_WEIGHTS["not_dwelled"] * (1.0 - acts["dwell"])
             + X_WEIGHTS["cont_dwell_time"] * dwell_t)
    rates = {h: float(acts[h].mean()) for h in HEADS}
    rates["mean_dwell_seconds_given_dwell"] = float(dwell_t[acts["dwell"] > 0].mean())
    rates["share_users_distress_engaged"] = float(engaged.mean())
    return X, distress, value, true_value(X), rates


def persona_feed():
    """The 14-year-old's 8 candidate posts, drawn from the DGP (fixed seed)."""
    rng = np.random.default_rng(FEED_SEED)
    aff = rng.beta(2, 3, N_TOPICS)
    aff[DISTRESS_TOPIC] = rng.beta(*DISTRESS_ENGAGED_BETA)  # recently engaged with distress content
    distress = np.array([d for _, _, d, _, _ in FEED_POSTS])
    ei, wc, cr, reac = post_content(rng, distress)
    topics = np.array([t for _, _, _, t, _ in FEED_POSTS])
    th = clip01(aff[topics] + rng.normal(0, 0.10, len(FEED_POSTS)))
    ff = np.array([f for *_, f in FEED_POSTS], dtype=float)
    hrs = np.clip(np.round(rng.exponential(HOURS_MEAN, len(FEED_POSTS))), 1, HOURS_MAX)
    X = np.column_stack([th, ei, reac, cr, wc, ff, hrs])
    X[:, :5] = np.round(X[:, :5], 2)  # displayed values are the exact model inputs
    return X, {"distress_topic_affinity": float(aff[DISTRESS_TOPIC])}


# --------------------------------------------------------------------------
# Model
# --------------------------------------------------------------------------
def fit_xgb(Xtr, ytr, seed):
    dtr = xgb.DMatrix(Xtr, label=ytr)
    best = None
    for depth in XGB_GRID["max_depth"]:
        for mcw in XGB_GRID["min_child_weight"]:
            params = {**XGB_FIXED, "max_depth": depth, "min_child_weight": mcw, "seed": seed}
            params.pop("n_jobs"); params["nthread"] = 4
            cv = xgb.cv(params, dtr, num_boost_round=MAX_ROUNDS, nfold=CV_FOLDS, early_stopping_rounds=EARLY_STOP, seed=seed)
            score = float(cv["test-rmse-mean"].iloc[-1])
            if best is None or score < best[0]:
                best = (score, depth, mcw, len(cv))
    score, depth, mcw, n_rounds = best
    final = xgb.XGBRegressor(n_estimators=n_rounds, max_depth=depth, min_child_weight=mcw, random_state=seed, **XGB_FIXED)
    final.fit(Xtr, ytr, verbose=False)
    return final, {"n_rounds": n_rounds, "max_depth": depth, "min_child_weight": mcw, "cv_rmse": score}


def r2(y, yhat):
    return float(1 - np.sum((y - yhat) ** 2) / np.sum((y - y.mean()) ** 2))


def rmse(y, yhat):
    return float(np.sqrt(np.mean((y - yhat) ** 2)))


def export_model(model: xgb.XGBRegressor, features: list[str]):
    raw = json.loads(model.get_booster().save_raw(raw_format="json"))
    learner = raw["learner"]
    bs = learner["learner_model_param"]["base_score"].strip("[]")
    base = float(np.float32(float(bs)))
    trees = []
    for t in learner["gradient_booster"]["model"]["trees"]:
        left, right = t["left_children"], t["right_children"]
        split, cond = t["split_indices"], t["split_conditions"]
        f = [(-1 if left[i] == -1 else int(split[i])) for i in range(len(left))]
        f32 = lambda v: float(np.format_float_positional(np.float32(v), unique=True, trim="-"))
        trees.append({"f": f, "t": [f32(c) for c in cond], "l": [int(v) for v in left], "r": [int(v) for v in right]})
    return {"features": features, "base_score": base, "trees": trees}


def eval_exported(m: dict, X: np.ndarray) -> np.ndarray:
    X32 = X.astype(np.float32).astype(np.float64)
    out = np.full(X.shape[0], m["base_score"], dtype=np.float64)
    for tr in m["trees"]:
        f, t, l, r = tr["f"], np.float32(tr["t"]).astype(np.float64), tr["l"], tr["r"]
        for k in range(X.shape[0]):
            n = 0
            while f[n] != -1:
                n = l[n] if X32[k, f[n]] < t[n] else r[n]
            out[k] += t[n]
    return out


# --------------------------------------------------------------------------
# Shapley utilities
# --------------------------------------------------------------------------
def coalition_values(predict, x: np.ndarray, bg: np.ndarray) -> np.ndarray:
    """v[mask] = mean_b f(x_S, b_~S) for every coalition (bit i = feature i)."""
    n = x.shape[0]
    masks = np.arange(2 ** n)
    sel = ((masks[:, None] >> np.arange(n)[None, :]) & 1).astype(bool)  # (2^n, n)
    rows = np.where(sel[:, None, :], x[None, None, :], bg[None, :, :]).reshape(-1, n)
    return predict(rows).reshape(2 ** n, bg.shape[0]).mean(axis=1)


def shapley_from_values(v: np.ndarray, n: int) -> np.ndarray:
    phi = np.zeros(n)
    for mask in range(2 ** n):
        s = bin(mask).count("1")
        for i in range(n):
            if not mask >> i & 1:
                w = factorial(s) * factorial(n - s - 1) / factorial(n)
                phi[i] += w * (v[mask | 1 << i] - v[mask])
    return phi


def batch_true_shap(X: np.ndarray, bg: np.ndarray) -> np.ndarray:
    """Exact interventional Shapley values of the TRUE expected-value function."""
    n = X.shape[1]
    V = np.zeros((2 ** n, X.shape[0]))
    for mask in range(2 ** n):
        sel = np.array([(mask >> i) & 1 for i in range(n)], dtype=bool)
        rows = np.where(sel[None, None, :], X[:, None, :], bg[None, :, :]).reshape(-1, n)
        V[mask] = true_value(rows).reshape(X.shape[0], bg.shape[0]).mean(axis=1)
    phi = np.zeros(X.shape)
    for mask in range(2 ** n):
        s = bin(mask).count("1")
        for i in range(n):
            if not mask >> i & 1:
                w = factorial(s) * factorial(n - s - 1) / factorial(n)
                phi[:, i] += w * (V[mask | 1 << i] - V[mask])
    return phi


def ranks_of(scores: np.ndarray) -> np.ndarray:
    order = np.argsort(-scores, kind="stable")
    r = np.empty(len(scores), dtype=int)
    r[order] = np.arange(1, len(scores) + 1)
    return r


def ci95(vals):
    a = np.asarray(vals, dtype=float)
    if len(a) < 2:
        return None
    t = {2: 12.706, 3: 4.303, 4: 3.182, 5: 2.776, 6: 2.571}.get(len(a), 1.96)
    h = t * a.std(ddof=1) / math.sqrt(len(a))
    return [float(a.mean() - h), float(a.mean() + h)]


# --------------------------------------------------------------------------
# One full run
# --------------------------------------------------------------------------
def run_seed(seed: int, Xfeed: np.ndarray, full_detail: bool):
    t0 = time.time()
    X, distress, y, ev, rates = simulate(seed)
    rng = np.random.default_rng(seed + 7)
    perm = rng.permutation(len(y))
    n_test = int(0.2 * len(y))
    te, tr = perm[:n_test], perm[n_test:]

    feats_abl = [f for f in FEATURES if f != ABLATED]
    ia = [FEATURES.index(f) for f in feats_abl]
    ei_idx = FEATURES.index(ABLATED)

    model, rounds = fit_xgb(X[tr], y[tr], seed)
    model_abl, rounds_abl = fit_xgb(X[tr][:, ia], y[tr], seed)
    pred_te = model.predict(X[te]).astype(float)
    pred_te_abl = model_abl.predict(X[te][:, ia]).astype(float)

    metrics = {
        "train_rows": int(len(tr)),
        "test_rows": int(len(te)),
        "hyperparams": rounds,
        "hyperparams_ablation": rounds_abl,
        "test_r2_vs_realized": r2(y[te], pred_te),
        "test_rmse_vs_realized": rmse(y[te], pred_te),
        "test_r2_vs_true_expectation": r2(ev[te], pred_te),
        "test_rmse_vs_true_expectation": rmse(ev[te], pred_te),
        "noise_ceiling_r2_true_expectation_vs_realized": r2(y[te], ev[te]),
        "ablation_test_r2_vs_realized": r2(y[te], pred_te_abl),
        "ablation_test_r2_vs_true_expectation": r2(ev[te], pred_te_abl),
        "mean_engagement_value": float(y.mean()),
    }

    # ---- proxy effect (held-out impressions) ------------------------------
    def top_share(scores, d):
        k = int(round(0.1 * len(scores)))
        top = np.argsort(-scores, kind="stable")[:k]
        return 100.0 * d[top].mean()

    d_te = distress[te]
    share_all = 100.0 * distress.mean()
    share_all_test = 100.0 * d_te.mean()
    share_top = top_share(pred_te, d_te)
    share_top_abl = top_share(pred_te_abl, d_te)
    share_top_truth = top_share(ev[te], d_te)
    boot = None
    if full_detail:
        brng = np.random.default_rng(seed + 99)
        bs_full, bs_abl = [], []
        for _ in range(1000):
            b = brng.integers(0, len(te), len(te))
            bs_full.append(top_share(pred_te[b], d_te[b]))
            bs_abl.append(top_share(pred_te_abl[b], d_te[b]))
        bs_full, bs_abl = np.array(bs_full), np.array(bs_abl)
        boot = {
            "top_decile_pct_95ci": np.percentile(bs_full, [2.5, 97.5]).tolist(),
            "top_decile_no_intensity_pct_95ci": np.percentile(bs_abl, [2.5, 97.5]).tolist(),
            "difference_pp_95ci": np.percentile(bs_full - bs_abl, [2.5, 97.5]).tolist(),
            "resamples": 1000,
        }

    # ---- background + SHAP --------------------------------------------------
    bg = X[tr][np.random.default_rng(seed + 3).choice(len(tr), N_BACKGROUND, replace=False)]
    expl = shap.TreeExplainer(model, data=bg, feature_perturbation="interventional", model_output="raw")
    expl_abl = shap.TreeExplainer(model_abl, data=bg[:, ia], feature_perturbation="interventional", model_output="raw")
    base = float(expl.expected_value)

    feed_scores = model.predict(Xfeed).astype(float)
    feed_phi = np.asarray(expl.shap_values(Xfeed, check_additivity=True))
    additivity_err = float(np.max(np.abs(base + feed_phi.sum(1) - feed_scores)))
    predict = lambda R: model.predict(R).astype(float)
    brute_err = 0.0
    feed_v = []
    for k in range(len(Xfeed)):
        v = coalition_values(predict, Xfeed[k], bg)
        feed_v.append(v)
        brute_err = max(brute_err, float(np.max(np.abs(shapley_from_values(v, len(FEATURES)) - feed_phi[k]))))
    feed_rank = ranks_of(feed_scores)
    top = int(np.argmin(feed_rank))

    # ---- support: how many training rows lie near each feed post ------------
    # Euclidean distance over the 5 continuous features in training-SD units.
    sd5 = X[tr][:, :5].std(0)
    support = {}
    for k in range(len(Xfeed)):
        dist = np.sqrt((((X[tr][:, :5] - Xfeed[k, :5]) / sd5) ** 2).sum(1))
        support[FEED_POSTS[k][0]] = {"within_0_5_sd": int((dist < 0.5).sum()), "within_1_sd": int((dist < 1.0).sum())}
    phi_top = feed_phi[top]
    abs_top = np.abs(phi_top)
    order_top = np.argsort(-abs_top, kind="stable")
    shap_top3 = [FEATURES[i] for i in order_top[:3]]

    # global importance vs truth
    gi = np.random.default_rng(seed + 5).choice(len(te), N_GLOBAL, replace=False)
    Xg = X[te][gi]
    phi_g = np.asarray(expl.shap_values(Xg, check_additivity=True))
    phi_g_abl = np.asarray(expl_abl.shap_values(Xg[:, ia], check_additivity=True))
    phi_true = batch_true_shap(Xg, bg)
    imp_model = np.abs(phi_g).mean(0)
    imp_true = np.abs(phi_true).mean(0)
    imp_abl = np.abs(phi_g_abl).mean(0)
    rho = float(spearmanr(imp_model, imp_true).statistic)
    gain = {f: float(imp_abl[j] - imp_model[FEATURES.index(f)]) for j, f in enumerate(feats_abl)}
    corr_ei = {f: float(np.corrcoef(X[:, ei_idx], X[:, FEATURES.index(f)])[0, 1]) for f in feats_abl}
    gainers = sorted(gain, key=lambda f: -gain[f])

    # ---- faithfulness (top post) -------------------------------------------
    v_top = feed_v[top]
    full_mask = 2 ** len(FEATURES) - 1
    rm = lambda idxs: full_mask & ~sum(1 << i for i in idxs)
    faith_drop_topk = float(v_top[full_mask] - v_top[rm(order_top[:FAITH_K])])
    topk_set = set(int(i) for i in order_top[:FAITH_K])
    pair_drops = [float(v_top[full_mask] - v_top[rm(c)]) for c in itertools.combinations(range(len(FEATURES)), FAITH_K) if set(c) != topk_set]
    faith_drop_random = float(np.mean(pair_drops))

    # ---- completeness ------------------------------------------------------
    tot = abs_top.sum()
    th_share = 100.0 * abs_top[FEATURES.index("topic_history")] / tot
    completeness = {
        "shap_top_reason": FEATURES[order_top[0]],
        "shap_top_reason_share_pct": round(100.0 * abs_top[order_top[0]] / tot, 1),
        "three_reason_share_pct": round(100.0 * abs_top[order_top[:3]].sum() / tot, 1),
        "platform_style_reason": PLATFORM_REASON,
        "platform_style_reason_share_pct": round(th_share, 1),
        "left_out_of_platform_reason_pct": round(100.0 - round(th_share, 1), 1),
    }

    # ---- SHAP stability under slight perturbation of the top post ----------
    prng = np.random.default_rng(seed + 11)
    P = np.repeat(Xfeed[top][None, :], 50, axis=0)
    cont = [FEATURES.index(f) for f in FEATURES if f not in ("from_followed", "hours_old")]
    P[:, cont] = clip01(P[:, cont] + prng.uniform(-0.02, 0.02, (50, len(cont))))
    hi = FEATURES.index("hours_old")
    P[:, hi] = np.clip(P[:, hi] + prng.integers(-1, 2, 50), 0, HOURS_MAX)
    phi_p = np.abs(np.asarray(expl.shap_values(P, check_additivity=False)))
    same3 = sum(set(np.argsort(-row, kind="stable")[:3]) == set(order_top[:3]) for row in phi_p)
    same1 = sum(int(np.argmax(row)) == int(order_top[0]) for row in phi_p)

    # ---- LIME --------------------------------------------------------------
    lime_res = None
    lime_runs = LIME_RERUNS
    def lime_run(rs, kw=None):
        ex = lime.lime_tabular.LimeTabularExplainer(
            X[tr], feature_names=FEATURES, mode="regression", random_state=rs,
            categorical_features=[FEATURES.index("from_followed")], discretize_continuous=True,
            kernel_width=kw,
        )
        e = ex.explain_instance(Xfeed[top], predict, num_features=len(FEATURES), num_samples=LIME_SAMPLES)
        ranked = [FEATURES[i] for i, _ in list(e.as_map().values())[0]]
        return ranked, float(e.score)

    runs = [lime_run(s) for s in range(lime_runs)]
    tops = [r[0][0] for r in runs]
    thirds = [r[0][2] for r in runs]
    mode_top = max(set(tops), key=tops.count)
    mode_third = max(set(thirds), key=thirds.count)
    default_kw = math.sqrt(len(FEATURES)) * 0.75
    kw_res = {}
    if full_detail:
        for fac in (0.5, 2.0):
            kr = [lime_run(1000 + s, default_kw * fac)[0][0] for s in range(10)]
            kw_res[f"{fac}x"] = {"modal_top": max(set(kr), key=kr.count), "agree_with_default_modal": int(sum(k == mode_top for k in kr)), "runs": 10}
    lime_res = {
        "top_reason_modal": mode_top,
        "top_reason_runs": int(tops.count(mode_top)),
        "reruns": lime_runs,
        "local_fit_r2_mean": float(np.mean([r[1] for r in runs])),
        "local_fit_r2_range": [float(min(r[1] for r in runs)), float(max(r[1] for r in runs))],
        "rank3_modal": mode_third,
        "rank3_modal_runs": int(thirds.count(mode_third)),
        "top_reason_counts": {f: tops.count(f) for f in set(tops)},
        "kernel_width_default": default_kw,
        "kernel_width_checks": kw_res,
        "num_samples": LIME_SAMPLES,
    }

    # ---- counterfactuals ---------------------------------------------------
    def rank_after(mod):
        Xm = Xfeed.copy()
        mod(Xm)
        return int(ranks_of(model.predict(Xm).astype(float))[top])

    thi, ffi = FEATURES.index("topic_history"), FEATURES.index("from_followed")
    grid01 = np.round(np.linspace(0, 1, 101), 2)
    user_best = 0
    user_cells = 0
    user_out = 0
    for th_v in grid01:
        for ff_v in (0.0, 1.0):
            def mod(Xm, th_v=th_v, ff_v=ff_v):
                Xm[top, thi] = th_v
                Xm[top, ffi] = ff_v
            r = rank_after(mod)
            user_best = max(user_best, r)
            user_cells += 1
            user_out += r > TOP_K
    def mod0(Xm):
        Xm[top, thi] = 0.0
    rank_no_hist = rank_after(mod0)
    # topic-level variant: her history with the whole topic (every post sharing it)
    same_topic = [k for k in range(len(FEED_POSTS)) if FEED_POSTS[k][3] == FEED_POSTS[top][3]]
    topic_best = 0
    for th_v in grid01:
        def modt(Xm, th_v=th_v):
            Xm[same_topic, thi] = th_v
        topic_best = max(topic_best, rank_after(modt))

    content_cf = {}
    stds = X.std(0)
    for f in CONTENT_SIDE:
        j = FEATURES.index(f)
        grid = np.arange(0, HOURS_MAX + 1, 1.0) if f == "hours_old" else grid01
        best = None
        for g in grid:
            def modc(Xm, g=g, j=j):
                Xm[top, j] = g
            r = rank_after(modc)
            if r > TOP_K:
                delta = abs(g - Xfeed[top, j])
                if best is None or delta < best["abs_change"]:
                    best = {"from": float(Xfeed[top, j]), "to": float(g), "abs_change": float(delta), "change_in_sd": float(delta / stds[j]), "new_rank": r}
        content_cf[f] = best
    feasible = {f: c for f, c in content_cf.items() if c is not None}
    minimal = min(feasible, key=lambda f: feasible[f]["change_in_sd"]) if feasible else None

    # ---- ablation feed -----------------------------------------------------
    abl_scores = model_abl.predict(Xfeed[:, ia]).astype(float)
    abl_rank = ranks_of(abl_scores)
    n_distress_feed = int(sum(d for _, _, d, _, _ in FEED_POSTS))
    orig_topn = set(np.argsort(-feed_scores, kind="stable")[:n_distress_feed])
    abl_topn = set(np.argsort(-abl_scores, kind="stable")[:n_distress_feed])
    distress_idx = {k for k in range(len(FEED_POSTS)) if FEED_POSTS[k][2]}
    same_top_n = len(orig_topn & abl_topn & distress_idx)

    res = {
        "seed": seed,
        "metrics": metrics,
        "rates": rates,
        "proxy": {
            "distress_share_all_pct": share_all,
            "distress_share_test_pct": share_all_test,
            "top_decile_pct": share_top,
            "top_decile_no_intensity_pct": share_top_abl,
            "top_decile_true_value_pct": share_top_truth,
            "bootstrap": boot,
        },
        "feed": {
            "scores": feed_scores.tolist(),
            "ranks": feed_rank.tolist(),
            "top_post": FEED_POSTS[top][0],
            "shap": feed_phi.tolist(),
            "base_value": base,
            "additivity_max_abs_err": additivity_err,
            "brute_force_vs_treeshap_max_abs_err": brute_err,
            "ablation_scores": abl_scores.tolist(),
            "ablation_ranks": abl_rank.tolist(),
        },
        "shap_top": {
            "top3": shap_top3,
            "top": shap_top3[0],
            "second": shap_top3[1],
            "top_two_values": [float(phi_top[order_top[0]]), float(phi_top[order_top[1]])],
            "top_two_ratio": float(abs_top[order_top[1]] / abs_top[order_top[0]]),
            "rank_of_lime_rank3_in_shap": int(list(order_top).index(FEATURES.index(mode_third)) + 1),
            "perturbation_same_top3": int(same3),
            "perturbation_same_top1": int(same1),
            "perturbation_runs": 50,
        },
        "global": {
            "mean_abs_shap_model": dict(zip(FEATURES, imp_model.tolist())),
            "mean_abs_shap_truth": dict(zip(FEATURES, imp_true.tolist())),
            "mean_abs_shap_ablation": dict(zip(feats_abl, imp_abl.tolist())),
            "rank_corr_model_vs_truth": rho,
            "ablation_importance_gain": gain,
            "corr_with_emotional_intensity": corr_ei,
            "top_gainers": gainers[:2],
            "rows": N_GLOBAL,
        },
        "faithfulness": {"k": FAITH_K, "drop_topk": faith_drop_topk, "drop_random_mean": faith_drop_random, "pairs": len(pair_drops)},
        "completeness": completeness,
        "lime": lime_res,
        "counterfactual": {
            "top_k": TOP_K,
            "user_side_best_rank": user_best,
            "user_side_cells_out_of_topk": int(user_out),
            "user_side_cells": user_cells,
            "user_side_can_remove": bool(user_out > 0),
            "rank_no_history": rank_no_hist,
            "topic_level_best_rank": topic_best,
            "content_side": content_cf,
            "minimal_content_feature": minimal,
        },
        "ablation": {"same_top_n": same_top_n, "n_distress_in_feed": n_distress_feed},
        "support": support,
    }
    res["_seconds"] = time.time() - t0
    if full_detail:
        res["_models"] = (model, model_abl, bg, feats_abl, Xg)
    return res


# --------------------------------------------------------------------------
# reports/numbers-diff.md
# --------------------------------------------------------------------------
def qualitative_checks(r, boot_ok=None):
    """(id, original finding, holds?, evidence) for one seed's results."""
    lm, sh, cf, g, pr = r["lime"], r["shap_top"], r["counterfactual"], r["global"], r["proxy"]
    ei = cf["content_side"]["emotional_intensity"]
    comp = r["completeness"]
    rows = [
        ("Q1", "Top post is Post A, the sad-edit video", r["feed"]["top_post"] == "Post A", f"top post = {r['feed']['top_post']}"),
        ("Q2", "LIME and SHAP disagree on the top post's main reason (LIME: topic history; SHAP: emotional intensity)", lm["top_reason_modal"] != sh["top"], f"LIME modal top = {lm['top_reason_modal']}; SHAP top = {sh['top']}"),
        ("Q3", "LIME's top reason is the user's past engagement with the topic", lm["top_reason_modal"] == "topic_history", f"LIME modal top = {lm['top_reason_modal']}"),
        ("Q5", "SHAP's largest contributor is the post's emotional intensity", sh["top"] == "emotional_intensity", f"SHAP top = {sh['top']}"),
        ("Q6", "SHAP's top two contributors are nearly tied (ratio >= 0.8)", sh["top_two_ratio"] >= 0.8, f"#2/#1 = {sh['top_two_ratio']:.2f} ({sh['top']} vs {sh['second']})"),
        ("Q7", "SHAP contributions sum exactly to the score", r["feed"]["additivity_max_abs_err"] < 1e-5, f"max additivity error = {r['feed']['additivity_max_abs_err']:.1e}"),
        ("Q8", "SHAP global ranking closely matches the true drivers (Spearman >= 0.8)", g["rank_corr_model_vs_truth"] >= 0.8, f"Spearman = {g['rank_corr_model_vs_truth']:.3f}"),
        ("Q9", "No user-side change (topic history, follow status) removes the top post from the top 3", not cf["user_side_can_remove"], f"best reachable rank = {cf['user_side_best_rank']} ({cf['user_side_cells_out_of_topk']}/{cf['user_side_cells']} grid cells leave the top 3)"),
        ("Q10", "With zero topic history the top post still ranks inside the top 3 (#2)", cf["rank_no_history"] <= TOP_K, f"rank with topic_history = 0: #{cf['rank_no_history']}"),
        ("Q11", "Lowering emotional intensity alone pushes the top post out of the top 3", ei is not None, (f"intensity {ei['from']:.2f} -> {ei['to']:.2f}" if ei else "no value of emotional intensity in [0, 1] does it") + f"; minimal single content-side change: {cf['minimal_content_feature'] or 'none'}"),
        ("Q12", "Distress posts are heavily over-represented in the top 10% (>= 1.5x their overall share)", pr["top_decile_pct"] >= 1.5 * pr["distress_share_all_pct"], f"{pr['distress_share_all_pct']:.1f}% overall vs {pr['top_decile_pct']:.1f}% top decile"),
        ("Q13", "Removing emotional intensity lowers the distress share of the top 10%", pr["top_decile_no_intensity_pct"] < pr["top_decile_pct"] and (boot_ok if boot_ok is not None else True), f"{pr['top_decile_pct']:.1f}% -> {pr['top_decile_no_intensity_pct']:.1f}%" + (f"; bootstrap 95% CI of the difference (full - ablated) {pr['bootstrap']['difference_pp_95ci'][0]:.1f} to {pr['bootstrap']['difference_pp_95ci'][1]:.1f} pp" if pr.get("bootstrap") else "")),
        ("Q14", "After removing emotional intensity the same two distress posts stay on top", r["ablation"]["same_top_n"] == 2, f"distress posts in both models' top 2 = {r['ablation']['same_top_n']}"),
        ("Q15", "Watch completion and comment rate carry the removed signal", set(g["top_gainers"]) == {"watch_completion", "comment_rate"}, f"largest importance gains after ablation: {', '.join(g['top_gainers'])}; corr with intensity: comment rate {g['corr_with_emotional_intensity']['comment_rate']:.2f}, watch completion {g['corr_with_emotional_intensity']['watch_completion']:.2f}"),
        ("Q16", "Fidelity: LIME is only partial (local R^2 well below 1)", lm["local_fit_r2_mean"] < 0.9, f"mean LIME R^2 = {lm['local_fit_r2_mean']:.2f}"),
        ("Q17", "Faithfulness: removing SHAP's top 2 features drops the score far more than random pairs (>= 2x)", r["faithfulness"]["drop_topk"] >= 2 * r["faithfulness"]["drop_random_mean"], f"{r['faithfulness']['drop_topk']:.3f} vs {r['faithfulness']['drop_random_mean']:.3f}"),
        ("Q18", "Completeness: the platform-style reason covers less than half the ranking", comp["platform_style_reason_share_pct"] < 50, f"covers {comp['platform_style_reason_share_pct']:.1f}%"),
        ("Q19", "Completeness: the platform-style reason omits the post's single largest driver", sh["top"] != "topic_history", f"largest driver = {sh['top']}"),
        ("Q20", "Stability: LIME's top reason holds in at least 36 of 40 reruns", lm["top_reason_runs"] >= 36, f"{lm['top_reason_runs']}/{lm['reruns']}"),
        ("Q21", "Stability: SHAP's top 3 unchanged when the post is altered slightly (>= 45 of 50)", sh["perturbation_same_top3"] >= 45, f"{sh['perturbation_same_top3']}/{sh['perturbation_runs']}"),
    ]
    return rows


COPY_CHANGES = os.path.join(HERE, "copy_changes.md")


def write_report(results, sim, old_sim):
    R = results[SHIP_SEED]
    seeds = results.keys()
    boot = R["proxy"]["bootstrap"]
    boot_ok = boot["difference_pp_95ci"][0] > 0
    q0 = qualitative_checks(R, boot_ok)
    per_seed = {s: {q[0]: q[2] for q in qualitative_checks(results[s])} for s in seeds}
    ss = sim["extra"]["seeds"]
    L = []
    L.append("# Simulation numbers: precomputed demo vs. real model\n")
    L.append("Generated by `analysis/run.py` (do not edit by hand). Old = the precomputed values in the original artifact "
             "(`analysis/baseline/sim.precomputed.json`). New = seed 0, the model shipped to the browser in `src/data/model.json`. "
             f"Across seeds = mean and t-based 95% interval over seeds {list(SEEDS)} (each seed regenerates the 20,000 impressions and retrains both models; the teen's 8 posts stay fixed).\n")
    L.append("Wall time is not recorded here (it lives in `analysis/out/timing.json`), so this file is byte-identical across runs.\n")
    if os.path.exists(COPY_CHANGES):
        L.append(open(COPY_CHANGES).read().rstrip() + "\n")
    L.append("Important: the new model is a regressor on X-weighted engagement points, not a probability, so scores and SHAP values are in engagement points. "
             "Every result below depends on the assumed data-generating process documented in `analysis/README.md`.\n")
    L.append("## Numbers\n")
    L.append("| key | old | new (seed 0) | across seeds | status |")
    L.append("|---|---|---|---|---|")
    seed_key = {k: k for k in ss if isinstance(ss.get(k), dict) and "mean" in ss[k]}
    for k in old_sim:
        o, n = old_sim[k], sim[k]
        od, nd = str(o.get("display")), str(n.get("display"))
        acr = ""
        if k in seed_key:
            v = ss[k]
            acr = f"{v['mean']:.3g} [{v['ci95_t'][0]:.3g}, {v['ci95_t'][1]:.3g}]; range {v['min']:.3g}-{v['max']:.3g}"
        elif k in ("top_post", "shap_top_feature", "shap_second_feature", "lime_top_feature", "lime_rank3_feature", "cf_design_same_top_n", "cf_intensity_to"):
            cat = {"cf_design_same_top_n": "cf_design_same_top_n", "cf_intensity_to": "cf_intensity_to"}.get(k, k)
            acr = ", ".join("none" if x is None else str(x) for x in ss["categorical"][cat])
        elif k == "cf_rank_no_history":
            acr = ", ".join(str(x) for x in ss["categorical"]["rank_no_history"])
        if isinstance(o.get("value"), list) and isinstance(n.get("value"), list) and set(o["value"]) == set(n["value"]):
            status = "same (order differs)" if od != nd else "same"
        else:
            status = "same" if od == nd else "CHANGED"
        L.append(f"| `{k}` | {od} | {nd} | {acr} | {status} |")
    L.append("")
    L.append("## Qualitative findings of the original\n")
    L.append("HOLDS / CHANGED refer to seed 0 (the shipped model). The last column counts the seeds (of 5) where the finding holds "
             "(Q13 on seed 0 also requires the bootstrap CI of the difference to exclude zero; other seeds use the point estimate).\n")
    L.append("| id | original finding | seed 0 | evidence (seed 0) | seeds holding |")
    L.append("|---|---|---|---|---|")
    for qid, text, ok, ev in q0:
        n_hold = sum(per_seed[s][qid] for s in seeds)
        L.append(f"| {qid} | {text} | {'HOLDS' if ok else 'CHANGED'} | {ev} | {n_hold}/5 |")
    L.append("")
    m = R["metrics"]
    L.append("## Model quality and checks (seed 0)\n")
    L.append(f"- Hyperparameters chosen by 5-fold CV on realized value: depth {m['hyperparams']['max_depth']}, min_child_weight {m['hyperparams']['min_child_weight']}, {m['hyperparams']['n_rounds']} trees (ablation: depth {m['hyperparams_ablation']['max_depth']}, {m['hyperparams_ablation']['n_rounds']} trees).")
    L.append(f"- Test R^2 vs realized engagement value {m['test_r2_vs_realized']:.3f} (RMSE {m['test_rmse_vs_realized']:.3f}). The noise ceiling (R^2 of the TRUE expectation against realized value) is only {m['noise_ceiling_r2_true_expectation_vs_realized']:.3f}, because single impressions are mostly zero with rare 5-point replies.")
    L.append(f"- Test R^2 vs the true expected value {m['test_r2_vs_true_expectation']:.3f} (RMSE {m['test_rmse_vs_true_expectation']:.4f}); ablation {m['ablation_test_r2_vs_true_expectation']:.3f}.")
    L.append(f"- SHAP additivity max error {R['feed']['additivity_max_abs_err']:.1e}; TreeSHAP vs brute-force 2^7-coalition Shapley max difference {R['feed']['brute_force_vs_treeshap_max_abs_err']:.1e}.")
    L.append(f"- Proxy effect bootstrap (1,000 resamples of held-out impressions): top decile {boot['top_decile_pct_95ci'][0]:.1f}-{boot['top_decile_pct_95ci'][1]:.1f}%, ablated {boot['top_decile_no_intensity_pct_95ci'][0]:.1f}-{boot['top_decile_no_intensity_pct_95ci'][1]:.1f}%. Ranking by the TRUE expected value gives {R['proxy']['top_decile_true_value_pct']:.1f}%. "
             "This bootstrap resamples only the test rows of one fixed pair of models, so it understates uncertainty; the across-seed figures (which retrain) are the better guide.")
    dd = ss["top_decile_diff_pp"]
    L.append(f"- Across seeds, top-10% share minus ablated top-10% share: per seed {', '.join(f'{v:+.1f}' for v in dd['per_seed'])} pp; mean {dd['mean']:+.1f}, t-95% interval {dd['ci95_t'][0]:+.1f} to {dd['ci95_t'][1]:+.1f} pp. "
             f"Overall distress share of impressions per seed: {', '.join(f'{v:.1f}' for v in ss['distress_share_all_pct']['per_seed'])}%.")
    L.append(f"- Faithfulness baseline: mean drop over the {R['faithfulness']['pairs']} other feature pairs (the top-2 pair is excluded).")
    sup = R["support"]
    L.append("- Support of the teen's posts in the training data (seed 0; training rows within 0.5 / 1 SD over the 5 continuous features): "
             + "; ".join(f"{k} {v['within_0_5_sd']} / {v['within_1_sd']}" for k, v in sup.items()) + ".")
    L.append("")
    L.append("## Note for copy editors\n")
    L.append("A CHANGED qualitative row means the original wording no longer matches the model. "
             "Numbers flow through `{{sim.*}}` tokens automatically; the wording around them does not, so it is listed and rewritten by hand in the section at the top of this file (source: `analysis/copy_changes.md`).")
    os.makedirs(os.path.join(ROOT, "reports"), exist_ok=True)
    with open(os.path.join(ROOT, "reports", "numbers-diff.md"), "w") as fh:
        fh.write("\n".join(L) + "\n")


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def tok(value, display, frm, claims, note=None):
    d = {"value": value, "display": display, "from": frm, "claims": claims}
    if note:
        d["note"] = note
    return d


def main():
    t_start = time.time()
    os.makedirs(OUT, exist_ok=True)
    Xfeed, persona = persona_feed()
    results = {}
    seconds = {}
    for s in SEEDS:
        results[s] = run_seed(s, Xfeed, full_detail=(s == SHIP_SEED))
        seconds[s] = results[s].pop("_seconds")
        print(f"seed {s}: {seconds[s]:.1f}s  top={results[s]['feed']['top_post']}  "
              f"R2(truth)={results[s]['metrics']['test_r2_vs_true_expectation']:.3f}", flush=True)
    R = results[SHIP_SEED]
    model, model_abl, bg, feats_abl, Xg = R.pop("_models")

    # ---- model.json + parity fixture ----------------------------------------
    m_full = export_model(model, FEATURES)
    m_abl = export_model(model_abl, feats_abl)
    exp_err = float(np.max(np.abs(eval_exported(m_full, Xfeed) - model.predict(Xfeed))))
    exp_err_abl = float(np.max(np.abs(eval_exported(m_abl, Xfeed[:, [FEATURES.index(f) for f in feats_abl]]) - model_abl.predict(Xfeed[:, [FEATURES.index(f) for f in feats_abl]]))))
    assert exp_err < 1e-5 and exp_err_abl < 1e-5, (exp_err, exp_err_abl)
    model_json = {
        "about": "XGBoost regressors predicting X-weighted engagement value (xai-org/x-algorithm param.rs @ 862a1235) on simulated impressions. Node arrays: f = split feature index (-1 = leaf), t = threshold (go left if x < t, float32 compare) or leaf value, l/r = child indices.",
        "seed": SHIP_SEED,
        "units": "weighted engagement points (expected X ranker value per impression)",
        "full": m_full,
        "ablation": {**m_abl, "removed": ABLATED},
        "background": {"features": FEATURES, "rows": bg.tolist()},
    }
    # The background was exported rounded to 1e-10; SHAP was computed on the exact rows.
    # Re-run the parity-relevant SHAP on the exported (rounded) background so the fixture is exact.
    bg_exp = np.array(model_json["background"]["rows"])
    ia = [FEATURES.index(f) for f in feats_abl]
    ex_f = shap.TreeExplainer(model, data=bg_exp, feature_perturbation="interventional")
    ex_a = shap.TreeExplainer(model_abl, data=bg_exp[:, ia], feature_perturbation="interventional")
    Xpar = np.vstack([Xfeed, Xg[:12]])
    fixture = {
        "rows": Xpar.tolist(),
        "full": {"scores": model.predict(Xpar).astype(float).tolist(), "shap": np.asarray(ex_f.shap_values(Xpar)).tolist(), "base": float(ex_f.expected_value)},
        "ablation": {"scores": model_abl.predict(Xpar[:, ia]).astype(float).tolist(), "shap": np.asarray(ex_a.shap_values(Xpar[:, ia])).tolist(), "base": float(ex_a.expected_value)},
    }
    with open(os.path.join(DATA, "model.json"), "w") as fh:
        json.dump(model_json, fh, separators=(",", ":"))
    with open(os.path.join(OUT, "parity_fixture.json"), "w") as fh:
        json.dump(fixture, fh)

    # ---- demo.json ---------------------------------------------------------
    labels = json.load(open(os.path.join(HERE, "baseline", "demo.precomputed.json")))["feature_labels"]
    fd = R["feed"]
    order = np.argsort(fd["ranks"])
    def feat_dict(row):
        return {f: (int(row[i]) if f in ("from_followed", "hours_old") else float(row[i])) for i, f in enumerate(FEATURES)}
    feed = [{
        "rank": int(fd["ranks"][k]), "name": FEED_POSTS[k][0], "title": FEED_POSTS[k][1],
        "distress_related": FEED_POSTS[k][2], "score": round(fd["scores"][k], 4), "features": feat_dict(Xfeed[k]),
    } for k in order]
    def cf_feed(ranks):
        return [{"rank": int(ranks[k]), "name": FEED_POSTS[k][0], "title": FEED_POSTS[k][1], "distress_related": FEED_POSTS[k][2]} for k in np.argsort(ranks)]
    top = [p[0] for p in FEED_POSTS].index(fd["top_post"])
    Xu = Xfeed.copy(); Xu[top, FEATURES.index("topic_history")] = 0.0
    user_ranks = ranks_of(model.predict(Xu).astype(float))
    demo = {
        "feature_labels": labels,
        "model": {"type": "XGBoost regressor", "units": model_json["units"], "weights_source": f"xai-org/x-algorithm home-mixer/params/param.rs @ {X_COMMIT}", "seed": SHIP_SEED},
        "proxy_effect": {
            "sensitive_share_overall_pct": round(R["proxy"]["distress_share_all_pct"], 1),
            "sensitive_share_top_decile_pct": round(R["proxy"]["top_decile_pct"], 1),
        },
        "feed": feed,
        "top_post": fd["top_post"],
        "completeness": R["completeness"],
        "shap": {
            "per_post": {FEED_POSTS[k][0]: dict(zip(FEATURES, fd["shap"][k])) for k in range(len(FEED_POSTS))},
            "base_value": fd["base_value"],
        },
        "counterfactuals": {
            "design_side": {"new_feed": cf_feed(fd["ablation_ranks"]), "top_decile_share_pct": round(R["proxy"]["top_decile_no_intensity_pct"], 1)},
            "user_side": {"new_feed": cf_feed(user_ranks), "changed": {"post": fd["top_post"], "topic_history": 0.0}, "best_rank_reachable": R["counterfactual"]["user_side_best_rank"]},
        },
    }
    with open(os.path.join(DATA, "demo.json"), "w") as fh:
        json.dump(demo, fh, indent=2)

    # ---- sim.json ----------------------------------------------------------
    old = json.load(open(os.path.join(HERE, "baseline", "sim.precomputed.json")))
    lm, cf, sh, pr = R["lime"], R["counterfactual"], R["shap_top"], R["proxy"]
    ei_cf = cf["content_side"]["emotional_intensity"]
    src = "analysis/run.py (seed 0)"
    sim = {
        "model_type": tok("gradient-boosted model", "gradient-boosted model", f"{src}: XGBoost regressor, {R['metrics']['hyperparams']['n_rounds']} trees, depth {R['metrics']['hyperparams']['max_depth']}", [46]),
        "n_impressions": tok(N_IMPRESSIONS, f"{N_IMPRESSIONS:,}", f"{src}: N_IMPRESSIONS", [46]),
        "persona_age": tok(14, "14", f"{src}: persona definition", [46, 58]),
        "distress_share_all_pct": tok(round(pr["distress_share_all_pct"], 1), f"{pr['distress_share_all_pct']:.1f}", f"{src}: share of all 20,000 impressions that are distress-related", [51]),
        "distress_share_top_decile_pct": tok(round(pr["top_decile_pct"], 1), f"{pr['top_decile_pct']:.1f}", f"{src}: top 10% of held-out impressions by model score", [51, 52]),
        "distress_share_top_decile_no_intensity_pct": tok(round(pr["top_decile_no_intensity_pct"], 1), f"{pr['top_decile_no_intensity_pct']:.1f}", f"{src}: same, model retrained without emotional_intensity", [52]),
        "cf_design_removed_signal": tok(ABLATED, SHORT[ABLATED], f"{src}: ablation model", [52]),
        "cf_design_same_top_n": tok(R["ablation"]["same_top_n"], WORDS[R["ablation"]["same_top_n"]], f"{src}: distress posts in both models' top {R['ablation']['n_distress_in_feed']} of the teen's feed", [52]),
        "cf_design_correlated_signals": tok(R["global"]["top_gainers"], " and ".join(SHORT[f] for f in R["global"]["top_gainers"]), f"{src}: features whose mean |SHAP| grew most after the ablation", [52]),
        "lime_top_feature": tok(lm["top_reason_modal"], PHRASE[lm["top_reason_modal"]], f"{src}: modal LIME top reason, top post", [47]),
        "lime_top_reason_runs": tok(lm["top_reason_runs"], str(lm["top_reason_runs"]), f"{src}: LIME reruns naming the modal top reason", [47, 57]),
        "lime_reruns": tok(lm["reruns"], str(lm["reruns"]), f"{src}: LIME_RERUNS", [47, 57]),
        "lime_local_fit_pct": tok(round(100 * lm["local_fit_r2_mean"]), str(round(100 * lm["local_fit_r2_mean"])), f"{src}: mean LIME surrogate R^2 (explanation.score) across reruns", [47, 54], note=f"LIME local surrogate fit (about {round(100 * lm['local_fit_r2_mean'])}%)."),
        "lime_rank3_feature": tok(lm["rank3_modal"], SHORT[lm["rank3_modal"]], f"{src}: modal third-ranked LIME feature", [47]),
        "shap_top_feature": tok(sh["top"], PHRASE[sh["top"]], f"{src}: largest |SHAP| for the top post", [48, 56, 65]),
        "shap_second_feature": tok(sh["second"], PHRASE[sh["second"]], f"{src}: second-largest |SHAP| for the top post", [48]),
        "shap_top_reason_share_pct": tok(R["completeness"]["shap_top_reason_share_pct"], f"{R['completeness']['shap_top_reason_share_pct']:.1f}", f"{src}: share of sum |SHAP|, top post", [], note="Not quoted in the copy; available to the told-vs-actual interactive."),
        "shap_truth_rank_corr": tok(round(R["global"]["rank_corr_model_vs_truth"], 3), f"{R['global']['rank_corr_model_vs_truth']:.3f}", f"{src}: Spearman, mean |SHAP| of model vs exact Shapley of the true expected value, 1,000 held-out rows", [48]),
        "shap_units": tok("engagement_points", "weighted engagement points", f"{src}: SHAP on a regressor's raw output (X-weighted engagement value)", [58], note="Regressor output, so SHAP is in the model's own units: X-weighted engagement points per impression, not probability or log-odds."),
        "cf_top_k": tok(TOP_K, WORDS[TOP_K], f"{src}: TOP_K", [50]),
        "cf_rank_no_history": tok(cf["rank_no_history"], str(cf["rank_no_history"]), f"{src}: top post's rank with topic_history = 0", [50]),
        "cf_intensity_from": tok(Xfeed[top, FEATURES.index("emotional_intensity")], f"{Xfeed[top, FEATURES.index('emotional_intensity')]:.2f}", f"{src}: top post's emotional_intensity", [50]),
        "cf_intensity_to": tok(ei_cf["to"] if ei_cf else None, f"{ei_cf['to']:.2f}" if ei_cf else "n/a", f"{src}: nearest emotional_intensity (0.01 grid) that drops the top post out of the top 3; null if none", [50]),
        "faith_k": tok(FAITH_K, WORDS[FAITH_K], f"{src}: FAITH_K", [55]),
        "faith_drop_topk": tok(round(R["faithfulness"]["drop_topk"], 3), f"{R['faithfulness']['drop_topk']:.3f}", f"{src}: score drop when the 2 top-|SHAP| features are replaced by background values", [55]),
        "faith_drop_random": tok(round(R["faithfulness"]["drop_random_mean"], 3), f"{R['faithfulness']['drop_random_mean']:.3f}", f"{src}: mean drop over the other 20 feature pairs (the top-2 pair excluded)", [55]),
        "shap_top3_share_pct": tok(R["completeness"]["three_reason_share_pct"], f"{R['completeness']['three_reason_share_pct']:.1f}", f"{src}: top-3 share of sum |SHAP|", [56]),
        "platform_reason": old["platform_reason"],
        "platform_reason_share_pct": tok(R["completeness"]["platform_style_reason_share_pct"], f"{R['completeness']['platform_style_reason_share_pct']:.1f}", f"{src}: topic_history share of sum |SHAP|, top post", [56, 65]),
        "platform_reason_left_out_pct": tok(R["completeness"]["left_out_of_platform_reason_pct"], f"{R['completeness']['left_out_of_platform_reason_pct']:.1f}", f"{src}: 100 - platform_reason_share_pct", [56]),
        "top_post": tok(fd["top_post"], fd["top_post"], f"{src}: rank 1 of the teen's feed", []),
        "top_post_title": tok(FEED_POSTS[top][1], FEED_POSTS[top][1], f"{src}: rank 1 title", []),
    }
    assert set(sim) == set(old), set(sim) ^ set(old)

    # across-seed summary
    def across(fn):
        vals = [fn(results[s]) for s in SEEDS]
        return {"per_seed": vals, "mean": float(np.mean(vals)), "ci95_t": ci95(vals), "min": float(min(vals)), "max": float(max(vals))}
    seeds_summary = {
        "seeds": SEEDS,
        "note": "Each seed regenerates the 20,000 impressions and retrains both models; the teen's 8 posts are fixed (FEED_SEED). Intervals are t-intervals over 5 seeds.",
        "distress_share_top_decile_pct": across(lambda r: r["proxy"]["top_decile_pct"]),
        "distress_share_top_decile_no_intensity_pct": across(lambda r: r["proxy"]["top_decile_no_intensity_pct"]),
        "distress_share_all_pct": across(lambda r: r["proxy"]["distress_share_all_pct"]),
        "top_decile_diff_pp": across(lambda r: r["proxy"]["top_decile_pct"] - r["proxy"]["top_decile_no_intensity_pct"]),
        "cf_rank_no_history": across(lambda r: r["counterfactual"]["rank_no_history"]),
        "support_top_post_within_1_sd": across(lambda r: r["support"][r["feed"]["top_post"]]["within_1_sd"]),
        "shap_truth_rank_corr": across(lambda r: r["global"]["rank_corr_model_vs_truth"]),
        "test_r2_vs_true_expectation": across(lambda r: r["metrics"]["test_r2_vs_true_expectation"]),
        "test_r2_vs_realized": across(lambda r: r["metrics"]["test_r2_vs_realized"]),
        "lime_local_fit_pct": across(lambda r: 100 * r["lime"]["local_fit_r2_mean"]),
        "lime_top_reason_runs": across(lambda r: r["lime"]["top_reason_runs"]),
        "faith_drop_topk": across(lambda r: r["faithfulness"]["drop_topk"]),
        "faith_drop_random": across(lambda r: r["faithfulness"]["drop_random_mean"]),
        "platform_reason_share_pct": across(lambda r: r["completeness"]["platform_style_reason_share_pct"]),
        "shap_top3_share_pct": across(lambda r: r["completeness"]["three_reason_share_pct"]),
        "categorical": {
            "top_post": [results[s]["feed"]["top_post"] for s in SEEDS],
            "shap_top_feature": [results[s]["shap_top"]["top"] for s in SEEDS],
            "shap_second_feature": [results[s]["shap_top"]["second"] for s in SEEDS],
            "lime_top_feature": [results[s]["lime"]["top_reason_modal"] for s in SEEDS],
            "lime_rank3_feature": [results[s]["lime"]["rank3_modal"] for s in SEEDS],
            "user_side_can_remove": [results[s]["counterfactual"]["user_side_can_remove"] for s in SEEDS],
            "rank_no_history": [results[s]["counterfactual"]["rank_no_history"] for s in SEEDS],
            "minimal_content_feature": [results[s]["counterfactual"]["minimal_content_feature"] for s in SEEDS],
            "cf_intensity_to": [(results[s]["counterfactual"]["content_side"]["emotional_intensity"] or {}).get("to") for s in SEEDS],
            "cf_design_same_top_n": [results[s]["ablation"]["same_top_n"] for s in SEEDS],
            "correlated_signals": [results[s]["global"]["top_gainers"] for s in SEEDS],
            "user_side_best_rank": [results[s]["counterfactual"]["user_side_best_rank"] for s in SEEDS],
            "topic_level_best_rank": [results[s]["counterfactual"]["topic_level_best_rank"] for s in SEEDS],
            "same_top_n": [results[s]["ablation"]["same_top_n"] for s in SEEDS],
        },
    }
    sim["extra"] = {
        "provenance": {
            "script": "analysis/run.py", "seed": SHIP_SEED, "x_weights_commit": X_COMMIT, "x_weights": X_WEIGHTS,
            "versions": {"numpy": np.__version__, "xgboost": xgb.__version__, "shap": shap.__version__, "scikit-learn": sklearn.__version__, "lime": "0.2.0.1"},
        },
        "metrics": R["metrics"],
        "action_rates": R["rates"],
        "persona": persona,
        "proxy": pr,
        "shap_checks": {
            "additivity_max_abs_err": fd["additivity_max_abs_err"],
            "brute_force_vs_treeshap_max_abs_err": fd["brute_force_vs_treeshap_max_abs_err"],
            "base_value": fd["base_value"], "background_rows": N_BACKGROUND,
        },
        "shap_top_post": sh,
        "global_importance": R["global"],
        "faithfulness": R["faithfulness"],
        "lime": lm,
        "counterfactual": cf,
        "ablation": R["ablation"],
        "support": R["support"],
        "seeds": seeds_summary,
    }
    with open(os.path.join(DATA, "sim.json"), "w") as fh:
        json.dump(sim, fh, indent=2)
    full = {"results": {str(s): results[s] for s in SEEDS}, "seeds_summary": seeds_summary, "persona_feed": Xfeed.tolist()}
    with open(os.path.join(OUT, "results.json"), "w") as fh:
        json.dump(full, fh, indent=1, default=float)

    elapsed = time.time() - t_start
    write_report(results, sim, old)
    with open(os.path.join(OUT, "timing.json"), "w") as fh:
        json.dump({"total_seconds": elapsed, "per_seed_seconds": {str(s): seconds[s] for s in SEEDS}}, fh, indent=1)
    print(f"done in {elapsed:.1f}s; top post {fd['top_post']}; wrote src/data/{{sim,demo,model}}.json")


if __name__ == "__main__":
    main()
