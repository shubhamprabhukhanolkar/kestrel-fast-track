import { test, expect } from "@playwright/test";

test("Two operators, persistent audio, CIBIL and password-protected email approval", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.locator(".login-story")).toHaveCount(0);
  await expect(page.locator(".persona-list button")).toHaveCount(2);
  await page.getByRole("button", { name: "Turn audio on" }).click();
  await expect(
    page.getByRole("button", { name: "Turn audio off" }),
  ).toHaveAttribute("aria-pressed", "true");
  await page.getByRole("button", { name: "Enter as Meena Pillai" }).click();
  await page.getByText("Edit score & source", {exact: true}).click();
  await page
    .getByRole("spinbutton", { name: "CIBIL score", exact: true })
    .fill("758");
  await page
    .getByRole("textbox", { name: "Score source / analyst note" })
    .fill("Supplied borrower report reviewed by analyst.");
  await page.getByRole("button", { name: "Save CIBIL information" }).click();
  await expect(
    page.getByText("Manually supplied", { exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Draft RM chaser", exact: true })
    .click();
  await expect(
    page.getByRole("textbox", { name: "Editable RM chaser draft" }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Submit current draft for authorization" })
    .click();
  await expect(page.locator(".email-approval .badge")).toHaveText(
    "Authorizer review pending",
  );
  await page.getByTitle("Switch operator persona").click();
  await page.getByRole("button", { name: "Arjun Iyer", exact: false }).click();
  await page.getByRole("button", { name: "Enter as Arjun Iyer" }).click();
  await page
    .getByRole("combobox", { name: "ACTIVE DOSSIER" })
    .selectOption("KF-2026-0892");
  await page
    .getByRole("button", { name: "Intake & Extraction", exact: true })
    .click();
  await page.getByLabel("Credit authorizer password").fill("wrong-password");
  await page
    .getByRole("button", { name: "Confirm password & approve email" })
    .click();
  await expect(page.getByRole("alert")).toContainText(
    "Authorizer password was not accepted",
  );
  await expect(page.locator(".email-approval .badge")).toHaveText(
    "Authorizer review pending",
  );
  await page
    .getByLabel("Credit authorizer password")
    .fill("BrowserAuthorizer2026!");
  await page
    .getByRole("button", { name: "Confirm password & approve email" })
    .click();
  await expect(page.locator(".email-approval .badge")).toHaveText(
    "Approved for sending",
  );
  await expect(page.locator(".cibil-headline")).toContainText("758");
  await expect(page.getByText("Edit score & source", {exact: true})).toHaveCount(0);
  await page
    .getByRole("button", { name: "FinOps & API Health", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Turn audio off" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Turn audio off" }).click();
  expect(await page.evaluate(() => localStorage.getItem("kestrel-audio"))).toBe(
    "off",
  );
  await page.screenshot({
    path: "../artifacts/two-operator-finance.png",
    fullPage: true,
  });
});
