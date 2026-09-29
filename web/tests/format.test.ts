import { describe, expect, it } from "vitest";
import { formatLatestYearLabel } from "../src/lib/format";

describe("formatLatestYearLabel", () => {
  it("formats a year with the required 'latest available' label (spec §3)", () => {
    expect(formatLatestYearLabel(2023)).toBe("latest available: 2023");
  });
});
