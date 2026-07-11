import { expect, test } from "@playwright/test";

test("feed to sourced branch pathway and evidence", async ({ page }) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: /What happened/ }),
  ).toBeVisible();

  await page
    .getByRole("link", {
      name: "Fixture: officials threaten to close the Strait of Hormuz",
    })
    .first()
    .click();
  await expect(page.getByRole("button", { name: "Skip reveal" })).toBeVisible();
  await page.getByRole("button", { name: "Skip reveal" }).click();

  await expect(
    page.getByRole("img", { name: /World map highlighting Strait of Hormuz/ }),
  ).toBeVisible();
  await expect(page.getByText("Unmet condition:")).toBeVisible();
  await expect(
    page.getByText("Conditional Pathway", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText("U.S. Energy Information Administration").first(),
  ).toBeVisible();

  await page.getByLabel("Consequence").selectOption("costs");
  await expect(page.getByRole("status")).toContainText(
    /Showing 2 of \d+ sourced claims/,
  );
  await page.getByLabel("Consequence").selectOption("all");

  const branch = page.getByRole("button", {
    name: /Explore branch: Transport cost/i,
  });
  await expect(branch).toBeVisible();
  await branch.click();
  await expect(page.getByRole("heading", { name: /Branch \d+/ })).toBeVisible();
  await expect(
    page.getByRole("heading", { name: /Global oil price.*Transport cost/ }),
  ).toBeVisible();
});

test("keyboard text chain exposes the same conditional claim and evidence", async ({
  page,
}) => {
  await page.goto("/story/story.fixture.threat_only_hormuz");
  await page.getByRole("button", { name: "Skip reveal" }).click();
  const textChain = page
    .getByRole("heading", { name: "Sourced claim chain" })
    .locator("..", { has: page.getByText("KEYBOARD & TEXT EQUIVALENT") })
    .locator("..", { has: page.getByRole("list") });
  const firstClaim = textChain.getByRole("button").first();
  await firstClaim.focus();
  await expect(firstClaim).toContainText("Conditional pathway");
  await expect(firstClaim).toContainText(
    "U.S. Energy Information Administration",
  );
  await firstClaim.press("Enter");
  await expect(page.getByText("Unmet condition:")).toBeVisible();
});

test("reduced motion opens directly to the static explorer", async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/story/story.fixture.threat_only_hormuz");
  await expect(page.getByRole("button", { name: "Skip reveal" })).toHaveCount(
    0,
  );
  await expect(
    page.getByRole("heading", { name: "Sourced claim chain" }),
  ).toBeVisible();
  await expect(page.getByText("Unmet condition:")).toBeVisible();
});

test("feed exposes empty and API error states without invented data", async ({
  page,
}) => {
  await page.goto("/?domain=not-a-fixture");
  await expect(
    page.getByRole("heading", { name: "Start from an established mechanism." }),
  ).toBeVisible();

  await page.route("**/api/feed**", (route) =>
    route.fulfill({
      status: 503,
      contentType: "application/json",
      body: JSON.stringify({ detail: "fixture outage" }),
    }),
  );
  await page.goto("/");
  await expect(page.getByRole("alert")).toContainText(
    "The feed could not be reached",
  );
});
