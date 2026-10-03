/** Build-time loader and validator for the editable Markdown content in
 * /content (ADR-0015). Invalid content throws, so the build fails. */
import { readFileSync } from "node:fs";
import path from "node:path";
import { JSON_SCHEMA, load } from "js-yaml";

export interface Opportunity {
  title: string;
  description: string;
  url: string;
  provider: string;
  last_checked: string;
}

export type ContentStatus = "draft" | "approved";

export interface MetricContent {
  metric_id: string;
  status: ContentStatus;
  reviewed_by: string | null;
  reviewed_on: string | null;
  what_this_means: string;
  opportunities: Opportunity[];
}

export interface GlossaryContent {
  status: ContentStatus;
  terms: Array<{ term: string; definition: string }>;
}

export interface AboutContent {
  status: ContentStatus;
  paragraphs: string[];
}

export class ContentError extends Error {}

const CONTENT_DIR = path.resolve(process.cwd(), "../content");

export function parseFrontMatter(
  raw: string,
  name: string,
): Record<string, unknown> {
  const m = /^---\r?\n([\s\S]*?)\r?\n---/.exec(raw);
  if (!m) throw new ContentError(`${name}: missing front-matter`);
  // JSON_SCHEMA keeps dates as strings instead of Date objects.
  const data = load(m[1], { schema: JSON_SCHEMA });
  if (typeof data !== "object" || data === null)
    throw new ContentError(`${name}: bad front-matter`);
  return data as Record<string, unknown>;
}

const isStr = (v: unknown): v is string =>
  typeof v === "string" && v.trim() !== "";
const isDate = (v: unknown) =>
  isStr(v) && /^\d{4}-\d{2}-\d{2}$/.test(v) && !Number.isNaN(Date.parse(v));

function isHttpsUrl(v: unknown): boolean {
  if (!isStr(v)) return false;
  try {
    return new URL(v).protocol === "https:";
  } catch {
    return false;
  }
}

function checkStatus(d: Record<string, unknown>, name: string): ContentStatus {
  if (d.status !== "draft" && d.status !== "approved") {
    throw new ContentError(`${name}: status must be draft or approved`);
  }
  if (
    d.status === "approved" &&
    !(isStr(d.reviewed_by) && isDate(d.reviewed_on))
  ) {
    throw new ContentError(
      `${name}: approved content needs reviewed_by and reviewed_on`,
    );
  }
  return d.status;
}

export function validateMetricContent(
  raw: string,
  metricId: string,
): MetricContent {
  const name = `content/metrics/${metricId}.md`;
  const d = parseFrontMatter(raw, name);
  if (d.metric_id !== metricId)
    throw new ContentError(`${name}: metric_id must be ${metricId}`);
  const status = checkStatus(d, name);
  if (!isStr(d.what_this_means))
    throw new ContentError(`${name}: what_this_means is required`);
  if (/\d/.test(d.what_this_means)) {
    throw new ContentError(
      `${name}: what_this_means must not contain digits (numbers come from the data)`,
    );
  }
  const opps = d.opportunities;
  if (!Array.isArray(opps) || opps.length < 2 || opps.length > 4) {
    throw new ContentError(`${name}: needs 2-4 opportunities`);
  }
  opps.forEach((o: Record<string, unknown>, i) => {
    for (const f of ["title", "description", "provider"]) {
      if (!isStr(o[f]))
        throw new ContentError(`${name}: opportunity ${i + 1} needs ${f}`);
    }
    if (!isHttpsUrl(o.url))
      throw new ContentError(
        `${name}: opportunity ${i + 1} needs a valid https url`,
      );
    if (!isDate(o.last_checked)) {
      throw new ContentError(
        `${name}: opportunity ${i + 1} needs last_checked as YYYY-MM-DD`,
      );
    }
  });
  return {
    metric_id: metricId,
    status,
    reviewed_by: (d.reviewed_by as string | null) ?? null,
    reviewed_on: (d.reviewed_on as string | null) ?? null,
    what_this_means: d.what_this_means.trim(),
    opportunities: opps as Opportunity[],
  };
}

export function validateGlossary(raw: string): GlossaryContent {
  const d = parseFrontMatter(raw, "content/glossary.md");
  const status = checkStatus(d, "content/glossary.md");
  const terms = d.terms;
  if (!Array.isArray(terms) || terms.length === 0)
    throw new ContentError("glossary: no terms");
  for (const t of terms as Array<Record<string, unknown>>) {
    if (!isStr(t.term) || !isStr(t.definition))
      throw new ContentError("glossary: term and definition required");
  }
  return { status, terms: terms as GlossaryContent["terms"] };
}

export function validateAbout(raw: string): AboutContent {
  const d = parseFrontMatter(raw, "content/about.md");
  const status = checkStatus(d, "content/about.md");
  if (!Array.isArray(d.paragraphs) || !d.paragraphs.every(isStr)) {
    throw new ContentError("about: paragraphs must be a list of text");
  }
  return { status, paragraphs: d.paragraphs as string[] };
}

const read = (rel: string) =>
  readFileSync(path.join(CONTENT_DIR, rel), "utf-8");

export function loadMetricContent(metricId: string): MetricContent {
  return validateMetricContent(read(`metrics/${metricId}.md`), metricId);
}
export const loadGlossary = () => validateGlossary(read("glossary.md"));
export const loadAbout = () => validateAbout(read("about.md"));
export const CONTENT_FILES = (metricIds: string[]) => [
  ...metricIds.map((m) => `metrics/${m}.md`),
  "glossary.md",
  "about.md",
];
export const readContentFile = read;
