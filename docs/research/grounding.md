# Grounding a simulated feed ranker: what is publicly documented (as of 2026-10-18)

Tags: **PRIMARY** = the platform's own docs or code, court/coroner records, the leaked documents themselves, or the peer-reviewed paper. **REPORTED** = reputable journalism describing leaked docs. **UNVERIFIED** = widely repeated, but I could not confirm it against a primary or reputable reported source.

Access caveats: WSJ, WaPo, CNN, PNAS, Science, ACM and DocumentCloud returned 403/451 to my fetcher. Where that happened I verified through syndicated copies (ADN for WaPo, abc17news for CNN), Europe PMC abstracts, or PDFs I downloaded and extracted text from. Each case is noted below.

---

## 1. Facebook Files / Facebook Papers: News Feed ranking (MSI)

**MSI point weights, H1 2018.** REPORTED. Source: CNN, Rachel Metz, 27 Oct 2021, "Likes, anger emojis and RSVPs: the math behind Facebook's News Feed — and how it backfired". I read the syndicated copy at https://abc17news.com/news/2021/10/27/likes-anger-emojis-and-rsvps-the-math-behind-facebooks-news-feed-and-how-it-backfired/ (cnn.com returned 451).
- The figures come from a 21 Dec 2017 internal note, described as "the final weight for the metric in the first half of 2018":
  - like = 1
  - reaction emoji, or reshare with no added text = 5
  - RSVP = 15
  - "significant" comment, message or reshare (at least 5 unique tokens, or a photo or video) = 30
- Relationship multipliers: same group "multiply by 0.5"; total strangers "Multiply by 0.3".
- The weights were informed by surveys of "over 69,000 people in five countries".
- Angry reaction, per CNN: it had "previously been demoted to 1.5 points". The July 2020 proposal reads: "After discussing with Comms to decide between Angry 0 vs 0.5 to see if one is more externally defendable…" and it set angry to zero around 1 Oct 2020.

**Reaction weight history.** REPORTED. Source: Washington Post, Merrill & Oremus, 26 Oct 2021, "Five points for anger, one for a 'like'". I read the syndicated copy at https://www.adn.com/nation-world/2021/10/26/five-points-for-anger-one-for-a-like-how-facebooks-formula-fostered-rage-and-misinformation/ (WaPo returned 403).
- 2017: "Each emotional reaction was worth five likes at the time." All five emoji were weighted equally at first. Techdirt and Cato criticised the headline as implying that anger alone got 5x.
- 2018: "Facebook cut it [angry] to four times a like".
- 2019: data scientists found that "posts that sparked angry reaction emoji were disproportionately likely to include misinformation, toxicity" and low-quality news.
- Sept 2020: angry was cut "to zero", and "love" and "sad" were boosted "to be worth two likes".
- After the change, "users began to get less misinformation, less 'disturbing' content and less 'graphic violence'", and "users' level of activity on Facebook was unaffected."
- Replies were weighted "up to 30 times as much as a like."
- Discrepancy: CNN's 1.5 and WaPo's 4x are both pre-zero values from different dates. Neither outlet gives a complete dated timeline. Present the sequence 5 → 4 → 1.5 → 0 as reported, not verified.

**Outrage and misinformation findings.** REPORTED.
- WSJ, Hagey & Horwitz, 15 Sept 2021, "Facebook Tried to Make Its Platform a Healthier Place. It Got Angrier Instead". The paywall blocked me, so I relied on reposts. Internal memo: "Misinformation, toxicity, and violent content are inordinately prevalent among reshares". The piece also covers the heavy weighting of reshares and BuzzFeed CEO Jonah Peretti's complaint.
- CNN (same article as above):
  - Nov 2018 memo, "Does Facebook reward outrage?", which said "the current set of financial incentives our algorithms create does not appear to be aligned with our mission."
  - 1 Apr 2019 note: European parties said MSI "changed the nature of politics. For the worse". In Poland, one party's posts went from half negative to 80% negative.

**"Downstream MSI."** UNVERIFIED as a weight. I found no reputable source that gives a numeric weight for it. A Gizmodo-published document titled "[LAUNCH] Replacing Downstream Impact for Civic and Health" shows that the concept existed internally. Do not quote a figure.

