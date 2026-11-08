import React, { useEffect, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './style.css';

type Case = { case_id: string; company: string; brand: string; reason: string; default_channel: string; required_actions: string[] };
type Session = { session_id: string; stage: string; version: number; generation_id: number; turn_id: number; last_response: string; outcome: null | Record<string, unknown>; case: Case };
type Event = { event_id: string; event_type: string; generation_id: number; timestamp_utc: string; payload: Record<string, unknown>; session_seq: number };
type Report = { checks: Record<string, unknown>; timing: Record<string, unknown>; limitations: string[] };
const stages: Record<string, string> = { identity: '身份确认', consent: '确认沟通意愿', explain: '整改说明', confirm: '结果确认', closed: '已结束', aborted: '已中断' };
const steps = ['identity', 'consent', 'explain', 'confirm', 'closed'];

function App() {
  const [token, setToken] = useState('');
  const [cases, setCases] = useState<Case[]>([]);
  const [selected, setSelected] = useState('');
  const [session, setSession] = useState<Session | null>(null);
  const [history, setHistory] = useState<Session[]>([]);
  const [events, setEvents] = useState<Event[]>([]);
  const [report, setReport] = useState<Report | null>(null);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [health, setHealth] = useState({ mode: 'unknown', voice_ready: false });
  const [voice, setVoice] = useState(false);
  const audio = useRef<HTMLAudioElement>(null);
  const connection = useRef<RTCPeerConnection | null>(null);
  const microphone = useRef<MediaStream | null>(null);
  const current = useRef<Session | null>(null);
  const chat = useRef<HTMLDivElement>(null);
  current.current = session;

  async function api<T>(path: string, body?: unknown, method?: string): Promise<T> {
    const res = await fetch(path, { method: method || (body === undefined ? 'GET' : 'POST'),
      headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      ...(body === undefined ? {} : { body: JSON.stringify(body) }) });
    const data = await res.json();
    if (!res.ok) throw new Error(data.message || (res.status === 422 ? '输入格式不正确，请检查后重试。' : `请求失败 (${res.status})`));
    return data as T;
  }
  async function run(work: () => Promise<void>) {
    setBusy(true); setError('');
    try { await work(); } catch (e) { setError(e instanceof Error ? e.message : String(e)); }
    finally { setBusy(false); }
  }
  async function load() {
    const status = await api<typeof health>('/health'); setHealth(status);
    const list = await api<Case[]>('/api/cases'); setCases(list);
    setSelected(prev => prev || list.find(x => x.default_channel === 'phone')?.case_id || '');
    setHistory(await api<Session[]>('/api/sessions'));
  }
  async function refresh(s: Session) {
    setSession(s);
    const [log, result] = await Promise.all([
      api<Event[]>(`/api/sessions/${s.session_id}/events`),
      api<Report>(`/api/sessions/${s.session_id}/report`),
    ]);
    setEvents(log); setReport(result);
  }
  useEffect(() => { void run(load); return stopAudio; }, []);
  useEffect(() => { chat.current?.scrollTo({ top: chat.current.scrollHeight }); }, [events.length]);
  useEffect(() => {
    if (!voice || !session) return;
    const id = window.setInterval(() => {
      void api<Session>(`/api/sessions/${session.session_id}`).then(refresh).catch(e => { setError(String(e)); stopAudio(); });
    }, 800);
    return () => clearInterval(id);
  }, [voice, session?.session_id, token]);

  function stopAudio() {
    connection.current?.close(); connection.current = null;
    microphone.current?.getTracks().forEach(t => t.stop()); microphone.current = null;
    if (audio.current) { audio.current.pause(); audio.current.srcObject = null; }
    setVoice(false);
  }
  async function startVoice(s: Session) {
    if (!window.isSecureContext || !navigator.mediaDevices) throw new Error('麦克风需要 HTTPS 或本机 localhost 页面。');
    try {
      microphone.current = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true }, video: false });
      const pc = new RTCPeerConnection(); connection.current = pc;
      microphone.current.getTracks().forEach(track => pc.addTrack(track, microphone.current!));
      pc.ontrack = e => { if (audio.current) { audio.current.srcObject = e.streams[0] || new MediaStream([e.track]); void audio.current.play().catch(() => setError('请点击播放按钮允许音频播放。')); } };
      pc.onconnectionstatechange = () => { if (['failed', 'disconnected'].includes(pc.connectionState)) { setError('语音连接中断，请检查网络后重新连接。'); stopAudio(); } };
      const channel = pc.createDataChannel('pipecat');
      channel.onmessage = e => {
        try {
          const event = JSON.parse(e.data);
          if (event.type === 'interrupt' && audio.current) { audio.current.muted = true; }
          if (event.type === 'audio-start' && audio.current) { audio.current.muted = false; }
        } catch { /* Unrecognized messages never execute actions. */ }
      };
      await pc.setLocalDescription(await pc.createOffer());
      await new Promise<void>((resolve, reject) => {
        if (pc.iceGatheringState === 'complete') return resolve();
        const timeout = setTimeout(() => reject(new Error('语音网络协商超时')), 10000);
        pc.onicegatheringstatechange = () => { if (pc.iceGatheringState === 'complete') { clearTimeout(timeout); resolve(); } };
      });
      const answer = await api<RTCSessionDescriptionInit>(`/api/sessions/${s.session_id}/offer`, { sdp: pc.localDescription!.sdp, type: 'offer' });
      await pc.setRemoteDescription(answer); setVoice(true);
    } catch (e) { stopAudio(); throw e; }
  }
  const active = session && !['closed', 'aborted'].includes(session.stage);
  const detail = session?.case || cases.find(c => c.case_id === selected);
  const conversation = events.filter(e => ['user.text', 'asr.final', 'response.validated'].includes(e.event_type));

  return <div className="shell">
    <aside className="sidebar">
      <div className="brand"><span className="brand-mark">语</span><div>智语外呼<small>资审服务工作台</small></div></div>
      <div className="nav-title">工作空间</div><div className="nav-current">通话与核验</div>
      <div className="sidebar-note">每一次沟通都有据可查<small>对话、业务回执与质检记录同步保留。</small></div>
      <label className="token-label">访问令牌<input type="password" value={token} onChange={e => setToken(e.target.value)} autoComplete="off" placeholder="本机模式可留空"/></label>
      <button className="subtle" onClick={() => void run(load)} disabled={busy}>连接工作空间</button>
      <div className="history"><h3>最近会话</h3>{history.length === 0 ? <small>尚无会话记录</small> : history.map(s => <button key={s.session_id} disabled={busy || !!active} onClick={() => void run(async () => { stopAudio(); await refresh(await api(`/api/sessions/${s.session_id}`)); })}>{s.case.company}<small>{stages[s.stage]} · {s.turn_id} 轮</small></button>)}</div>
      <footer>基线研发环境<small>仅用于脱敏或合成业务任务</small></footer>
    </aside>
    <main>
      <header><div><h1>通话工作台</h1><p>确认身份，说明整改，核验结果。</p></div><span className={'mode ' + (health.mode === 'mock' ? 'mock' : '')}>{health.mode === 'mock' ? '模拟联调 · 文字交互' : health.voice_ready ? '实时语音已就绪' : '正在连接'}</span></header>
      {error && <div role="alert" className="error">{error}<button onClick={() => setError('')} aria-label="关闭提示">×</button></div>}
      <div className="workspace">
        <section className="conversation-panel">
          <div className="task-select"><label>选择外呼任务<select value={selected} disabled={!!active || busy} onChange={e => setSelected(e.target.value)}>{cases.map(c => <option key={c.case_id} value={c.case_id}>{c.company}{c.default_channel === 'written' ? '（站内处理）' : ''}</option>)}</select></label>
            <button className="primary" disabled={busy || !!active || !selected} onClick={() => void run(async () => { stopAudio(); const s = await api<Session>('/api/sessions', { case_id: selected, request_id: crypto.randomUUID() }); await refresh(s); await load(); })}>开始新会话</button></div>
          <ol className="steps">{steps.map((s, i) => <li key={s} className={session?.stage === s ? 'current' : session && steps.indexOf(session.stage) > i ? 'done' : ''}><span>{i+1}</span>{stages[s]}</li>)}</ol>
          <div className="chat" ref={chat} aria-live="polite">{!session ? <div className="empty"><div className="empty-icon">听</div><h2>准备好，再开始沟通</h2><p>选择一个任务，确认资料后开始会话。<br/>模拟模式用于验证流程，不代表语音验收完成。</p></div> : conversation.map(e => <article className={'bubble ' + (e.event_type === 'response.validated' ? 'assistant' : 'merchant')} key={e.event_id}><small>{e.event_type === 'response.validated' ? '审核助手' : '商家'}<time>{new Date(e.timestamp_utc).toLocaleTimeString('zh-CN')}</time></small><p>{String(e.payload.text)}</p></article>)}</div>
          <div className="composer"><form onSubmit={e => { e.preventDefault(); if (!session || !message.trim()) return; const text = message; void run(async () => { const s = await api<Session>(`/api/sessions/${session.session_id}/turns`, { text, request_id: crypto.randomUUID(), expected_version: session.version }); setMessage(''); await refresh(s); await load(); }); }}><input aria-label="商家回复" placeholder={active ? '输入商家回复，例如“我是负责人”' : '开始会话后输入回复'} value={message} onChange={e => setMessage(e.target.value)} disabled={!active || busy || voice}/><button className="primary" disabled={!active || busy || !message.trim() || voice}>发送</button></form>
            <div className="call-actions"><button disabled={!active || busy || !health.voice_ready} onClick={() => void run(async () => { if (voice) stopAudio(); else if (session) await startVoice(session); })}>{voice ? '断开麦克风' : '接入实时语音'}</button><span>{session ? `${session.turn_id} 轮对话 · ${stages[session.stage]}` : '尚未开始'}</span><button className="danger" disabled={!active || busy} onClick={() => void run(async () => { stopAudio(); if (session) { await refresh(await api(`/api/sessions/${session.session_id}/end`, {})); await load(); } })}>结束会话</button></div><audio ref={audio} autoPlay controls hidden={!voice}/></div>
        </section>
        <aside className="inspection"><section><h2>本次任务</h2>{detail ? <><dl><dt>商家</dt><dd>{detail.company}</dd><dt>品牌</dt><dd>{detail.brand}</dd><dt>审核事项</dt><dd>{detail.reason}</dd></dl><h3>整改要求</h3><ul>{detail.required_actions.map(a => <li key={a}>{a}</li>)}</ul></> : <p>连接后选择任务。</p>}</section>
          <section><h2>结果核验<span className={session?.outcome ? 'success' : 'pending'}>{session?.outcome ? '已回写' : '待完成'}</span></h2>{report ? <ul className="checks">{Object.entries({身份确认: report.checks.identity_confirmed, 沟通意愿: report.checks.consent_confirmed, 结果确认: report.checks.result_confirmed, 回写回执: report.checks.writeback_committed}).map(([k,v]) => <li key={k}><span>{k}</span><b className={v ? 'success' : 'pending'}>{v ? '已确认' : '未确认'}</b></li>)}</ul> : <p>会话开始后展示核验结果。</p>}<p className="muted">未确认的结果不会记为已同意。没有音频测量时，不显示时延成绩。</p></section>
          <section><h2>追踪记录</h2>{session ? <><code>{session.session_id.slice(0,16)}</code><p className="muted">已记录 {events.length} 个事件</p><details><summary>查看事件时间线</summary><ol className="trace">{events.map(e => <li key={e.event_id}><b>{e.session_seq}</b> {e.event_type}</li>)}</ol></details><button className="export" onClick={() => { const blob = new Blob([JSON.stringify({ session, events, report }, null, 2)], {type:'application/json'}); const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href=url; a.download=`session-${session.session_id}.json`; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000); }}>导出本次记录</button></> : <p className="muted">每通会话分配独立追踪编号。</p>}</section>
        </aside>
      </div>
    </main>
  </div>;
}

createRoot(document.getElementById('root')!).render(<App/>);

