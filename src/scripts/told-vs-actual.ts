import { $, readJson, announce } from "./lib/dom";
import { setPressed, isPressed } from "./lib/controls";

interface TvaData {
  toldPct: number;
  leftPct: number;
  topLabel: string;
  topFeature: string;
  toldLabel: string;
  leftTotal: number;
  leftOut: { feature: string; label: string; sharePct: number }[];
}

const root = document.querySelector<HTMLElement>("[data-told-vs-actual]");
if (root) {
  const data = readJson<TvaData>("told-vs-actual-data");
  const chip = $<HTMLButtonElement>("[data-tva-chip]", root);
  const sentence = $("[data-tva-sentence]", root);
  const empty = $("[data-rest-empty]", root);
  const fill = $("[data-rest-fill]", root);
  const pct = (n: number) => `${n.toFixed(1)}%`;
  const top = data.topLabel.toLowerCase();

  const textFor = (on: boolean) =>
    on
      ? `The one-line reason leaves out ${pct(data.leftPct)} of the ranking, including ${top}, the largest single factor.`
      : `The one-line reason accounts for ${pct(data.toldPct)} of the ranking and leaves out ${pct(data.leftPct)}, including ${top}, the largest single factor.`;

  const apply = (on: boolean, speak: boolean) => {
    root.dataset.open = on ? "true" : "false";
    setPressed(chip, on);
    // Hidden layer stays out of the accessibility tree; the sentence carries the content.
    empty.toggleAttribute("aria-hidden", on);
    fill.setAttribute("aria-hidden", "true");
    if (speak) announce(sentence, textFor(on));
    else sentence.textContent = textFor(on);
  };

  chip.addEventListener("click", () => apply(!isPressed(chip), true));
  apply(false, false);
}
