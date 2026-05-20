"""
星轨人格 MBTI 后端 · Vercel 版
数据存在 GitHub 仓库中，不会丢失
"""

import json, os, uuid, hashlib, time
from datetime import datetime, timedelta, timezone
from collections import Counter
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import urllib.request, urllib.error, base64

TOKEN = os.environ.get("GH_TOKEN", "")
REPO = "6624-lab/MBTI-Steller-backend"
DATA_PATH = "results.json"

TYPE_DATA = {
    "INTJ": "星域建筑师", "INTP": "星际逻辑师", "ENTJ": "星系统帅", "ENTP": "星际辩手",
    "INFJ": "星海先知", "INFP": "星梦诗人", "ENFJ": "星团启迪者", "ENFP": "星云探险家",
    "ISTJ": "星轨守护者", "ISFJ": "星尘守护者", "ESTJ": "星区执行官", "ESFJ": "星港管家",
    "ISTP": "星舰工匠", "ISFP": "星尘艺术家", "ESTP": "星际冒险家", "ESFP": "星辉表演者",
}

app = FastAPI(title="星轨人格后台")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_cache = {"data": None, "ts": 0}

def _load():
    now = time.time()
    if _cache["data"] is not None and (now - _cache["ts"]) < 30:
        return _cache["data"]
    req = urllib.request.Request(BLOB_URL, headers={"User-Agent": "mbti-backend"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            if isinstance(data, list):
                data = {"results": data, "pageviews": []}
            _cache["data"] = data
            _cache["ts"] = now
            return data
    except Exception:
        empty = {"results": [], "pageviews": []}
        _cache["data"] = empty
        return empty

def _save(data):
    raw = json.dumps(data, ensure_ascii=False).encode()
    req = urllib.request.Request(BLOB_URL, data=raw,
        headers={"User-Agent": "mbti-backend", "Content-Type": "application/json"},
        method="PUT")
    try:
        urllib.request.urlopen(req, timeout=15)
    except Exception as e:
        print(f"Save error: {e}")
    _cache["data"] = data
    _cache["ts"] = time.time()

INDEX_HTML = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>星轨人格 · 星际 MBTI 测试</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;600;700;900&display=swap');

  * { margin: 0; padding: 0; box-sizing: border-box; }

  :root {
    --bg: #0a0a1a;
    --card-bg: rgba(255,255,255,0.04);
    --card-border: rgba(255,255,255,0.08);
    --text: #e8e6f0;
    --text-dim: rgba(255,255,255,0.45);
    --accent: #7c5cfc;
    --accent-glow: rgba(124,92,252,0.35);
    --gradient-1: #7c5cfc;
    --gradient-2: #e04a8f;
    --gradient-3: #f5a623;
    --radius: 20px;
  }

  body {
    font-family: 'Noto Sans SC', -apple-system, sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
    overflow-x: hidden;
    line-height: 1.6;
  }

  /* ── Stars Canvas ── */
  #stars-canvas {
    position: fixed;
    top: 0; left: 0;
    width: 100%; height: 100%;
    z-index: 0;
    pointer-events: none;
  }

  /* ── Nebula overlay ── */
  .nebula {
    position: fixed;
    top: -30%; left: -20%;
    width: 140%; height: 140%;
    z-index: 0;
    pointer-events: none;
    background:
      radial-gradient(ellipse 70% 60% at 20% 80%, rgba(124,92,252,0.08) 0%, transparent 70%),
      radial-gradient(ellipse 50% 50% at 80% 20%, rgba(224,74,143,0.06) 0%, transparent 60%),
      radial-gradient(ellipse 40% 40% at 50% 50%, rgba(245,166,35,0.04) 0%, transparent 50%);
  }

  /* ── Container ── */
  .container {
    position: relative;
    z-index: 1;
    max-width: 640px;
    margin: 0 auto;
    padding: 40px 20px 80px;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
  }

  /* ════════ START SCREEN ════════ */
  .screen { display: none; width: 100%; }
  .screen.active { display: flex; flex-direction: column; align-items: center; }

  #start-screen {
    justify-content: center;
    min-height: 90vh;
    text-align: center;
    padding-top: 10vh;
  }

  .logo-icon {
    font-size: 64px;
    margin-bottom: 16px;
    animation: float 4s ease-in-out infinite;
  }
  @keyframes float {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-12px); }
  }

  .title {
    font-size: clamp(32px, 7vw, 52px);
    font-weight: 900;
    background: linear-gradient(135deg, var(--gradient-1), var(--gradient-2), var(--gradient-3));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: 0.02em;
    line-height: 1.2;
    margin-bottom: 8px;
  }

  .subtitle {
    font-size: clamp(14px, 2.5vw, 18px);
    color: var(--text-dim);
    font-weight: 300;
    letter-spacing: 0.15em;
    margin-bottom: 32px;
  }

  .desc-text {
    font-size: 15px;
    color: rgba(255,255,255,0.55);
    max-width: 420px;
    line-height: 1.8;
    margin-bottom: 40px;
  }

  .btn {
    background: linear-gradient(135deg, var(--gradient-1), var(--gradient-2));
    color: #fff;
    border: none;
    padding: 16px 48px;
    border-radius: 50px;
    font-size: 17px;
    font-weight: 700;
    cursor: pointer;
    transition: all 0.3s ease;
    font-family: inherit;
    letter-spacing: 0.05em;
    position: relative;
    overflow: hidden;
  }
  .btn::before {
    content: '';
    position: absolute;
    top: -2px; left: -2px;
    right: -2px; bottom: -2px;
    background: linear-gradient(135deg, var(--gradient-1), var(--gradient-2), var(--gradient-3));
    border-radius: 52px;
    z-index: -1;
    opacity: 0;
    transition: opacity 0.3s;
  }
  .btn:hover {
    transform: translateY(-2px) scale(1.02);
    box-shadow: 0 8px 32px var(--accent-glow);
  }
  .btn:hover::before { opacity: 1; }
  .btn:active { transform: scale(0.97); }

  .btn-outline {
    background: transparent;
    border: 1.5px solid rgba(255,255,255,0.15);
    padding: 12px 32px;
    font-size: 14px;
    font-weight: 500;
  }
  .btn-outline:hover {
    border-color: var(--accent);
    background: rgba(124,92,252,0.08);
    box-shadow: none;
  }

  /* ════════ QUESTION SCREEN ════════ */
  #quiz-screen { padding-top: 20px; }

  .quiz-header {
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 32px;
  }

  .question-counter {
    font-size: 13px;
    color: var(--text-dim);
    letter-spacing: 0.05em;
  }
  .question-counter strong {
    color: var(--text);
    font-size: 18px;
  }

  .progress-bar-track {
    flex: 1;
    height: 4px;
    background: rgba(255,255,255,0.08);
    border-radius: 4px;
    margin: 0 16px;
    overflow: hidden;
  }
  .progress-bar-fill {
    height: 100%;
    width: 0%;
    background: linear-gradient(90deg, var(--gradient-1), var(--gradient-2));
    border-radius: 4px;
    transition: width 0.6s cubic-bezier(0.22,1,0.36,1);
  }

  .dimension-tag {
    font-size: 11px;
    padding: 4px 12px;
    border-radius: 20px;
    background: rgba(124,92,252,0.12);
    color: var(--accent);
    letter-spacing: 0.08em;
    font-weight: 600;
  }

  .question-card {
    width: 100%;
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: var(--radius);
    padding: 40px 28px;
    backdrop-filter: blur(12px);
    animation: cardIn 0.5s ease-out;
  }
  @keyframes cardIn {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
  }

  .question-text {
    font-size: clamp(18px, 3.5vw, 22px);
    font-weight: 600;
    text-align: center;
    line-height: 1.5;
    margin-bottom: 36px;
    min-height: 2.4em;
  }

  .options {
    display: flex;
    flex-direction: column;
    gap: 14px;
  }

  .option-btn {
    display: flex;
    align-items: center;
    gap: 16px;
    width: 100%;
    padding: 18px 24px;
    background: rgba(255,255,255,0.03);
    border: 1.5px solid rgba(255,255,255,0.08);
    border-radius: 16px;
    color: var(--text);
    font-size: 15px;
    font-family: inherit;
    cursor: pointer;
    transition: all 0.25s ease;
    text-align: left;
    line-height: 1.5;
  }
  .option-btn:hover {
    background: rgba(124,92,252,0.08);
    border-color: var(--accent);
    transform: translateX(4px);
  }
  .option-btn:active { transform: scale(0.98); }

  .option-icon {
    font-size: 28px;
    flex-shrink: 0;
    width: 48px;
    height: 48px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(255,255,255,0.04);
    border-radius: 12px;
  }
  .option-btn:hover .option-icon {
    background: rgba(124,92,252,0.12);
  }

  .option-label {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: var(--text-dim);
    margin-bottom: 2px;
  }

  /* ════════ RESULT SCREEN ════════ */
  #result-screen {
    padding-top: 30px;
    text-align: center;
  }

  .result-type {
    font-size: clamp(42px, 8vw, 64px);
    font-weight: 900;
    background: linear-gradient(135deg, var(--gradient-1), var(--gradient-2));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: 0.08em;
    margin-bottom: 4px;
  }

  .result-name {
    font-size: 22px;
    font-weight: 600;
    margin-bottom: 24px;
  }

  .result-badge {
    display: inline-flex;
    gap: 8px;
    margin-bottom: 28px;
    flex-wrap: wrap;
    justify-content: center;
  }
  .badge-item {
    padding: 6px 16px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.05em;
  }
  .badge-item.ei { background: rgba(124,92,252,0.12); color: #7c5cfc; }
  .badge-item.sn { background: rgba(224,74,143,0.12); color: #e04a8f; }
  .badge-item.tf { background: rgba(245,166,35,0.12); color: #f5a623; }
  .badge-item.jp { background: rgba(76,201,160,0.12); color: #4cc9a0; }

  .result-card {
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: var(--radius);
    padding: 32px 24px;
    backdrop-filter: blur(12px);
    margin-bottom: 20px;
    text-align: left;
    width: 100%;
    animation: cardIn 0.5s ease-out 0.2s both;
  }

  .result-card h3 {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 12px;
    color: var(--accent);
    letter-spacing: 0.05em;
  }

  .result-card p {
    font-size: 14px;
    color: rgba(255,255,255,0.7);
    line-height: 1.8;
  }

  .dimension-scores {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin-bottom: 20px;
    width: 100%;
  }
  .dim-score-card {
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 14px;
    padding: 16px;
    text-align: center;
    animation: cardIn 0.5s ease-out 0.3s both;
  }
  .dim-score-card .dim-label {
    font-size: 11px;
    color: var(--text-dim);
    letter-spacing: 0.08em;
    margin-bottom: 4px;
  }
  .dim-score-card .dim-value {
    font-size: 20px;
    font-weight: 700;
  }
  .dim-score-card .dim-bar {
    height: 3px;
    border-radius: 3px;
    background: rgba(255,255,255,0.06);
    margin-top: 8px;
    overflow: hidden;
  }
  .dim-score-card .dim-bar-fill {
    height: 100%;
    border-radius: 3px;
    transition: width 1s ease;
  }

  .result-actions {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
    justify-content: center;
    margin-top: 12px;
  }

  .share-toast {
    position: fixed;
    bottom: 40px;
    left: 50%;
    transform: translateX(-50%) translateY(80px);
    background: rgba(255,255,255,0.1);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(255,255,255,0.12);
    padding: 12px 28px;
    border-radius: 12px;
    color: #fff;
    font-size: 14px;
    z-index: 100;
    opacity: 0;
    transition: all 0.4s ease;
    pointer-events: none;
  }
  .share-toast.show {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
  }

  /* ── Responsive ── */
  @media (max-width: 480px) {
    .container { padding: 24px 16px 60px; }
    .question-card { padding: 28px 18px; }
    .option-btn { padding: 14px 16px; font-size: 14px; }
    .option-icon { width: 40px; height: 40px; font-size: 22px; }
    .dimension-scores { grid-template-columns: 1fr; }
    .result-actions { flex-direction: column; align-items: center; }
    .result-actions .btn { width: 100%; }
  }
</style>
</head>
<body>

<canvas id="stars-canvas"></canvas>
<div class="nebula"></div>

<div class="container">

  <!-- ════════ START SCREEN ════════ -->
  <div id="start-screen" class="screen active">
    <div class="logo-icon">🌌</div>
    <h1 class="title">星轨人格</h1>
    <p class="subtitle">STELLAR PERSONALITY ATLAS</p>
    <p class="desc-text">
      穿越 20 道星际回廊，<br>
      每一次选择都在描摹你的灵魂光谱。<br>
      这不是一道测试——<br>
      这是一次与自己的星海对话。
    </p>
    <button class="btn" onclick="startQuiz()">✦ 启程星途</button>
  </div>

  <!-- ════════ QUIZ SCREEN ════════ -->
  <div id="quiz-screen" class="screen">
    <div class="quiz-header">
      <span class="question-counter">
        <strong id="q-num">1</strong> / <span id="q-total">20</span>
      </span>
      <div class="progress-bar-track">
        <div class="progress-bar-fill" id="progress-fill"></div>
      </div>
      <span class="dimension-tag" id="dim-tag">E/I</span>
    </div>

    <div class="question-card" id="question-card">
      <div class="question-text" id="question-text"></div>
      <div class="options" id="options-container"></div>
    </div>
  </div>

  <!-- ════════ RESULT SCREEN ════════ -->
  <div id="result-screen" class="screen">
    <div class="result-type" id="result-type">ENFP</div>
    <div class="result-name" id="result-name">冒险家</div>
    <div class="result-badge" id="result-badge"></div>

    <div class="dimension-scores" id="dim-scores"></div>

    <div class="result-card">
      <h3>✦ 人格星图</h3>
      <p id="result-desc"></p>
    </div>

    <div class="result-card">
      <h3>✦ 能量特质</h3>
      <p id="result-traits"></p>
    </div>

    <div class="result-card">
      <h3>✦ 星际箴言</h3>
      <p id="result-quote"></p>
    </div>

    <div class="result-actions">
      <button class="btn" id="share-btn" onclick="shareResult()">📡 分享星图</button>
      <button class="btn btn-outline" onclick="restartQuiz()">↺ 重新启程</button>
    </div>
  </div>

</div>

<div class="share-toast" id="share-toast">✨ 链接已复制，转发即可分享你的星图！</div>

<script>
  // ═══ Stars ═══
  const canvas = document.getElementById('stars-canvas');
  const ctx = canvas.getContext('2d');
  let stars = [];
  let mouseX = 0, mouseY = 0;

  function resizeCanvas() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  }
  resizeCanvas();
  window.addEventListener('resize', resizeCanvas);
  window.addEventListener('mousemove', e => { mouseX = e.clientX; mouseY = e.clientY; });

  function initStars() {
    stars = [];
    const count = Math.floor((canvas.width * canvas.height) / 6000);
    for (let i = 0; i < count; i++) {
      stars.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        r: Math.random() * 1.8 + 0.3,
        a: Math.random() * 0.8 + 0.2,
        speed: Math.random() * 0.015 + 0.003,
        driftX: (Math.random() - 0.5) * 0.3,
        driftY: (Math.random() - 0.5) * 0.3,
      });
    }
  }
  initStars();

  let shootingStars = [];
  function addShootingStar() {
    if (Math.random() > 0.005) return;
    shootingStars.push({
      x: Math.random() * canvas.width,
      y: 0,
      vx: -2 - Math.random() * 4,
      vy: 1 + Math.random() * 2,
      len: 40 + Math.random() * 60,
      life: 1,
    });
  }

  function drawStars() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    for (const s of stars) {
      s.x += s.driftX + (mouseX - canvas.width/2) * 0.00002 * s.speed * 5;
      s.y += s.driftY + (mouseY - canvas.height/2) * 0.00002 * s.speed * 5;
      if (s.x < -10) s.x = canvas.width + 10;
      if (s.x > canvas.width + 10) s.x = -10;
      if (s.y < -10) s.y = canvas.height + 10;
      if (s.y > canvas.height + 10) s.y = -10;

      const pulse = s.a * (0.7 + 0.3 * Math.sin(Date.now() * s.speed));
      ctx.beginPath();
      ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(220, 210, 255, ${pulse})`;
      ctx.fill();
    }

    // shooting stars
    for (let i = shootingStars.length - 1; i >= 0; i--) {
      const ss = shootingStars[i];
      ss.x += ss.vx;
      ss.y += ss.vy;
      ss.life -= 0.018;
      if (ss.life <= 0) { shootingStars.splice(i, 1); continue; }
      ctx.beginPath();
      ctx.moveTo(ss.x, ss.y);
      ctx.lineTo(ss.x - ss.vx * ss.len / 4, ss.y - ss.vy * ss.len / 4);
      const grad = ctx.createLinearGradient(ss.x, ss.y, ss.x - ss.vx * 20, ss.y - ss.vy * 20);
      grad.addColorStop(0, `rgba(255, 255, 255, ${ss.life})`);
      grad.addColorStop(1, `rgba(124, 92, 252, 0)`);
      ctx.strokeStyle = grad;
      ctx.lineWidth = 1.6;
      ctx.stroke();
    }

    addShootingStar();
    requestAnimationFrame(drawStars);
  }
  drawStars();

  // ═══ Questions ═══
  const questions = [
    // E/I
    { q: '周末的星舰休息日，你更愿意怎么度过？', dim: 'EI', a: '🌊', at: '去星际枢纽找朋友们狂欢', b: '🌙', bt: '在自己的舱室里看书观星', key: 'E' },
    { q: '面对一个陌生星域，你的第一反应是？', dim: 'EI', a: '🛸', at: '发信号召集探索队一起出发', b: '🔭', bt: '先自己研究星图再决定', key: 'E' },
    { q: '星际聚会上，你通常是哪种角色？', dim: 'EI', a: '🎙️', at: '穿梭在各星系间的社交蝴蝶', b: '🌌', bt: '待在最舒服的小圈子里深聊', key: 'E' },
    { q: '你的能量补给方式是？', dim: 'EI', a: '⚡', at: '在热闹的星际市集充电', b: '🔋', bt: '在私人星舰的安静角落恢复', key: 'E' },
    { q: '最喜欢的交流方式？', dim: 'EI', a: '📡', at: '全频道广播，和所有人对话', b: '📨', bt: '一对一深空通信', key: 'E' },
    // S/N
    { q: '欣赏星云时，你更关注什么？', dim: 'SN', a: '🎨', at: '它的颜色层次和具体形状', b: '💫', bt: '它背后蕴含的宇宙故事和隐喻', key: 'S' },
    { q: '你更擅长哪种星际任务？', dim: 'SN', a: '🔧', at: '维修星舰的具体部件', b: '🧠', bt: '设计全新的星际航行理论', key: 'S' },
    { q: '谈到未来星际殖民，你最关心？', dim: 'SN', a: '📋', at: '建设步骤、资源分配这些细节', b: '🚀', bt: '人类文明的无限可能性', key: 'S' },
    { q: '读星际日志时你更喜欢？', dim: 'SN', a: '📖', at: '真实探险家的航行记录', b: '🌠', bt: '充满想象力的星际科幻小说', key: 'S' },
    { q: '做决定时你更依赖？', dim: 'SN', a: '📊', at: '以往任务中的实际经验', b: '💡', bt: '说不清道不明的直觉预感', key: 'S' },
    // T/F
    { q: '队友因任务失误而沮丧，你会？', dim: 'TF', a: '🧮', at: '帮他分析失误原因和解决方案', b: '🤗', bt: '先安慰情绪，让他知道我在乎', key: 'T' },
    { q: '做重要星际决策时，你更看重？', dim: 'TF', a: '⚖️', at: '逻辑推演和原则底线', b: '💝', bt: '对人的影响和各方感受', key: 'T' },
    { q: '你更欣赏哪种星舰船长？', dim: 'TF', a: '🎯', at: '公正果断、对事不对人的', b: '🤝', bt: '善解人意、凝聚团队的', key: 'T' },
    { q: '星际议会辩论时你更在意？', dim: 'TF', a: '✅', at: '谁的观点更正确合理', b: '💔', bt: '辩论会不会伤害彼此关系', key: 'T' },
    { q: '评价一部星际电影时你更看重？', dim: 'TF', a: '🧩', at: '剧情逻辑和世界观自洽性', b: '🎭', bt: '它带给我的情感冲击', key: 'T' },
    // J/P
    { q: '你的星舰驾驶舱通常是？', dim: 'JP', a: '📐', at: '仪表盘井然有序，每样东西都在该在的位置', b: '🎨', bt: '乱中有序，只有你知道东西在哪儿', key: 'J' },
    { q: '星际旅行你更喜欢哪种方式？', dim: 'JP', a: '🗺️', at: '提前规划好每一站停靠点', b: '🌀', bt: '随兴致漂流向任何星域', key: 'J' },
    { q: '面对一个未标注星域的探索？', dim: 'JP', a: '📋', at: '先制定详细的探索计划', b: '🤸', bt: '跳进飞船就走，路上再说', key: 'J' },
    { q: '面对任务截止日期你？', dim: 'JP', a: '⏰', at: '提前完成，留足检查时间', b: '🔥', bt: '最后时刻灵感爆发冲刺完成', key: 'J' },
    { q: '你更享受哪种状态？', dim: 'JP', a: '🏛️', at: '一切安排妥当带来的确定感', b: '🎪', bt: '灵活应变、自由自在的不确定性', key: 'J' },
  ];

  // ═══ Type Data ═══
  const typeData = {
    'INTJ': { name: '星域建筑师', desc: '你是宇宙中最深邃的蓝图绘制者。你的大脑是一座永不熄灭的星图工坊——战略、系统、长远规划是你的母语。你不在乎是否被理解，因为你生来就是为了实现别人连想都不敢想的未来。你需要的不是掌声，是执行的力量。', traits: '• 独立深度思考者，擅长抽象战略\n• 对知识有近乎偏执的渴求\n• 高标准、高要求，包括对自己\n• 外表冷静，内心澎湃的变革者', quote: '"星辰不会问方向是否正确，它们只是燃烧。"' },
    'INTP': { name: '星际逻辑师', di: 'INTP', desc: '你是宇宙间最不倦的真理探索者。万物皆可解构，一切皆可质疑——你活在一个由逻辑和原理构建的多维宇宙中。你不追求答案，你追求更优雅的问题。别人看到的是故障，你看到的是一道迷人的思维谜题。', traits: '• 分析狂人，模式识别天赋异禀\n• 对感兴趣的事物极度专注\n• 擅长抽象推理和理论构建\n• 自由思考者，厌恶教条束缚', quote: '"宇宙的答案是42——但问题是，42是什么的答案？"' },
    'ENTJ': { name: '星系统帅', desc: '你是天生的指挥官，在混沌中看到秩序，在废墟中看到帝国。你的思维如超新星爆发般犀利——目标明确、行动果断、不容拖沓。你不需要征求许可来实现愿景，你只需要一个足够强大的战略。别人追随你，因为你能把不可能变成计划书。', traits: '• 天生的领导者，果断决策者\n• 高效执行力和战略远见\n• 直面冲突，推动变革\n• 追求成就和影响力', quote: '"银河不会自己征服——总要有人画出航图。"' },
    'ENTP': { name: '星际辩手', desc: '你是宇宙中最危险的智慧火花。没有你不敢挑战的假设，没有你不敢推翻的体系。你的思维如量子跳跃般不可预测——前一秒在讨论暗物质，下一秒就在构思如何用橡皮筋和重力井做一顿星际早餐。你最大的敌人？无聊。', traits: '• 思维敏捷，辩论冠军\n• 创新点子源源不断\n• 挑战权威，享受智力碰撞\n• 适应力极强，即兴发挥高手', quote: '"质疑一切——包括这句话。"' },
    'INFJ': { name: '星海先知', desc: '你是宇宙中最温柔的觉醒者。你拥有一双能看透灵魂的眼睛和一颗能感受整个星系脉动的心。你能感知到别人连自己都没意识到的情绪暗流。你来到这个星系不是为了随波逐流——你是来愈合、启迪、改变的。', traits: '• 深刻的直觉和洞察力\n• 强烈的理想主义和使命感\n• 善于倾听，深度共情\n• 追求意义和连接', quote: '"最亮的星，往往最孤独——但也最温柔。"' },
    'INFP': { name: '星梦诗人', desc: '你是散落在宇宙间的迷人秘密。你的内心世界比整个银河系还要宽广——那里有最绚烂的想象、最纯粹的理想和最深沉的情感。你活在可能性里，用理想主义的滤镜看世界。你无法改变宇宙的冷漠，但你可以为它写下诗篇。', traits: '• 丰富的内心世界和想象力\n• 坚定的核心价值观\n• 真诚、善良、包容\n• 追寻真实和自我表达', quote: '"在冰冷宇宙中，做自己才是最勇敢的航行。"' },
    'ENFJ': { name: '星团启迪者', desc: '你是宇宙的粘合剂，是星系间最温暖的光芒。你拥有一套内置的情感雷达——总能精准捕捉到每个人的需要和潜力。你不是在带领，你是在点亮。别人在你身边会不由自主地想要成为更好的自己。', traits: '• 天生的导师和激励者\n• 极强的人际感知力\n• 帮助他人成长的热情\n• 创造和谐的团队氛围', quote: '"照亮别人，不是燃烧自己——是让群星一起闪耀。"' },
    'ENFP': { name: '星云探险家', desc: '你是宇宙中最自由的风。你对世界的好奇心像一个永远填不满的黑洞——你热爱人、热爱想法、热爱一切可能性。你的热情有传染性，你可以在任何地方找到快乐和意义。你不是在寻找自己，你是在创造自己。', traits: '• 热情洋溢，感染力满分\n• 创造力爆棚，点子制造机\n• 深切关注人和情感\n• 追求自由和多样体验', quote: '"宇宙这么大，怎么舍得只活一种活法？"' },
    'ISTJ': { name: '星轨守护者', desc: '你是银河系的可靠锚点。当所有人在浮躁中迷失方向，你是那道稳定不变的航标。你的世界建立在秩序、责任和可信赖之上。你从不承诺你做不到的事，而你承诺的事——即便宇宙崩塌，你也会做到。', traits: '• 可靠稳重，言出必行\n• 注重细节和执行力\n• 传统和秩序感的守护者\n• 勤奋务实，默默付出', quote: '"秩序不是束缚——是自由的骨架。"' },
    'ISFJ': { name: '星尘守护者', desc: '你是宇宙中最静默而坚定的温暖。你记得每个人的喜好，注意到每处细微的变化，在最需要的时候递上最恰当的帮助。你从不追求聚光灯，但你存在的星系总是因为你的守护而更加安宁。', traits: '• 温柔体贴，善于照顾他人\n• 极强的责任心和奉献精神\n• 注重传统和安全感\n• 默默付出不求回报', quote: '"真正的光芒，不需要尖叫——它温暖就好。"' },
    'ESTJ': { name: '星区执行官', desc: '你是星系中最实际的掌舵者。规则、秩序、效率——这些不是枷锁，是你的工具箱。你清楚知道如何让一切运转起来，也毫不畏惧做出艰难的决定。你建立的结构让整个团队可以稳定运行。', traits: '• 天生的组织者和执行者\n• 务实高效，注重结果\n• 明确的是非观和责任感\n• 带领团队向前推进', quote: '"一个被执行的计划，胜过一百个完美的空想。"' },
    'ESFJ': { name: '星港管家', desc: '你是星际社区的心脏和灵魂。你有一种天赋——把陌生人变成朋友，把一群个体凝聚成一个真正的团队。你的温暖和责任感让周围的人感到被关怀和被重视。你不是在组织活动，你是在编织关系网络。', traits: '• 体贴入微，重视人际关系\n• 强烈的社群意识\n• 乐于奉献和帮助\n• 创造温暖和谐的氛围', quote: '"家不是飞船——家是你在乎的人所在的地方。"' },
    'ISTP': { name: '星舰工匠', desc: '你是危机中最冷静的存在。当警报声响起、系统崩溃、所有人都慌乱时，你已经开始动手解决问题了。你的双手能理解任何机器的语言，你的大脑只在乎一件事——什么方法最有效？', traits: '• 动手能力极强，实干家\n• 危机时刻的定海神针\n• 追求效率和最简方案\n• 独立自主，不喜束缚', quote: '"动手之前不需要理解——动手之后自然就理解了。"' },
    'ISFP': { name: '星尘艺术家', desc: '你是宇宙中最安静的美学灵魂。你用五种感官体验世界，把每一刻活成一幅画、一首诗。你的温柔和敏感不是弱点——那是你感受这个世界的超能力。你不必大声宣告你是谁，你的存在本身就是一种美。', traits: '• 独特而细腻的审美力\n• 温柔敏感，善解人意\n• 独立自由，忠于内心\n• 用行动而非言语表达', quote: '"美不需要被定义——它只需要被感受。"' },
    'ESTP': { name: '星际冒险家', desc: '你是活在当下的火花。行动是你的第一语言，风险是你的调味料。你不会坐在那儿计划——你已经跳进星舰出发了。你的魅力、胆量和临场反应让你在任何环境中都能脱颖而出。犹豫？那是别人的事。', traits: '• 行动派，胆大心细\n• 魅力四射，社交达人\n• 极强的临场应变能力\n• 享受冒险和刺激', quote: '"犹豫的人还在看星图——我已在下一个星系了。"' },
    'ESFP': { name: '星辉表演者', desc: '你是星系聚光灯下的明星。你不是在炫耀——你只是在做你自己，而你的自己恰好光芒万丈。你的热情如超新星般不可忽视，你让每一刻都变得值得纪念。生活不是彩排，而你每天都在上演最精彩的版本。', traits: '• 活力四射，快乐源泉\n• 天生的表演者和社交家\n• 热爱生活，享受当下\n• 用热情感染每一个人', quote: '"生命太短，当然要活得闪闪发光。"' }
  };

  // ═══ State ═══
  let currentQ = 0;
  let scores = { E: 0, I: 0, S: 0, N: 0, T: 0, F: 0, J: 0, P: 0 };
  const TOTAL = questions.length;

  document.getElementById('q-total').textContent = TOTAL;

  function startQuiz() {
    showScreen('quiz-screen');
    currentQ = 0;
    scores = { E: 0, I: 0, S: 0, N: 0, T: 0, F: 0, J: 0, P: 0 };
    showQuestion();
  }

  function showScreen(id) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    document.getElementById(id).classList.add('active');
  }

  function showQuestion() {
    const q = questions[currentQ];
    document.getElementById('q-num').textContent = currentQ + 1;
    document.getElementById('progress-fill').style.width = `${(currentQ / TOTAL) * 100}%`;

    const dimMap = { EI: 'E/I', SN: 'S/N', TF: 'T/F', JP: 'J/P' };
    document.getElementById('dim-tag').textContent = dimMap[q.dim];

    document.getElementById('question-text').textContent = q.q;

    const container = document.getElementById('options-container');
    container.innerHTML = `
      <button class="option-btn" onclick="answer('${q.key}')">
        <span class="option-icon">${q.a}</span>
        <span>${q.at}</span>
      </button>
      <button class="option-btn" onclick="answer('${q.key === 'E' ? 'I' : q.key === 'S' ? 'N' : q.key === 'T' ? 'F' : 'P'}')">
        <span class="option-icon">${q.b}</span>
        <span>${q.bt}</span>
      </button>
    `;

    // animate
    const card = document.getElementById('question-card');
    card.style.animation = 'none';
    requestAnimationFrame(() => {
      card.style.animation = 'cardIn 0.4s ease-out';
    });
  }

  function answer(chosen) {
    const q = questions[currentQ];
    let opposite;
    switch (q.dim) {
      case 'EI': opposite = q.key === 'E' ? 'I' : 'E'; break;
      case 'SN': opposite = q.key === 'S' ? 'N' : 'S'; break;
      case 'TF': opposite = q.key === 'T' ? 'F' : 'T'; break;
      case 'JP': opposite = q.key === 'J' ? 'P' : 'J'; break;
    }
    scores[chosen] = (scores[chosen] || 0) + 1;
    scores[opposite] = (scores[opposite] || 0);

    currentQ++;
    if (currentQ < TOTAL) {
      showQuestion();
    } else {
      showResult();
    }
  }

  function showResult(fromShare) {
    const ei = scores.E >= scores.I ? 'E' : 'I';
    const sn = scores.S >= scores.N ? 'S' : 'N';
    const tf = scores.T >= scores.F ? 'T' : 'F';
    const jp = scores.J >= scores.P ? 'J' : 'P';
    const type = ei + sn + tf + jp;
    const data = typeData[type] || typeData['ENFP'];

    document.getElementById('result-type').textContent = type;
    document.getElementById('result-name').textContent = data.name;
    document.getElementById('result-desc').textContent = data.desc;
    document.getElementById('result-traits').innerHTML = data.traits.replace(/\n/g, '<br>');
    document.getElementById('result-quote').textContent = data.quote;

    const badge = document.getElementById('result-badge');
    badge.innerHTML = `
      <span class="badge-item ei">${ei === 'E' ? '🌐 外向' : '🌙 内向'}</span>
      <span class="badge-item sn">${sn === 'S' ? '🔍 实感' : '💫 直觉'}</span>
      <span class="badge-item tf">${tf === 'T' ? '🧠 理性' : '💖 感性'}</span>
      <span class="badge-item jp">${jp === 'J' ? '📋 计划' : '🌀 随性'}</span>
    `;

    const dimScores = document.getElementById('dim-scores');
    const pairs = [
      { label: '外向 E / 内向 I', a: 'E', b: 'I', color: '#7c5cfc' },
      { label: '实感 S / 直觉 N', a: 'S', b: 'N', color: '#e04a8f' },
      { label: '理性 T / 感性 F', a: 'T', b: 'F', color: '#f5a623' },
      { label: '计划 J / 随性 P', a: 'J', b: 'P', color: '#4cc9a0' },
    ];
    dimScores.innerHTML = pairs.map(({ label, a, b, color }) => {
      const total = scores[a] + scores[b];
      const pctA = total > 0 ? Math.round((scores[a] / total) * 100) : 50;
      const pctB = total > 0 ? Math.round((scores[b] / total) * 100) : 50;
      const displayA = a === ei ? scores[a] + ' ✓' : scores[a];
      const displayB = b === jp ? scores[b] + ' ✓' : scores[b];
      const key = ei === a ? a : b;
      return `
        <div class="dim-score-card">
          <div class="dim-label">${label}</div>
          <div class="dim-value" style="color:${color}">${scores[a]} : ${scores[b]}</div>
          <div class="dim-bar">
            <div class="dim-bar-fill" style="width:${pctA}%;background:${color}"></div>
          </div>
        </div>
      `;
    }).join('');

    showScreen('result-screen');
    window.scrollTo({ top: 0, behavior: 'smooth' });

    // Update share URL with type
    updateShareURL(type);

    // Submit result to backend (silently) — skip for shared link views
    if (!fromShare) {
      submitResult(type, data.name);
    }
  }

  function updateShareURL(type) {
    const url = new URL(window.location.href);
    url.searchParams.set('type', type);
    window.history.replaceState({}, '', url);
  }

  // Submit result to backend silently
  function submitResult(type, name) {
    const scores = window.scores || {};
    fetch('https://mbti-steller-backend.vercel.app/api/submit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ type, name, scores })
    }).catch(() => { /* silent fail */ });
  }

  function shareResult() {
    const type = document.getElementById('result-type').textContent;
    const name = document.getElementById('result-name').textContent;
    const url = window.location.href.split('?')[0] + '?type=' + type;
    const text = `🌌 我测出了「${type} - ${name}」！\n你也来绘制你的星轨人格图谱吧 ✨\n${url}`;

    if (navigator.share && /iPhone|iPad|iPod|Android/i.test(navigator.userAgent)) {
      navigator.share({ title: '星轨人格测试', text, url }).catch(() => {});
    } else {
      navigator.clipboard.writeText(text).then(() => {
        const toast = document.getElementById('share-toast');
        toast.classList.add('show');
        setTimeout(() => toast.classList.remove('show'), 3000);
      }).catch(() => {
        // fallback
        const toast = document.getElementById('share-toast');
        toast.textContent = '✨ 复制失败，请手动复制上方链接';
        toast.classList.add('show');
        setTimeout(() => toast.classList.remove('show'), 4000);
      });
    }
  }

  function restartQuiz() {
    startQuiz();
  }

  // ═══ Handle URL type param (share result view) ═══
  (function handleSharedResult() {
    const params = new URLSearchParams(window.location.search);
    const sharedType = params.get('type');
    if (sharedType && typeData[sharedType]) {
      // Instead of showing result directly, show start screen but highlight the shared result
      // Actually let's just show the result directly when shared
      setTimeout(() => {
        scores = { E: 0, I: 0, S: 0, N: 0, T: 0, F: 0, J: 0, P: 0 };
        // Fake scores to match type
        if (sharedType[0] === 'E') scores.E = 5; else scores.I = 5;
        if (sharedType[1] === 'S') scores.S = 5; else scores.N = 5;
        if (sharedType[2] === 'T') scores.T = 5; else scores.F = 5;
        if (sharedType[3] === 'J') scores.J = 5; else scores.P = 5;
        showResult(true);
      }, 300);
    }
  })();
</script>
</body>
</html>

"""

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>星轨人格 · 数据面板</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: -apple-system, 'Noto Sans SC', sans-serif;
    background: #0a0a1a; color: #e8e6f0;
    min-height: 100vh; padding: 32px 20px;
  }
  .container { max-width: 1100px; margin: 0 auto; }
  h1 {
    font-size: 28px; font-weight: 700;
    background: linear-gradient(135deg, #7c5cfc, #e04a8f);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; margin-bottom: 6px;
  }
  .subtitle { color: rgba(255,255,255,0.4); font-size: 14px; margin-bottom: 32px; }

  .stat-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 32px; }
  .stat-card {
    background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px; padding: 24px; text-align: center;
  }
  .stat-card .num { font-size: 36px; font-weight: 900; color: #7c5cfc; }
  .stat-card .label { font-size: 13px; color: rgba(255,255,255,0.45); margin-top: 4px; }

  .chart-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 32px; }
  .chart-card {
    background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px; padding: 24px;
  }
  .chart-card h3 { font-size: 16px; color: var(--text, #e8e6f0); margin-bottom: 16px; }
  .chart-card canvas { max-height: 280px; }

  .type-rank { width: 100%; border-collapse: collapse; font-size: 14px; }
  .type-rank th { text-align: left; padding: 10px 12px; color: rgba(255,255,255,0.4); font-weight: 500; border-bottom: 1px solid rgba(255,255,255,0.06); }
  .type-rank td { padding: 10px 12px; border-bottom: 1px solid rgba(255,255,255,0.04); }
  .type-rank .bar { height: 6px; border-radius: 6px; background: linear-gradient(90deg, #7c5cfc, #e04a8f); }
  .type-badge {
    display: inline-block; padding: 2px 10px; border-radius: 10px;
    font-size: 12px; font-weight: 700; letter-spacing: 0.05em;
  }

  .recent-list { font-size: 13px; }
  .recent-list td { padding: 6px 12px; border-bottom: 1px solid rgba(255,255,255,0.03); }

  @media (max-width: 700px) { .chart-grid { grid-template-columns: 1fr; } }
</style>
</head>
<body>
<div class="container">
  <h1>🌌 星轨人格 · 数据面板</h1>
  <p class="subtitle">实时统计 · 所有测试结果汇总</p>

  <div class="stat-grid" id="statGrid"></div>

  <div class="chart-grid">
    <div class="chart-card"><h3>📊 类型分布</h3><canvas id="typeChart"></canvas></div>
    <div class="chart-card"><h3>📈 近7天趋势</h3><canvas id="trendChart"></canvas></div>
  </div>

  <div class="chart-grid">
    <div class="chart-card">
      <h3>🏆 类型排行榜</h3>
      <table class="type-rank" id="rankTable">
        <thead><tr><th>类型</th><th>名称</th><th>人数</th><th>占比</th><th></th></tr></thead>
        <tbody id="rankBody"></tbody>
      </table>
    </div>
    <div class="chart-card">
      <h3>🕐 最近测试</h3>
      <table class="type-rank recent-list">
        <thead><tr><th>类型</th><th>名称</th><th>时间</th></tr></thead>
        <tbody id="recentBody"></tbody>
      </table>
    </div>
  </div>
</div>

<script>
const COLORS = ['#7c5cfc','#e04a8f','#f5a623','#4cc9a0','#3b82f6','#a855f7','#ec4899','#14b8a6','#f97316','#6366f1','#8b5cf6','#06b6d4','#d946ef','#22c55e','#eab308','#f43f5e'];

fetch('/api/stats')
  .then(r => r.json())
  .then(d => {
    // Stats
    const latestCount = d.daily_trend.length > 0 ? d.daily_trend.reduce((a,b)=>a+b.count, 0) : 0;
    document.getElementById('statGrid').innerHTML = `
      <div class="stat-card"><div class="num">${d.total}</div><div class="label">总测试人数</div></div>
      <div class="stat-card"><div class="num">${d.type_distribution.length}</div><div class="label">出现的人格类型</div></div>
      <div class="stat-card"><div class="num">${d.total > 0 ? (d.type_distribution[0]?.pct || 0) + '%' : '-'}</div><div class="label">最热门类型占比</div></div>
      <div class="stat-card"><div class="num">${d.total > 0 ? d.dimensions.E + d.dimensions.I : 0}</div><div class="label">E/I 维度总票数</div></div>
    `;

    // Type chart
    const types = d.type_distribution.slice(0, 16);
    new Chart(document.getElementById('typeChart'), {
      type: 'bar',
      data: {
        labels: types.map(t => t.type),
        datasets: [{
          label: '人数',
          data: types.map(t => t.count),
          backgroundColor: types.map((_, i) => COLORS[i % COLORS.length] + '80'),
          borderColor: types.map((_, i) => COLORS[i % COLORS.length]),
          borderWidth: 1,
          borderRadius: 4,
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
          y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.04)' }, ticks: { color: 'rgba(255,255,255,0.4)' } },
          x: { grid: { display: false }, ticks: { color: 'rgba(255,255,255,0.6)', font: { weight: 'bold' } } }
        }
      }
    });

    // Trend chart
    const days = d.daily_trend.length > 0 ? d.daily_trend : [{date:'暂无数据', count:0}];
    new Chart(document.getElementById('trendChart'), {
      type: 'line',
      data: {
        labels: days.map(x => x.date.slice(5)),
        datasets: [{
          label: '每日测试数',
          data: days.map(x => x.count),
          borderColor: '#7c5cfc',
          backgroundColor: 'rgba(124,92,252,0.1)',
          fill: true,
          tension: 0.3,
          pointBackgroundColor: '#7c5cfc',
          pointRadius: 4,
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
          y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.04)' }, ticks: { color: 'rgba(255,255,255,0.4)' } },
          x: { grid: { display: false }, ticks: { color: 'rgba(255,255,255,0.4)' } }
        }
      }
    });

    // Rank table
    const maxCount = d.type_distribution.length > 0 ? d.type_distribution[0].count : 1;
    document.getElementById('rankBody').innerHTML = d.type_distribution.map((t, i) => `
      <tr>
        <td><span class="type-badge" style="background:${COLORS[i%COLORS.length]}22;color:${COLORS[i%COLORS.length]}">${t.type}</span></td>
        <td>${t.name}</td>
        <td><strong>${t.count}</strong></td>
        <td>${t.pct}%</td>
        <td style="width:120px"><div class="bar" style="width:${(t.count/maxCount)*100}%"></div></td>
      </tr>
    `).join('');

    // Recent
    document.getElementById('recentBody').innerHTML = d.recent.map(r => `
      <tr>
        <td><span class="type-badge" style="background:rgba(124,92,252,0.15);color:#7c5cfc">${r.type}</span></td>
        <td>${r.name}</td>
        <td style="color:rgba(255,255,255,0.35)">${r.created_at?.slice(5,16) || '-'}</td>
      </tr>
    `).join('');
  });
</script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def index(): return INDEX_HTML

@app.get("/health")
async def health(): return {"status": "ok"}

@app.post("/api/submit")
async def submit(request: Request):
    try: body = await request.json()
    except: raise HTTPException(400, "Invalid JSON")
    t = body.get("type", "").upper()
    if t not in TYPE_DATA: raise HTTPException(400, f"Invalid type: {t}")
    ip = hashlib.md5((request.client.host or "").encode()).hexdigest()[:8]
    rec = {"id": uuid.uuid4().hex[:12], "type": t, "name": body.get("name",""),
           "scores": body.get("scores",{}), "ip": ip,
           "ua": request.headers.get("user-agent",""),
           "ts": datetime.now(timezone.utc).isoformat()}
    data = _load()
    data.setdefault("results", []).append(rec)
    _save(data)
    return {"id": rec["id"], "type": t}

@app.post("/api/pageview")
async def pageview(request: Request):
    data = _load()
    ip = hashlib.md5((request.client.host or "").encode()).hexdigest()[:8]
    data.setdefault("pageviews", []).append({"t": datetime.now(timezone.utc).isoformat(), "ip": ip})
    _save(data)
    return {"ok": True}

@app.get("/api/stats")
async def stats():
    data = _load()
    results = data.get("results", [])
    pvs = data.get("pageviews", [])
    total = len(results)
    type_dist = []
    if total > 0:
        for t, cnt in Counter(r["type"] for r in results).most_common():
            type_dist.append({"type": t, "name": TYPE_DATA.get(t,""), "count": cnt, "pct": round(cnt/total*100,1)})
    today = datetime.now(timezone.utc).date().isoformat()
    daily = []
    for i in range(6, -1, -1):
        d = (datetime.now(timezone.utc).date() - timedelta(days=i)).isoformat()
        cnt = sum(1 for r in results if r.get("ts","").startswith(d))
        daily.append({"date": d, "count": cnt})
    dims = {"E":0,"I":0,"S":0,"N":0,"T":0,"F":0,"J":0,"P":0}
    for r in results:
        t = r.get("type","")
        if len(t)==4:
            for c in t: dims[c] = dims.get(c,0)+1
    recent = sorted(results, key=lambda x: x.get("ts",""), reverse=True)[:20]
    return {"total": total, "pageviews": len(pvs),
            "pageview_today": sum(1 for p in pvs if p.get("t","").startswith(today)),
            "type_distribution": type_dist, "daily_trend": daily,
            "dimensions": dims,
            "recent": [{"type":r["type"],"name":r.get("name",""),"created_at":r.get("ts","")} for r in recent]}

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(): return DASHBOARD_HTML

@app.post("/api/clear")
async def clear(): _save({"results":[],"pageviews":[]}); return {"ok": True}