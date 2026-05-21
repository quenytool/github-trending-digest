#!/usr/bin/env python3
"""
GitHub Trending scraper + humorous blog post generator.
No external LLM required — uses templates with humor injection.
"""
import json
import os
import re
import random
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# ── config ───────────────────────────────────────────────────────
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "site" / "posts"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
TRENDING_URL = "https://github.com/trending"

# ── humor templates ──────────────────────────────────────────────

TITLE_TEMPLATES = [
    "🚀 今日 GitHub 热搜：{top_repo} 霸榜，开发者集体失眠",
    "🔥 GitHub 日报 {date}：今天的代码，明天的 bug",
    "📡 GitHub 雷达 {date}：{top_repo} 带着 {stars} 颗星杀过来了",
    "🍿 程序员今日吃瓜：{top_repo} 爆火，{language} 又双叒叕赢了",
    "🌍 GitHub 今日战报：谁在提交代码，谁在制造 issue",
    "🐼 GitHub 趋势速递 {date}：{count} 个项目今天值得你 star",
    "⚡️ GitHub 热搜榜 {date}：{top_repo} 让 {stars} 个开发者点了收藏",
    "🤖 AI 日报不能写？没事，GitHub 日报照常营业 | {date}",
]

INTROS = [
    "早上好，各位键盘侠。今天的 GitHub Trending 告诉我们：世界各地的开发者们依然在不睡觉地写代码。以下是今日战况 ⬇️",
    "又到了一天一度的「看看别人在卷什么」环节。准备好你的 star 键，Let's go 🚀",
    "每天打开 GitHub Trending 的瞬间，就像拆盲盒——你不知道会看到一个改变世界的项目，还是又一个「用 Rust 重写一切」的尝试。今日拆盒结果如下：",
    "众所周知，GitHub Trending 是程序员界的「今日头条」。今日头条播报开始 📢",
    "起床上班第一件事：打开电脑。第二件事：打开 GitHub Trending 看看又有多少大牛做出了你一年前的 TODO 项目 😭",
    "今日 GitHub 浓度检测完毕。以下是高浓度项目报告 ☕️",
    "警告：以下内容可能导致大量 star 行为、clone 冲动以及「我也能做」的幻觉。请谨慎阅读 ⚠️",
    "各位摸鱼选手请注意，今日 GitHub Trending 已更新。老板不在的时候看看正好 👀",
]

OUTROS = [
    "以上就是今天的 GitHub 热搜。去 star 吧，反正你的 repo 列表已经 3000+ 了，不在乎多几个。",
    "今天的播报就到这里。记得多喝水，少熬夜，代码跑得过初一跑不过十五。明天见 👋",
    "如果你觉得这些项目不够有趣，不妨自己造一个——然后你就会发现，GitHub Trending 上的项目背后都是无数个不眠之夜。🌙",
    "散会！今天又有 N 个新项目加入了你的「迟早会看」收藏夹。我懂的。",
    "下课！去给这些项目贡献 PR 吧——或者至少把 star 点了，给开发者一点心理安慰。",
]

REPO_JOKES = [
    lambda r: f"**{r['name']}** — {r['desc'][:80]}...  {r.get('stars_today', '?')} 人今天被这个项目征服。它的存在证明了：好代码不需要 README 写三页。",
    lambda r: f"**{r['name']}** 今天拿了 {r.get('stars_today', '?')} 颗星星，比某些人一辈子拿的赞还多 ⭐",
    lambda r: f"**{r['name']}** — {r.get('lang', 'Unknown')} 写的，当然好（不是）。{r['desc'][:60]}...  {r.get('stars_today', '?')} 人表示「先 star 为敬」。",
    lambda r: f"**{r['name']}** — 如果你还没 star，那你可能错过了今天的船票。{r.get('stars_today', '?')} 人已经上船了。",
    lambda r: f"**{r['name']}** — {r['desc'][:70]}... 翻译成人话就是：又一个「简单、快速、强大」的东西，而且这次可能是真的。",
    lambda r: f"**{r['name']}** — 用 {r.get('lang', '某种神秘语言')} 写就。今天获得了 {r.get('stars_today', '?')} 颗星，证明 {r.get('lang', '它')} 还活着且活得挺好。",
    lambda r: f"**{r['name']}** — {r['desc'][:60]}...  听起来像个周末项目，但它已经有 {r.get('total_stars', '?')} 总星了。周末项目，认真的吗？",
]

