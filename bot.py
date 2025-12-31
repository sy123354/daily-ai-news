import os
import feedparser
import google.generativeai as genai
import requests
import json
from datetime import datetime, timedelta

# --- 配置区域 ---
# 你可以在这里修改你想看的 RSS 源
RSS_URLS = [
    "https://techcrunch.com/category/artificial-intelligence/feed/", # TechCrunch AI
    "https://openai.com/blog/rss.xml", # OpenAI Blog
    "https://www.theverge.com/rss/artificial-intelligence/index.xml", # The Verge AI
]

# 初始化配置
if "GEMINI_API_KEY" not in os.environ:
    raise ValueError("缺少 GEMINI_API_KEY，请在 Secrets 中配置")
if "LARK_WEBHOOK" not in os.environ:
    raise ValueError("缺少 LARK_WEBHOOK，请在 Secrets 中配置")

genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

def get_ai_summary(title, content):
    """调用 Gemini 总结新闻"""
    prompt = f"""
    你是一个科技新闻分析师。请阅读以下新闻标题和摘要，用中文写出一句简短、吸引人的核心看点总结（50字以内）。
    新闻标题: {title}
    新闻摘要: {content}
    总结:
    """
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception:
        return "（内容过长或无法读取，建议点击原文查看）"

def send_lark_message(cards):
    """发送飞书卡片"""
    url = os.environ["LARK_WEBHOOK"]
    headers = {"Content-Type": "application/json"}
    payload = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "template": "blue",
                "title": {"content": "🤖 AI 每日情报 (自动推送)", "tag": "plain_text"}
            },
            "elements": cards
        }
    }
    requests.post(url, headers=headers, data=json.dumps(payload))

def main():
    print("🚀 任务启动...")
    cards = []
    # 只抓取最近 24 小时的新闻
    time_limit = datetime.now() - timedelta(hours=24) 

    has_news = False

    for url in RSS_URLS:
        print(f"正在读取: {url}")
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:3]: # 每个源只取最新3条
                # 这里简化处理，直接抓取最新的
                title = entry.title
                link = entry.link
                summary = entry.get('summary', entry.get('description', ''))[:1000]

                # AI 总结
                ai_text = get_ai_summary(title, summary)

                # 组装卡片
                cards.append({
                    "tag": "div",
                    "text": {"content": f"**📌 {title}**\n{ai_text}", "tag": "lark_md"}
                })
                cards.append({
                    "tag": "action",
                    "actions": [{
                        "tag": "button",
                        "text": {"content": "🔗 阅读原文", "tag": "plain_text"},
                        "url": link,
                        "type": "default"
                    }]
                })
                cards.append({"tag": "hr"})
                has_news = True
        except Exception as e:
            print(f"抓取错误 {url}: {e}")

    if has_news:
        cards.append({
            "tag": "note",
            "elements": [{"content": f"更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Powered by Gemini", "tag": "plain_text"}]
        })
        send_lark_message(cards)
        print("✅ 消息已发送到飞书")
    else:
        print("📭 今天暂时没有新消息")

if __name__ == "__main__":
    main()
