/** Policy spectrum (design.md 8.1): filter chips, switch, listbox of marks, profile panel / mobile accordion. */
import { announce, readJson } from "./lib/dom";
import { initListbox, isOn, isPressed, setPressed, setSwitch } from "./lib/controls";

interface Data {
  total: number;
  defaultId: string;
  measures: { id: string; type: string; requiresExplanation: boolean; label: string }[];
}

function init(root: HTMLElement): void {
  const data = readJson<Data>("policy-spectrum-data");
  const listbox = root.querySelector<HTMLElement>("[data-listbox]");
  const profilesBox = root.querySelector<HTMLElement>("[data-profiles]");
  const live = root.querySelector<HTMLElement>("[data-count]");
  const toggle = root.querySelector<HTMLElement>("[data-explain-toggle]");
  const chips = Array.from(root.querySelectorAll<HTMLElement>("[data-filter]"));
  if (!listbox || !profilesBox) return;

  const opts = Array.from(listbox.querySelectorAll<HTMLAnchorElement>(".mark"));
  const optById = new Map(opts.map((o) => [o.dataset.id!, o]));
  const profiles = new Map(
    Array.from(root.querySelectorAll<HTMLElement>("[data-profile]")).map((p) => [p.dataset.profile!, p]),
  );
  const slots = new Map(Array.from(root.querySelectorAll<HTMLElement>("[data-slot]")).map((s) => [s.dataset.slot!, s]));
  const info = new Map(data.measures.map((m) => [m.id, m]));

  const mq = window.matchMedia("(max-width: 39.99rem)");
  let mobile = mq.matches;
  let selected: string | null = data.defaultId;
  let type = "All";
  let needExplanation = false;

  const matches = (id: string) => {
    const m = info.get(id)!;
    return (type === "All" || m.type === type) && (!needExplanation || m.requiresExplanation);
  };

  const ctl = initListbox(listbox, {
    orientation: "horizontal",
    onSelect: (o) => {
      if (!mobile) select(o.dataset.id!);
    },
  });

  function placeTabStop(): void {
    if (mobile) return;
    const sel = selected && matches(selected) ? optById.get(selected) : undefined;
    const target = sel ?? opts.find((o) => o.getAttribute("aria-disabled") !== "true");
    opts.forEach((o) => (o.tabIndex = o === target ? 0 : -1));
    if (target) ctl.focusIndex(opts.indexOf(target));
  }

  function render(): void {
    for (const [id, p] of profiles) {
      const open = id === selected;
      if (open) p.setAttribute("data-active", "");
      else p.removeAttribute("data-active");
      const home = mobile ? slots.get(id) : profilesBox;
      if (open && home && p.parentElement !== home) home.appendChild(p);
      if (!open && p.parentElement !== profilesBox) profilesBox!.appendChild(p);
    }
    for (const o of opts) {
      const open = o.dataset.id === selected;
      if (mobile) {
        o.removeAttribute("aria-selected");
        o.setAttribute("aria-expanded", open ? "true" : "false");
        o.setAttribute("aria-controls", `profile-${o.dataset.id}`);
      } else {
        o.removeAttribute("aria-expanded");
        o.removeAttribute("aria-controls");
        o.setAttribute("aria-selected", open ? "true" : "false");
      }
    }
    placeTabStop();
  }

  function select(id: string | null): void {
    selected = id;
    render();
  }

  function applyMode(): void {
    mobile = mq.matches;
    if (mobile) {
      listbox!.removeAttribute("role");
      listbox!.removeAttribute("aria-orientation");
      for (const o of opts) {
        o.removeAttribute("role");
        o.tabIndex = 0;
      }
    } else {
      listbox!.setAttribute("role", "listbox");
      listbox!.setAttribute("aria-orientation", "horizontal");
      for (const o of opts) o.setAttribute("role", "option");
      if (!selected) selected = data.defaultId;
    }
    render();
  }

  // Anchors are no-JS jump links; with JS they select.
  listbox.addEventListener("click", (e) => {
    const o = (e.target as HTMLElement).closest<HTMLAnchorElement>(".mark");
    if (!o) return;
    e.preventDefault();
    if (o.getAttribute("aria-disabled") === "true") return;
    if (mobile) select(selected === o.dataset.id ? null : o.dataset.id!);
  });
  // Space on a link should select (initListbox handles it in listbox mode); on mobile it activates like a button.
  listbox.addEventListener("keydown", (e) => {
    if (mobile && e.key === " ") {
      e.preventDefault();
      (e.target as HTMLElement).click();
    }
  });

  function applyFilter(): void {
    let n = 0;
    for (const o of opts) {
      const ok = matches(o.dataset.id!);
      if (ok) n++;
      if (ok) {
        o.removeAttribute("aria-disabled");
        o.style.opacity = "";
      } else {
        o.setAttribute("aria-disabled", "true");
        o.style.opacity = "0.4";
      }
    }
    placeTabStop();
    const label = n === 1 ? "measure" : "measures";
    const sentence = `Showing ${n} of ${data.total} ${label}${n === 0 ? ". No measure matches both filters" : ""}`;
    if (live) {
      live.textContent = "";
      announce(live, sentence);
    }
  }

  for (const chip of chips) {
    chip.addEventListener("click", () => {
      const f = chip.dataset.filter!;
      type = isPressed(chip) && f !== "All" ? "All" : f;
      for (const c of chips) setPressed(c, c.dataset.filter === type);
      applyFilter();
    });
  }
  toggle?.addEventListener("click", () => {
    needExplanation = !isOn(toggle);
    setSwitch(toggle, needExplanation);
    applyFilter();
  });

  mq.addEventListener("change", applyMode);
  applyMode();
}

document.querySelectorAll<HTMLElement>("[data-policy-spectrum]").forEach(init);
