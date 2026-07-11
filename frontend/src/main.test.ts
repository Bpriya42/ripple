import { describe, expect, it } from "vitest";

import { milestone } from "./main";

describe("Milestone 0 frontend baseline", () => {
  it("does not claim a later milestone", () => {
    expect(milestone).toBe(0);
  });
});
