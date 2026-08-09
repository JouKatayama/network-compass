import { expect, test } from "@playwright/test";

const apiBaseUrl = process.env.E2E_API_BASE_URL ?? "http://127.0.0.1:8000";

test("My Network graph foundation is available", async ({ page }) => {
  await page.goto("/");

  await expect(page).toHaveURL(/\/network$/);
  await expect(
    page.getByRole("heading", { level: 1, name: "My Network" }),
  ).toBeVisible();
  await expect(page.getByLabel("37人を表示。全体92人")).toBeVisible();
  await expect(page.getByRole("button", { name: "拡大" })).toBeVisible();
  await expect(page.getByRole("button", { name: "縮小" })).toBeVisible();
  await expect(page.getByRole("button", { name: "全体を表示" })).toBeVisible();
  await expect(
    page.getByRole("button", { name: "自分を中心に" }),
  ).toBeVisible();
  await expect(page.getByText("久しぶり")).toBeVisible();
});

test("P001 remembers P018 and reaches P067 without fabricated history", async ({
  page,
}) => {
  await page.goto("/network");

  const search = page.getByRole("combobox", { name: "人を検索" });
  await search.fill("P018");
  await page
    .getByRole("option", { name: /Synthetic Person P018/ })
    .getByRole("button")
    .click();

  await expect(
    page.getByRole("heading", { level: 2, name: "Synthetic Person P018" }),
  ).toBeVisible();
  await expect(page.locator(".relationship-badge")).toHaveText(
    "久しぶりのつながり",
  );
  await expect(page.locator(".timeline-list")).toContainText("Project");
  await expect(
    page.getByRole("heading", { name: "共通のプロジェクト" }),
  ).toBeVisible();

  await page
    .getByRole("button", { name: "この人からつながりを広げる" })
    .click();
  await expect(
    page.getByRole("button", { name: "この人から展開済み" }),
  ).toBeDisabled();

  await search.fill("P067");
  await page
    .getByRole("option", { name: /Synthetic Person P067/ })
    .getByRole("button")
    .click();

  await expect(
    page.getByRole("heading", { level: 2, name: "Synthetic Person P067" }),
  ).toBeVisible();
  await expect(page.locator(".relationship-badge")).toHaveText(
    "まだ直接話したことはありません",
  );
  await expect(page.locator(".connection-path")).toContainText(
    "Synthetic Person P001",
  );
  await expect(page.locator(".connection-path")).toContainText(
    "Synthetic Person P010",
  );
  await expect(page.locator(".timeline-section")).toContainText(
    "まだ直接話した記録はありません",
  );
  await expect(page.locator(".timeline-list")).toHaveCount(0);
});

test("API health endpoint is available", async ({ request }) => {
  const response = await request.get(`${apiBaseUrl}/health`);

  expect(response.status()).toBe(200);
  await expect(response.json()).resolves.toEqual({ status: "ok" });
});
