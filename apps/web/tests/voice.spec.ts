import { test, expect } from '@playwright/test';

test('real WebRTC transport delivers synthetic tone and browser playback receipts', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByText('实时语音已就绪')).toBeVisible();
  await page.getByRole('button', { name: '开始新会话' }).click();
  await page.getByRole('button', { name: '接入实时语音' }).click();
  await expect(page.getByRole('button', { name: '断开麦克风' })).toBeVisible();
  const sessions = await (await page.request.get('/api/sessions')).json();
  const sid = sessions[0].session_id;
  await expect.poll(async () => {
    const events = await (await page.request.get(`/api/sessions/${sid}/events`)).json();
    return events.map((e: {event_type:string}) => e.event_type);
  }, { timeout: 20000 }).toContain('playback.completed');
  const events = await (await page.request.get(`/api/sessions/${sid}/events`)).json();
  expect(events.some((e: {event_type:string}) => e.event_type === 'voice.connected')).toBe(true);
  expect(events.some((e: {event_type:string}) => e.event_type === 'tts.generated')).toBe(true);
  await page.getByRole('button', { name: '结束会话' }).click();
  await expect.poll(async () => (await (await page.request.get(`/api/sessions/${sid}`)).json()).stage).toBe('aborted');
});
