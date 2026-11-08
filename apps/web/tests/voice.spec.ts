import { test, expect } from '@playwright/test';

test('real WebRTC transport delivers synthetic tone and browser playback receipts', async ({ page }) => {
  await page.addInitScript(() => {
    const original = RTCPeerConnection.prototype.createDataChannel;
    const start = AudioBufferSourceNode.prototype.start;
    const stop = AudioBufferSourceNode.prototype.stop;
    const state = { starts: 0, stops: 0, channel: null as RTCDataChannel | null };
    (window as any).__playbackTest = state;
    RTCPeerConnection.prototype.createDataChannel = function(label, options) {
      const channel = original.call(this, label, options); state.channel = channel; return channel;
    };
    AudioBufferSourceNode.prototype.start = function(...args) { state.starts++; start.apply(this, args); };
    AudioBufferSourceNode.prototype.stop = function(...args) { state.stops++; stop.apply(this, args); };
  });
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
  // Adversarial late-packet test at the browser boundary, separate from model quality.
  const playback = await page.evaluate(() => {
    const state = (window as any).__playbackTest;
    const send = (data: object) => state.channel.dispatchEvent(new MessageEvent('message', { data: JSON.stringify(data) }));
    const pcm = btoa(String.fromCharCode(...new Uint8Array(4800)));
    send({type:'audio-start',generation_id:0,text:'测试'});
    send({type:'audio-chunk',generation_id:0,seq:0,sample_rate:24000,pcm});
    send({type:'interrupt',generation_id:0});
    const beforeLate = state.starts;
    send({type:'audio-chunk',generation_id:0,seq:1,sample_rate:24000,pcm});
    send({type:'audio-start',generation_id:0,text:'旧回复'});
    send({type:'audio-chunk',generation_id:0,seq:0,sample_rate:24000,pcm});
    return {beforeLate,afterLate:state.starts,stops:state.stops};
  });
  expect(playback.stops).toBeGreaterThan(0);
  expect(playback.afterLate).toBe(playback.beforeLate);
  await page.getByRole('button', { name: '结束会话' }).click();
  await expect.poll(async () => (await (await page.request.get(`/api/sessions/${sid}`)).json()).stage).toBe('aborted');
});
