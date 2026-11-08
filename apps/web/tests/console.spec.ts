import { test, expect } from '@playwright/test';

test('four-turn text task, receipt, audit export and history', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByText('模拟联调 · 文字交互')).toBeVisible();
  await page.getByRole('button', { name: '开始新会话' }).click();
  await expect(page.getByText('您好，我是商家资质审核智能助手。', { exact: false })).toBeVisible();
  for (const text of ['我是负责人', '方便，请说', '明白了，我会补齐重新提交', '确认，我会补齐重新提交']) {
    await page.getByRole('textbox', { name: '商家回复' }).fill(text);
    await page.getByRole('button', { name: '发送', exact: true }).click();
    await expect(page.getByRole('textbox', { name: '商家回复' })).toHaveValue('');
  }
  await expect(page.getByText('已回写', { exact: true })).toBeVisible();
  await expect(page.locator('.checks b.success')).toHaveCount(4);
  const sessions = await (await page.request.get('/api/sessions')).json();
  expect(sessions[0].outcome.merchant_response).toBe('will_resubmit');
  expect(sessions[0].outcome.needs_human).toBe(false);
  await expect(page.getByText('4 轮对话 · 已结束', { exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: '接入实时语音' })).toBeDisabled();
  await page.getByText('查看事件时间线').click();
  await expect(page.getByText('tool.committed', { exact: false })).toBeVisible();
  const download = page.waitForEvent('download');
  await page.getByRole('button', { name: '导出本次记录' }).click();
  expect((await download).suggestedFilename()).toMatch(/^session-.*\.json$/);
  await page.screenshot({ path: '../../runtime/console-desktop.png', fullPage: true });
});

test('written case is rejected and mobile layout fits', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/');
  await page.getByLabel('选择外呼任务').selectOption('demo-written');
  await page.getByRole('button', { name: '开始新会话' }).click();
  await expect(page.getByRole('alert')).toContainText('站内处理');
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
  await page.screenshot({ path: '../../runtime/console-mobile.png', fullPage: true });
});
