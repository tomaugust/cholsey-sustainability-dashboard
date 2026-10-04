import { dataset } from "./data";

export const SITE_NAME = "Cholsey Parish Sustainability Dashboard";
export const SITE_DESCRIPTION =
  "How Cholsey is doing on trees, green space and home energy, compared with nearby parishes, South Oxfordshire and England.";
export const REPO_URL =
  "https://github.com/tomaugust/cholsey-sustainability-dashboard";
export const OGL_URL =
  "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/";
export const OGL_TEXT =
  "Contains public sector information licensed under the Open Government Licence v3.0.";

/** Flip to true at launch (docs/launch-checklist.md). Until then pages ask
 * search engines not to index them (ADR-0016: URL unshared, content is draft). */
export const LAUNCHED = false;

/** Most recent retrieval date across every row on the site (YYYY-MM-DD). */
export function dataLastRefreshed(): string {
  const dates = Object.values(dataset.metrics)
    .flat()
    .map((r) => r.retrieved_at.slice(0, 10));
  return dates.sort().at(-1) ?? "unknown";
}
