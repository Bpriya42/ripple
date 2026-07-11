import { describe, expect, it } from "vitest";

import type { RippleEdge } from "../api/client";
import { claimText } from "./StoryPage";

const threatOnlyEdge = {
  condition_met: false,
  required_condition: "material disruption to Strait of Hormuz oil transit",
  mechanism:
    "a material transit disruption can put upward pressure on oil prices.",
  claim_state: "conditional_pathway",
} as RippleEdge;

describe("causal claim language", () => {
  it("names the unmet condition for a threat-only pathway", () => {
    const text = claimText(threatOnlyEdge);
    expect(text).toContain("Conditional pathway");
    expect(text).toContain("If material disruption");
    expect(text).not.toContain("has raised");
  });

  it("labels a condition-met mechanism without inventing an observed effect", () => {
    const text = claimText({
      ...threatOnlyEdge,
      condition_met: true,
      claim_state: "established_mechanism",
    });
    expect(text).toContain("Established mechanism");
    expect(text).not.toContain("Observed effect");
  });
});
