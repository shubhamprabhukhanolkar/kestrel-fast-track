import { test, expect } from "@playwright/test";
import fs from "node:fs";

test("Help covers operations before and after sign-in, searches and downloads", async ({
  page,
}) => {
  await page.goto("/");
  const helpButton = page.getByRole("button", { name: "Help & Tutorial" });
  await helpButton.click();
  const guide = page.getByRole("dialog", { name: "Help & Tutorial" });
  await expect(guide).toBeVisible();
  await expect(
    guide.getByRole("heading", { name: "Getting started with your case" }),
  ).toBeVisible();
  await expect(guide.getByRole("searchbox")).toBeFocused();
  await guide.getByRole("searchbox").fill("15 MB");
  await guide
    .getByRole("button", {
      name: "Documents & intake requirements",
      exact: true,
    })
    .click();
  await expect(
    guide.getByRole("heading", { name: "Documents & intake requirements" }),
  ).toBeVisible();
  await expect(
    guide.getByText(/This replaces that document type/),
  ).toBeVisible();
  const downloadPromise = page.waitForEvent("download");
  await guide.getByRole("button", { name: "Download operating guide" }).click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toBe("Kestrel-Operating-Guide.md");
  const contents = fs.readFileSync(await download.path(), "utf8");
  for (const text of [
    "RM chaser",
    "₹25,00,000",
    "60",
    "Arjun Iyer",
    "1,000,000",
    "15 MB",
  ])
    expect(contents).toContain(text);
  expect(contents).not.toContain("KestrelOperator2026!");
  await guide.getByRole("searchbox").fill("zzzz-no-such-topic");
  await expect(
    guide.getByRole("heading", { name: "No matching topics" }),
  ).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(guide).not.toBeVisible();
  await expect(helpButton).toBeFocused();
  await page.getByRole("button", { name: "Enter as Meena Pillai" }).click();
  await helpButton.click();
  await page
    .getByRole("navigation", { name: "Help topics" })
    .getByRole("button", {
      name: "Finance, costs & provider failover",
      exact: true,
    })
    .click();
  await page.screenshot({
    path: "../artifacts/help-desktop.png",
    fullPage: true,
  });
  await guide.getByRole("button", { name: "Open FinOps & API Health" }).click();
  await expect(guide).not.toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Every agent action, accounted for." }),
  ).toBeVisible();
});

test("Help remains usable on a phone", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await page.getByRole("button", { name: "Help & Tutorial" }).click();
  const guide = page.getByRole("dialog", { name: "Help & Tutorial" });
  await guide.getByRole("searchbox").fill("chaser");
  await guide
    .getByRole("navigation", { name: "Help topics" })
    .getByRole("button", { name: "Edit & instruct the RM chaser", exact: true })
    .click();
  await expect(
    guide.getByRole("heading", { name: "Edit & instruct the RM chaser" }),
  ).toBeVisible();
  const bounds = await guide.boundingBox();
  expect(bounds.x).toBeGreaterThanOrEqual(0);
  expect(bounds.x + bounds.width).toBeLessThanOrEqual(390);
  await page.screenshot({
    path: "../artifacts/help-mobile.png",
    fullPage: true,
  });
  await guide.getByRole("button", { name: "Close help" }).click();
  await expect(guide).not.toBeVisible();
});
