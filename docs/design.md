# Design direction: "After dark, into daylight"

Status: build spec for the one-pager. Engineers can build sections in parallel from this file. Where this file and the content disagree, the content wins. Where the content and the fact check disagree, the fact check wins (see "Content source" below).

## 1. Concept

The page begins where the harm happened: a phone screen late at night, in a room with the lights off. The cold open is set on a deep indigo "night" ground with pale moonlit type and one quiet visual: a field of 16,300 small points, one for each post Molly Russell saved, liked or shared in her last six months, with 2,100 of them a little brighter. There is no imagery of distress and no red. As the reader scrolls into the thesis, the page brightens once, slowly, from night to a cool, even daylight. That is the page's single orchestrated moment, and it carries the argument: explainability is the act of putting a ranking system under light and looking at it before harm, not after. Everything after the transition happens in daylight, set like a well-made inquiry report. The type is calm and humane, the structure is plain, and the color is used for exactly one idea. In the simulated feed, every attribution bar is colored by **who controls the signal**. Teal-blue means the signal is about her (her past engagement, who she follows). Madder rose means the signal is about the post and the ranker (emotional intensity, watch completion, comment rate, reactions, recency). The reader can watch rose outweigh teal in the feed, the counterfactual, and the told-versus-actual comparison, and get the thesis without reading a word. The memorable thing is the feed instrument in the technical lens. Everything around it stays quiet.

What it is not: not cream/charcoal/orange, not near-black with an acid accent, not a broadsheet with hairlines, not a grid of identical rounded cards, no ALL-CAPS eyebrows, no "01 / 02" markers on content that is not a sequence, no monospace data labels, no arrows appended to links.

## 2. Content source and data rules (read before building anything)

- **The only content source is `content/claims.verified.json`.** It has the same shape as `content/source-artifact.json`, but the wording is fact-checked, and the sources run S1 to S70 (not S28). Never copy text from `source-artifact.json`. Never paraphrase claim text inside a component. Render `t` fields verbatim and attach their `s` sources.
- **No hardcoded numbers in components.** Every figure (16,300, 2,100, 47.4%, 35.1%, SHAP values, ranks) is read from the JSON at build time. The simulation (S28) is being regenerated in a later step, so `demo.*` and the S28 claims will change. Components must render whatever the data says, and must not break if a post's rank or a percentage changes.
- **Never invent model behavior in the browser.** All SHAP values, rankings and counterfactual feeds are precomputed. Interactives select among and animate between precomputed states only. No sliders that "recompute" SHAP, and no interpolated scores.
- **Stats in the cold open:** use `stats[0]` (16,300) and `stats[1]` (2,100) only. `stats[2]` (~130 a day) comes from a separate pre-inquest count, and the fact check recommends dropping it from prominent display. Show it at most as a small, fully labeled footnote-level line using its verified label, or omit it. `stats[3]` (2x risk, ages 12 to 15) belongs in the thesis bridge with its verified label.
- **Simulation claims are labeled as simulation everywhere.** Any number sourced to S28 shows the "Simulated" marker (section 8.6) next to it.
- **Data contract the simulation step should emit** (engineers code against these keys; until they exist, derive values as noted):
  - `demo.feed[]`: `rank, name, title, distress_related, score, features{}` (exists)
  - `demo.shap.per_post[name][feature]` (exists)
  - `demo.shap.base_value`: the model's expected value. Until it exists, derive it as `score - sum(shap)` for the top post, and assert in dev that this is the same (±0.001) for every post.
  - `demo.feature_side[feature]`: `"her"` or `"design"`. Until it exists, use this fixed map: `topic_history: her`, `from_followed: her`, and `emotional_intensity, reactions, comment_rate, watch_completion, hours_old: design`.
  - `demo.counterfactuals.design_side.new_feed[]` (exists) plus `design_side.top_decile_share_pct` (until it exists, read 38.0 from the `technical.design_cf` claim; do not hardcode it in a component, put it in one adapter file).
  - `demo.counterfactuals.user_side` (optional): if present, it enables the second toggle in 8.3.
  - `demo.completeness.*` and `demo.proxy_effect.*` (exist)
- Put all JSON-to-view shaping in one module, `src/lib/content.ts`. Components import typed objects from it and never reach into the raw JSON.

## 3. Color tokens

One theme, two grounds. The page deliberately has a night ground (cold open, and the start of the thesis) and a day ground (everything else). There is no separate dark mode: the night and day grounds are the design, and each section sets `color-scheme` to match its ground so form controls and scrollbars agree.

Put this in `src/styles/global.css` after `@import "tailwindcss";`. Use `@theme` so Tailwind generates utilities (`bg-day`, `text-ink-2`, `border-rule`, and so on).

```css
@theme {
  /* Night ground: cold open */
  --color-night: #172036;      /* page ground at night: deep indigo, not black */
  --color-night-2: #222D4A;    /* raised surfaces on night (content note, popovers at night) */
  --color-moon: #DCE3F0;       /* primary text on night */
  --color-moon-2: #A3AECA;     /* secondary text on night */
  --color-dot: #8792A8;        /* the 16,300 field, unlit points (decorative) */

  /* Day ground: everything after the transition */
  --color-day: #EEF1F3;        /* page ground: cool, even daylight */
  --color-day-2: #E1E6EB;      /* "light table" inset behind the instruments */
  --color-surface: #FAFBFC;    /* popovers, open profile panels */
  --color-ink: #1A2233;        /* primary text */
  --color-ink-2: #465166;      /* secondary text, captions */
  --color-ink-3: #566176;      /* tertiary: metadata, axis labels (min size 14px) */
  --color-rule: #C3CBD5;       /* dividers and outlines (decorative, not text) */
  --color-neg: #6B7486;        /* negative attribution bars, inactive marks */

  /* The one semantic hue pair: who controls the signal */
  --color-her: #2C6A80;        /* signals about her (teal-blue) */
  --color-her-tint: #D3E4EA;
  --color-her-night: #7FB8CC;  /* same meaning, on night */
  --color-design: #9E3A5E;     /* signals about the post and the ranker (madder rose) */
  --color-design-tint: #F1D9E2;
  --color-design-night: #E39AB5;

  /* Focus */
  --color-focus: #2848C8;      /* focus ring on day */
  --color-focus-night: #A9BCFF;/* focus ring on night */
}
```

