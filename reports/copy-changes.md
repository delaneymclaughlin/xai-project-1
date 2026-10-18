# Copy changes

What changed between `content/claims.verified.json` and the new page copy in `content/site.json`, and why. Every fact on the page comes from the fact-checked text. Nothing was dropped and no new facts were added. A script checked that all 67 ledger claims appear in the copy and that every claim still carries all of its source ids.

## The big picture

The old site gave every section the same template and every policy card seven labeled fields, and it wrote in long, hedged sentences. The new copy is one scroll with a story arc:

| # | Section | Heading | Paired interactive |
|---|---|---|---|
| 0 | Cold open | What the feed chose for Molly | Stat counters; 2,100 of 16,300 drawn as a dot field |
| 1 | Thesis | Checking IDs at the door | Four lens chips that pin as a progress bar |
| 2 | Act 1, Ethics | Engagement is a choice someone made | Ranking-loop diagram that lights up per principle |
| 3 | Act 2, Law | Twelve measures, one blind spot | Access-to-design spectrum of all 12 measures, filtered by type and explanation level |
| 4 | Act 3, Model | Opening up a feed we built ourselves | Simulated feed with SHAP bars, LIME/SHAP switch, remove-a-signal toggle, test scorecard |
| 5 | Act 4, Public | What the "why am I seeing this" button leaves out | Told-vs-actual split panel; flip cards for the three platform features |
| 6 | Conclusion | The tools to look first already exist | Recap of the four takeaways |
| 7 | Limitations | What this project can't show | none |
| 8 | Sources | Every claim, checked | Searchable ledger with verdict chips |

Each act keeps its research question, its intro, its argument and its takeaway.

## How the writing changed

- **Shorter sentences.** Long multi-clause sentences were split, mostly at "and" or "which". For example, "which determine who is able to use these platforms but do not address the engagement-driven design" became "Those rules decide who gets to use a platform. They leave alone the engagement-driven design that causes the harm in the first place."
- **Less padding.** "Is able to" became "can", "in order to" became "to", and so on. Contractions are used where they read naturally.
- **No em dashes.** The page doesn't use em dashes or "not X but Y" slogans, and it avoids forced lists of three. The places where the copy does say "not X" are your own contrasts, kept on purpose because they carry the argument (for example, "defines the harm by whether a feed is personalized, not by what the feed is optimized to maximize").
- **Sharp headings.** Sentence case, each one making a claim. No more "Philosophical Lens".
- **One-line hooks.** Each principle and method got a short line (for example, Nonmaleficence: "Harm you can see coming is harm you can prevent."). These lines restate your argument. They are not new claims and carry no citations.

## Policy cards: seven fields down to four

Each card used to show Targets, Build, XAI, XAI methods, Feasibility and Gap, plus a status. Now each card has:

1. **Headline:** a one-line verdict drawn from your old "gap" text (for example, Australia: "Keeps under-16s off. Leaves the ranking alone.").
2. **Status:** a short pill (for example, "Partly in effect; in litigation") plus the full dated status text.
3. **What it does:** the old *targets* and *build* text combined.
4. **Explanation?:** the old *xai* and *xai methods* text combined, with a level badge (none, indirect, implicit, global or local).
5. **The catch:** the old *feasibility* and *gap* text combined.

The headline and the status pill are new labels in your voice. Check that you agree with each one. The `spectrum` number on each measure only places its dot on the visual. It is not data, and the page should say so in a caption.

Where two fields repeated a fact, the repeat was cut and the fact kept once:
- **UK:** the annual risk-assessment review now appears once, in "What it does".
- **DSA Art. 27:** "can be read in multiple ways" now appears once, under Explanation.
- **KOSA:** the August 5 committee date now appears once, in Status.
- **New Mexico:** the $567M abatement order now appears once, in Status. The May 2026 bench trial date and the quote "require legislative or executive branch action" are still there.

The planned-bans status is now one item per country, each cited to its own source (Malaysia S41, Indonesia S42, Denmark S40, France S36, Greece S38, Spain S39, UK S37, overview S4). Before, all eight sources sat on one long sentence. The sources come from the same fact-check evidence list.

## Wording you should know about

- **Cold open:** the coroner's finding now comes before the Children's Commissioner's quote, so the legal finding leads. The quotes themselves are unchanged.
- **Beneficence:** "On this essay's reading" is now "On this project's reading", because the page is not an essay.
- **Autonomy:** "autonomy is not merely a choice but the set of conditions that make choice possible" is now "autonomy is the set of conditions that make choice possible, which is more than the choice itself". The meaning is the same without the "not merely X but Y" construction.
- **Memo 3** was retitled from "Require design-stage review for systems that rank content for minors" to "Review ranking systems for minors before they ship". The body is unchanged in substance. All four memos still say "would", because they are proposals.
- **Policy intro:** the sentence listing the old card fields was replaced with one describing the new card layout.

## Simulation numbers are tokens now

No number from the simulation is typed into the copy. Each one is a token like `{{sim.distress_share_top_decile_pct}}`, and `simTokens` in site.json lists every token's current value and where it came from. There are 32 tokens: 29 used in the copy and 3 extra for the interactives. The ledger text for the 12 simulation claims (46–58 and 65) uses the same tokens, so the ledger updates with the page. The phrase "top 10%" is left as plain text because it defines the decile; it is not a result.

Some wording depends on how the simulation comes out, not just on its numbers. Examples are "nearly tied with", "which SHAP did not", "the same two posts stayed at the top", and the Pass/Partial/Fail labels on the tests. These are listed in `simQualitative`. Re-read each one after the model is regenerated.

## Flags carried over from the fact check

- **SHAP units:** test 5 says "a SHAP value in probability units", and the unit is now a token (`shap_units`). TreeSHAP on a classifier reports log-odds by default, so the regenerated simulation must report the unit it actually uses.
- **KOSA, Sept. 30 block:** Rand Paul's block of the passage attempt rests on a single outlet. It's kept because it is in the verified text. If you want to play it safe, cut that clause and keep "not yet law" plus the House bill.
- **Greece:** the final vote is scheduled for Oct. 22, which is after the due date. The line is accurate as of Oct. 18, but it will go stale.
- **~130 a day:** this stat now has visible fine print saying it is a separate pre-inquest count, not an average of the 16,300 posts.
- **Public-feature mock-ups:** the told-vs-actual panel must look like a generic illustration. It must not imitate TikTok's or Meta's real interface.
