import { expect, test } from "@playwright/test";

test("Milestone 0 placeholder names the deferred UI", async ({ page }) => {
  await page.goto("/");
  await expect(
    page.getByText("Ripple UI begins in Milestone 2."),
  ).toBeVisible();
});