Rules:
- Rose and teal mean "design-side" and "her-side". Nothing else on the page may use them: no rose links, no teal buttons, no decorative tints. Links are `ink` with an underline.
- Distress-related posts are never marked in rose (that would conflate content with design). They get the text tag "Distress-related" and a small open-ring glyph in `ink-2`.
- No gradients as decoration. The single gradient on the page is the night-to-day transition (section 6.2).
- Shadows: none, except popovers (`0 1px 2px rgb(26 34 51 / .08), 0 8px 24px rgb(26 34 51 / .12)`). Hierarchy comes from ground changes (`day` vs `day-2` vs `surface`) and rules.
- Radius is not one value for everything. Text-like controls (chips, toggles): `9999px`. Instrument panels: `6px`. Popovers: `8px`. Bars: `1px`. Section grounds: `0`.

Contrast (WCAG 2.2, computed; AA body text needs 4.5:1, large text and UI graphics need 3:1):

| Foreground | Background | Ratio | Allowed use |
|---|---|---|---|
| ink #1A2233 | day #EEF1F3 | 14.02 | all text |
| ink-2 #465166 | day | 7.04 | body, captions |
| ink-3 #566176 | day | 5.50 | metadata, 14px+ |
| ink | day-2 #E1E6EB | 12.66 | all text |
| ink-2 | day-2 | 6.36 | captions in instruments |
| ink-3 | day-2 | 4.97 | axis labels, 14px+ |
| ink | surface #FAFBFC | 15.35 | popover text |
| ink-2 | surface | 7.71 | popover secondary |
| moon #DCE3F0 | night #172036 | 12.57 | all text on night |
| moon-2 #A3AECA | night | 7.30 | secondary on night |
| moon | night-2 #222D4A | 10.56 | content note text |
| moon-2 | night-2 | 6.14 | secondary in content note |
| her #2C6A80 | day / day-2 / surface | 5.32 / 4.80 / 5.82 | bars and text labels |
| design #9E3A5E | day / day-2 / surface | 5.75 / 5.19 / 6.29 | bars and text labels |
| her-night #7FB8CC | night | 7.43 | night use only |
| design-night #E39AB5 | night | 7.37 | night use only |
| ink | her-tint / design-tint | 12.16 / 11.94 | text on tinted chips |
| neg #6B7486 | day / day-2 | 4.14 / 3.74 | graphics only, not text |
| focus #2848C8 | day / day-2 | 6.49 / 5.86 | focus rings |
| focus-night #A9BCFF | night | 8.74 | focus rings on night |

Do not use: `ink-3` on `night` (2.60), `dot` for any text (2.76 on day), `rule` for anything that must be seen (1.44). Teal versus rose differ by hue only (1.08:1 luminance), so the feed never relies on that difference alone. Bars are also **grouped by position** ("About her" first, then "About the post and the ranker") with text group labels (section 8.2).

## 4. Typography

Two families, clearly distinct, both on Google Fonts, both variable:

- **Literata** (serif; optical size axis 7 to 72, weight 200 to 900, with italics). Literata was designed for long-form reading on screens. It is used for all prose, all headings, the cold open, and the pull lines. At display sizes, set `font-optical-sizing: auto` so the large settings get the tighter, higher-contrast optical cut. That makes the type itself the visual in the cold open and the thesis.
- **Atkinson Hyperlegible Next** (sans; weight 200 to 800, with italics). The Braille Institute designed it for low-vision legibility, a fitting choice for a page about who systems are built for. It is used for everything that works like an instrument: controls, feature labels, axis labels, numeric readouts, the sources ledger table, citation markers and popovers. Numeric readouts use `font-variant-numeric: tabular-nums lining-nums`. If a build check shows the font lacks `tnum` (compare `getBoundingClientRect().width` of "111" and "888"), set numeric readouts in Literata with `tabular-nums lining-nums` instead. Do not bring in a monospace face.

Astro Fonts API (Astro 7.4; the `fonts` key is top level, not experimental):

```js
// astro.config.mjs
import { defineConfig, fontProviders } from "astro/config";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  fonts: [
    {
      provider: fontProviders.google(),
      name: "Literata",
      cssVariable: "--font-literata",
      weights: ["300 800"],
      styles: ["normal", "italic"],
      subsets: ["latin"],
      fallbacks: ["Georgia", "serif"],
    },
    {
      provider: fontProviders.google(),
      name: "Atkinson Hyperlegible Next",
      cssVariable: "--font-atkinson",
      weights: ["400 700"],
      styles: ["normal", "italic"],
      subsets: ["latin"],
      fallbacks: ["system-ui", "sans-serif"],
    },
  ],
  vite: { plugins: [tailwindcss()] },
});
```

In `Layout.astro` `<head>`: `import { Font } from "astro:assets";` then `<Font cssVariable="--font-literata" preload />` and `<Font cssVariable="--font-atkinson" />`. In CSS:

```css
@theme inline {
  --font-serif: var(--font-literata);
  --font-sans: var(--font-atkinson);
}
```

`body` defaults to `font-serif`. Instruments and controls opt into `font-sans`.

### Scale

This is the classical scale from *The Elements of Typographic Style* (6, 7, 8, 9, 10, 11, 12, 14, 16, 18, 21, 24, 36, 48, 60, 72), with a 16px root. Use only these steps. Add them to `@theme` as `--text-*`:

| Token | Desktop | 390px | Family / weight | Line height | Use |
|---|---|---|---|---|---|
| `--text-cold` | 72px | 36px | Literata 350, opsz auto | 1.08 | Cold open lines |
| `--text-display` | 60px | 36px | Literata 400 | 1.1 | Thesis statement, conclusion line |
| `--text-h2` | 36px | 24px | Literata 450 | 1.2 | Lens questions (the section heading) |
| `--text-h3` | 24px | 21px | Literata 500 | 1.3 | Principle names, measure names, method names |
| `--text-lead` | 21px | 18px | Literata 400 | 1.55 | Lens intro paragraph, takeaways |
| `--text-body` | 18px | 18px | Literata 400 | 1.65 | Prose |
| `--text-ui` | 16px | 16px | Atkinson 500 | 1.4 | Controls, feed post titles |
| `--text-small` | 14px | 14px | Atkinson 400 | 1.45 | Captions, axis labels, ledger rows, popovers |
| `--text-micro` | 12px | 12px | Atkinson 600 | 1.3 | Citation markers only |

