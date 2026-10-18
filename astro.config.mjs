// @ts-check
import { defineConfig, fontProviders } from "astro/config";
import tailwindcss from "@tailwindcss/vite";

// Fully static output (the default). No adapter: Cloudflare serves ./dist as
// static assets (see wrangler.jsonc).
export default defineConfig({
  // Placeholder until the workers.dev URL is known. Used for canonical/OG URLs.
  site: "https://xai-feed-brief.workers.dev",
  // Keep spaces around inline links and citation markers in prose
  // (Astro 7 defaults to JSX-style whitespace collapsing).
  compressHTML: true,
  vite: { plugins: [tailwindcss()] },
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
});
