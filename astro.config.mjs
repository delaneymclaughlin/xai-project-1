// @ts-check
import { defineConfig, fontProviders } from "astro/config";
import tailwindcss from "@tailwindcss/vite";

// Fully static output (the default). No adapter: Cloudflare serves ./dist as
// static assets (see wrangler.jsonc).
export default defineConfig({
  // Placeholder until the workers.dev URL is known. Used for canonical/OG URLs.
  site: 'https://xai-1.delaneymclaughlin.com',
  // Keep spaces around inline links and citation markers in prose
  // (Astro 7 defaults to JSX-style whitespace collapsing).
  compressHTML: true,
  vite: { plugins: [tailwindcss()] },
  fonts: [
    {
      provider: fontProviders.google(),
      name: "Anton",
      cssVariable: "--font-anton",
      weights: [400],
      styles: ["normal"],
      subsets: ["latin"],
      fallbacks: ["Impact", "Haettenschweiler", "Arial Narrow", "sans-serif"],
    },
    {
      provider: fontProviders.google(),
      name: "Libre Baskerville",
      cssVariable: "--font-baskerville",
      weights: [400, 700],
      styles: ["normal", "italic"],
      subsets: ["latin"],
      fallbacks: ["Baskerville", "Georgia", "serif"],
    },
  ],
});
