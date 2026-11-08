type Request = <T>(path: string, body?: unknown) => Promise<T>;

/** Input RTP and output PCM both travel over the authenticated WebRTC connection.
 * Every queued audio node belongs to one generation and is stopped on interruption.
 */
export class VoiceConnection {
  private pc = new RTCPeerConnection({ iceServers: [] });
  private context = new AudioContext();
  private stream: MediaStream | null = null;
  private nodes = new Set<AudioBufferSourceNode>();
  private generation = -1;
  private seq = 0;
  private nextTime = 0;
  private receivedEnd = false;
  private text = '';
  private started = false;
  private stopped = false;
  private ping: ReturnType<typeof setInterval> | null = null;
  constructor(private sid: string, private api: Request, private error: (message: string) => void) {}

  async connect() {
    if (!window.isSecureContext || !navigator.mediaDevices) throw new Error('麦克风需要 HTTPS 或本机 localhost 页面。');
    await this.context.resume();
    this.stream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true }, video: false });
    this.stream.getTracks().forEach(track => this.pc.addTrack(track, this.stream!));
    const channel = this.pc.createDataChannel('pipecat', { ordered: true });
    channel.onopen = () => { this.ping = setInterval(() => { if (channel.readyState === 'open') channel.send('ping'); }, 1000); };
    channel.onmessage = event => {
      try { this.message(JSON.parse(event.data)); }
      catch { this.fail('语音数据异常，播放已停止。'); }
    };
    this.pc.onconnectionstatechange = () => {
      if (['failed', 'disconnected'].includes(this.pc.connectionState)) this.fail('语音连接中断，请检查网络并创建新会话。');
    };
    await this.pc.setLocalDescription(await this.pc.createOffer());
    await new Promise<void>((resolve, reject) => {
      if (this.pc.iceGatheringState === 'complete') return resolve();
      const timeout = setTimeout(() => reject(new Error('语音网络协商超时')), 10000);
      this.pc.onicegatheringstatechange = () => {
        if (this.pc.iceGatheringState === 'complete') { clearTimeout(timeout); resolve(); }
      };
    });
    const answer = await this.api<RTCSessionDescriptionInit>(`/api/sessions/${this.sid}/offer`, { sdp: this.pc.localDescription!.sdp, type: 'offer' });
    await this.pc.setRemoteDescription(answer);
  }

  private event(kind: string, chars = 0) {
    if (this.generation < 0) return;
    // AudioContext scheduling/completion is browser evidence, not an acoustic measurement.
    void this.api(`/api/sessions/${this.sid}/events`, { event_id: crypto.randomUUID(), event_type: kind,
      generation_id: this.generation, client_time_ms: performance.now(), played_chars: chars })
      .catch(() => { this.error('播放回执保存失败，请查阅记录；本次不能视为完整验收。'); });
  }

  private clearPlayback() {
    const hadAudio = this.nodes.size > 0;
    for (const node of this.nodes) { node.onended = null; node.stop(); node.disconnect(); }
    this.nodes.clear();
    this.nextTime = this.context.currentTime;
    this.receivedEnd = false;
    if (hadAudio) this.event('playback.stopped');
  }

  private message(event: Record<string, any>) {
    if (this.stopped) return;
    if (event.type === 'interrupt') {
      this.clearPlayback(); this.generation = Math.max(this.generation, Number(event.generation_id)) + 1;
    } else if (event.type === 'audio-start' && event.generation_id >= this.generation) {
      this.clearPlayback(); this.generation = event.generation_id; this.seq = 0;
      this.text = event.text; this.started = false;
    } else if (event.type === 'audio-chunk' && event.generation_id === this.generation) {
      if (event.seq !== this.seq++ || typeof event.pcm !== 'string' || event.pcm.length > 16000) throw new Error('sequence');
      if (![16000, 22050, 24000, 48000].includes(event.sample_rate)) throw new Error('rate');
      const raw = atob(event.pcm);
      if (!raw.length || raw.length % 2) throw new Error('pcm');
      const bytes = Uint8Array.from(raw, char => char.charCodeAt(0));
      const view = new DataView(bytes.buffer);
      const buffer = this.context.createBuffer(1, bytes.length / 2, event.sample_rate);
      const output = buffer.getChannelData(0);
      for (let i = 0; i < output.length; i++) output[i] = view.getInt16(i * 2, true) / 32768;
      if (this.nextTime - this.context.currentTime > 3) throw new Error('playback backlog');
      const node = this.context.createBufferSource(); node.buffer = buffer; node.connect(this.context.destination);
      const start = Math.max(this.context.currentTime + .02, this.nextTime);
      this.nextTime = start + buffer.duration;
      this.nodes.add(node);
      const generation = this.generation;
      node.onended = () => {
        this.nodes.delete(node); node.disconnect();
        if (generation === this.generation && this.receivedEnd && this.nodes.size === 0) this.event('playback.completed', this.text.length);
      };
      node.start(start);
      if (!this.started) { this.started = true; this.event('playback.started'); }
    } else if (event.type === 'audio-end' && event.generation_id === this.generation) {
      if (event.chunks !== this.seq || !this.seq) throw new Error('truncated audio');
      this.receivedEnd = true;
      if (this.nodes.size === 0) this.event('playback.completed', this.text.length);
    } else if (event.type === 'error') {
      this.fail(String(event.message));
    }
  }

  private fail(message: string) { this.error(message); this.close(); }

  close() {
    if (this.stopped) return;
    this.stopped = true; this.clearPlayback();
    if (this.ping) clearInterval(this.ping);
    this.stream?.getTracks().forEach(track => track.stop());
    this.pc.close(); void this.context.close();
    void this.api(`/api/sessions/${this.sid}/disconnect`, {}).catch(() => this.error('断线状态未保存，请手动结束会话。'));
  }
}
