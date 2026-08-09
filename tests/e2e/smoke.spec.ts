import { expect, test } from "@playwright/test";

import {
  createLargeNetworkFixture,
  networkFixture,
} from "../../apps/web/tests/network-fixture";

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
  await page.getByRole("option", { name: /Synthetic Person P018/ }).click();

  await expect(
    page.getByRole("dialog", { name: /Synthetic Person P018/ }),
  ).toBeFocused();
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
  await expect(page.getByLabel("38人を表示。全体92人")).toBeVisible();

  await search.fill("P067");
  await expect(
    page.getByRole("option", { name: /Synthetic Person P067/ }),
  ).toBeVisible();
  await search.press("ArrowDown");
  await search.press("Enter");

  await expect(
    page.getByRole("dialog", { name: /Synthetic Person P067/ }),
  ).toBeFocused();
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

  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(search).toBeFocused();
});

test("network failure is safe and retryable", async ({ page }) => {
  let attempts = 0;
  await page.route("**/api/network", async (route) => {
    attempts += 1;
    if (attempts <= 2) {
      await route.fulfill({
        body: JSON.stringify({
          error: {
            code: "NETWORK_UNAVAILABLE",
            message: "internal database detail must not be rendered",
            requestId: "req_e2e",
          },
        }),
        contentType: "application/json",
        status: 502,
      });
      return;
    }
    await route.fulfill({
      body: JSON.stringify(networkFixture),
      contentType: "application/json",
      status: 200,
    });
  });

  await page.goto("/network");
  await expect(page.locator(".error-state[role='alert']")).toContainText(
    "ネットワークを表示できませんでした",
  );
  await expect(
    page.getByText("internal database detail must not be rendered"),
  ).toHaveCount(0);
  await page.getByRole("button", { name: "再読み込み" }).click();
  await expect(page.getByTestId("network-graph-canvas")).toBeVisible();
});

test("60-person partial projection remains usable", async ({
  page,
}, testInfo) => {
  const largeNetwork = createLargeNetworkFixture();
  await page.route("**/api/network", async (route) => {
    await route.fulfill({
      body: JSON.stringify(largeNetwork),
      contentType: "application/json",
      status: 200,
    });
  });
  const startedAt = Date.now();

  await page.goto("/network");
  await expect(page.getByLabel("60人を表示。全体92人")).toBeVisible();
  await expect(
    page.getByText(/一部のプロフィール情報は限定的です/),
  ).toBeVisible();
  await expect(page.locator(".large-network-notice")).toContainText(
    "60人を表示しています",
  );
  expect(Date.now() - startedAt).toBeLessThan(8_000);

  const visualEvidence = await page.locator(".network-page").screenshot({
    animations: "disabled",
  });
  expect(visualEvidence.byteLength).toBeGreaterThan(10_000);
  await testInfo.attach("NC-010 60-person visual state", {
    body: visualEvidence,
    contentType: "image/png",
  });

  await page.getByRole("button", { name: "1-hop" }).click();
  await expect(page.getByLabel("25人を表示。全体92人")).toBeVisible();
  await expect(page.locator(".large-network-notice")).toHaveCount(0);
  await page.getByRole("button", { name: "拡大" }).focus();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("button", { name: "拡大" })).toBeFocused();
});

test("API health endpoint is available", async ({ request }) => {
  const response = await request.get(`${apiBaseUrl}/health`);

  expect(response.status()).toBe(200);
  await expect(response.json()).resolves.toEqual({ status: "ok" });
});