LANG_OBSERVATIONS = {
    "Rust": [
        "Rust 项目又上榜了。我就问一句：你们到底写了多少遍「用 Rust 重写」？ 🦀",
        "Rust 选手今天依然活跃。他们的信念是：能用 lifetime 解决的问题，绝不用 GC。",
    ],
    "Python": [
        "Python 再次上榜。简单、优雅，唯一的问题是缩进错了会爆炸 🐍",
        "Python 选手：pip install 一下，问题解决了一半。另一半是版本冲突。",
    ],
    "TypeScript": [
        "TypeScript 项目上榜。类型安全的快乐，只有写过 any 的人才能体会。",
        "TypeScript 又来了。记住：any 是毒药，never 是解药。",
    ],
    "JavaScript": [
        "JavaScript 项目今天也上榜了。`npm install` 之后你的 node_modules 又多了 800 个依赖。",
    ],
    "Go": [
        "Go 语言项目上榜。简洁、并发、没有泛型——等等，现在有了。",
    ],
    "C++": [
        "C++ 项目今天上榜。Segfault 是每个 C++ 程序员的成人礼。",
    ],
    "C": [
        "C 语言：50 年了，依然是操作系统和嵌入式的不二之选。致敬。",
    ],
}

# ── scraping ─────────────────────────────────────────────────────

def fetch_trending(proxies=None):
    """Fetch and parse GitHub Trending page."""
    r = requests.get(TRENDING_URL, headers=HEADERS, proxies=proxies, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    
    repos = []
    for article in soup.find_all("article", class_="Box-row"):
        repo = {}
        
        # Name + owner
        h2 = article.find("h2", class_="h3")
        if h2 and h2.find("a"):
            href = h2.find("a").get("href", "")
            repo["name"] = href.strip("/")
            repo["url"] = f"https://github.com{href}"
        
        # Description
        desc = article.find("p", class_="col-9")
        repo["desc"] = desc.text.strip() if desc else ""
        
        # Language
        lang = article.find("span", itemprop="programmingLanguage")
        repo["lang"] = lang.text.strip() if lang else "Unknown"
        
        # Stars today
        for span in article.find_all("span"):
            txt = span.text.strip()
            if "stars today" in txt:
                repo["stars_today"] = txt
        
        # Total stars + forks from links
        for a in article.find_all("a", class_="Link"):
            txt = a.text.strip()
            href = a.get("href", "")
            if "/stargazers" in href and txt:
                repo["total_stars"] = txt
            elif "/forks" in href and txt:
                repo["forks"] = txt
        
        repos.append(repo)
    
    return repos


# ── blog generation ──────────────────────────────────────────────

def generate_blog(repos, date_str):
    """Generate a humorous markdown blog post from trending repos."""
    lines = []
    
    top = repos[0] if repos else {"name": "某个神秘项目", "stars_today": "?"}
    top_name = top["name"].split("/")[-1] if "/" in top["name"] else top["name"]
    
    # Title
    title_tmpl = random.choice(TITLE_TEMPLATES)
    title = title_tmpl.format(
        top_repo=top_name,
        date=date_str,
        stars=top.get("stars_today", "?"),
        language=top.get("lang", "Unknown"),
        count=len(repos),
    )
    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"> 📅 {date_str}  |  🔍 共收录 {len(repos)} 个热门项目")
    lines.append("")
    
    # Intro
    lines.append(random.choice(INTROS))
    lines.append("")
    
    # Stats overview
    lines.append("---")
    lines.append("")
    lines.append("## 📊 今日统计")
    lines.append("")
    
    langs = {}
    for r in repos:
        l = r.get("lang", "Unknown")
        langs[l] = langs.get(l, 0) + 1
    
    top_langs = sorted(langs.items(), key=lambda x: x[1], reverse=True)[:5]
    lang_line = " | ".join(f"**{l}**: {c}" for l, c in top_langs)
    lines.append(f"主力语言：{lang_line}")
    
    # Language observation
    if top_langs:
        top_lang = top_langs[0][0]
        if top_lang in LANG_OBSERVATIONS:
            lines.append("")
            lines.append(f"> {random.choice(LANG_OBSERVATIONS[top_lang])}")
    
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Repo list
    lines.append("## 🔥 热门项目 Top 10")
    lines.append("")
    
    for i, repo in enumerate(repos[:10]):
        lines.append(f"### {i+1}. {repo['name']}")
        lines.append("")
        lines.append(random.choice(REPO_JOKES)(repo))
        lines.append("")
        
        # Stats row
        stats_parts = []
        if "stars_today" in repo:
            stats_parts.append(f"⭐ {repo['stars_today']}")
        if "total_stars" in repo:
            stats_parts.append(f"📦 总星 {repo['total_stars']}")
        if "forks" in repo:
            stats_parts.append(f"🍴 {repo['forks']}")
        if "lang" in repo:
            stats_parts.append(f"💻 {repo['lang']}")
        
        lines.append(" | ".join(stats_parts))
        lines.append(f"[🔗 查看项目]({repo['url']})")
        lines.append("")
    
    # Honorable mentions
    if len(repos) > 10:
        lines.append("---")
        lines.append("")
        lines.append("## 🫡 荣誉提名")
        lines.append("")
        for repo in repos[10:15]:
            name_short = repo["name"].split("/")[-1] if "/" in repo["name"] else repo["name"]
            lines.append(f"- **{repo['name']}** — {repo['desc'][:80]}{'...' if len(repo['desc']) > 80 else ''}  ⭐ {repo.get('stars_today', '?')}")
        lines.append("")
    
    # Outro
    lines.append("---")
    lines.append("")
    lines.append(random.choice(OUTROS))
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*🤖 本文由自动化脚本生成。幽默感如有冒犯，纯属巧合。数据来源：github.com/trending*")
    
    return "\n".join(lines)


