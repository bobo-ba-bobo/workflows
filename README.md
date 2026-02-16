# Discord Automation Bots

GitHub Actions로 자동 실행되는 Discord 봇 모음

## 🤖 Bots

### 1. Tech News Bot (`tech-news-discord.py`)
RSS 피드에서 테크 뉴스를 가져와 Discord에 자동 포스팅

**뉴스 소스:**
- 🔥 Hacker News (300+ 포인트)
- 📰 TechCrunch
- 🚀 Product Hunt

**실행 주기:** 매시간
**GitHub Secrets:** `DISCORD_WEBHOOK_URL`

---

### 2. Podcasts Bot (`podcasts-discord.py`)
팟캐스트 새 에피소드를 감지하고 Claude API로 요약 생성

**팟캐스트:**
- 🎙️ Lenny's Podcast
- 💰 20VC by Harry Stebbings
- 🚀 a16z Podcast
- 📈 Acquired

**실행 주기:** 매일 1회 (9 AM UTC / 6 PM KST)
**GitHub Secrets:**
- `PODCAST_DISCORD_WEBHOOK_URL`
- `CLAUDE_API_KEY`

**특징:**
- AI 요약 생성 (한국어 bullet points)
- 이미 본 에피소드 추적 (`seen_episodes.json`)
- 자동 커밋 & 푸시로 상태 저장

---

## ⚙️ 설정 방법

### GitHub Secrets 추가
1. Repository Settings → Secrets and variables → Actions
2. New repository secret 클릭
3. 다음 secrets 추가:
   - `DISCORD_WEBHOOK_URL` - Tech news 채널 webhook
   - `PODCAST_DISCORD_WEBHOOK_URL` - Podcasts 채널 webhook
   - `CLAUDE_API_KEY` - Anthropic Claude API key

### 로컬 테스트

**Tech News Bot:**
```bash
pip install feedparser requests
DISCORD_WEBHOOK_URL='your-webhook-url' python3 tech-news-discord.py
```

**Podcasts Bot:**
```bash
pip install feedparser requests anthropic
DISCORD_WEBHOOK_URL='your-webhook-url' CLAUDE_API_KEY='your-api-key' python3 podcasts-discord.py
```

---

## 📁 파일 구조
```
.
├── tech-news-discord.py          # Tech news RSS bot
├── podcasts-discord.py            # Podcast summary bot
├── seen_episodes.json             # Podcast tracking (auto-updated)
├── .github/workflows/
│   ├── rss-bot.yml                # Tech news workflow (hourly)
│   └── podcast-bot.yml            # Podcast workflow (daily)
└── README.md
```

## 라이센스
MIT
