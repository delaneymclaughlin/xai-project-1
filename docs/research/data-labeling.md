# Research: content data and LLM-label rigor for the XAI feed-ranker project
Compiled 2026-10-18. Sources were checked live where marked [verified]. [UNVERIFIED] marks anything I could not confirm from a primary source.

## Part A: Datasets

| Dataset | Size / schema | Who labeled | License / terms | Real engagement? | Cautions |
|---|---|---|---|---|---|
| **Dreaddit** (Turcan & McKeown, LOUHI 2019) [paper](https://aclanthology.org/D19-6213/), [arXiv](https://arxiv.org/abs/1911.00133); HF mirror [andreagasparini/dreaddit](https://huggingface.co/datasets/andreagasparini/dreaddit) | 3,553 labeled 5-sentence segments from 2,929 posts (train 2,838 / test 715). Binary stress label plus `confidence` (annotator agreement fraction). 10 subreddits in 5 domains: abuse, anxiety, financial, PTSD, social. Includes LIWC and syntax features [verified, paper and HF schema] | MTurk crowd, at least 5 workers per segment, majority vote. Fleiss κ = 0.47 (moderate) [verified] | Paper gives a download URL but no license. The HF mirror lists no license. Reddit-derived text [UNVERIFIED license] | **Yes.** The mirror has `social_karma`, `social_upvote_ratio`, `social_num_comments`, `social_timestamp` [verified via HF datasets-server] | Abuse and PTSD narratives. Text is verbatim Reddit, so quotes can be searched back to their authors. |
| **GoEmotions** (Google) [HF](https://huggingface.co/datasets/google-research-datasets/go_emotions) | About 58k Reddit comments. 27 emotions plus neutral, multi-label. Simplified config: 43,410 / 5,426 / 5,427. The `raw` config has one row per rater (211k rows) with `rater_id` [verified] | 3 English-speaking crowdworkers in India per item [verified, card] | Apache-2.0 [verified] | No score or upvote fields. Has `subreddit`, `link_id`, `author` [verified] | Usernames are included, so drop `author`. Rater pool is one country, which is a known annotator-population bias. |
| **WASSA-2017 EmoInt** (Mohammad & Bravo-Marquez) [arXiv 1708.03700](https://arxiv.org/abs/1708.03700) | 7,097 tweets (anger 1,701, fear 2,252, joy 1,611, sadness 1,533). Real-valued intensity in [0,1] from best-worst scaling [verified] | CrowdFlower crowd, 3 annotators per 4-tuple. Split-half reliability (Pearson) 0.80 to 0.88 [verified] | "Freely available", but no explicit license. Twitter ToS applies [UNVERIFIED license] | No | Tweets. Low risk. |
| **SemEval-2018 Task 1 Affect in Tweets** [S18-1001](https://aclanthology.org/S18-1001.pdf) | EI-reg / V-reg intensity in 0–1. Successor to EmoInt [partly verified] | Crowd, best-worst scaling | No explicit license found [UNVERIFIED] | No | |
| **Measuring Hate Speech** (UC Berkeley D-Lab) [HF](https://huggingface.co/datasets/ucberkeley-dlab/measuring-hate-speech) | 39,565 comments, 7,912 annotators, 135,556 rows. 10 ordinal items plus IRT `hate_speech_score` (>0.5 roughly hate, < -1 counter-speech). Annotator demographic columns (gender, race, age, education, income, ideology, etc.) [verified] | Crowd, with demographics. IRT corrects for rater severity | CC-BY-4.0 [verified] | No. Source platforms are coded but not named on the card | Hateful text. Good for testing LLM-vs-annotator-subgroup agreement, but off-topic for distress. |
| **Civil Comments / Jigsaw** [HF google/civil_comments](https://huggingface.co/datasets/google/civil_comments) | About 2M comments. Fractional toxicity plus 6 subtypes [verified] | Crowd (rater details not on the card) | CC0 [verified] | No (this HF version) | Known identity-term bias. Identity-mention columns are not in this HF version; they are in the Kaggle "Unintended Bias" release [UNVERIFIED here] |
| **TweetEval** [HF](https://huggingface.co/datasets/cardiffnlp/tweet_eval) | `emotion` subset: 3,257 / 374 / 1,421, labels anger / joy / optimism / sadness [verified] | Inherited from SemEval sources | Per-subset. `emotion` is "Undefined". Twitter ToS [verified] | No | |
| **Reddit Mental Health Dataset** (Low et al. 2020) [Zenodo](https://zenodo.org/records/3941387) | 28 subreddits (15 MH incl. r/suicidewatch, 2 broad MH, 11 controls), 2018–2020, about 827k users, 3.1 GB, plus TF-IDF/feature CSVs [verified] | **No human labels.** The subreddit is a self-selection proxy | ODC-PDDL, but "re-use ... subject to Reddit API terms" [verified] | Not described on the Zenodo page [UNVERIFIED] | Contains r/suicidewatch. Large and unlabeled. |
| **SMHD** (Cohan et al., COLING 2018) [page](https://ir.cs.georgetown.edu/resources/smhd.html) | Users with self-reported diagnoses (9 conditions) plus matched controls | Self-report patterns | **Gated** by a data usage agreement [terms not read: UNVERIFIED] | — | Not appropriate for a course website. |
| **UMD Reddit Suicidality Dataset v2** / CLPsych 2019 [page](https://users.umiacs.umd.edu/~resnik/umd_reddit_suicidality_dataset.html) | Expert- and crowd-annotated suicide risk levels | Experts and crowd | **Gated.** Requires documented IRB approval; advisor sign-off is not enough for grad students [verified]. CLPsych 2021 ran in a secure enclave | — | Do not use. Students cannot get access in time, and the content is too sensitive. |

**Reddit terms context.** In May 2023, Reddit said research use must be non-commercial, must not redistribute Reddit data or "derivative products", and must anonymize published results ([r/modnews post, via mirror](https://lr.sudovanilla.org/r/modnews/duplicates/13wshdp)). I could not verify the current Developer Terms text. Conservative reading: publish aggregate statistics and paraphrases, not a re-hosted text-plus-label file.

### Recommendation
- **Primary content pool: Dreaddit.** It is the only candidate that combines human labels close to distress (stress), real engagement counts (karma, upvote ratio, number of comments), and plausibly "distress-adjacent" topical subreddits, all at a laptop-friendly size (3.5k). Its human ceiling (κ = 0.47) is a useful reference: an LLM should not be expected to beat what humans agree on with each other.
- **Gold / validation for LLM labels:**
  - **GoEmotions `raw`** (Apache-2.0, per-rater labels). Use it for a negative-affect / sadness / fear / nervousness proxy and for per-rater agreement and Dawid-Skene.
  - **EmoInt 2017**, for real-valued *intensity*: check LLM intensity against BWS scores with Pearson/Spearman, against its split-half ceiling of 0.80–0.88.
  - Optional: **Measuring Hate Speech**, only if you want to show subgroup agreement with annotator demographics.
- **Avoid:** SMHD, UMD/CLPsych (gated), and r/suicidewatch from Low et al. (not needed, highest risk).

### Website safety
- Never show raw post text. Show LLM-written paraphrased or synthetic titles, plus an attribute vector.
- Do not publish `post_id`, `author`, or verbatim quotes. Verbatim Reddit text can be searched back to its author.
- Content-warn the abuse and PTSD material. State that no real minor's data is used; the 14-year-old is simulated.
- Publish derived labels only as aggregates or with paraphrased text, given the unclear Dreaddit license and Reddit's terms.

## Part B: Literature

- **Gilardi, Alizadeh & Kubli 2023, PNAS 120(30)** ([arXiv 2303.15056](https://arxiv.org/abs/2303.15056)). On 2,382 tweets, zero-shot ChatGPT beat MTurk on 4 of 5 tasks, its intercoder agreement exceeded crowd and trained annotators, and it cost under $0.003 per annotation [verified].
- **Törnberg 2023** ([arXiv 2304.06588](https://arxiv.org/abs/2304.06588)). GPT-4 inferring politicians' party from tweets had higher accuracy and reliability, and equal or lower bias, than experts and crowd [verified].
- **Ziems et al. 2024, Computational Linguistics** ([arXiv 2305.03514](https://arxiv.org/abs/2305.03514)). Tested 13 models on 25 computational social science benchmarks. LLMs do not beat the best fine-tuned models but reach "fair" agreement with humans, so the authors recommend using them in partnership with humans [verified].
- **Reiss 2023** ([arXiv 2304.11085](https://arxiv.org/abs/2304.11085)). ChatGPT annotation consistency across prompt variants, parameters, and repeats can fall below reliability thresholds. Pooling repetitions helps, and human validation is required [verified].
- **Pangakis, Wolken & Fasching 2023** ([arXiv 2306.00176](https://arxiv.org/abs/2306.00176)). Across 27 tasks on 11 datasets, GPT-4 performance is "highly contingent" on dataset and task, so validate against human labels task by task [verified].
- **Sclar et al., ICLR 2024** ([arXiv 2310.11324](https://arxiv.org/abs/2310.11324)). Formatting changes alone moved accuracy by up to 76 points (LLaMA-2-13B). They propose FormatSpread to report performance intervals over formats [verified].
- **Zheng et al., ICLR 2024** ([arXiv 2309.03882](https://arxiv.org/abs/2309.03882)). Option-ID "selection bias" (for example, a preference for "A") across 20 LLMs. PriDe debiases by permuting options [verified].
- **Persona effects:**
  - Hu & Collier, ACL 2024 ([2024.acl-long.554](https://aclanthology.org/2024.acl-long.554)): persona variables explain under 10% of annotation variance [verified].
  - Beck et al., EACL 2024 ([2024.eacl-long.159](https://aclanthology.org/2024.eacl-long.159)): sociodemographic prompting effects vary widely by model and prompt, so use caution in annotation [verified].
- **Baumann et al. 2025, "LLM Hacking"** ([arXiv 2509.08825](https://arxiv.org/abs/2509.08825)). Replicated 37 tasks from 21 studies with 13M labels from 18 LLMs. About 31% of 2,361 hypotheses reached incorrect conclusions with state-of-the-art LLMs, and about half with small ones. Human labels protect against false positives, and regression corrections trade Type I against Type II errors [verified]. This is the strongest single motivation for the downstream robustness check.
- **Egami et al., NeurIPS 2023, DSL** ([arXiv 2306.04746](https://arxiv.org/abs/2306.04746)). Even 80–90% accurate surrogate labels can bias downstream estimates and break confidence intervals. DSL uses a gold subset sampled with *known probabilities* and gives valid inference [verified].
- **Angelopoulos et al., Prediction-Powered Inference** ([arXiv 2301.09633](https://arxiv.org/abs/2301.09633)). Valid confidence intervals for means, quantiles, and regression coefficients from a small labeled set plus model predictions, with no assumptions about the model. PPI++: [arXiv 2311.01453](https://arxiv.org/abs/2311.01453) [verified]. The *Science* 2023 venue is widely cited, but I did not confirm it.
- **Dawid & Skene 1979**, *Applied Statistics* 28(1):20–28. EM estimation of per-annotator confusion matrices [citation from memory, UNVERIFIED page numbers].
- **Sap et al., ACL 2019** ([P19-1163](https://aclanthology.org/P19-1163/)). African American English tweets were up to 2x more likely to be labeled offensive, and dialect priming of annotators reduces this [verified].
- **Hofmann et al., Nature 2024** ([doi 10.1038/s41586-024-07856-5](https://pmc.ncbi.nlm.nih.gov/articles/PMC11374696/)). Covert dialect prejudice in LLMs, which alignment can mask [verified].
- **Monroe, Colaresi & Quinn 2008**, "Fightin' Words", *Political Analysis* 16(4):372–403 (doi 10.1093/pan/mpn018). Log-odds with an informative Dirichlet prior. Python: [`fightin-words`](https://pypi.org/project/fightin-words/), [ConvoKit FightingWords](https://convokit.cornell.edu/documentation/fightingwords.html) [verified via secondary sources].
- **Reliability thresholds:**
  - Krippendorff (2004, *Content Analysis*, 2nd ed.): α ≥ 0.800 is reliable, and 0.667 ≤ α < 0.800 supports only tentative conclusions [standard; from memory, not re-checked today].
  - Landis & Koch (1977) κ bands: 0.41–0.60 moderate, 0.61–0.80 substantial [from memory].

## Part B: Labeling model, GPT-6 Luna (verified on OpenAI docs, 2026-10-18)

- **Model ID:** `gpt-6-luna`. It is the only snapshot. Context is 1.05M tokens, max output 128k, knowledge cutoff 2026-05-18 ([model page](https://developers.openai.com/api/docs/models/gpt-6-luna)). Launched about 2026-09-22 per press ([VentureBeat](https://venturebeat.com/technology/openai-releases-gpt-6-sol-and-luna-models-slashing-api-costs-50-or-more)).
- **Pricing per 1M tokens, short context ≤272K** ([pricing](https://developers.openai.com/api/docs/pricing)):
  - Standard: $0.10 input, $0.01 cached input, $0.50 output.
  - Batch and Flex: $0.05 input, $0.005 cached input, $0.25 output.
  - Long-context rates are higher.
  - Some aggregators list different prices (for example, PricePerToken shows $0.20/$1.00). Treat OpenAI's page as authoritative.
- **Rate limits** (as listed on the model page): Build tier 5,000 RPM, 2M TPM, 20M-token batch queue; Launch tier 10,000 RPM, 10M TPM, 1B queue. I did not confirm which tier a new key starts on.
- **Structured outputs:** supported. Endpoints are Chat Completions, Responses, and Batch.
- **Temperature, logprobs, and seed:**
  - Luna is a reasoning model with `reasoning.effort` ∈ {none, low, medium (default), high, xhigh, max}.
  - The migration guide says "When reasoning effort is not `none`, remove `temperature`, `top_p`, and `top_logprobs`" (and `logprobs` on Chat Completions) ([guide](https://developers.openai.com/api/docs/guides/latest-model)).
  - **Implication:** run labeling at `reasoning_effort="none"` to get temperature control and label-token logprobs. This is inferred from the guide; the model page itself does not list these parameters. Verify with one test call.
  - `seed`: OpenAI documents it as best-effort only, with no determinism guarantee ([cookbook](https://developers.openai.com/cookbook/examples/reproducible_outputs_with_the_seed_parameter)). I could not verify support on Luna [UNVERIFIED]. Record `system_fingerprint` if it is returned.
- **Setup:**
  - Set `OPENAI_API_KEY` and use the `openai` Python SDK (`uv add openai`).
  - Batch API: upload a JSONL file (each line has `custom_id`, `method`, `url`, `body`; one model per file) with `purpose="batch"`, then create the batch with `completion_window="24h"`. Download `output_file_id`, and match results by `custom_id` because output order is not preserved ([batch guide](https://developers.openai.com/api/docs/guides/batch)).
  - Limits: 50,000 requests and 200 MB per file. Output files are deleted after 30 days.
- **Cheap extra model for robustness, all OpenAI and all documented on the pricing page:** `gpt-5-nano` (batch $0.025 / $0.20) or `gpt-4.1-nano` (batch $0.05 / $0.20). Optional: a local open-weights model through Ollama as a cross-family check. This is not required, because every test below works with a single model.

## Part B: Protocol (single labeling model, statistical tests)

**0. Pre-registration.** Commit a `prereg.md` and the frozen prompt files, with a git hash, *before* any labeling. It fixes the label definitions, prompt cells, metrics, thresholds, which scheme is "primary", and the headline hypotheses. Report every cell, not just the best one; Baumann et al. show cherry-picking a configuration is how wrong conclusions happen.

**1. Labels.** For each item, collect:
- `distress_related` (yes/no)
- `emotional_intensity` (0–4, or 0–100)
- `arousal` (low / med / high)
- `topic` (fixed list)

Use strict JSON-schema structured output. Run at `reasoning_effort=none` so logprobs are available.

**2. Factorial prompt design.** 4 framings × 2 option orders × 2 scale formats = 16 cells:
- **Framing:**
  - neutral annotator
  - harm-salient ("you protect teens")
  - benefit-salient ("support-seeking content helps people")
  - persona ("you are a 14-year-old")
- **Option order:** forward or reversed.
- **Scale format:** 5-point labeled vs 0–100.

Every item goes through every cell at temperature 0. That gives a fully *paired* (within-item) design. On a 1,000-item subsample, add 3 more samples per cell at temperature 1 to estimate sampling noise.

**3. Tests.** All are on paired data. Treat the item as the unit and bootstrap over items.
- **Label-distribution shift across framings:**
  - G-test or chi-square on the cell × label contingency table (`scipy.stats.chi2_contingency(..., lambda_="log-likelihood")`). Because the same items appear in every cell, also run the paired tests:
    - McNemar for binary pairs
    - Stuart–Maxwell for multi-class
    - Cochran's Q across all framings (`statsmodels`)
  - Jensen–Shannon divergence between label distributions (`scipy.spatial.distance.jensenshannon`), with a 95% item-bootstrap CI.
  - Permutation test: shuffle framing labels *within item* (10,000 permutations) to get a null for JSD and for the change in positive rate.
  - Correct across the 16 cells and 4 labels with Holm or Benjamini–Hochberg.
- **Lexical skew:**
  - Run Monroe et al. weighted log-odds with an informative Dirichlet prior (prior = the full corpus) for "labeled distress = 1 vs 0", separately for human labels and for each framing.
  - Report the Spearman correlation of each framing's z-score vector with the human z-scores, and the top-50 term overlap (Jaccard).
  - Also run log-odds on *flip items* (positive under harm-salient but negative under neutral). This shows exactly which vocabulary a framing triggers on, for example profanity, dialect markers, or identity terms. That last check ties to the Sap et al. 2019 and Hofmann et al. 2024 findings.
- **Agreement with human gold, per cell:**
  - Dreaddit: Cohen's κ against the human majority, plus κ restricted to high-confidence items (`confidence` ≥ 0.8).
  - GoEmotions raw: Krippendorff's α with the LLM added as one more rater. Use the `krippendorff` package with nominal or ordinal level.
  - Macro-F1 and confusion matrices, using `sklearn`.
  - EmoInt intensity: Pearson and Spearman.
  - Calibration from logprobs: Brier score and ECE, plus a reliability diagram.
  - **Bar to clear:** the LLM is "human-comparable" if its agreement with the majority is not lower than the human inter-rater ceiling (Dreaddit κ 0.47; EmoInt split-half r 0.80–0.88). Krippendorff's α ≥ 0.667 across cells is the minimum for cross-prompt stability.
- **Variance decomposition:**
  - Fit a crossed mixed model, intensity ~ framing + order + format + (1|item), with the temperature-1 repeats as residual. Use `statsmodels.MixedLM`, or a GLMM / linear-probability model for binary labels.
  - Report the shares of variance for item, prompt factors, item×prompt, and sampling. The goal is item variance far above prompt variance. Hu & Collier's under-10% persona share is a reference point, not a threshold.
  - Also report Krippendorff's α *across the 16 cells*, treating cells as raters.
- **Subgroup error parity:** report κ and F1 by Dreaddit domain (abuse / anxiety / financial / PTSD / social) and by text features (length, a profanity flag). Use a permutation test for the gap.

**4. Aggregation and debiasing.**
- Primary label: majority or mean across the 16 cells (multi-prompt ensemble, as in Reiss).
- Dawid–Skene with cells as "annotators", using `crowd-kit` [package name from memory: UNVERIFIED]. Caveat: cells are not independent raters.
- Flag "unstable" items (cross-cell agreement < 80%; this is a project choice, not a literature threshold). Report results both with and without them.
- **PPI / DSL correction** of headline proportions and regression coefficients, using the human-labeled subset: Dreaddit's human labels on *all* items serve as the gold set with known sampling probability 1, or draw a random subsample of 500 to show that the correction works. PPI is in the `ppi_python` package [UNVERIFIED name]; DSL has an R package (`dsl`) [UNVERIFIED].

**5. Downstream robustness.** Re-run the full pipeline under each labeling scheme:
- human labels
- neutral cell
- harm-salient cell
- benefit-salient cell
- persona cell
- ensemble
- PPI-corrected

The pipeline is GBM ranker → amplification of distress content for the simulated teen → SHAP vs LIME rank agreement (Kendall τ of top features) → counterfactuals. Present a table of headline numbers by scheme. A finding counts as robust only if its direction and significance hold across all schemes, or are explicitly reported where they do not.

**6. API calls and cost (GPT-6 Luna, Batch).**
- **Items:** Dreaddit 3,553 + GoEmotions gold subsample 2,000 + EmoInt subsample 2,000 ≈ 7,500.
- **Calls:**
  - Main design: 7,500 × 16 = 120,000 calls.
  - Repeats: 1,000 × 16 × 3 = 48,000 calls.
  - Total: about 168,000 calls.
- **Assumed tokens per call:** about 550 input (about 420 for the shared prompt prefix, about 130 for the item), about 40 output (JSON, effort none). These are my estimates; measure them on a pilot of 50 items.
- **Totals:** about 92M input and 6.7M output tokens.
- **Cost:**
  - Batch: 92 × $0.05 + 6.7 × $0.25 ≈ **$6.3**.
  - With prompt caching on the prefix (batch cached rate $0.005), roughly $2–3, if caching applies in batch.
  - Standard (non-batch) is about double, around $13.
  - A `gpt-5-nano` robustness pass costs roughly $3–4 on batch.
- **Throughput:** at most 50k requests per file means 4 or more batch files. A 20M-token queue limit on the Build tier means running about 5 batches *sequentially*. Each completes within 24h.

**7. What to put on the website.**
- The pre-registration link and hash, plus the frozen prompts.
- A dataset card covering source, labelers, license caveats, and the redaction policy.
- An agreement table: per cell × label, showing κ/α/F1 against the human ceiling.
- A JSD heatmap across framings with permutation p-values.
- A variance-decomposition bar chart.
- Lexical-skew plots for human vs each framing (paraphrased or neutral terms only; mask sensitive tokens).
- A calibration plot.
- An unstable-item rate.
- The downstream-robustness table, with the human-label row first.
- A "limitations" box: the single-model family; Dreaddit is "stress", not clinical distress; the Reddit/US-centric populations; the India-based GoEmotions raters.

## Flags (could not verify)
- Licenses: no explicit license found for Dreaddit, EmoInt 2017, or SemEval-2018 Task 1.
- Low et al. dataset: engagement columns not confirmed.
- PPI: *Science* venue not confirmed.
- Dawid–Skene: page numbers not re-checked.
- Package names: `crowd-kit`, `ppi_python`, and the R `dsl` package not re-checked.
- GPT-6 Luna: `seed` support not verified. Temperature and logprobs support at effort `none` is inferred from the migration guide.
- Current Reddit Developer Terms text not read (only the May 2023 statement).
- Krippendorff and Landis & Koch thresholds quoted from memory.
