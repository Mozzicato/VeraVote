import { expect, test, type Page } from "@playwright/test";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const SHOTS = "e2e/screenshots";

// Not a real image: the server only checks the PNG signature, and the demo uses simulated extraction.
const fakePng = (tag: string) => ({
  name: `${tag}.png`,
  mimeType: "image/png",
  buffer: Buffer.concat([Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]), Buffer.alloc(40_000, tag)]),
});

async function viewAs(page: Page, name: string | null) {
  const select = page.locator("header select").first();
  await expect(select.locator("option").nth(1)).toBeAttached();
  if (name === null) await select.selectOption("");
  else await select.selectOption({ label: await select.locator("option", { hasText: name }).first().innerText() });
}

test.describe.configure({ mode: "serial" });

test.beforeAll(async ({ request }) => {
  expect((await request.post(`${API}/demo/reset`)).ok()).toBeTruthy();
});

test("public search by landmark and the four scenarios", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("Demo with simulated data.")).toBeVisible();
  await page.getByLabel(/Search by polling-unit name/).fill("mosque");
  await page.getByRole("button", { name: "Find", exact: true }).click();
  await expect(page.getByText("Known locally as “Town Mosque”")).toBeVisible();
  await page.screenshot({ path: `${SHOTS}/01-home-search.png`, fullPage: true });

  await page.getByLabel(/Search by polling-unit name/).fill("Central School");
  await page.getByRole("button", { name: "Find", exact: true }).click();
  await page.getByRole("link", { name: /Central Primary School I\b/ }).first().click();
  await expect(page.getByText("Records agree").first()).toBeVisible();
  await expect(page.getByRole("table")).toBeVisible();
  await page.screenshot({ path: `${SHOTS}/02-scenario-a.png`, fullPage: true });

  await page.goto("/discrepancies");
  await expect(page.getByText("votes apart, at most")).toBeVisible();
  await expect(page.getByText("20", { exact: true })).toBeVisible();
  await page.getByRole("link", { name: "Central Primary School II" }).click();
  await expect(page.getByRole("heading", { level: 1, name: "Central Primary School II" })).toBeVisible();
  await expect(page.getByText("Records differ").first()).toBeVisible();
  await expect(page.getByRole("columnheader", { name: /Record C.*Official/ })).toBeVisible();
  await expect(page.getByRole("columnheader", { name: /Record A.*Transparency Watch/ })).toBeVisible();
  await expect(page.getByText("not, by itself, proof of wrongdoing")).toBeVisible();
  await expect(page.locator("main")).not.toContainText(/fraud|rigged/i);
  await page.screenshot({ path: `${SHOTS}/03-scenario-b.png`, fullPage: true });

  await page.goto("/");
  await page.getByLabel(/Search by polling-unit name/).fill("Jetty");
  await page.getByRole("button", { name: "Find", exact: true }).click();
  await page.getByRole("link", { name: /Riverside Community Hall/ }).first().click();
  await expect(page.getByText("only one usable record")).toBeVisible();

  await page.goto("/");
  await page.getByLabel(/Search by polling-unit name/).fill("Health Centre");
  await page.getByRole("button", { name: "Find", exact: true }).click();
  await page.getByRole("link", { name: /Hilltop Health Centre/ }).first().click();
  await expect(page.getByText(/citizen-submitted lead\(s\) are pending verification/)).toBeVisible();
  await expect(page.locator("main")).not.toContainText("Amaka");
});

test("phone layout has no horizontal scroll", async ({ page }) => {
  await page.setViewportSize({ width: 360, height: 780 });
  for (const path of ["/", "/pu/2", "/submit", "/about"]) {
    await page.goto(path);
    await page.waitForLoadState("networkidle");
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    expect(overflow, `horizontal overflow on ${path}`).toBeLessThanOrEqual(0);
  }
  await page.goto("/pu/2");
  await expect(page.getByText("scroll sideways")).toBeVisible();
  // The pinned field-name column keeps rows readable while the table scrolls.
  const bnp = page.getByRole("rowheader", { name: /BNP/ });
  await bnp.scrollIntoViewIfNeeded();
  await page.locator("table").evaluate((t) => t.parentElement!.scrollBy({ left: 400 }));
  const box = await bnp.boundingBox();
  expect(box!.x, "field-name column stays pinned at the left edge").toBeGreaterThanOrEqual(0);
  expect(box!.x).toBeLessThan(20);
  await page.screenshot({ path: `${SHOTS}/04-mobile-unit.png`, fullPage: true });
});

