/**
 * GH Trend Digest — Frontend Logic
 * Loads post index and renders blog posts from static JSON.
 */

const POSTS_DIR = "posts";
const INDEX_URL = `${POSTS_DIR}/index.json`;

// ── DOM refs ──────────────────────────────────────────────────
const $postList   = document.getElementById("post-list");
const $postDetail = document.getElementById("post-detail");
const $loading    = document.getElementById("loading");
const $empty      = document.getElementById("empty-state");
const $error      = document.getElementById("error-state");
const $errorMsg   = document.getElementById("error-msg");
const $postCount  = document.getElementById("post-count");
const $heroStats  = document.getElementById("hero-stats");

// ── State ─────────────────────────────────────────────────────
let posts = [];

// ── Init ──────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", init);

async function init() {
  try {
    const resp = await fetch(INDEX_URL);
    if (!resp.ok) {
      if (resp.status === 404) {
        showEmpty();
        return;
      }
      throw new Error(`HTTP ${resp.status}`);
    }
    posts = await resp.json();
    if (!posts.length) {
      showEmpty();
      return;
    }
    renderList();
    updateStats();
  } catch (e) {
    showError(e.message);
  }
}

// ── Show states ───────────────────────────────────────────────
function showEmpty() {
  $loading.classList.add("hidden");
  $empty.classList.remove("hidden");
}

function showError(msg) {
  $loading.classList.add("hidden");
  $error.classList.remove("hidden");
  $errorMsg.textContent = msg || "无法加载文章列表，请稍后再试。";
}

// ── Stats ─────────────────────────────────────────────────────
function updateStats() {
  const total = posts.length;
  let totalRepos = 0;
  let topStars = "";
  posts.forEach(p => {
    totalRepos += p.count || 0;
    if (p.top_stars && (!topStars || parseInt(p.top_stars) > parseInt(topStars))) {
      topStars = p.top_stars;
    }
  });

  $postCount.textContent = `${total} 篇`;

  $heroStats.innerHTML = `
    <div class="stat"><span class="stat-num">${total}</span><span class="stat-label">已收录</span></div>
    <div class="stat"><span class="stat-num">${totalRepos}</span><span class="stat-label">热门项目</span></div>
    <div class="stat"><span class="stat-num">${topStars || "—"}</span><span class="stat-label">最高日星</span></div>
  `;
}

// ── Render list ───────────────────────────────────────────────
function renderList() {
  $loading.classList.add("hidden");
  $postList.innerHTML = "";

  posts.forEach((post, i) => {
    const card = document.createElement("div");
    card.className = "post-card fade-in";
    card.style.animationDelay = `${i * 40}ms`;
    card.addEventListener("click", () => loadPost(post.date));

    const dateStr = formatDate(post.date);
    const topRepoShort = post.top_repo
      ? post.top_repo.split("/").pop()
      : "";

    card.innerHTML = `
      <div class="post-card-left">
        <span class="post-card-date">${dateStr}</span>
        <span class="post-card-meta">
          <span>📦 ${post.count || 0} 个项目</span>
        </span>
      </div>
      <div class="post-card-right">
        <span class="post-card-repo">${topRepoShort || "—"}</span>
        <span class="post-card-stars">${post.top_stars || ""}</span>
      </div>
    `;

    $postList.appendChild(card);
  });
}

// ── Load post ─────────────────────────────────────────────────
async function loadPost(date) {
  $postList.style.display = "none";
  $postDetail.classList.remove("hidden");
  $postDetail.innerHTML = `
    <div class="loading">
      <div class="loading-spinner"></div>
      <p>加载中...</p>
    </div>
  `;

  try {
    const resp = await fetch(`${POSTS_DIR}/${date}.json`);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const data = await resp.json();

    const html = marked.parse(data.blog_md);
    const dateDisplay = formatDate(date);

    $postDetail.innerHTML = `
      <div class="detail-header">
        <button class="btn-back" onclick="goBack()">
          ← 返回列表
        </button>
        <div class="detail-date">📅 ${dateDisplay}</div>
      </div>
      <div class="detail-content fade-in">
        ${html}
      </div>
    `;

    window.scrollTo({ top: 0, behavior: "smooth" });
  } catch (e) {
    $postDetail.innerHTML = `
      <div class="error-state">
        <div class="empty-icon">⚠️</div>
        <h2>加载失败</h2>
        <p>无法加载 ${date} 的文章：${e.message}</p>
        <button class="btn-back" onclick="goBack()" style="margin-top:16px">← 返回列表</button>
      </div>
    `;
  }
}

// ── Go back ───────────────────────────────────────────────────
function goBack() {
  $postDetail.classList.add("hidden");
  $postDetail.innerHTML = "";
  $postList.style.display = "";
  window.scrollTo({ top: 0, behavior: "smooth" });
}

// ── Helpers ───────────────────────────────────────────────────
function formatDate(dateStr) {
  const d = new Date(dateStr + "T00:00:00Z");
  const weekdays = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"];
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  const wd = weekdays[d.getDay()];
  return `${y}年${m}月${day}日 ${wd}`;
}

// ── Keyboard nav ──────────────────────────────────────────────
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    if (!$postDetail.classList.contains("hidden")) {
      goBack();
    }
  }
});