**Are the originals accessible?** PRIMARY. Yes, in redacted form.
- Gizmodo Facebook Papers directory: https://gizmodo.com/facebook-papers-how-to-read-1848702919. It hosts the files on DocumentCloud. These titles are the most likely to contain weights:
  - "MSI Documentation": https://www.documentcloud.org/documents/21601216-tier2_rank_other_undated-1
  - "Planned MSI Metric Changes in 2020": https://www.documentcloud.org/documents/21601680-tier0_rank_ro_0920-1
  - "MSI Metric Changes for 2020 H1": https://www.documentcloud.org/documents/21601827-tier2_rank_ro_0120
  - "[LAUNCH] Using p(anger) to Reduce the Impact Angry Reactions Have on Ranking Levers": https://www.documentcloud.org/documents/21601629-tier0_rank_ro_0920
  - "Should We Reduce the MSI Weight of Sticker Comments?": https://www.documentcloud.org/documents/21601969-tier0_rank_pr_0719
  - "Max Reshare Depth Experiment": https://www.documentcloud.org/documents/21602015-tier1_rank_pr_1119
  - "MSI Metric Note Series": https://www.documentcloud.org/documents/21602262-tier2_fa_rank_exp_1119
  - "Political Party Response to '18 Algorithmic Change": https://www.documentcloud.org/documents/21748430-tier2_eu_news_ir_0419
  - "What Happens If We Delete Ranked Feed?": https://www.documentcloud.org/documents/21748432-tier2_news_ir_0218
  - **I could not open these (403).** The team should open them in a browser and cite the page that holds each weight.
- FBarchive.org, from Harvard's Public Interest Tech Lab (lead: Latanya Sweeney). Searchable since 18 Oct 2023 with a free registered account. The names of private individuals are redacted. Sources: https://gijn.org/stories/introducing-fbarchive-a-new-searchable-repository-of-facebook-whistleblower-documents/ and Journalist's Resource.

## 2. Instagram teen research and Instagram ranking

**Teen decks.** PRIMARY. Meta published its own annotated versions on 29 Sept 2021:
- https://about.fb.com/wp-content/uploads/2021/09/Instagram-Teen-Annotated-Research-Deck-1.pdf
- https://about.fb.com/wp-content/uploads/2021/09/Instagram-Teen-Annotated-Research-Deck-2.pdf
- Meta's response post: https://about.fb.com/news/2021/09/research-teen-well-being-and-instagram/
- Per the Boston Globe, the decks are "Teen Mental Health Deep Dive" (2019; 40 teens in qualitative research plus about 2,500 surveyed in the US and UK) and "Hard Life Moments" (a 6-country survey, n≈22,410). I did not verify which deck is No. 1 and which is No. 2.
- REPORTED (WSJ, 14 Sept 2021) and confirmed in substance by Meta:
  - "We make body image issues worse for one in three teen girls." Meta's own post says this means one in three "of those teenage girls who told us they were experiencing body image issues", not one in three of all teen girls.
  - Among teens reporting suicidal thoughts, 13% (UK) and 6% (US) traced the desire to Instagram. Meta's counter: about "1%" of all teens surveyed. Meta gives the sample as 1,296 US teens and 1,309 UK teens.
- I found nothing in these decks about how the ranker works. They measure user perceptions, not ranking outputs.

**How Instagram ranks.** PRIMARY.
- Instagram Engineering, "Scaling the Instagram Explore recommendations system" (9 Aug 2023): https://engineering.fb.com/2023/08/09/ml-applications/scaling-instagram-explore-recommendations-system/
  - Formula: **"Expected Value = W_click * P(click) + W_like * P(like) – W_see_less * P(see less) + etc."**
  - The probabilities come from a multi-task multi-label (MTML) model. The weighted combination is "a formula that we call value model (VM)".
  - "Tuning the weights of the VM allows us to explore different tradeoffs between online engagement metrics." **No weights are published.**
- Mosseri, "Instagram Ranking Explained" (31 May 2023): https://about.instagram.com/blog/announcements/instagram-ranking-explained
  - Feed: "how likely you are to spend a few seconds on a post, comment on it, like it, share it, and tap on the profile photo."
  - Explore: "likes, saves, and shares".
  - Reels: "reshare a reel, watch a reel all the way through, like it, and go to the audio page."