test("citizen submits an evidence lead without an account", async ({ page }) => {
  await page.goto("/");
  await viewAs(page, null);
  await page.goto("/submit");
  await page.getByPlaceholder("Unit name, code or landmark").fill("Motor Park");
  await page.getByRole("button", { name: "Find" }).click();
  await page.getByRole("button", { name: /Hilltop Motor Park/ }).click();
  await page.locator('input[type="file"]').setInputFiles(fakePng("lead"));
  await page.getByLabel("Phone or email for follow-up (optional)").fill("0800-private");
  await page.getByRole("checkbox").check();
  await page.getByRole("button", { name: "Submit evidence" }).click();
  await expect(page.getByText("We received your evidence")).toBeVisible();
  await expect(page.getByText(/^VV-[0-9A-F]{8}$/)).toBeVisible();
  await page.screenshot({ path: `${SHOTS}/05-lead-receipt.png`, fullPage: true });
});

test("volunteer applies, trains, passes and is not shown as INEC-accredited", async ({ page }) => {
  await page.goto("/");
  await viewAs(page, null);
  await page.goto("/volunteer");
  await page.getByLabel("Full name").fill("Test Volunteer");
  await page.getByLabel(/Phone number/).fill(`+23480${Date.now().toString().slice(-8)}`);
  await page.getByLabel("State").selectOption({ index: 1 });
  await page.getByLabel("LGA you'd like to cover").selectOption({ index: 1 });
  await page.getByRole("checkbox").check();
  await page.getByRole("button", { name: "Apply" }).click();

  await expect(page.getByText("Confirm your phone number")).toBeVisible();
  await page.getByLabel("One-time code").fill("123456");
  await page.getByRole("button", { name: "Verify" }).click();
  const readButtons = page.getByRole("button", { name: "I've read this" });
  for (let left = 5; left > 0; left--) {
    await expect(readButtons).toHaveCount(left);
    await readButtons.first().click();
  }
  const answers = [0, 1, 1, 1, 1, 2, 1, 1, 1, 1];
  await expect(page.getByText("Pass mark: 80%")).toBeVisible();
  const groups = page.locator("fieldset");
  for (let i = 0; i < answers.length; i++) await groups.nth(i).getByRole("radio").nth(answers[i]).check();
  await page.getByRole("button", { name: "Submit answers" }).click();
  await expect(page.getByText("VeraVote-trained community contributor (not INEC-accredited)")).toBeVisible();
  await expect(page.locator("header select").first()).toContainText("Test Volunteer"); // header knows the new account
  await expect(page.locator("nav").getByRole("link", { name: "My assignments" })).toBeVisible();
  await page.screenshot({ path: `${SHOTS}/06-volunteer-approved.png`, fullPage: true });
});

