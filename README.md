# Tech News Discord Bot

RSS 피드를 가져와서 Discord에 자동으로 포스팅하는 봇입니다.

## 뉴스 소스
- 🔥 **Hacker News** (300+ 포인트)
- 📰 **TechCrunch**
- 🚀 **Product Hunt**

## 작동 방식
- GitHub Actions로 매시간 자동 실행
- 최근 2시간 이내 글만 필터링
- Discord Webhook으로 전송

## 설정 방법

1. Discord Webhook URL 생성
2. GitHub Repository Settings → Secrets → New secret
   - Name: `DISCORD_WEBHOOK_URL`
   - Value: 당신의 webhook URL

3. GitHub Actions가 자동으로 매시간 실행됩니다

## 로컬 테스트

```bash
pip install feedparser requests
DISCORD_WEBHOOK_URL='your-webhook-url' python3 rss_discord.py
```

## 라이센스
MIT