## 3. Meta system cards (PRIMARY)

- Clegg, "How AI Influences What You See on Facebook and Instagram", June 2023: https://about.fb.com/news/2023/06/how-ai-ranks-content-on-facebook-and-instagram/
  - "22 system cards".
  - "predicting that you will share a post is one factor".
  - Some predictions are "based on user feedback received through surveys".
  - "no single prediction is a perfect gauge…"
- Card index: https://transparency.meta.com/features/explaining-ranking/ (fb-feed, fb-reels, fb-stories, ig-feed, ig-explore, ig-stories, ig-reels-chaining, and others).
- **IG Explore** (updated 22 Jun 2026): https://transparency.meta.com/features/explaining-ranking/ig-explore/
  - Prediction targets: follow author; view >5 s; watch >95% of a video; "Not Interested"; comment; like; reshare; click-and-engage; save; full-screen click.
  - Pipeline: about 1,500 candidates → two-tower model keeps the top 100 → late-stage "multi-task, multi-label neural network".
- **IG Feed** (updated 29 Jun 2026): https://transparency.meta.com/features/explaining-ranking/ig-feed/
  - Prediction targets: swipe through the whole carousel; "enjoy this post"; skip; time on the author's profile; DM share; time on post; >10 s on the first post; sound on; session continuation.
  - Ranking: a relevance score over about 500 posts.
- **IG Reels chaining** (updated 11 Nov 2025): https://transparency.meta.com/features/explaining-ranking/ig-reels-chaining/
  - Prediction targets: use the audio; watch <3 s; "Interested"; comment; watch more than 95% of users who watched reels of the same length; full-screen click; reshare; share off-platform; follow.
- **FB Feed** (updated 6 Oct 2026): https://transparency.meta.com/features/explaining-ranking/fb-feed/
  - Prediction targets: scroll past instead of engaging; skip a Story-in-Feed; skip a video channel; click "Interested"; enter full screen; view the likers list; strong intent to engage with a group or with friends; outside-link click and dwell.
  - Ranking: a "relevance score for about 500 posts". Integrity demotions are applied before ranking.
- **What no card gives:** the combination weights, or any formula beyond "relevance score". Use the cards to justify the *prediction targets*, not the *weights*.

## 4. TikTok "Algo 101" (REPORTED)

- Source: NYT, Ben Smith, 5 Dec 2021, "How TikTok Reads Your Mind": https://www.nytimes.com/2021/12/05/business/media/tiktok-algorithm.html. Secondary coverage: Gizmodo (https://gizmodo.com/leaked-tiktok-doc-reveals-its-obvious-secret-to-an-addi-1848166901) and DeepLearning.AI's The Batch (https://www.deeplearning.ai/the-batch/what-makes-tiktok-tick).
- Formula: **Plike × Vlike + Pcomment × Vcomment + Eplaytime × Vplaytime + Pplay × Vplay**. P = predicted probability, E = estimated playtime, V = value weight.
- The document calls the equation "highly simplified".
- Per Gizmodo, TikTok confirmed the document is genuine. The NYT did not publish the document, so it is **not publicly available** and the V values are unknown.
- Stated goals: growing DAU, with retention and time spent as the drivers.

## 5. X/Twitter open-source ranker

**2023 release.** PRIMARY. https://github.com/twitter/the-algorithm-ml, file `projects/home/recap/README.md`, weights "as of April 5, 2023". The score is Σ weight_i × P(engagement_i):

| engagement | weight |
|---|---|
| fav | 0.5 |
| retweet | 1.0 |
| reply | 13.5 |
| good_profile_click | 12.0 |
| video_playback50 | 0.005 |
| reply_engaged_by_author | 75.0 |
| good_click | 11.0 |
| good_click_v2 | 10.0 |
| negative_feedback_v2 | -74.0 |
| report | -369.0 |