test("verifier corrects a misread figure, accepts, then attaches the official copy", async ({ page }) => {
  await page.goto("/");
  await viewAs(page, "Chika Umeh");
  await page.goto("/verify");
  await expect(page.getByText("✓ Audit log intact")).toBeVisible();
  await page.getByRole("link", { name: /Open Space beside Town Mosque/ }).click();
  await expect(page.getByText("Original document")).toBeVisible();
  await expect(page.locator("img")).toBeVisible();

  // True figures for SIM-01-01-003 from the simulated sheet.
  const truth: Record<string, string> = {
    "Number of accredited voters": "350", "Adaeze Okafor (APX)": "130", "Bello Musa (BNP)": "129",
    "Chinedu Eze (CPD)": "70", "Total valid votes": "329", "Rejected votes": "8", "Total votes cast": "337",
  };
  const flagged = page.locator("li", { hasText: "check this" });
  await expect(flagged).toHaveCount(1);
  const label = (await flagged.locator("label").first().innerText()).trim();
  await flagged.getByRole("textbox").fill(truth[label]);
  await flagged.getByPlaceholder("Reason for correction").fill("Digits transposed by extraction");
  await expect(page.getByText("✓ The figures above add up.")).toBeVisible(); // checks update before saving
  await page.screenshot({ path: `${SHOTS}/07-verify-correction.png`, fullPage: true });
  await page.getByRole("button", { name: "Save figures" }).click();
  await expect(page.getByText("Figures saved")).toBeVisible();
  await page.getByRole("button", { name: "Confirm extraction" }).click();
  await expect(page.getByText("Extraction confirmed.")).toBeVisible();
  await page.getByRole("button", { name: "Accept for comparison" }).click();
  await expect(page.getByText("Accepted for comparison.")).toBeVisible();
  await expect(page.getByText("Not enough to compare").first()).toBeVisible();

  await page.getByRole("link", { name: "Open the unit workspace" }).click();
  await page.getByText("Attach the official result document").click();
  const keys = ["Number of accredited voters", "Adaeze Okafor (APX)", "Bello Musa (BNP)",
    "Chinedu Eze (CPD)", "Total valid votes", "Rejected votes", "Total votes cast"];
  for (const k of keys) await page.locator("label", { hasText: k }).getByRole("textbox").fill(truth[k]);
  await page.getByRole("button", { name: "Attach document" }).click();
  await expect(page.getByText("Unit status is now: consistent evidence")).toBeVisible();
  await page.screenshot({ path: `${SHOTS}/08-unit-workspace.png`, fullPage: true });
});

test("sensitive outcome needs a senior reviewer", async ({ page }) => {
  await page.goto("/");
  await viewAs(page, "Chika Umeh");
  await page.goto("/verify/unit/2/1");
  await page.getByRole("button", { name: "Open investigation" }).click();
  await page.getByLabel("Findings (internal)").fill("Both observer photos agree; official copy shows BNP +20.");
  await page.getByLabel("Outcome").selectOption("discrepancy_confirmed");
  await page.getByLabel("Public summary").fill(
    "Two independent observer photos agree with each other but differ from the official copy by 20 votes for one candidate.");
  await page.getByRole("button", { name: "Complete review" }).click();
  await expect(page.getByText(/waiting for a senior reviewer/)).toBeVisible();

  await viewAs(page, "Yusuf Garba");
  await page.reload();
  await page.getByRole("button", { name: "Approve and publish" }).click();
  await expect(page.getByText("Review completed").first()).toBeVisible();
  await page.goto("/pu/2");
  await expect(page.getByText(/differ from the official copy by 20 votes/)).toBeVisible();
});

test("contributor captures evidence and gets a receipt", async ({ page }) => {
  await page.goto("/");
  await viewAs(page, "Tunde Bakare");
  await page.goto("/contributor");
  await expect(page.getByText("Riverside Community Hall").first()).toBeVisible();
  await page.locator('input[type="file"]').first().setInputFiles(fakePng("field"));
  await page.getByRole("button", { name: "Save and submit" }).click();
  await expect(page.getByText("Received by server").first()).toBeVisible();
  await expect(page.getByText("SHA-256 fingerprint", { exact: true })).toBeVisible();
  await expect(page.locator('input[type="file"]').first()).toHaveValue("");
  await page.screenshot({ path: `${SHOTS}/09-contributor-receipt.png`, fullPage: true });
});

test("coordinator sees honest coverage and approves a request", async ({ page }) => {
  await page.goto("/");
  await viewAs(page, "Funke Adebayo");
  await page.goto("/organisation");
  await expect(page.getByText("counted as observed only once evidence")).toBeVisible();
  await expect(page.getByText(/Emeka Nwosu asks to cover St. Peter/)).toBeVisible();
  await page.screenshot({ path: `${SHOTS}/10-coverage.png`, fullPage: true });
  await page.getByRole("button", { name: "Approve" }).click();
  await expect(page.getByText(/Emeka Nwosu asks to cover/)).toHaveCount(0);
});
