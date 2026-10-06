import { expect, test } from '@playwright/test';

test('mentor workspace loads and exposes the floating mentor', async ({ page, request }) => {
  const health = await request.get('http://127.0.0.1:8000/api/v1/health');
  expect(health.ok()).toBeTruthy();

  await page.goto('/');
  await expect(page.getByText('AI Coding Mentor')).toBeVisible();
  await expect(page.getByText('AI MENTOR')).toBeVisible();
  await expect(page.getByText('Run code')).toBeVisible();
});
