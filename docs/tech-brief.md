# Tech brief: one-page static site on Astro 7.4 + Tailwind 4.3 + Cloudflare Workers

Written 2026-10-18 for the `build/one-pager` branch. Every snippet below was **built and checked** in a scratch copy of this repo, using the installed `astro@7.4.0`, `vite@8.3.4`, `tailwindcss@4.3.3` and `@tailwindcss/vite@4.3.3`, plus `wrangler@4.151.1` installed only in that scratch copy. "Verified" means `astro build` succeeded and the emitted `dist/` HTML/CSS was inspected, or `wrangler deploy --dry-run` succeeded. Each claim was checked against the installed types in `node_modules/astro/dist/types/public/config.d.ts`, `node_modules/astro/components/Font.astro` and `node_modules/astro/dist/assets/fonts/**`, as well as the official docs listed at the end.

Environment facts:
- Node >= 22.22.0 (the `engines` field in both `package.json` and astro's own `package.json`). Local Node is 22.23.3.
- Astro 7 ships Vite 8 (Rolldown), Zod 4 and the Rust `.astro` compiler.
- Output is `"static"` by default. Do **not** add `output`, `adapter` or `@astrojs/cloudflare`.

---

## 1. Target file layout

```
astro.config.mjs          # fonts + tailwind vite plugin
wrangler.jsonc            # assets-only Worker (no main)
src/styles/global.css     # @import "tailwindcss"; @theme tokens
src/layouts/Layout.astro  # <head>: <Font/> tags, meta, global.css import
src/pages/index.astro     # the one page
src/pages/404.astro       # optional; served by not_found_handling "404-page"
src/components/*.astro    # sections; interactives as custom elements + <script>
src/icons/*.svg           # imported as components
content/source-artifact.json  # imported directly (no content collection needed)
```

Import the content as plain JSON: `import data from "../../content/source-artifact.json";`. The strict tsconfig preset resolves JSON modules, so this needs no loader or collection. Its top-level keys are `title, subtitle, author, affil, hook, stats, thesis, philosophy, policy, technical, public, conclusion, limitations, sources, ledger, demo`.

---

## 2. Fonts API (stable since v6, top-level `fonts`)

This is **not** `experimental.fonts` any more. That flag was removed in v6, and putting it under `experimental` is a type error. Helpers come from `astro/config`. The `<Font />` component comes from `astro:assets`.

### Config (verified)

```js
// astro.config.mjs
// @ts-check
import { defineConfig, fontProviders } from "astro/config";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  site: "https://<name>.<subdomain>.workers.dev", // optional; set once known
  vite: { plugins: [tailwindcss()] },
  fonts: [
    {
      provider: fontProviders.fontsource(),
      name: "Source Serif 4",
      cssVariable: "--font-source-serif",
      weights: ["200 900"],          // variable font: give a range string
      styles: ["normal", "italic"],
      subsets: ["latin"],
      fallbacks: ["Georgia", "serif"],
    },
    {
      provider: fontProviders.google(),
      name: "Inter",
      cssVariable: "--font-inter",
      weights: [400, 600],           // numbers or strings both accepted
      styles: ["normal"],
      subsets: ["latin"],
      fallbacks: ["system-ui", "sans-serif"],
    },
  ],
});
```

Per-family options and their defaults, from the installed types:

| key | type | default |
|---|---|---|
| `provider` | `fontProviders.{adobe,bunny,fontshare,fontsource,google,googleicons,local,npm}()` (call the function) | required |
| `name` | family name as the provider knows it | required |
| `cssVariable` | must start with `--` | required |
| `weights` | `Array<number\|string>`; `"100 900"` for a variable range | `[400]` only |
| `styles` | `"normal" \| "italic" \| "oblique"` | `["normal","italic"]` |
| `subsets` | `string[]` | `["latin"]` |
| `formats` | `"woff2" \| "woff" \| "otf" \| "ttf" \| "eot"` | `["woff2"]` |
| `fallbacks` | `string[]`; end with a generic family | `["sans-serif"]` |
| `optimizedFallbacks` | boolean (size-adjust metric fallbacks) | `true` |
| `display` | `auto\|block\|swap\|fallback\|optional` | `"swap"` |
| also | `unicodeRange`, `stretch`, `featureSettings`, `variationSettings`, `options` (provider-specific) | |

What the build does (observed):
- The font files are downloaded at build time and self-hosted under `dist/_astro/fonts/*.woff2`. They are cached in `node_modules/.astro/fonts`, so the **first build needs network**.
- `<Font />` inlines a `<style>` with the `@font-face` rules and a `:root{--font-source-serif: "<hashed family>", "<hashed family> fallback: Times New Roman", Georgia, serif;}` declaration.
- The metric fallback is computed from the generic family (`serif` gives Times New Roman, `sans-serif` gives Arial). It is inserted **before** your listed fallbacks.
- If you use a weight in CSS that isn't in `weights`, the browser synthesizes it (faux bold). List every weight you use.

Local files (if needed): use `provider: fontProviders.local()` with `options: { variants: [{ src: ["./src/assets/fonts/X.woff2"], weight: "400", style: "normal" }] }`. Keep the files in `src/`, not `public/`, or they ship twice.

### `<Font />` in the layout `<head>` (verified)

```astro
---
// src/layouts/Layout.astro
import { Font } from "astro:assets";
import "../styles/global.css";
const { title, description } = Astro.props;
---
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{title}</title>
    <meta name="description" content={description} />
    <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
    <!-- preload only the face used above the fold -->
    <Font cssVariable="--font-source-serif" preload={[{ weight: 400, style: "normal" }]} />
    <Font cssVariable="--font-inter" />
  </head>
  <body>
    <slot />
  </body>
</html>
```

The props come from `node_modules/astro/components/Font.astro`:
- `cssVariable` must match a configured family. Otherwise the build throws `FontFamilyNotFound`, and the prop is typed as a union of your variables.
- `preload` takes `boolean | Array<{ weight?, style?, subset? }>`, and defaults to `false`, which means no preload.
  - `preload` (true) preloads **every** file of the family.
  - A filter like `[{ weight: 400, style: "normal" }]` matches inside a variable range. In the verified build, `400` matched `"200 900"` and only the roman file was preloaded, not the italic.
  - The emitted tag is `<link rel="preload" href="/_astro/fonts/<hash>.woff2" as="font" type="font/woff2" crossorigin>`.
- Every `cssVariable` you use in CSS needs its own `<Font />`. Without it the variable is undefined and the text falls back silently.

Also exported from `astro:assets`: `fontData` (resolved data keyed by cssVariable) and `experimental_getFontFileURL`. Neither is needed here.

### Wiring into Tailwind v4 (verified)

Use **`@theme inline`** when a theme value references another variable. The docs prescribe this, and it makes the utility emit `font-family: var(--font-source-serif)` directly:

```css
@theme inline {
  --font-serif: var(--font-source-serif);
  --font-sans: var(--font-inter);
}
```

Built CSS contains `.font-serif{font-family:var(--font-source-serif)}`. Without `inline`, the utility points at Tailwind's own `--font-serif` variable, which in turn points at the Astro variable. That is an extra layer of indirection the Astro docs don't use. Use `inline` for font aliases.

---

## 3. Tailwind CSS 4.3 with Astro

Already configured: `@tailwindcss/vite` is in `vite.plugins`, and `src/styles/global.css` contains `@import "tailwindcss";`. Do **not** add `@astrojs/tailwind` (deprecated, v3 only), `tailwind.config.js` or `postcss.config.*`. In v4 the configuration lives in CSS.

Import the stylesheet once, in the layout frontmatter (`import "../styles/global.css";`). Don't `<link>` it from `public/`.

### Editorial `global.css` (verified to compile)

```css
@import "tailwindcss";

/* font aliases -> Astro Fonts variables */
@theme inline {
  --font-serif: var(--font-source-serif);
  --font-sans: var(--font-inter);
}

/* design tokens: each generates utilities (bg-paper, text-ink, text-accent, border-rule, xs:...) */
@theme {
  --color-ink: oklch(0.22 0.02 260);
  --color-ink-muted: oklch(0.45 0.02 260);
  --color-paper: oklch(0.985 0.005 90);
  --color-rule: oklch(0.88 0.01 90);
  --color-accent: oklch(0.55 0.19 28);
  --breakpoint-xs: 30rem;
}

/* custom utilities: use @utility, NOT @layer utilities (v3 syntax) */
@utility measure { max-width: 68ch; }

/* class/attribute-driven dark mode if a toggle is wanted; default is prefers-color-scheme */
@custom-variant dark (&:where([data-theme=dark], [data-theme=dark] *));

@layer base {
  html { @apply bg-paper text-ink font-serif; }
}
```

Best practice for a long-form editorial page:
- Put tokens in `@theme`, not in arbitrary values. Use `--color-*`, `--font-*`, `--text-*`, `--spacing`, `--breakpoint-*`. Tokens become utilities and also CSS variables usable in component `<style>` blocks as `var(--color-accent)`.
- Cap body copy at `measure` (about 65 to 70ch). Use `font-serif` for prose and `font-sans` for UI, labels, charts and tables. Use `tabular-nums` for numbers in tables and charts.
- Use `text-balance` on headings and `text-pretty` on paragraphs (both built into v4).
- Long prose: `@tailwindcss/typography` is not installed. Skip it. Write a small `@layer base` or `.prose`-like block by hand, since there is only one page.
- Respect motion: `motion-safe:` and `motion-reduce:` variants.
- Class names built at runtime (`"bg-" + color`) are not detected. Write full class names literally, or toggle `data-*` attributes and style them with `data-[state=on]:...` variants.
- Astro scoped `<style>` blocks can use `@apply` only after `@reference "../styles/global.css";` at the top of that block. Prefer plain CSS with `var(--color-*)` there instead.

---

## 4. Deploying to Cloudflare Workers: static assets, no adapter

This was verified with `wrangler 4.151.1`. `npx wrangler deploy --dry-run` printed "Read N files from the assets directory ... No bindings found. --dry-run: exiting now." No Cloudflare login is needed for a dry run.

### `wrangler.jsonc` (repo root)

```jsonc
{
  "$schema": "./node_modules/wrangler/config-schema.json",
  "name": "xai-feed-brief",
  // set to the deploy date
  "compatibility_date": "2026-10-18",
  "assets": {
    "directory": "./dist",
    "not_found_handling": "404-page",
    "html_handling": "auto-trailing-slash"
  }
}
```

Notes, checked against developers.cloudflare.com (Wrangler configuration, Static Assets, and the Astro framework guide) and docs.astro.build/en/guides/deploy/cloudflare/:
- **No `main`.** The Wrangler configuration reference says "The `main` key is optional for assets-only Workers." Do not add `binding` or `run_worker_first`, because both only matter when a Worker script exists.
- `not_found_handling` takes `"none"` (the default, which returns a bare 404), `"404-page"` (serves the nearest `404.html`) or `"single-page-application"`. Use `"404-page"` and ship `src/pages/404.astro`. **Do not use SPA mode**: it would return `index.html` with a 200 status for every typo URL.
- `html_handling` takes `"auto-trailing-slash"` (the default, fine with Astro's `/index.html` output), `"force-trailing-slash"`, `"drop-trailing-slash"` or `"none"`. Listing it explicitly is optional.
- `.wrangler/` is created locally by `wrangler dev`, so add it to `.gitignore`.
- Do **not** install `@astrojs/cloudflare`, and do not set `output: "server"`. The adapter is only for SSR, and it changes the build output layout.

### `package.json` changes

```bash
npm i -D wrangler@^4.151.1
```

```json
"scripts": {
  "dev": "astro dev",
  "build": "astro build",
  "preview": "astro preview",
  "astro": "astro",
  "deploy": "astro build && wrangler deploy",
  "deploy:dry": "astro build && wrangler deploy --dry-run",
  "cf:dev": "astro build && wrangler dev"
}
```

`wrangler 4.151.1` was published 2026-10-16, two days ago. It installed and dry-ran cleanly. The caret range resolves to it.

---

## 5. Other Astro 7 features worth using on one static page

### Client-side scripts (vanilla TS, no framework)
- A bare `<script>` with no attributes, or only `src`, is **processed**: it is TypeScript, bundled with its imports, emitted as `type="module"`, deduplicated per page, and inlined when small. Since v6, scripts and styles render **in source order where you put them**. The old hoisting to `<head>` is gone. In the verified build the script stayed at the end of `<body>`.
- Any other attribute (`is:inline`, `define:vars`, `type="..."`, `async`) opts **out** of processing. The script then has no TS, no imports and no bundling, and it is duplicated per component instance. So **don't use `define:vars`** for the demo.
- Pass server data to the client through `data-*` attributes and read them with a custom element. This pattern was verified; TS non-null assertions and `as` casts compile fine:

```astro
---
import data from "../../content/source-artifact.json";
---
<feed-demo data-config={JSON.stringify(data.demo)}>
  <button type="button">Run</button>
  <output></output>
</feed-demo>

<script>
  class FeedDemo extends HTMLElement {
    connectedCallback() {
      const cfg = JSON.parse(this.dataset.config ?? "{}") as Record<string, unknown>;
      this.querySelector("button")!.addEventListener("click", () => {
        this.querySelector("output")!.textContent = String(Object.keys(cfg).length);
      });
    }
  }
  customElements.define("feed-demo", FeedDemo);
</script>
```

If the precomputed `demo` payload is large, `import` the JSON **inside** the `<script>` instead of serializing it into an attribute. Vite then bundles it as a hashed JS chunk.

### SVG as components (stable)
`import Dot from "../icons/dot.svg";` gives `<Dot width={12} height={12} fill="currentColor" aria-hidden="true" />`. The build inlined an `<svg>` element, and props override attributes in the file. Use `SvgComponent` from `astro/types` to type them. Good for icons and diagram glyphs.

### Images
`<Image />` and `<Picture />` from `astro:assets` (sharp is installed) support `layout="constrained" | "full-width" | "fixed"` and `priority` (eager loading plus high fetchpriority; use it on at most one hero image). Most figures here will be hand-built SVG or HTML charts, so this is only relevant if a raster image is added.

### Optional: `security: { csp: true }` (stable since v6)
Verified on static output. Astro emits a `<meta http-equiv="content-security-policy">` with sha256 hashes for its own scripts and styles, including the `<Font />` styles. If you enable it:
- **Never** write `style="..."` attributes in markup, and never call `el.setAttribute("style", …)`. Both are blocked. Setting `el.style.width = …` from JS (the CSSOM) is fine.
- No inline `on*=` handlers.
- The build always warns about Shiki. That warning is harmless when no code blocks are rendered.

Recommendation given the deadline: **leave it off** unless there is time to click through every interactive.

### Experimental flags present in 7.4 types (none needed)
`clientPrerender`, `contentIntellisense`, `chromeDevtoolsWorkspace`, `svgOptimizer` (`import { svgoOptimizer } from "astro/config"`; `experimental: { svgOptimizer: svgoOptimizer() }` builds fine), `collectionStorage`, `incrementalBuild`, `redirectPage` (7.4), `parallelPrerender` (7.4). For a single page, `svgOptimizer` is the only one that could help, and only marginally. Skip it. Don't add the removed flags `fonts`, `csp`, `rustCompiler`, `queuedRendering`, `cache` or `logger`; they are stable or top-level now.

### Dev server
Per AGENTS.md, run `astro dev --background`, then `astro dev status|logs|stop`. These subcommands are new in v7.

---

## 6. Gotchas agents commonly get wrong in Astro 6/7

1. **Whitespace collapses JSX-style by default.** `compressHTML` defaults to `'jsx'` since v7. This was verified, and it matters a lot for prose with inline links and citations. This source:
   ```astro
   <p>
     Breaks before
     <a href="#">link</a>
     and after.
   </p>
   ```
   renders `Breaks before<a>link</a>and after.`, with the spaces lost.
   - Text and inline elements on one line keep their spaces (`One line <a>link</a> stays.` is fine).
   - Fix 1: keep inline runs on one line, or insert `{" "}` at line breaks next to inline elements.
   - Fix 2: set `compressHTML: true` in the config to restore v6 behavior. Verified: the same source then renders `Breaks before <a>link</a> and after.` with the spaces kept.

   **Recommendation: set `compressHTML: true`**, because this page is mostly long prose with inline citation links. Visually re-check citations either way.
2. **The Rust compiler is strict.** Unclosed non-void tags are build errors. Invalid nesting such as `<div>` inside `<p>` or `<figure>` inside `<p>` is no longer auto-fixed, so the browser closes the `<p>` early. Use `<div>` wrappers for blocks that contain figures or lists.
3. **Fonts are top-level `fonts`**, not `experimental.fonts`. The provider is a function call (`fontProviders.google()`). `<Font />` is imported from `astro:assets`. In Tailwind, use `@theme inline`.
4. **Tailwind v4 is configured in CSS.** There is no `tailwind.config.js`, no `@tailwind base/components/utilities` and no `@astrojs/tailwind`. Use `@utility` for custom utilities.
5. **No Cloudflare adapter for static sites.** Use an assets-only `wrangler.jsonc` with no `main`. Use `"404-page"`, not SPA, for `not_found_handling`.
6. **Scripts are not hoisted** (since v6), and any extra attribute disables processing.
7. Removed or renamed APIs:
   - `Astro.glob()` is gone; use `import.meta.glob()`.
   - `<ViewTransitions />` is now `<ClientRouter />`. It isn't needed for a single page; don't add it.
   - Import Zod from `astro/zod`.
   - `import.meta.env` values are no longer coerced, so `"true"` stays a string.
8. **`src/fetch.ts` is reserved** in v7 (advanced routing). Don't create a file with that name.
9. **Markdown now renders with Sätteri** by default. Remark and rehype plugins need `@astrojs/markdown-remark` with `markdown.processor: unified()`. This doesn't matter here, because the content is JSON.
10. **Type checking:** `astro check` needs `@astrojs/check` and `typescript`, which are not installed, and it prompts to install them. Use `astro build` as the gate. It fails on template and compile errors, but it does not type-check `<script>` TS.

---

## 7. Final `astro.config.mjs` to use

```js
// @ts-check
import { defineConfig, fontProviders } from "astro/config";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  compressHTML: true, // keep spaces around inline links in prose (see gotcha 1)
  vite: { plugins: [tailwindcss()] },
  fonts: [
    {
      provider: fontProviders.fontsource(),
      name: "Source Serif 4",
      cssVariable: "--font-source-serif",
      weights: ["200 900"],
      styles: ["normal", "italic"],
      subsets: ["latin"],
      fallbacks: ["Georgia", "serif"],
    },
    {
      provider: fontProviders.google(),
      name: "Inter",
      cssVariable: "--font-inter",
      weights: [400, 600],
      styles: ["normal"],
      subsets: ["latin"],
      fallbacks: ["system-ui", "sans-serif"],
    },
  ],
});
```

The font families are suggestions. Any family on Fontsource or Google works the same way, but keep the `cssVariable` names in sync with `@theme inline` and the `<Font />` tags.

Ship checklist:
1. Run `npm run build`, then inspect `dist/index.html`. Check spacing around links, check that the fonts load, and check for console errors.
2. Run `npm run deploy:dry`.
3. Run `npm run deploy`. This needs `wrangler login` or `CLOUDFLARE_API_TOKEN`.

---

## Sources

- Installed types: `node_modules/astro/dist/types/public/config.d.ts` (`fonts` at about line 2919, `experimental` at about line 3258, `compressHTML` default `'jsx'`), `node_modules/astro/components/Font.astro`, `node_modules/astro/dist/assets/fonts/providers/index.d.ts`, `node_modules/astro/dist/assets/fonts/types.d.ts`, `node_modules/astro/dist/config/entrypoint.d.ts`, `node_modules/astro/client.d.ts`.
- Astro docs:
  - https://docs.astro.build/en/guides/fonts/
  - https://docs.astro.build/en/guides/upgrade-to/v7/
  - https://docs.astro.build/en/guides/upgrade-to/v6/
  - https://docs.astro.build/en/guides/client-side-scripts/
  - https://docs.astro.build/en/guides/images/
  - https://docs.astro.build/en/guides/deploy/cloudflare/
- Astro blog: https://astro.build/blog/astro-6/ and https://astro.build/blog/astro-7/
- Cloudflare:
  - https://developers.cloudflare.com/workers/static-assets/
  - https://developers.cloudflare.com/workers/static-assets/routing/static-site-generation/
  - https://developers.cloudflare.com/workers/wrangler/configuration/
  - https://developers.cloudflare.com/workers/framework-guides/web-apps/astro/
