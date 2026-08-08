import { expect, test } from "@playwright/test";

const apiBaseUrl = process.env.E2E_API_BASE_URL ?? "http://127.0.0.1:8000";

test("foundation web page is available", async ({ page }) => {
  await page.goto("/");

  await expect(
    page.getByRole("heading", { level: 1, name: "Network Compass" }),
  ).toBeVisible();
  await expect(
    page.getByText("Repository foundation is running."),
  ).toBeVisible();
});

test("API health endpoint is available", async ({ request }) => {
  const response = await request.get(`${apiBaseUrl}/health`);

  expect(response.status()).toBe(200);
  await expect(response.json()).resolves.toEqual({ status: "ok" });
});