**2026 re-release: CONFIRMED.** PRIMARY. https://github.com/xai-org/x-algorithm ("Algorithm powering the For You feed on X", Apache-2.0).
- GitHub API: the repo was created 2026-01-19T23:12:35Z and the first commit is 2026-01-20. The last commit I read is 862a1235 (2026-10-17), out of 51 commits.
- What changed versus 2023:
  - Ranking is now **Phoenix, a Grok-based transformer** that reads the viewer's engagement history, served by a Rust "home-mixer". Retrieval combines Thunder (in-network) with out-of-network sources.
  - **The Jan 2026 release published the action list but not the weights.** The README's "13 Aug 2026" note says that release "Adds key configuration parameters (including weights used to blend predicted action values into a score for a post)". It also adds training code with synthetic data and the visibility-filtering systems.
  - The README says a cron job syncs the defaults in `param.rs` to the "primary production values", so the weights move over time. **Pin the commit SHA when you cite them.**
- README formula: "Final Score = Σ (weight_i × P(action_i))". This is followed by an author-diversity decay, an out-of-network multiplier below 1, a new-author boost, and a separate VM-ranker rerank.
- Negative-score handling: `xai-value-model/scoring.rs` maps (score + |Σneg|)/Σ|w| × offset when the score is negative.
- Weights from `home-mixer/params/param.rs` at commit 862a1235:

| action | weight | action | weight |
|---|---|---|---|
| favorite | 0.66 | share | 2.0 |
| reply | 5.0 (+15.0 bidirectional-follow boost → 20) | share via DM | 5.0 |
| retweet | 1.0 | share via copy link | 20.0 |
| quote | 5.0 | follow author | 4.0 |
| click | 0.3 | dwell (prob.) | 0.05 |
| open link | 0.2 | cont. dwell time | 0.006 |
| photo expand | 0.05 | cont. click dwell time | 0.4 |
| video open | 0.02 | quoted click | 0.05 |
| profile click | 0.0 | VQV | 0.0 |
| post unexplored | 0.015 | not dwelled | -0.02 |
| not interested | -52.272 | mute author | -58.8 |
| block author | -31.2 | **report** | **-234.0** |

- Differences from 2023:
  - Reply drops from 13.5 to 5 (20 between mutual follows).
  - The single negative-feedback term (-74) splits into not-interested, mute and block.
  - Report goes from -369 to -234.
  - New terms for share, copy-link share and continuous dwell time.
  - The "reply engaged by author" weight (75) is gone.
- The README's own example ("468 times higher weight than a like" = 234/0.5) implies the fav weight was 0.5 in August and 0.66 by October. This is direct evidence of drift.
- The repo's own comments are useful for an XAI argument. The weights "reflect a combination of how much an action is valued in ranking and typical propensities", and "the baseline probability of a Report is more than 1000x lower than a Like".
- July 2026 change log for the bidirectional boost: `docs/BIDIRECTIONAL_BOOST_CHANGE.md`. A/B arms tested 5, 10, 15 and 20; 20 rolled out on 13 Jul; it was cut to 15 on 24 Jul. This is a real-world precedent for the "sweep a weight and audit" methodology.
- **Not in the repo:** the production model weights.

## 6. YouTube (PRIMARY, from the papers' own text, which I extracted)

- **Covington, Adams & Sargin, RecSys 2016**, "Deep Neural Networks for YouTube Recommendations": https://research.google/pubs/deep-neural-networks-for-youtube-recommendations/
  - The ranking objective is "generally a simple function of expected watch time per impression".
  - "Ranking by click-through rate often promotes deceptive videos… ('clickbait')".
  - Method: weighted logistic regression in which positive impressions are weighted by watch time. The learned odds are "approximately E[T](1+P)… Since P is small, this product is close to E[T]."
- **Zhao et al., RecSys 2019**, "Recommending What Video to Watch Next: A Multitask Ranking System": https://research.google/pubs/recommending-what-video-to-watch-next-a-multitask-ranking-system/ (doi 10.1145/3298689.3346997)
  - Objectives fall into "engagement objectives" (clicks, watches; classification plus time-spent regression) and "satisfaction objectives" (like, dismissal, rating).
  - Combination: "a combination function in the form of weighted multiplication. The weights are manually tuned".
  - Architecture: MMoE, plus a shallow tower for selection and position bias.
  - **No weights are published.**

## 7. Empirical effect sizes (PRIMARY, peer-reviewed; abstracts via Europe PMC)

