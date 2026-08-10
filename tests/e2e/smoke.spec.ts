import { expect, test } from "@playwright/test";

import {
  createLargeNetworkFixture,
  networkFixture,
} from "../../apps/web/tests/network-fixture";

const apiBaseUrl = process.env.E2E_API_BASE_URL ?? "http://127.0.0.1:8000";

test.describe.configure({ mode: "serial" });

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

test("analog capture validates, cancels, restores focus, and fits 390 CSS pixels", async ({
  page,
}) => {
  await page.setViewportSize({ height: 844, width: 390 });
  await page.goto("/network");

  const search = page.getByRole("combobox", { name: "人を検索" });
  await search.fill("P018");
  await page.getByRole("option", { name: /Synthetic Person P018/ }).click();
  await expect(
    page.getByRole("heading", { level: 2, name: "Synthetic Person P018" }),
  ).toBeVisible();
  const timelineCountBefore = await page.locator(".timeline-list li").count();
  const captureButton = page.getByRole("button", { name: /接点を記録/ });
  await captureButton.click();

  await expect(
    page.getByRole("heading", { level: 2, name: "接点を記録" }),
  ).toBeFocused();
  await expect(page.getByRole("radio", { name: "コーヒー" })).not.toBeChecked();
  await expect(page.getByRole("radio", { name: "しっかり" })).not.toBeChecked();
  await page.getByRole("button", { name: "この接点を保存" }).click();
  await expect(page.getByText("接点の種類を選んでください。")).toBeVisible();
  await expect(page.getByText("時間の長さを選んでください。")).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);

  await page.keyboard.press("Escape");
  await expect(captureButton).toBeFocused();
  await expect(
    page.getByRole("heading", { level: 2, name: "Synthetic Person P018" }),
  ).toBeVisible();
  await expect(page.locator(".timeline-list li")).toHaveCount(
    timelineCountBefore,
  );
});

test("P001 records a retry-safe coffee with dormant P018 and sees RECONNECTED", async ({
  page,
}) => {
  const captureBodies: Array<Record<string, unknown>> = [];
  let captureAttempts = 0;
  await page.route("**/api/interactions", async (route) => {
    captureAttempts += 1;
    captureBodies.push(
      route.request().postDataJSON() as Record<string, unknown>,
    );
    if (captureAttempts === 1) {
      await route.fulfill({
        body: JSON.stringify({
          error: {
            code: "NETWORK_UNAVAILABLE",
            message: "private upstream detail must not be rendered",
            requestId: "req_nc011_retry",
          },
        }),
        contentType: "application/json",
        status: 502,
      });
      return;
    }
    await route.continue();
  });

  await page.goto("/network");
  const search = page.getByRole("combobox", { name: "人を検索" });
  await search.fill("P018");
  await page.getByRole("option", { name: /Synthetic Person P018/ }).click();
  await expect(
    page.getByRole("heading", { level: 2, name: "Synthetic Person P018" }),
  ).toBeVisible();
  const coffeeTimelineCountBefore = await page
    .getByText("コーヒーを飲みながら話しました")
    .count();
  await page.getByRole("button", { name: /接点を記録/ }).click();
  await page.getByRole("radio", { name: "コーヒー" }).focus();
  await page.keyboard.press("Space");
  await page.getByRole("radio", { name: "しっかり" }).focus();
  await page.keyboard.press("Space");
  await page.getByRole("button", { name: "この接点を保存" }).click();

  const safeError = page
    .getByRole("alert")
    .filter({ hasText: "保存できませんでした" });
  await expect(safeError).toContainText("保存できませんでした");
  await expect(safeError).not.toContainText(
    "private upstream detail must not be rendered",
  );
  await expect(page.getByRole("radio", { name: "コーヒー" })).toBeChecked();
  await expect(page.getByRole("radio", { name: "しっかり" })).toBeChecked();

  await page.getByRole("button", { name: "この接点を保存" }).click();
  await expect(page.locator(".relationship-badge")).toHaveText(
    "再びつながった関係",
  );
  await expect(page.locator(".timeline-list")).toContainText(
    "コーヒーを飲みながら話しました",
  );
  await expect(
    page.getByRole("dialog", { name: /Synthetic Person P018/ }),
  ).toBeFocused();
  await expect(page.getByTestId("network-graph-canvas")).toBeVisible();

  expect(captureBodies).toHaveLength(2);
  expect(captureBodies[1]).toEqual(captureBodies[0]);
  expect(captureBodies[0]).toMatchObject({
    durationBucket: "MEDIUM",
    type: "COFFEE",
  });
  expect(captureBodies[0]).not.toHaveProperty("confidence");
  expect(captureBodies[0]).not.toHaveProperty("relationshipState");

  const replay = await page.request.post("/api/interactions", {
    data: captureBodies[0],
  });
  expect(replay.status()).toBe(200);
  await expect(replay.json()).resolves.toMatchObject({
    interactionId: expect.any(String),
    replayed: true,
  });
  await expect(page.getByText("コーヒーを飲みながら話しました")).toHaveCount(
    coffeeTimelineCountBefore + 1,
  );
});

test("API health endpoint is available", async ({ request }) => {
  const response = await request.get(`${apiBaseUrl}/health`);

  expect(response.status()).toBe(200);
  await expect(response.json()).resolves.toEqual({ status: "ok" });
});
