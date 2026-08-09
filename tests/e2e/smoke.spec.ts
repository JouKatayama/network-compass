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

test("API health endpoint is available", async ({ request }) => {
  const response = await request.get(`${apiBaseUrl}/health`);

  expect(response.status()).toBe(200);
  await expect(response.json()).resolves.toEqual({ status: "ok" });
});
