/** Build-time loader and validator for the editable Markdown content in
 * /content (ADR-0015). Invalid content throws, so the build fails. */
import { existsSync, readFileSync } from "node:fs";
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

export interface MethodologyContent {
  status: ContentStatus;
  sections: Array<{ heading: string; paragraphs: string[] }>;
}

export interface HomeContent {
  status: ContentStatus;
  title: string;
  lede: string;
  beats: Array<{ id: string; heading: string; text: string }>;
}

export class ContentError extends Error {}

// Works from the repo root or from web/ (where the build and tests run).
const CONTENT_DIR =
  [
    path.resolve(process.cwd(), "content"),
    path.resolve(process.cwd(), "../content"),
  ].find((d) => existsSync(path.join(d, "glossary.md"))) ??
  path.resolve(process.cwd(), "../content");

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
  isStr(v) &&
  /^\d{4}-\d{2}-\d{2}$/.test(v) &&
  !Number.isNaN(Date.parse(v)) &&
  new Date(`${v}T00:00:00Z`).toISOString().slice(0, 10) === v;

/** Prose must not carry figures: every number on the site comes from the data. */
function noDigits(text: string, where: string) {
  if (/\d/.test(text)) {
    throw new ContentError(
      `${where} must not contain digits (numbers come from the data)`,
    );
  }
}

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
  noDigits(d.what_this_means, `${name}: what_this_means`);
  const opps = d.opportunities;
  if (!Array.isArray(opps) || opps.length < 2 || opps.length > 4) {
    throw new ContentError(`${name}: needs 2-4 opportunities`);
  }
  opps.forEach((o: Record<string, unknown>, i) => {
    for (const f of ["title", "description", "provider"]) {
      if (!isStr(o[f]))
        throw new ContentError(`${name}: opportunity ${i + 1} needs ${f}`);
    }
    noDigits(`${o.title} ${o.description}`, `${name}: opportunity ${i + 1}`);
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
  for (const t of terms as Array<Record<string, string>>)
    noDigits(`${t.term} ${t.definition}`, "glossary");
  return { status, terms: terms as GlossaryContent["terms"] };
}

export function validateAbout(raw: string): AboutContent {
  const d = parseFrontMatter(raw, "content/about.md");
  const status = checkStatus(d, "content/about.md");
  if (!Array.isArray(d.paragraphs) || !d.paragraphs.every(isStr)) {
    throw new ContentError("about: paragraphs must be a list of text");
  }
  for (const p of d.paragraphs as string[]) noDigits(p, "about");
  return { status, paragraphs: d.paragraphs as string[] };
}

export function validateMethodology(raw: string): MethodologyContent {
  const d = parseFrontMatter(raw, "content/methodology.md");
  const status = checkStatus(d, "content/methodology.md");
  const sections = d.sections;
  if (!Array.isArray(sections) || sections.length === 0) {
    throw new ContentError("methodology: no sections");
  }
  for (const sec of sections as Array<Record<string, unknown>>) {
    if (
      !isStr(sec.heading) ||
      !Array.isArray(sec.paragraphs) ||
      !sec.paragraphs.every(isStr)
    ) {
      throw new ContentError(
        "methodology: each section needs a heading and paragraphs",
      );
    }
    noDigits(
      `${sec.heading} ${(sec.paragraphs as string[]).join(" ")}`,
      "methodology",
    );
  }
  return { status, sections: sections as MethodologyContent["sections"] };
}

export function validateHome(raw: string): HomeContent {
  const d = parseFrontMatter(raw, "content/home.md");
  const status = checkStatus(d, "content/home.md");
  if (!isStr(d.title) || !isStr(d.lede))
    throw new ContentError("home: title and lede are required");
  noDigits(`${d.title} ${d.lede}`, "home");
  const beats = d.beats;
  if (!Array.isArray(beats) || beats.length !== 4)
    throw new ContentError("home: needs exactly 4 beats");
  for (const b of beats as Array<Record<string, unknown>>) {
    if (!isStr(b.id) || !isStr(b.heading) || !isStr(b.text)) {
      throw new ContentError("home: each beat needs id, heading and text");
    }
    noDigits(`${b.heading} ${b.text}`, "home");
  }
  return {
    status,
    title: d.title,
    lede: d.lede,
    beats: beats as HomeContent["beats"],
  };
}

const read = (rel: string) =>
  readFileSync(path.join(CONTENT_DIR, rel), "utf-8");

export function loadMetricContent(metricId: string): MetricContent {
  return validateMetricContent(read(`metrics/${metricId}.md`), metricId);
}
export const loadGlossary = () => validateGlossary(read("glossary.md"));
export const loadMethodology = () =>
  validateMethodology(read("methodology.md"));
export const loadHome = () => validateHome(read("home.md"));
export const loadAbout = () => validateAbout(read("about.md"));
export const readContentFile = read;