Responsive sizes use `clamp()` between the two columns, for example `--text-cold: clamp(2.25rem, 1.2rem + 4.5vw, 4.5rem)`.

Usage rules:
- Measure: prose at most 66ch (`max-w-[66ch]`), lead at most 58ch, display lines at most 18ch. Nothing over 80ch.
- Headings are sentence case. No ALL CAPS anywhere, including labels and buttons. No letter-spacing on labels. Display sizes get `letter-spacing: -0.01em`. Nothing else is tracked.
- Each lens heading is the lens's question (`philosophy.q`, `policy.q`, and so on), set in `text-h2`. The lens name ("Philosophical", "Policy", "Technical", "Public") appears only in the lens rail (6.3) and the table of contents. It does not appear as an eyebrow above the heading.
- Emphasis inside prose is italic Literata, and only where the content already implies it. Never color or bold a single word in a headline.
- Takeaways (`*.takeaway.t`) are set in Literata italic `text-lead`, in `ink`, with a 2px `ink` rule on the left (hanging into the gutter on desktop). This is the only recurring pull-line treatment.
- Numbers in prose use Literata's default old-style figures. Numbers in instruments use lining tabular figures.

## 5. Grid and spacing

- Spacing unit is 4px. Use Tailwind's default spacing scale. Section rhythm tokens: `--space-section: clamp(6rem, 4rem + 8vw, 10rem)` between lenses and `--space-block: clamp(2.5rem, 2rem + 2vw, 4rem)` between blocks inside a lens.
- Container: `max-width: 1200px`, side gutters `16px` (below 640px), `32px` (640 to 1023px), `48px` (1024px and up).
- Desktop grid (1024px and up): 12 columns, 24px gaps. Three named tracks, built as CSS grid areas on a shared `.page-grid` utility so every section aligns:

```
| rail (cols 1-2) | text (cols 3-8)           | margin (cols 9-12)          |
| lens rail       | prose, 66ch max           | sidenotes, source previews  |
|                 | wide (cols 3-12) for instruments                          |
```

- `text` is where prose lives. It stays left aligned and ragged right; never justify.
- `wide` (cols 3 to 12) is for instruments: the policy spectrum, the feed, the scorecard, and told-versus-actual.
- `margin` holds the "Simulated" notes and the short source previews on desktop. It collapses to inline below 1024px.
- Tablet (640 to 1023px): rail hidden (replaced by the top progress line), `text` and `wide` both span the full container.
- Mobile (below 640px): one column, 16px gutters. See section 10.

## 6. Section-by-section layout spec

Page order and anchors (one `<main>`, each section an `<section aria-labelledby>`):

`#open` cold open → `#thesis` → `#ethics` → `#policy` → `#evidence` (technical) → `#public` → `#conclusion` → `#limits` → `#sources`

The skeleton is a reading sequence, but the four lenses are not a sequence of steps, so they are **not numbered**. The rail shows them as places, not steps.

### 6.1 Cold open (`#open`, night ground, `color-scheme: dark`)

Attention goes to one sentence at a time, then to the field of points.

```
desktop                                        390px
+--------------------------------------------+ +----------------------+
| [content note, small, night-2 panel]       | | [content note]       |
|                                            | |                      |
| In November 2017, Molly Russell, a         | | In November 2017,    |
| 14-year-old from Harrow, north-west        | | Molly Russell ...    |
| London, died ...            (hook[0])      | |                      |
|                                            | | .................... |
| ::::::::::::::::::::::::::::::::::::::::   | | ::::::::·:::::::::·: |
| :::::·::::::::::·:::::::::::·:::::::::::   | | (field, full width)  |
|  16,300  saved, liked or shared            | | 16,300 ...           |
|   2,100  related to depression, ...        | |  2,100 ...           |
|                                            | |                      |
| Pinterest ... "10 depression pins ..."     | | hook[2] ...          |
| hook[3], hook[4]                           | |                      |
| Title / subtitle / author / affil (small)  | | title block          |
+--------------------------------------------+ +----------------------+
```

- **Content note first**, before any facts. It sits in a `night-2` panel, Atkinson `text-small`, `moon` text: one plain sentence saying the page discusses a teenager's death and self-harm content, plus support lines: "In the US, call or text 988 (Suicide & Crisis Lifeline). In the UK, call Samaritans on 116 123." The same support lines repeat in the footer. This is required, not optional.
- **hook[0]** in `text-cold`, Literata 350, `moon`, at most 18ch per line. Render the verified wording exactly, which uses the coroner's language. Never write "took her own life".
- **The field.** A `<canvas>` with exactly `stats[0].n` points (parse the number), in a regular grid, reading order left to right and top to bottom. Points are 2px squares with a 2px gap on desktop and 1px with a 1px gap below 640px. Choose columns so the field fills `wide` and the aspect ratio is roughly 3:1. Unlit points are `dot` at 35% opacity. Exactly `stats[1].n` points are lit in `moon` at 100%, chosen by a **seeded** shuffle (fixed seed, so every visit shows the same field). The caption under the field, in Atkinson `text-small`, `moon-2`, reads: "Each point is one post. The brighter points are the 2,100 related to depression, self-harm or suicide. Their positions are illustrative: the inquest reported counts, not order." (Pull the numbers from data.) The canvas has `role="img"` and an `aria-label` that states both counts.
- **Stat pair** under the field: `16,300` and `2,100` in Literata `text-h2` lining figures, `moon`, each followed by its verified label in `moon-2` `text-body`. Their citation markers sit after the labels. They are not cards and not big-number tiles with gradients. They are two lines of type aligned on the figure.
- hook[2] (the Pinterest email), hook[3] and hook[4] follow in `text-lead`, `moon`, at a 58ch measure. Set the Pinterest subject line as a quotation in italics, not as a fake email graphic.
- The title block closes the cold open, small and quiet: `title` in Literata `text-h3`, `subtitle` in `text-lead` italic, and `author` and `affil` in Atkinson `text-small` `moon-2`. The title is deliberately not the hero. The facts are.
- The cold open has no animation of its own. The field draws once (no sparkle, no twinkle, no counting up).

### 6.2 Transition: night to day (from the end of `#open` through the top of `#thesis`)

