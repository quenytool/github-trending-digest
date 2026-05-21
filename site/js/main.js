/**
 * GH Trend Digest — Frontend Logic
 * Loads post index and renders blog posts from static JSON.
 */
(function() {
  "use strict";

  var POSTS_DIR = "posts";
  var INDEX_URL = POSTS_DIR + "/index.json";

  // ── DOM refs ──────────────────────────────────────────────
  var $postList   = document.getElementById("post-list");
  var $postDetail = document.getElementById("post-detail");
  var $loading    = document.getElementById("loading");
  var $empty      = document.getElementById("empty-state");
  var $error      = document.getElementById("error-state");
  var $errorMsg   = document.getElementById("error-msg");
  var $postCount  = document.getElementById("post-count");
  var $heroStats  = document.getElementById("hero-stats");

  var posts = [];

  // ── Init (run immediately, DOM is ready since script is at end of body) ──
  init();

  function init() {
    fetch(INDEX_URL)
      .then(function(resp) {
        if (!resp.ok) {
          if (resp.status === 404) { showEmpty(); return; }
          throw new Error("HTTP " + resp.status);
        }
        return resp.json();
      })
      .then(function(data) {
        if (!data || !data.length) { showEmpty(); return; }
        posts = data;
        renderList();
        updateStats();
      })
      .catch(function(e) {
        showError(e.message || "Network error");
      });
  }

  // ── States ────────────────────────────────────────────────
  function showEmpty() {
    $loading.classList.add("hidden");
    $empty.classList.remove("hidden");
  }

  function showError(msg) {
    $loading.classList.add("hidden");
    $error.classList.remove("hidden");
    $errorMsg.textContent = msg || "无法加载文章列表，请稍后再试。";
  }

  // ── Stats ─────────────────────────────────────────────────
  function updateStats() {
    var total = posts.length;
    var totalRepos = 0;
    var topStars = "";
    posts.forEach(function(p) {
      totalRepos += p.count || 0;
      if (p.top_stars && (!topStars || parseInt(p.top_stars) > parseInt(topStars))) {
        topStars = p.top_stars;
      }
    });
    $postCount.textContent = total + " 篇";
    $heroStats.innerHTML =
      '<div class="stat"><span class="stat-num">' + total + '</span><span class="stat-label">已收录</span></div>' +
      '<div class="stat"><span class="stat-num">' + totalRepos + '</span><span class="stat-label">热门项目</span></div>' +
      '<div class="stat"><span class="stat-num">' + (topStars || "—") + '</span><span class="stat-label">最高日星</span></div>';
  }

  // ── Render list ───────────────────────────────────────────
  function renderList() {
    $loading.classList.add("hidden");
    $postList.innerHTML = "";

    posts.forEach(function(post, i) {
      var card = document.createElement("div");
      card.className = "post-card fade-in";
      card.style.animationDelay = (i * 40) + "ms";
      card.addEventListener("click", function() { loadPost(post.date); });

      var dateStr = formatDate(post.date);
      var topRepoShort = post.top_repo ? post.top_repo.split("/").pop() : "";

      card.innerHTML =
        '<div class="post-card-left">' +
          '<span class="post-card-date">' + dateStr + '</span>' +
          '<span class="post-card-meta"><span>📦 ' + (post.count || 0) + ' 个项目</span></span>' +
        '</div>' +
        '<div class="post-card-right">' +
          '<span class="post-card-repo">' + (topRepoShort || "—") + '</span>' +
          '<span class="post-card-stars">' + (post.top_stars || "") + '</span>' +
        '</div>';

      $postList.appendChild(card);
    });
  }

  // ── Load post ─────────────────────────────────────────────
  function loadPost(date) {
    $postList.style.display = "none";
    $postDetail.classList.remove("hidden");
    $postDetail.innerHTML =
      '<div class="loading"><div class="loading-spinner"></div><p>加载中...</p></div>';

    fetch(POSTS_DIR + "/" + date + ".json")
      .then(function(resp) {
        if (!resp.ok) throw new Error("HTTP " + resp.status);
        return resp.json();
      })
      .then(function(data) {
        // Use marked.parse() if available, otherwise fall back to plain text
        var html;
        if (typeof marked !== "undefined" && marked.parse) {
          html = marked.parse(data.blog_md);
        } else {
          html = "<pre>" + escapeHtml(data.blog_md) + "</pre>";
        }
        var dateDisplay = formatDate(date);

        $postDetail.innerHTML =
          '<div class="detail-header">' +
            '<button class="btn-back" onclick="window._goBack()">← 返回列表</button>' +
            '<div class="detail-date">📅 ' + dateDisplay + '</div>' +
          '</div>' +
          '<div class="detail-content fade-in">' + html + '</div>';

        window.scrollTo({ top: 0, behavior: "smooth" });
      })
      .catch(function(e) {
        $postDetail.innerHTML =
          '<div class="error-state">' +
            '<div class="empty-icon">⚠️</div>' +
            '<h2>加载失败</h2>' +
            '<p>无法加载 ' + date + ' 的文章：' + (e.message || "") + '</p>' +
            '<button class="btn-back" onclick="window._goBack()" style="margin-top:16px">← 返回列表</button>' +
          '</div>';
      });
  }

  // ── Go back ───────────────────────────────────────────────
  function goBack() {
    $postDetail.classList.add("hidden");
    $postDetail.innerHTML = "";
    $postList.style.display = "";
    window.scrollTo({ top: 0, behavior: "smooth" });
  }
  window._goBack = goBack;

  // ── Helpers ───────────────────────────────────────────────
  function formatDate(dateStr) {
    var d = new Date(dateStr + "T00:00:00Z");
    var weekdays = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"];
    var y = d.getFullYear();
    var m = String(d.getMonth() + 1).padStart(2, "0");
    var day = String(d.getDate()).padStart(2, "0");
    var wd = weekdays[d.getDay()];
    return y + "年" + m + "月" + day + "日 " + wd;
  }

  function escapeHtml(text) {
    return text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  // ── Keyboard nav ──────────────────────────────────────────
  document.addEventListener("keydown", function(e) {
    if (e.key === "Escape" && !$postDetail.classList.contains("hidden")) {
      goBack();
    }
  });

})();
