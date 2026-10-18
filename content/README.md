# content/

## site.json schema (v1)

`site.json` is the copy for the single-page scrolling story. It is the only file the page should read for text. Treat it as the source of truth and edit it directly.

```ts
type Text = {
  t: string;          // one span of copy (a sentence or a few). May contain {{sim.<key>}} tokens.
  s: string[];        // source ids (keys of `sources`), rendered as citation markers after the span
  claims: number[];   // ledger claim ids this span carries; [] for the author's own analysis
};
type Para = Text[];   // spans rendered inline, joined by a space

type Interactive = {
  id: string;         // component name, e.g. "policy-spectrum", "sim-feed", "told-vs-actual"
  describe: string;   // what the component does (spec for the build step)
  data: string[];     // which parts of site.json it reads
  note?: string;
} | null;

type SectionBase = {
  id: string;         // anchor id: cold-open, thesis, act-ethics, act-law, act-model, act-public,
                      //            conclusion, limitations, sources
  kind: "coldOpen" | "thesis" | "act" | "conclusion" | "limitations" | "sources";
  kicker: string;     // small label above the heading
  heading: string;
  interactive: Interactive;
};

type Site = {
  schemaVersion: 1;
  meta: { title; subtitle; author; affil; asOf: "YYYY-MM-DD"; description };
  simTokens: Record<string, {
    value: number | string | string[];  // raw value from the simulation
    display: string;                    // what replaces {{sim.key}} in copy
    from: string;                       // where the current value came from
    claims: number[];                   // ledger claims that use it
    note?: string;
  }>;
  simQualitative: { where; phrase; holds_if }[];  // wording that depends on sim outcomes
  sections: Section[];                            // in scroll order
  ledger: {
    id: number; text: string; sources: string[];
    verdict: "supported" | "partially_supported" | "outdated" | "pending_simulation";
    section: string;           // section id where the claim appears
    where: string;             // original site/poster location (for the poster)
    simulated?: true;          // S28 claim; text uses {{sim.*}} tokens
  }[];
  sources: Record<string, { title: string; url: string | null }>;  // S1..S70
  simData: object;             // copy of claims.verified.json "demo" (feed, SHAP per post,
                               // completeness, design-side counterfactual) for the interactives
};
```

Section-specific fields:

| kind / id | extra fields |
|---|---|
| `coldOpen` | `paragraphs: Para[]`, `stats: {n, l, fine?, s, claims}[]`, `after: Para[]` |
| `thesis` | `paragraphs: Para[]` |
| `act` (all) | `act: 1..4`, `lens`, `question`, `intro: Para`, `takeaway: Para` |
| `act-ethics` | `pillars: {name, line, body: Para}[]` (4) |
| `act-law` | `measures: Measure[]` (12), `health {heading, body}`, `audit {heading, body}`, `memos {heading, items: {title, relates: measureId[], body}[]}` |
| `act-model` | `proxy {heading, stat {n, l}, body}`, `methods: {name, line, what, result}[]` (3), `designCf {heading, body}`, `testsIntro: Para`, `tests: {name, score, verdict: "pass"\|"mixed"\|"fail", body}[]` (5) |
| `act-public` | `features: {name, says, limits}[]` (3), `gap {heading, body}`, `stakes {heading, body}` |
| `conclusion` | `paragraphs: Para[]` |
| `limitations` | `items: Para[]` |
| `sources` | `intro: Para` (the ledger and sources live at top level) |

```ts
type Measure = {
  id: string; type: "Access" | "Design" | "Transparency" | "Liability";
  juris: string; name: string;
  statusTag: string;          // short pill text
  headline: string;           // one-line verdict (author's analysis, uncited)
  spectrum: number;           // 0 = who can get in .. 100 = how the feed works. Editorial placement for the visual only.
  statusDisplay: "text" | "list";  // "list": render each status span as a list item (planned bans, one per country)
  status: Para; does: Para;
  explain: { level: "none" | "indirect" | "implicit" | "global" | "local"; text: Para };
  catch: Para;                // feasibility + what it leaves untouched
};
```

### Rendering rules

- Replace every `{{sim.key}}` with `simTokens[key].display` at build time, in sections and in `ledger[].text`. A missing key should fail the build.
- A span with `s` gets citation markers linking to `#src-S#`. A span with `claims` links to `#claim-<id>` in the ledger.
- `simData` and `simTokens` are regenerated together by the simulation step. After regenerating, re-read every entry in `simQualitative` and fix the wording if its `holds_if` no longer holds.

Other files here: `claims.verified.json` (fact-checked content, verdicts, evidence) and `source-artifact.json` (original, superseded; do not use for copy).
