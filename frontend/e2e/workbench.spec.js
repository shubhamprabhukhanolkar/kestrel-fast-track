import { test, expect } from "@playwright/test";
import fs from "node:fs";
test("Five screens, grounded verification, tone studio, failover and human signature", async ({
  page,
}) => {
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Select your operator persona" }),
  ).toBeVisible();
  await page.screenshot({
    path: "../artifacts/login-light.png",
    fullPage: true,
  });
  await page.getByRole("button", { name: "Enter as Meena Pillai" }).click();
  await expect(
    page.getByRole("heading", {
      name: "Good decisions start with complete evidence.",
    }),
  ).toBeVisible();
  await page.getByRole("tab", { name: "Pending cases (7)" }).click();
  await page.screenshot({
    path: "../artifacts/pending-cases.png",
    fullPage: true,
  });
  await page.getByRole("button", { name: "₹25 lakh & above (3)" }).click();
  await page.getByRole("button", { name: "Open Narmada Textiles" }).click();
  await expect(
    page.getByRole("button", { name: "Run cited extraction" }),
  ).toBeDisabled();
  await expect(
    page.getByText("₹25L+ · Standard review", { exact: true }),
  ).toBeVisible();
  await page.getByRole("tab", { name: "Pending cases (7)" }).click();
  await page
    .getByRole("button", { name: "Open Deccan Precision Logistics" })
    .click();
  await page
    .getByRole("button", { name: "Draft RM chaser", exact: true })
    .click();
  const draft = page.getByRole("textbox", { name: "Editable RM chaser draft" });
  await expect(draft).toBeVisible();
  await draft.fill(
    "Dear RM, my manually edited request for the missing returns.",
  );
  await page
    .getByRole("textbox", { name: "Instructions for the drafter agent" })
    .fill("Use bullets and request the returns by Friday.");
  const revisionRequest = page.waitForRequest(
    (r) => r.url().endsWith("/toner/preview") && r.method() === "POST",
  );
  await page
    .getByRole("button", { name: "Revise draft with instructions" })
    .click();
  const revisionPayload = (await revisionRequest).postDataJSON();
  expect(revisionPayload.current_draft).toContain("my manually edited request");
  expect(revisionPayload.instructions).toContain("by Friday");
  await expect(
    page.getByRole("button", { name: "Revise draft with instructions" }),
  ).toBeEnabled();
  await page.getByRole("tab", { name: "Pending cases (7)" }).click();
  await page
    .getByRole("button", { name: "Open Shree Ganesh Surgicals" })
    .click();
  await page.getByRole("button", { name: "Run cited extraction" }).click();
  await expect(
    page.locator(".node-event").filter({ hasText: "Citation QA: 0 issues." }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Open verification workspace" }),
  ).toBeVisible();
  await page.screenshot({
    path: "../artifacts/intake-light.png",
    fullPage: true,
  });
  await page
    .getByRole("button", { name: "Open verification workspace" })
    .click();
  await expect(
    page.getByRole("heading", { name: "Cited spreading sheet" }),
  ).toBeVisible();
  await expect(page.locator(".source-line.highlighted")).toContainText(
    "2025-11 credits INR 1420000.00",
  );
  await page
    .getByPlaceholder("Describe what you checked against the source…")
    .fill("Confirmed exact amount on the indexed native PDF line.");
  await page
    .getByRole("button", { name: "Confirm & log verification" })
    .click();
  await expect(page.getByText("1/60 verified", { exact: true })).toBeVisible();
  await page.getByRole("cell", { name: /Bank debits/ }).click();
  await expect(page.locator(".source-line.highlighted")).toContainText(
    "debits",
  );
  await page.getByRole("button", { name: "Switch to dark mode" }).click();
  await expect(page.locator("html")).toHaveClass(/dark/);
  await page.screenshot({
    path: "../artifacts/verification-dark.png",
    fullPage: true,
  });
  await page
    .getByRole("button", { name: "Prompt & Toner Studio", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Agent prompt editor" }),
  ).toBeVisible();
  const prompt = page.getByRole("textbox", {
    name: "Toner & communication system prompt",
  });
  await prompt.fill(
    (await prompt.inputValue()) + " Preserve the audit context.",
  );
  await page.getByRole("button", { name: "Save new version" }).click();
  await expect(page.getByText("v2 active", { exact: true })).toBeVisible();
  await page
    .getByRole("button", { name: "Polite RM Document Chaser", exact: false })
    .click();
  await page.getByRole("button", { name: "Generate tone preview" }).click();
  await expect(page.locator(".dossier-paper")).toContainText("Dear Vikram");
  await page.screenshot({
    path: "../artifacts/studio-dark.png",
    fullPage: true,
  });
  await page.getByTitle("Switch operator persona").click();
  await page.getByRole("button", { name: "Arjun Iyer", exact: false }).click();
  await page.getByRole("button", { name: "Enter as Arjun Iyer" }).click();
  await page
    .getByRole("button", { name: "FinOps & API Health", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "API redundancy controller" }),
  ).toBeVisible();
  await page.getByRole("tab", { name: "Cost calculation" }).click();
  await expect(
    page.getByRole("heading", { name: "How model costs are calculated" }),
  ).toBeVisible();
  await expect(page.locator(".cost-model-card")).toHaveCount(2);
  await page.getByRole("spinbutton", { name: "Input tokens" }).fill("1000000");
  await page.getByRole("spinbutton", { name: "Output tokens" }).fill("0");
  const prices = await page.evaluate(async () =>
    (await fetch("/api/v1/finops/pricing")).json(),
  );
  const totals = await page.locator(".cost-total").allTextContents();
  expect(Number(totals[0].replace(/[^\d.]/g, ""))).toBe(
    prices.models[0].input_rate,
  );
  expect(Number(totals[1].replace(/[^\d.]/g, ""))).toBe(
    prices.models[1].input_rate,
  );
  await page.screenshot({
    path: "../artifacts/model-cost-calculation.png",
    fullPage: true,
  });
  await page.getByRole("tab", { name: "Spend & API health" }).click();
  await page
    .getByRole("switch", { name: "Simulate Gemini service outage" })
    .click();
  await expect(
    page.getByRole("switch", { name: "Simulate Gemini service outage" }),
  ).toBeChecked();
  await page.getByRole("button", { name: "Run failover test action" }).click();
  await expect(page.locator(".telemetry-table tbody tr").first()).toContainText(
    "groq_backup",
  );
  await expect(page.locator(".telemetry-table tbody tr").nth(1)).toContainText(
    "error_503",
  );
  await page.screenshot({
    path: "../artifacts/finops-dark.png",
    fullPage: true,
  });
  await page
    .getByRole("switch", { name: "Simulate Gemini service outage" })
    .click();
  await page.getByTitle("Switch operator persona").click();
  await page.getByRole("button", { name: "Arjun Iyer", exact: false }).click();
  await page.getByRole("button", { name: "Enter as Arjun Iyer" }).click();
  await expect(page.getByText("60/60 verified", { exact: true })).toBeVisible();
  await page
    .getByPlaceholder(
      "Record your assessment, evidence reviewed, and reasons for accepting or declining exceptions…",
    )
    .fill(
      "Reviewed all 60 verified figures, monthly GST and bank reconciliation, and cash-share notes. No unresolved exceptions; human credit judgement recorded.",
    );
  await page.getByPlaceholder("Type Arjun Iyer").fill("Arjun Iyer");
  await page
    .getByRole("button", { name: "Sign & record audit outcome" })
    .click();
  await expect(
    page.getByText("Signed & locked", { exact: true }),
  ).toBeVisible();
  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByRole("button", { name: "Switch to light mode" }).click();
  await page.screenshot({
    path: "../artifacts/mobile-light.png",
    fullPage: true,
  });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBeTruthy();
  await expect(
    page
      .locator(".guardrail")
      .getByText("NO MODEL APPROVES CREDIT", { exact: true }),
  ).toBeVisible();
  expect(errors).toEqual([]);
});
