/**
 * Sources, ledger and fact-check status, read from the fact-checked
 * content/claims.verified.json (authoritative for source ids and wording).
 */
import verified from "../../content/claims.verified.json";

export interface Source {
  id: string;
  n: number;
  title: string;
  url: string | null;
}

const rawSources = verified.sources as Record<string, { title: string; url: string | null }>;

export const sources: Source[] = Object.entries(rawSources)
  .map(([id, v]) => ({ id, n: Number(id.slice(1)), title: v.title, url: v.url }))
  .sort((a, b) => a.n - b.n);

const byId = new Map(sources.map((s) => [s.id, s]));

export function source(id: string): Source {
  const s = byId.get(id);
  if (!s) throw new Error(`Unknown source id: ${id}`);
  return s;
}

export type Verdict =
  | "supported"
  | "partially_supported"
  | "outdated"
  | "unverifiable"
  | "pending-simulation";

export const verdictLabel: Record<Verdict, string> = {
  supported: "Supported",
  partially_supported: "Corrected",
  outdated: "Updated",
  unverifiable: "Unverifiable",
  "pending-simulation": "Simulation",
};

export const verdictHelp: Record<Verdict, string> = {
  supported: "Accurate as checked against the source.",
  partially_supported: "Core is right; wording was corrected to match the source.",
  outdated: "Was true once; updated to the status as of October 2026.",
  unverifiable: "No source could be found to back it.",
  "pending-simulation": "Result of this project's simulated feed (S28); not checked against outside sources.",
};

interface FactRaw {
  verdict?: string;
  changed?: boolean;
  note?: string;
}

export interface LedgerRow {
  id: number;
  text: string;
  sources: string[];
  where: string;
  verdict: Verdict | null;
  changed: boolean;
  note: string;
}

const facts = verified.factcheck as unknown as Record<string, FactRaw>;

export const ledger: LedgerRow[] = verified.ledger.map((row) => {
  const f = facts[String(row.id)] ?? {};
  const v = f.verdict as Verdict | undefined;
  return {
    id: row.id,
    text: row.text,
    sources: row.sources,
    where: row.where,
    verdict: v && v in verdictLabel ? v : null,
    changed: Boolean(f.changed),
    note: f.note ?? "",
  };
});

export const limitations: string[] = verified.limitations.map((l) => l.t);
