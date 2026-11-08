import { test, expect } from '@playwright/test';
import { readFile, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';

test.beforeEach(async ({ page }) => {
  // Synthetic merchant wav is injected into a MediaStream, then encoded as actual WebRTC RTP.
  await page.addInitScript(() => {
    const context = new AudioContext();
    const destination = context.createMediaStreamDestination();
    const silence = context.createConstantSource(); silence.offset.value = 0;
    silence.connect(destination); silence.start();
    const measurement = { end: 0, starts: [] as number[], input: [] as number[] };
    (window as any).__measurement = measurement;
    navigator.mediaDevices.getUserMedia = async () => { await context.resume(); return destination.stream; };
    (window as any).__say = async (base64: string) => {
      const raw = Uint8Array.from(atob(base64), c => c.charCodeAt(0));
      const buffer = await context.decodeAudioData(raw.buffer);
      const source = context.createBufferSource(); source.buffer = buffer; source.connect(destination);
      measurement.end = 0;
      await context.resume();
      return new Promise<void>(resolve => { source.onended = () => { measurement.end = performance.now(); measurement.input.push(measurement.end); resolve(); }; source.start(); });
    };
    const start = AudioBufferSourceNode.prototype.start;
    AudioBufferSourceNode.prototype.start = function(...args) {
      if (this.context !== context && measurement.end) {
        measurement.starts.push(performance.now() - measurement.end);
        measurement.end = 0;
      }
      start.apply(this, args);
    };
  });
});

test('four real model speech rounds with browser audio injection', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByText('实时语音已就绪')).toBeVisible({timeout:15000});
  await page.getByRole('button', {name:'开始新会话'}).click();
  await page.getByRole('button', {name:'接入实时语音'}).click();
  const sessions = await (await page.request.get('/api/sessions')).json();
  const sid = sessions[0].session_id;
  const events = async () => (await (await page.request.get(`/api/sessions/${sid}/events`)).json());
  const played = async () => (await events()).filter((e:any) => e.event_type === 'playback.completed').length;
  await expect.poll(played,{timeout:45000}).toBe(1);
  const states = ['consent','explain','confirm','closed'];
  for (let i=0;i<4;i++) {
    const wav = await readFile(resolve(`../../runtime/real-input/${i}.wav`));
    await page.evaluate(base64 => (window as any).__say(base64), wav.toString('base64'));
    await expect.poll(async () => (await (await page.request.get(`/api/sessions/${sid}`)).json()).stage, {timeout:45000}).toBe(states[i]);
    await expect.poll(played,{timeout:45000}).toBe(i+2);
  }
  const session = await (await page.request.get(`/api/sessions/${sid}`)).json();
  expect(session.outcome.merchant_response).toBe('will_resubmit');
  const measurement = await page.evaluate(() => (window as any).__measurement);
  expect(measurement.starts).toHaveLength(4);
  await writeFile(resolve(`../../runtime/real-browser-${sid}.json`), JSON.stringify({session, events:await events(), measurement,
    label:'synthetic-input WebRTC real models; browser schedule latency, not official acoustic measurement'}, null, 2));
  await page.screenshot({path:'../../runtime/real-browser-complete.png',fullPage:true});
  await page.request.post(`/api/sessions/${sid}/disconnect`,{data:{}});
});

test('real speech interrupts opening audio without completing old playback or writing a result', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByText('实时语音已就绪')).toBeVisible({timeout:15000});
  await page.getByRole('button', {name:'开始新会话'}).click();
  await page.getByRole('button', {name:'接入实时语音'}).click();
  const sessions = await (await page.request.get('/api/sessions')).json();
  const sid = sessions[0].session_id;
  const events = async () => (await (await page.request.get(`/api/sessions/${sid}/events`)).json());
  await expect.poll(async () => (await events()).some((e:any) => e.event_type === 'playback.started' && e.generation_id === 0), {timeout:30000}).toBe(true);
  const wav = await readFile(resolve('../../runtime/real-input/0.wav'));
  await page.evaluate(base64 => (window as any).__say(base64), wav.toString('base64'));
  await expect.poll(async () => (await events()).some((e:any) => e.event_type === 'playback.stopped' && e.generation_id === 0), {timeout:15000}).toBe(true);
  await expect.poll(async () => (await (await page.request.get(`/api/sessions/${sid}`)).json()).stage, {timeout:30000}).toBe('consent');
  await expect.poll(async () => (await events()).some((e:any) => e.event_type === 'playback.completed' && e.generation_id > 0), {timeout:30000}).toBe(true);
  await page.getByRole('button', {name:'结束会话'}).click();
  await expect.poll(async () => (await (await page.request.get(`/api/sessions/${sid}`)).json()).stage).toBe('aborted');
  const session = await (await page.request.get(`/api/sessions/${sid}`)).json();
  const evidence = await events();
  expect(session.outcome).toBeNull();
  expect(evidence.some((e:any) => e.event_type === 'playback.completed' && e.generation_id === 0)).toBe(false);
  expect(evidence.some((e:any) => e.event_type === 'tool.committed')).toBe(false);
  await writeFile(resolve(`../../runtime/real-interrupt-${sid}.json`), JSON.stringify({session,events:evidence,
    label:'Synthetic speech interrupts real model audio; not human/acoustic acceptance'}, null, 2));
});