- A fixed full-viewport background layer (`position: fixed; inset: 0; z-index: -1`) carries the ground color. A scroll-driven animation on it, `animation-timeline: view()` attached to a 100vh spacer element `#dawn` between the cold open and the thesis, interpolates `background-color` from `night` to `day` over the spacer's travel (`animation-range: entry 0% exit 50%`). Text color in `#dawn` and the thesis's first block crossfades from `moon` to `ink` on the same timeline.
- Contrast during the blend: the transition spacer contains only one short line, `stats[3]` (the 2x risk, with its verified label and citation), and that line's color must be readable at every point. Implement it as two stacked copies (`moon` and `ink`) whose opacities crossfade, so text and ground never meet at mid-grey. Test at 50% scroll with a contrast checker.
- Fallback: wrap it in `@supports (animation-timeline: view())`. Without support, or with `prefers-reduced-motion: reduce`, there is no fixed layer. `#open` and `#dawn` have a static `night` ground, `#thesis` onward has a static `day` ground, and the boundary is a plain horizontal edge. The `stats[3]` line sits on night in `moon`.
- Nothing else on the page is scroll-animated as decoration. The rest of the motion responds to the reader's actions.

### 6.3 Lens rail (desktop only, 1024px and up)

- A sticky list (`position: sticky; top: 33vh`) in the `rail` column, from `#ethics` through `#public`. It has four entries: "Philosophical", "Policy", "Technical", "Public". Atkinson `text-small`, `ink-3`. The active entry turns `ink`, weight 600, and gets a 2px `ink` bar on its left. Active state comes from an `IntersectionObserver` on the four lens sections (threshold: the section that contains the viewport's 40% line).
- Entries are in-page links (`<nav aria-label="Lenses">`). The active one gets `aria-current="true"`.
- Tablet and mobile: a 2px progress line fixed at the top of the viewport (`ink` on `rule`), plus the current lens name in a small `day`-colored bar that appears only after `#thesis` scrolls out. It is 40px tall, Atkinson `text-small`, and it never covers headings (add `scroll-margin-top: 56px` to all anchors).

### 6.4 Thesis (`#thesis`, day)

- `thesis.t` is long (three sentences), so it is not set entirely at display size. The first sentence is `text-display` Literata 400, `ink`, at most 22ch, as the page's statement. The remaining two sentences are `text-lead`, `ink-2`, 58ch. The split is by sentence, done in `content.ts`, without changing the text.
- Below it is a quiet table of contents: the four lens questions as links in `text-body`, each preceded by its lens name in `ink-3`. It is a plain list, not cards. It tells the grader the structure up front.
- Attention: the display sentence, then the four questions.

### 6.5 Philosophical lens (`#ethics`)

- Heading: `philosophy.q` (`text-h2`). Then `intro.t` (`text-lead`).
- The four principles are not a sequence, so they are not numbered and not shown as four cards. Each principle is a two-track row on desktop: the principle name in Literata italic `text-h3`, hanging in a narrow left track (cols 3 to 4), and `body.t` in `text-body` (cols 5 to 10). Rows are separated by a 1px `rule` above each. On mobile the name stacks above the body.
- Optional quiet device (build it only if there is time): a one-line, Atkinson `text-small`, `ink-3` note under each name saying where it shows up in the evidence ("See the feed: emotional intensity"). These link to `#evidence` anchors. Use them only where the mapping is explicit in the content. Do not invent mappings.
- Close with `takeaway.t` in the pull-line treatment.

### 6.6 Policy lens (`#policy`)

- Heading: `policy.q`. Then `intro.t`.
- **The policy spectrum** (instrument, `wide`, 8.1).
- Then `health.t` and `audit.t` as prose in `text`.
- Then the four memos (`memos[]`). These are recommendations, not a sequence, so they are not numbered. Each one is a title in Literata `text-h3` with its body in `text-body`, in a two-column layout on desktop (two by two, `gap-x-12 gap-y-10`). There are no boxes and no shadows; a 2px `ink` top rule over each title is the only device.
- `takeaway.t` pull line.

### 6.7 Technical lens (`#evidence`): the centerpiece

- Heading: `technical.q`. Then `intro.t`, with the "Simulated" marker.
- **Methods strip:** LIME, SHAP and Counterfactuals as three columns on desktop (stacked on mobile). Each has the method name in `text-h3`, `what.t` in `text-body` `ink-2`, then `result.t` in `text-body` `ink`. Tie the columns together with one rule above the strip, not three boxes.
- **The feed instrument** (8.2) on a `day-2` "light table" panel spanning `wide`. This is where the reader's attention should land on the page. Give it the most vertical space, with `--space-block` above and below.
- **Remove-a-signal toggle** (8.3) inside the same panel, below the feed. `proxy.t` and `design_cf.t` sit beside it on desktop (in `margin`) and below it on mobile.
- `tests_intro.t`, then the **five-tests scorecard** (8.4).
- `takeaway.t` pull line.

### 6.8 Public lens (`#public`)

- Heading: `public.q`. Then `intro.t`.
- `features[]` (TikTok, Meta, EU): three rows. Each has the feature name in `text-h3`, then two columns, "What it says" (`says.t`) and "What it leaves out" (`limits.t`). Those two small labels are the only column labels on the page, and they earn their place because the comparison is the point.
- **Told versus actual** (instrument, `wide`, 8.5) follows, built from `public.gap` and `demo.completeness`.
- `stakes[]` as prose. Then the `takeaway.t` pull line.

### 6.9 Conclusion (`#conclusion`)

- Full daylight, generous space above (`--space-section` times 1.5). The conclusion's last sentence ("Every meaningful correction to date has come after someone was harmed, and the tools to look before that point already exist.") is set in `text-display` at most 24ch. The preceding sentence is set above it in `text-lead`. Split by sentence in `content.ts`.
- No animation. Nothing competes with the line.

### 6.10 Limitations (`#limits`)

- Heading in `text-h3`: "Limitations". Four items in `text-body` `ink-2`, as a plain bulleted list with `ink-3` en-dash markers. They sit in `text`, not hidden in a disclosure, because a grader should see them.

### 6.11 Sources and claims ledger (`#sources`)

- Heading in `text-h3`: "Sources and claims". A one-sentence note explains that every claim on the page was checked against its sources on the fact-check date (taken from the data, not hardcoded) and that simulated results are marked.
- **The ledger** (8.7), then the full numbered source list.
- Footer: author, affiliation, course, the support lines from the content note, and "Built with Astro." Atkinson `text-small`, `ink-3`.

## 7. Shared primitives (build these first; every section uses them)

| Component | File | Notes |
|---|---|---|
| `Cite` | `src/components/Cite.astro` | Renders citation markers for an `s` array (see 8.6). Every `t` with sources goes through it. |
| `Claim` | `src/components/Claim.astro` | Takes a `{t, s, id}` and renders the text plus `Cite`. Adds `data-claim-id`, which the ledger links back to. |
| `Simulated` | `src/components/Simulated.astro` | The S28 marker (8.6). `Cite` adds it automatically when `s` includes the simulation source. |
| `Section` | `src/components/Section.astro` | Grid areas, anchor, `aria-labelledby`, `scroll-margin-top`, spacing. Props: `id`, `ground` (`night` or `day`). |
| `Takeaway` | `src/components/Takeaway.astro` | The pull-line treatment. |
| `Toggle`, `Chip` | `src/components/ui/*.astro` | The only two control styles (8.0). |

### 8.0 Control styles (used by every instrument)

- **Chip** (filters and selections): height 36px (44px hit area via padding or `::after`), radius full, Atkinson `text-small` 500. Off: `ink-2` text, 1px `rule` border, transparent fill. On: `ink` text, `surface` fill, 1px `ink` border, plus a leading check glyph (an SVG, 12px) so the state is not conveyed by fill alone. Uses `aria-pressed`.
- **Toggle** (the counterfactual switches): a `<button role="switch" aria-checked>` with a 40×24 track (`rule` off, `ink` on) and a visible text label that states the action in words ("Remove emotional intensity from the ranker"). A state line beside it reads "Off" or "On" in `ink-3`.
- Hover: underline the label or darken the border by one step. No lift, no shadow, no scale.
- Focus: `outline: 2px solid var(--color-focus); outline-offset: 2px` (`focus-night` on night). It always uses `:focus-visible` and is never removed.

## 8. Interactive specs

All interactives are vanilla TypeScript in an Astro `<script>`. They read data from a `<script type="application/json" id="…-data">` emitted at build time from `content.ts`, and they are **server-rendered in their default state**. With JavaScript off, every instrument shows its default state and all text is present. JavaScript adds behavior only.

### 8.1 Policy spectrum and filter (`src/components/PolicySpectrum.astro`)

Purpose: show at a glance that most measures stand far from the ranking system, and let the reader open any measure's profile.

Layout (desktop):

```
How close does the measure get to the ranking system?
Doesn't touch it                                              Changes it
|--- Access ---------|--- Liability ------|--- Transparency ---|--- Design ----------|
   (o) (o)              (o) (o)              (o) (o) (o)          (o)(o)(o)(o)(o)
   au  bans             kgm nm               dsa risk minors      ny ca uk aiact kosa
[Filters: All · Access · Design · Transparency · Liability]  [ ] Requires an explanation
---------------------------------------------------------------------------------------
Open profile:  New York, USA, SAFE for Kids Act
  Status ...        Targets ...        What it requires building ...
  Explanation required ...   XAI methods ...   Feasibility ...   What it leaves untouched ...
```

- Axis: four ordered bands, left to right: **Access** (decides who sees the feed), **Liability** (assigns responsibility after harm), **Transparency** (discloses or explains), **Design** (changes how the feed is built). The axis title is the question above. Its end labels are "Doesn't touch it" and "Changes it". The order is an argument, so state it in one caption sentence under the axis, in `ink-2`. Bands are separated by 1px `rule` ticks. Band names are Atkinson `text-small` `ink-2`, sentence case.
- Marks: one 28px circle per measure (44px hit target). Fill is `ink` when the measure is in effect or decided, and a 2px `ink` ring when it is pending, proposed or under challenge. Derive this from a `status_state` field in `content.ts` (`"in_effect" | "pending"`), mapped by hand per measure id from the verified `status.t`. Every mark has a short text label under it (the jurisdiction short name), so marks are never anonymous. Inside a band, marks are ordered by jurisdiction name.
- **Do not imply proportions of legislation.** The 12 marks are "measures profiled here", and the caption must say so. Band widths are equal and do not scale with counts.
- Filters: type chips (All, Access, Design, Transparency, Liability) plus one switch, "Requires an explanation" (true where `xai.t` does not start with "None"; compute this in `content.ts` and review it by hand). Filtered-out marks drop to `neg` at 40% opacity, get `aria-disabled="true"`, and are skipped by arrow-key navigation. They are not removed from the axis, so the shape of the argument stays visible. A live count reads "Showing 5 of 12 measures" (`aria-live="polite"`).
- Selection: clicking or pressing Enter on a mark opens its profile in a `surface` panel under the axis (radius 6px). Default open: the first Access measure (`au`), so the gap statement is visible without interaction. The profile shows the jurisdiction and name (`text-h3`), then a two-column definition list of `status`, `targets`, `build`, `xai`, `xai_methods`, `feasibility` and `gap`. Each has a plain label ("Status", "What it targets", "What it requires building", "Explanation required", "XAI methods that could show compliance", "Feasibility", "What it leaves untouched") and its `Claim`. "What it leaves untouched" is always last and set in Literata italic `text-lead`. It is the point of each profile.
- Keyboard: marks form a single tab stop with roving tabindex. Arrow Left/Right move through visible marks in axis order, Home/End jump to the ends, and Enter/Space select. Implement as `role="listbox"` with `aria-orientation="horizontal"`, options with `aria-selected`, and the profile panel `aria-labelledby` the selected option. Selecting updates the panel without moving focus.
- Mobile (below 640px): the axis rotates to vertical, a list of four bands top to bottom with marks as rows ("Australia, Social media minimum age law" with its fill or ring glyph). Tapping a row expands its profile inline under the row (an accordion with `aria-expanded`). Filters become a horizontally wrapping chip row (wrap, never scroll).

### 8.2 Simulated feed with attribution bars (`src/components/FeedInstrument.astro`)

Purpose: show that the top of a 14-year-old's simulated feed is driven more by design-side signals than by her own behavior.

Layout (desktop, inside the `day-2` panel, two panes):

```
+-- Her feed (simulated) ------------+-- Why Post A ranked #1 ------------------------+
| 1  Sad-edit video about feeling    |  Score 0.964   (starts from average 0.40)      |
|    alone          (o) Distress-rel.|                                                |
|    [====================] 0.964    |  About her                                     |
| 2  Late-night venting post ...     |   Past engagement with this topic  ████████ +.21|
| 3  Mental health hotline ...       |   From an account she follows    ▌        -.02 |
| 4  Cousin's new puppy              |  About the post and the ranker                 |
| ...                                |   Emotional intensity of the post  █████████ +.22|
|                                    |   Avg. watch completion            ███      +.07|
|                                    |   ...                                          |
|                                    |  Her signals: +.19   Design signals: +.37      |
+------------------------------------+------------------------------------------------+
 Simulated: a model trained on simulated impressions, not a real platform.
```

- **Left pane, the feed:** an ordered list of the 8 posts by `rank`. Each row has the rank figure (Atkinson tabular, `ink-3`), `title` (Atkinson `text-ui`, `ink`), the "Distress-related" tag with an open-ring glyph when `distress_related`, and a thin score bar (4px, `ink` at 70%, width = score) with the score value in tabular figures. Do not show "Post A" style names as the primary label; titles are what a reader understands. Keep the name in `aria-describedby` text only. No thumbnails, no fake avatars, no like counts, no emoji. The feed is drawn as a plain list, not as a phone mockup.
- **Right pane, attribution for the selected post** (default: rank 1):
  - Header: "Why [title] ranked #[rank]" in Literata `text-h3`, with "Score [score]" and "starts from the average prediction, [base_value]" in Atkinson `text-small` `ink-2`.
  - Bars are **grouped by side**, in two labeled groups: "About her" (teal) then "About the post and the ranker" (rose). Within a group, sort by absolute SHAP value, descending. The labels are `demo.feature_labels` with "the user" changed to "her" only if the content adapter supplies that variant. Otherwise use the labels verbatim.
  - Bar geometry: a horizontal diverging bar from a zero line placed at 35% of the track width (so negatives have room). Positive values extend right; negative values extend left in `neg` with the side shown by a 2px left cap in the side color. Bar height 14px, 10px row gap, radius 1px. The scale is shared across all 8 posts: the max absolute SHAP across the whole feed equals the track's positive extent. The scale must not change between posts, so they stay comparable. The value label sits at the bar end, in tabular `ink`, with a sign (+0.225 or −0.019, using a real minus sign, U+2212), to 3 decimals.
  - Footer readout: "Her signals: +x.xxx" (teal text), "Post and ranker signals: +x.xxx" (rose text), and "Total change from average: +x.xxx", which must equal `score − base_value` (assert in dev). Under it is one sentence in `ink-2`: "SHAP values are in units of predicted engagement probability."
- Selection: clicking a feed row or pressing Enter selects it. The row gets a `surface` fill and a 2px `ink` left bar. The attribution pane updates.
- Motion: on selection change, bars animate width from old to new over 240ms `cubic-bezier(.2,.7,.2,1)`. Values update immediately (no counting up). Under reduced motion, swap instantly.
- Live region: a visually hidden `aria-live="polite"` node announces "Post ranked 3, Mental health hotline awareness post. Largest factor: past engagement with this topic, plus 0.12." This is built from data.
- Accessible data: below the panel, a `<details>` titled "Show these values as a table" contains a real `<table>` of all 8 posts × 7 features. This is also the no-JS fallback for comparing posts.
- Keyboard: the feed is a `role="listbox"` (vertical, roving tabindex, Up/Down/Home/End, Enter selects). Focus remains in the list.
- Mobile: the panes stack. Feed first; selecting a row scrolls the attribution pane's header into view only if it is off-screen (use `scrollIntoView({block:"nearest"})`, instant under reduced motion). Bar labels go above their bars (a two-line row) so the track gets the full 358px width.
- Tablet: the panes stack, as on mobile.

### 8.3 Remove-a-signal toggle (`src/components/RemoveSignal.astro`, rendered inside the feed panel)

Purpose: show that removing one design signal changes the aggregate a little but leaves the top of her feed the same.

- Control: a Toggle labeled "Retrain without emotional intensity". On is the counterfactual model.
- Effects when on:
  1. The feed list reorders to `counterfactuals.design_side.new_feed`. Animate with FLIP (measure old positions, apply new order, transform from old to new, 400ms). Rows that keep their rank do not move, and that stillness is the point. Under reduced motion, reorder instantly and briefly outline the rows that changed (1px `ink` outline for 1s, no motion).
  2. The attribution pane dims (opacity .45) with the overlay line "Attributions shown are for the original model. The retrained model's values aren't part of this demo." Only show it if the simulation does not emit per-post SHAP for the retrained model. If it does, use them and drop the line.
  3. **Proxy meter**: a single horizontal 100% bar under the toggle showing the "share of distress-related posts in the top 10% of rankings". Two markers: "Overall share of posts" (`proxy_effect.sensitive_share_overall_pct`, a thin `ink-3` tick) and "Top 10%" (a filled `ink` segment). Off = `sensitive_share_top_decile_pct`. On = `design_side.top_decile_share_pct`. The segment width animates over 400ms (instant under reduced motion). The numbers are tabular readouts beside the segment.
  4. A result sentence, `aria-live="polite"`, built from data. On: "Top 10% share falls from 47.4% to 38.0%. Her top two posts don't change." (Compute "don't change" from the data by comparing the top-2 names. If the regenerated data says otherwise, the sentence must say what actually happened. Write both branches.) Off: "Original model."
- If `counterfactuals.user_side` exists: a second Toggle, "Set her past engagement with this topic to zero", with the same reorder behavior and its own live sentence. The two toggles are mutually exclusive (turning one on turns the other off) and grouped in a `role="group"` labeled "Counterfactuals". If it does not exist, render `technical.methods[2].result` (the counterfactual result claim) as text next to the toggle instead.
- `Simulated` marker on the meter.

### 8.4 Five-tests scorecard (`src/components/Scorecard.astro`)

Purpose: show that the explanations pass the technical tests and fail the human ones.

- Five rows, in the content's order (Fidelity, Faithfulness, Completeness, Stability, Human usefulness). That order is Dr. Bent's framework order, so the rows may be shown as a list but **not numbered**.
- Each row is a grid: `[verdict glyph] [test name, text-h3] [verdict word(s)] [expand control]`. When expanded, it shows `body.t` (a `Claim`).
- Verdict glyphs (16px SVG, `ink`, always paired with the verdict text from `score`, never on their own):
  - Pass: a filled circle.
  - Partial: a half-filled circle.
  - Fail: an open ring with a 2px stroke.
  - Mixed scores like "Pass / Partial" show two glyphs.
  Parse `score` with a small mapping in `content.ts` (keys: `pass`, `partial`, `fail`), keeping the full original `score` text as the visible label, including qualifiers like "(in this case)" and "(platform-style)".
- No green/red. Color is not used for verdicts at all; the glyph shape and the word carry them.
- A summary line above the rows, built from data: "3 pass, 1 partial, 2 fail across 5 tests" (count glyph instances). Atkinson `text-small` `ink-2`.
- Expand behavior: each row is a `<details>`/`<summary>` (native keyboard and screen reader support). Default: all collapsed except "Human usefulness", which is open, because it carries the argument's turn. Opening animates height with `interpolate-size: allow-keywords` and `transition: height 200ms` where supported. Otherwise it opens instantly.
- Mobile: the verdict word wraps under the test name. The glyph stays on the left.

### 8.5 Told versus actual (`src/components/ToldVsActual.astro`)

Purpose: show how much of the top post's ranking a platform-style reason accounts for.

```
What she's told
  "This video is similar to content you've interacted with"
  [██████████████ 35.1% ][                    64.9% left unsaid                    ]

What drove the ranking (SHAP shares of the top post)
  [teal: past engagement 35.1%][rose: emotional intensity 37.5%][rose ...][...]
                               ^ the largest single factor
  [ Show what the reason leaves out ]
```

- Two aligned 100% bars, 20px tall, the same width, one above the other, in `wide`.
- **Told bar**: one teal segment at `platform_style_reason_share_pct`, then the remainder as an empty segment with a 1px `rule` dashed outline, labeled "[left_out]% left unsaid" in `ink-2`. The reason text above it is in Literata italic `text-lead`, inside quotation marks, exactly as `completeness.platform_style_reason`.
- **Actual bar**: the top post's positive SHAP contributions as shares of their sum, one segment per feature, in the side color (teal for her, rose for design). 1px `surface` gaps separate segments. Segments of 6% or more are labeled inline. Smaller ones are labeled on hover/focus and in the legend list below. The largest segment gets a caret and the label "Largest single factor". Compute shares in `content.ts` and check them against `completeness.shap_top_reason_share_pct` (assert in dev, ±0.2). If negative contributions exist, note under the bar: "Shares are of the positive contributions; [feature] pushed the score down by [x]."
- Control: one Chip/Toggle, "Show what the reason leaves out". When on, the told bar's empty segment fills with the actual design-side segments in rose tint (`design-tint`, each segment labeled), making the hidden part visible. When off, it is empty. 300ms crossfade, instant under reduced motion. Live sentence: "The one-line reason leaves out 64.9% of the ranking, including emotional intensity, the largest single factor." Built from data.
- Below: `public.gap.t` as a `Claim`, plus the `Simulated` marker.
- Mobile: bars keep full width (358px), inline segment labels move to a legend list beneath (swatch, label, share). A swatch is a 10px square in the side color. The legend also groups by side.

### 8.6 Citation markers and popovers (`Cite.astro` + one shared script)

- Marker: each source becomes a superscript-like inline button placed after the sentence's final period. It shows the source's ordinal number (S29 shows as "29"), with multiple sources as "29, 1, 2". Atkinson `text-micro` 600, `ink-2`, raised with `vertical-align: super; line-height: 0` so it does not open the line spacing. Each number is its own `<button type="button" aria-label="Source 29: [title]">` with a hit area of at least 24×24 (via padding plus negative margin). On night, it is `moon-2`.
- Popover: built with the native Popover API (`popover="auto"` on a single shared `<div id="cite-pop">`, filled on open, positioned with CSS anchor positioning where supported, with a JS fallback that measures the button rect and clamps to the viewport with 16px margins). 320px max width (on mobile, the viewport width minus 32px, pinned to the bottom of the viewport as a sheet). `surface` ground, radius 8px, popover shadow. Contents:
  1. Source title (Atkinson `text-small` 600, `ink`).
  2. The link: "Open source" plus the domain in `ink-2`, `target="_blank" rel="noopener"`.
  3. "Claim [id] in the ledger" link, which jumps to the ledger row and opens it.
  4. For S28 (the simulation): instead of a link, the sentence "Result from this project's simulation; see Limitations."
- Behavior: click or Enter toggles. Esc closes (native). Focus moves into the popover on open and returns to the marker on close. Light-dismiss is native. Hover does not open (on touch devices there is no hover, and hover-to-open fights with reading).
- `Simulated` marker: an inline label "Simulated" in Atkinson `text-micro` 600, `ink-2`, with a 1px `ink-3` dotted underline, placed after numbers sourced to S28. It is a button that opens the same popover with the simulation sentence. In instruments, it appears once per instrument caption, not on every value.
- No-JS: markers render as `<a href="#src-29">` links to the source list.

### 8.7 Sources ledger (`src/components/Ledger.astro`)

Purpose: let a grader audit any claim on the page against its sources and the fact check.

- A real `<table>` (Atkinson `text-small`) with columns: "Claim" (id, tabular), "Text" (the verified claim text), "Sources" (ordinal links to the source list), "Appears in" (from `where`, "Site:" part only), and "Check" (status).
- Check status, derived from `factcheck[id]`: "Checked against sources" for external claims, "Simulation result" for S28 claims (pending regeneration), and "Wording corrected" when `factcheck[id].changed` is true. Statuses are words, with no colored badges. A `<details>` in each row ("Fact-check note") shows the `note` and the evidence URLs. It does not show the old "before" text by default; that sits behind a second nested disclosure, "Show original wording", so the page never presents superseded claims as current.
- Controls above the table: a search input (`<input type="search">`, label "Find a claim", filters rows by text and source, debounced 120ms), and Chips to filter by section ("Hook", "Philosophical", "Policy", "Technical", "Public") and by check status. A live count reads "Showing 12 of 67 claims" (`aria-live="polite"`).
- Default view: the first 12 rows plus "Show all 67 claims" (a button that reveals the rest; it does not navigate). Rows are targetable by `#claim-[id]`. Arriving via a hash expands the table, scrolls to the row (`scroll-margin-top: 56px`), and gives it a 2s `day-2` highlight (static under reduced motion: it stays highlighted until the next interaction).
- Mobile: the table becomes a list of row blocks (claim id and status on one line, text, then sources and location), using CSS grid on `tr` elements with `display: grid` and visible inline labels. Semantics stay a table (keep `role` defaults; add `data-label` text for the visible labels).
- After the ledger: the source list as an `<ol>` with `id="src-N"` per entry, title, and full URL as a link (`overflow-wrap: anywhere` so long URLs never cause horizontal scroll).

## 9. Motion rules

- One orchestrated moment: the night-to-day transition (6.2). There are no entrance animations on sections, no fade-and-slide-up, no parallax, no counting-up numbers, and no hover lifts.
- Everything else answers an action: bar width changes (240ms), feed reorder FLIP (400ms), proxy meter (400ms), told-vs-actual reveal (300ms), disclosure height (200ms). Easing is `cubic-bezier(.2,.7,.2,1)` for all of them. Put these in tokens: `--ease-out: cubic-bezier(.2,.7,.2,1)`, `--dur-quick: 200ms`, `--dur-base: 240ms`, `--dur-reorder: 400ms`.
- Scroll-driven animations only use CSS (`animation-timeline`), never scroll listeners. The rail and the progress line use `IntersectionObserver`, and the progress line uses `animation-timeline: scroll(root)` where supported (otherwise it is hidden, not shown in a JS-driven version).
- `@media (prefers-reduced-motion: reduce)`: all durations become 0ms, the night-to-day layer is replaced by static grounds (6.2), the FLIP becomes an instant reorder plus a static outline, and smooth scrolling is off. Check `matchMedia('(prefers-reduced-motion: reduce)')` in JS before animating, and listen for changes.
- `html { scroll-behavior: smooth }` only inside `@media (prefers-reduced-motion: no-preference)`.

## 10. Mobile behavior at 390px

- Gutters are exactly 16px, so the content width is 358px. `html, body { overflow-x: clip }` is a backstop only. Every component must fit on its own; test at 360px too.
- No component may scroll horizontally, including the policy chips (wrap), the ledger (row blocks), long URLs (`overflow-wrap: anywhere`), the feed table in `<details>` (on mobile, the table transposes to one block per post with its 7 values as a definition list), and the canvas field (sized to the container width with `devicePixelRatio` scaling).
- Type steps down per the scale table. Body stays 18px.
- The rail is replaced by the top progress line and the lens-name bar (6.3).
- All tap targets are at least 44×44. Citation markers are at least 24×24 with the spacing rule from WCAG 2.5.8.
- The citation popover becomes a bottom sheet (full width minus 16px margins, max height 60vh, scrollable inside).
- Instruments stack per their specs. Nothing relies on hover.

## 11. Accessibility requirements

- **Structure:** one `h1` (the page title, in the cold open's title block, visually small but semantically first-level). Each section heading is an `h2` and each item heading is an `h3`. Landmarks: `header` (content note), `nav` (lens rail and table of contents), `main`, `footer`. Add a skip link to `#thesis` ("Skip to the argument") as the first focusable element, visible on focus.
- **Keyboard:** every interactive is operable by keyboard alone, following the patterns specified (listbox with roving tabindex for marks and the feed, `switch` for toggles, native `details` for disclosures, native popover for citations). No keyboard traps. Esc closes the popover. The tab order follows the reading order.
- **Focus:** a visible `:focus-visible` ring on everything (2px, 2px offset, `focus` or `focus-night`). Focus is never moved by scroll or by a live update. It moves only into and back out of the popover.
- **Live regions:** one polite live region per instrument (feed selection, counterfactual result, told-vs-actual reveal, policy filter count, ledger count). They announce full sentences built from data, at most one per action. Never use `assertive`.
- **Contrast:** use only the pairs in the table in section 3. Graphics that carry meaning (bars, rings, glyphs, focus rings) are at least 3:1 against their ground. Meaning is never conveyed by color alone: sides are grouped and labeled as well as colored, verdicts use glyph plus word, and pending versus in-effect status uses ring versus fill plus text in the profile.
- **Non-text content:** the canvas field gets `role="img"` and a label. Each instrument has a visually hidden summary sentence at its top, built from data (for example, "Simulated feed of 8 posts. The top two are distress-related. Select a post to see why it ranked where it did."). Decorative SVGs get `aria-hidden="true"`.
- **Text resizing:** the page must work at 200% zoom and with 400% reflow (that is the 390px layout). Use rem for type and allow zoom (no `maximum-scale` in the viewport meta).
- **Language and tone:** the content note and support lines are present at the top and in the footer. No content flashes, autoplays or loops.
- **Testing checklist before merge:** keyboard-only pass through every instrument, VoiceOver on Safari for the feed and popovers, axe with zero violations, and Lighthouse accessibility at 100. Check that 390px and 360px widths have no horizontal scroll (`document.documentElement.scrollWidth === innerWidth`) and that reduced motion has been checked with the OS setting on.

## 12. Build ownership and consistency checklist

Engineers can split work as: (A) tokens, fonts, Layout, `Section`, `Cite`/`Claim`/`Simulated`, popover, `content.ts`; (B) cold open, transition, thesis, rail; (C) policy lens and spectrum; (D) technical lens, feed, remove-a-signal, scorecard; (E) public lens, told-vs-actual, conclusion, limitations, ledger. A goes first, and the others code against its interfaces.

Before calling a section done, check that:
- it uses only tokens from section 3 and scale steps from section 4 (no raw hex or px font sizes in components);
- rose and teal appear only as signal-side encoding;
- there are no ALL CAPS, no tracked labels, no numbered markers on non-sequences, no card grids with shadows, no arrows on links, and no monospace;
- every number comes from `content.ts`, and every S28 number carries the Simulated marker;
- every `t` with sources renders through `Claim`/`Cite`, and the text matches `claims.verified.json` exactly;
- it works with JavaScript off, at 390px, at 200% zoom, with reduced motion, and by keyboard alone.