# ── main ─────────────────────────────────────────────────────────

def main():
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")
    
    # Proxy support
    proxies = None
    http_proxy = os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy")
    https_proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    if http_proxy or https_proxy:
        proxies = {"http": http_proxy, "https": https_proxy}
    
    print(f"🔍 Fetching GitHub Trending for {date_str}...")
    repos = fetch_trending(proxies=proxies)
    print(f"✅ Found {len(repos)} trending repos")
    
    # Generate blog
    blog = generate_blog(repos, date_str)
    
    # Save as JSON (raw data + rendered blog)
    output = {
        "date": date_str,
        "repos": repos,
        "blog_md": blog,
        "generated_at": now.isoformat(),
    }
    
    # Save daily file
    filepath = OUTPUT_DIR / f"{date_str}.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    # Update index
    update_index()
    
    print(f"📝 Saved to {filepath}")
    
    # Print first few lines of blog as preview
    print("\n" + "=" * 60)
    print("📰 BLOG PREVIEW:")
    print("=" * 60)
    for line in blog.split("\n")[:15]:
        print(line)


def update_index():
    """Update posts index JSON for the frontend."""
    index_path = OUTPUT_DIR / "index.json"
    posts = []
    
    for f in sorted(OUTPUT_DIR.glob("????-??-??.json")):
        try:
            with open(f, "r") as fp:
                data = json.load(fp)
            posts.append({
                "date": data["date"],
                "count": len(data.get("repos", [])),
                "top_repo": data["repos"][0]["name"] if data.get("repos") else None,
                "top_stars": data["repos"][0].get("stars_today", "") if data.get("repos") else "",
            })
        except (json.JSONDecodeError, KeyError, IndexError):
            continue
    
    with open(index_path, "w") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)
    
    print(f"📋 Updated index: {len(posts)} posts")


if __name__ == "__main__":
    main()
