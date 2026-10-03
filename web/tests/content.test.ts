import { describe, expect, it } from "vitest";
import {
  ContentError,
  loadAbout,
  loadGlossary,
  loadMetricContent,
  readContentFile,
  validateAbout,
  validateGlossary,
  validateMetricContent,
} from "../src/lib/content";
import { fleschReadingEase } from "../src/lib/readability";
import { dataset } from "../src/lib/data";

const metricIds = Object.keys(dataset.config.metrics);

describe("real content files", () => {
  it.each(metricIds)(
    "%s has valid content (2-4 opportunities, valid urls and dates)",
    (id) => {
      const c = validateMetricContent(readContentFile(`metrics/${id}.md`), id);
      expect(c.opportunities.length).toBeGreaterThanOrEqual(2);
    },
  );
  it("glossary and about validate", () => {
    expect(
      validateGlossary(readContentFile("glossary.md")).terms.length,
    ).toBeGreaterThan(5);
    expect(
      validateAbout(readContentFile("about.md")).paragraphs.length,
    ).toBeGreaterThan(0);
  });
  it("reports readability of the reader-facing text (warning only, never fails)", () => {
    const texts: Record<string, string> = {};
    for (const id of metricIds) {
      const c = loadMetricContent(id);
      texts[`metrics/${id}.md`] = [
        c.what_this_means,
        ...c.opportunities.map((o) => o.description),
      ].join("\n\n");
    }
    texts["glossary.md"] = loadGlossary()
      .terms.map((t) => `${t.term}. ${t.definition}`)
      .join(" ");
    texts["about.md"] = loadAbout().paragraphs.join(" ");
    for (const [f, text] of Object.entries(texts)) {
      const score = fleschReadingEase(text);
      if (score < 60)
        console.warn(
          `readability warning: ${f} Flesch reading ease ${score.toFixed(0)} (< 60)`,
        );
      expect(Number.isFinite(score)).toBe(true);
    }
  });
});

const good = `---
metric_id: x
status: draft
reviewed_by: null
reviewed_on: null
what_this_means: Plain words.
opportunities:
  - {title: A, description: B, url: "https://example.org/a", provider: P, last_checked: 2026-10-03}
  - {title: A2, description: B2, url: "https://example.org/b", provider: P, last_checked: 2026-10-03}
---
`;

describe("validateMetricContent", () => {
  it("accepts a good file", () => {
    expect(validateMetricContent(good, "x").opportunities).toHaveLength(2);
  });
  it.each([
    ["too few opportunities", good.replace(/  - \{title: A2.*\n/, "")],
    ["bad url", good.replace("https://example.org/a", "http://example.org/a")],
    [
      "bad date",
      good.replace(
        "last_checked: 2026-10-03}\n  - {title: A2",
        "last_checked: soon}\n  - {title: A2",
      ),
    ],
    ["digits in copy", good.replace("Plain words.", "Cholsey has 12 trees.")],
    ["wrong metric id", good.replace("metric_id: x", "metric_id: y")],
    [
      "approved without reviewer",
      good.replace("status: draft", "status: approved"),
    ],
    ["no front-matter", "hello"],
  ])("rejects %s", (_n, raw) => {
    expect(() => validateMetricContent(raw, "x")).toThrow(ContentError);
  });
});

describe("fleschReadingEase", () => {
  it("scores simple text higher than dense text", () => {
    expect(
      fleschReadingEase("The cat sat on the mat. It was warm."),
    ).toBeGreaterThan(
      fleschReadingEase(
        "Institutional apportionment methodologies necessitate considerable epistemological scrutiny.",
      ),
    );
  });
});