| Study | Finding usable as a parameter |
|---|---|
| Brady et al. 2017 PNAS, doi 10.1073/pnas.1618923114 | n=563,312 tweets. Moral-emotional words "increased their diffusion by a factor of 20% for each additional word"; the effect was stronger within ideological groups. |
| Rathje, Van Bavel & van der Linden 2021 PNAS, doi 10.1073/pnas.2024292118 | n=2,730,215 FB and Twitter posts. "Each individual term referring to the political out-group increased the odds of a social media post being shared by 67%". Out-group language was about 4.8x as strong as negative affect and about 6.7x as strong as moral-emotional language. It was a "very strong predictor of 'angry' reactions". |
| Berger & Milkman 2012 JMR, doi 10.1509/jmr.10.0353 | About 7,000 NYT articles. High-arousal emotion (awe, anger, anxiety) is more viral; sadness is less viral. **The frequently cited "+34% odds per 1 SD of anger" is UNVERIFIED**: I saw it only in blogs and could not extract it from the PDF. Check Table 4 of the paper before using it. |
| Guess et al. 2023 Science, doi 10.1126/science.abp9364 | Chronological feed vs algorithmic feed in the 2020 election: "substantially decreased the time they spent". Political and **untrustworthy** content *increased*; uncivil and slur content on FB decreased; no significant change in polarization over 3 months. Critique: Bagchi et al. (2024) argue that Meta's emergency "break-glass" changes reduced misinformation in the control group. That critique is REPORTED; I did not verify its Science eLetter. |
| Guess et al. 2023 Science, doi 10.1126/science.add8424 | Removing reshares cut political news (including untrustworthy sources), clicks and reactions, and lowered news knowledge. No polarization effect. |
| Nyhan et al. 2023 Nature, doi 10.1038/s41586-023-06297-w | Cutting like-minded sources by about one third reduced uncivil exposure and had no attitudinal effect (n=23,377). |
| Amnesty, 7 Nov 2023, "Driven into the Darkness": https://www.amnesty.org/en/latest/news/2023/11/tiktok-risks-pushing-children-towards-harmful-content/ | Over 30 automated accounts posing as 13-year-olds (Kenya, USA). After 5–6 h, "almost 1 in 2 videos were mental health-related and potentially harmful", about 10x the rate for control accounts. Manual accounts: more than half of For You videos were about mental health within 3–20 min. This is an NGO audit, not peer-reviewed. |
| CCDH, Dec 2022, "Deadly by Design": https://counterhate.com/research/deadly-by-design/ | Test accounts as 13-year-olds in 4 countries. Suicide content within 2.6 min and eating-disorder content within 8 min, each on one account. Mental-health and body-image videos about every 39 s. NGO audit; TikTok disputes the method. |
| Molly Russell PFD report, 13 Oct 2022 (ref 2022-0315): https://www.judiciary.uk/prevention-of-future-death-reports/molly-russell-prevention-of-future-deaths-report/ | PRIMARY. The recommendations name "the use of algorithms to provide content". Coroner's conclusion, 30 Sept 2022 (REPORTED full text, e.g. AOL/PA): platforms "operated in such a way using algorithms as to result, in some circumstances, of binge periods of images, video clips and text some of which were selected and provided without Molly requesting them". "16,300 posts saved/liked/shared, 2,100 on depression, self-harm or suicide in the last 6 months" is REPORTED (inquest evidence via The Times and others). I did not verify it against a primary transcript. |

---

## RECOMMENDATION: a defensible simulated ranker

**Architecture.** Industry-standard and documented by YouTube 2019, IG Explore 2023, X 2023/2026 and TikTok 2021.
1. **Candidates.** Synthetic posts with interpretable content features:
   - topic, including a "distress/self-harm-adjacent" flag
   - arousal and valence
   - moral-emotional word count
   - out-group term count
   - format, length, author tie strength, recency
   - Synthetic users carry interest vectors and a vulnerability trait.
2. **Multi-task prediction heads.** One GBM per target (LightGBM/XGBoost; TreeSHAP is exact for these):
   - P(like), P(comment), P(reshare), P(save), P(not-interested/hide), P(report)
   - E[watch-time fraction] (regression)
   - Justification: every target appears in a Meta system card, Mosseri's post, the X action list, or TikTok's formula.
3. **Value model.**
   - score = Σ wᵢ·P̂ᵢ, matching the Explore VM, the X README and the TikTok formula. This is a weighted sum, which keeps SHAP additive across heads. YouTube's weighted product is an alternative worth noting.
   - Optional out-of-network multiplier and author-diversity decay (X).
4. **Feed.** Top-k selection. Then simulate a session feedback loop (the user's interests drift toward what they consume) to reproduce the rabbit-hole dynamic that the Amnesty and CCDH audits describe.
5. **Audit.**
   - SHAP on each head *and* on the composite score. Because the composite is linear in the heads, its attribution = Σ wᵢ·SHAP(headᵢ).
   - Counterfactuals: "what is the minimal feature change that drops this post out of the top-k?"
   - LIME on the composite.

**Value-weight presets.** Report all three. Never present any of them as "Instagram's" weights.

| Preset | Source | Notes |
|---|---|---|
| MSI-2018 | CNN/WaPo (REPORTED) | like 1, reaction 5, simple reshare 5, significant comment/reshare 30, RSVP 15 |
| MSI-2020 | WaPo/CNN (REPORTED) | angry reaction 0, love/sad 2 |
| X-2023 | twitter/the-algorithm-ml (PRIMARY) | fixed by date (5 Apr 2023) |
| X-2026 | xai-org/x-algorithm @862a1235 (PRIMARY) | preferred as the most current *primary* source; changes over time, so pin the SHA |

Map the presets onto the heads explicitly. For example: X `favorite`→P(like), `reply`→P(comment), `retweet`+`share`→P(reshare), `cont_dwell_time`→watch time, `not_interested`/`mute`/`block`→P(hide), `report`→P(report). Disclose that the mapping is approximate.

**Evidence-based parameters** (used to generate synthetic engagement labels):
- Each moral-emotional word: ×1.20 on reshare odds (Brady). Sweep 1.10–1.30.
- Each out-group term: ×1.67 on share odds (Rathje). Sweep 1.3–2.0. Also raises P(angry reaction).
- Arousal: positive effect on sharing, with sadness lower than anger, anxiety or awe (Berger & Milkman, direction only). Do not use 34% until it is verified.
- Distress-content dynamics: use Amnesty's 5–6 h figure (about 1 in 2 videos) and CCDH's minutes-scale onset as **validation targets** for the simulation's emergent behaviour, not as inputs.
- Reality check: per Guess 2023, chronological ranking lowers engagement and time spent but does *not* uniformly lower bad content (untrustworthy content rose). The simulation should be able to reproduce this, not presuppose that "algorithmic = worse".

**Must be assumed and disclosed:**
- Base rates of each action. The only grounding is X's statement that report is more than 1000x rarer than like. Sweep P(like) 2–10%, P(comment) 0.5–3%, P(reshare) 0.2–2%, P(report) 0.001–0.01%. These ranges are assumptions.
- Instagram, Reels and TikTok value weights. **Never published.** Meta calls them tunable tradeoffs.
- Downstream-MSI weight: not public.
- The causal link "engagement → harm to the teen". The Instagram decks are self-reported correlations, and Meta itself says they are "not fit" for statistical estimates.
- Translating NGO audit timelines into model parameters.
- Interactions among features (e.g. vulnerability × distress content): no published estimate.

**Sensitivity sweeps to report:**
- The weight on P(comment), from 1 to 30 relative to like (this spans X-2026's 5 and MSI's 30).
- The angry/outrage-proxy weight: 5 → 1.5 → 0, replaying the 2017–2020 history.
- A negative-feedback weight of 0 vs X-2026 values.
- Ranking-objective swaps: engagement VM vs watch-time-only (YouTube 2016) vs chronological.
- The effect-size multipliers across the ranges above.
- For each sweep, the metric is the share of distress-flagged items in a vulnerable user's top-k over a simulated session, plus whether SHAP and counterfactuals correctly attribute that share to the outrage/distress features. That attribution test is the XAI claim.

**Framing line for the paper:** "The structure (multi-task engagement predictions combined by a linear value model) and the prediction targets are documented by the platforms. The value weights come from leaked (MSI, reported) or open-sourced (X, primary) systems. The content-to-engagement effect sizes come from peer-reviewed studies. Base rates and all Instagram/TikTok weights are assumptions and are swept."
