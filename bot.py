import os
import feedparser
import google.generativeai as genai
import requests
import json
from datetime import datetime, timedelta

# ================= 配置区域 =================

# 1. 设定你的口味 (AI 会根据这个筛选)
USER_INTERESTS = """
我只对以下内容感兴趣：
1. 大语言模型 (LLM) 的最新技术突破 (如 GPT-5, Gemini, DeepSeek, Claude)。
2. AI 在编程和开发工具中的应用 (如 GitHub Copilot, Cursor)。
3. 有趣的 AI 开源项目，或者 Product Hunt 上的热门 AI 新产品。

我不喜欢：
1. 纯粹的股价涨跌、公司财报分析。
2. 区块链、加密货币相关的新闻。
3. 过于泛泛的行业分析文章。
"""

# 2. 设定新闻源 (已为你添加 Hacker News, 36Kr, Product Hunt)
RSS_URLS = [
    "https://techcrunch.com/category/artificial-intelligence/feed/",      # TechCrunch AI
    "https://openai.com/blog/rss.xml",                                    # OpenAI Blog
    "https://news.ycombinator.com/rss",                                   # Hacker News (极客头条)
    "https://www.36kr.com/feed",                                          # 36氪 (国内科技)
    "https://www.producthunt.com/feed",                                   # Product Hunt (新产品发现)
]

# ===========================================

# --- 初始化检查 ---
if "GEMINI_API_KEY" not in os.environ:
    print("❌ 错误：缺少 GEMINI_API_KEY")
    exit(1)
if "LARK_WEBHOOK" not in os.environ:
    print("❌ 错误：缺少 LARK_WEBHOOK")
    exit(1)

genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

def check_if_interesting(title, content):
    """AI 筛选器"""
    print(f"🕵️ 正在筛选: {title[:30]}...")
    try:
        prompt = f"""
        任务：你是一个新闻过滤器。请根据我的兴趣标准，判断这条新闻是否值得推荐。
        
        【我的兴趣】：
        {USER_INTERESTS}
        
        【新闻标题】：{title}
        【新闻摘要】：{content[:500]}
        
        请只回答 "Yes" 或 "No"。如果不确定，回答 "No"。
        """
        response = model.generate_content(prompt)
        result = response.text.strip().lower()
        
        if "yes" in result:
            return True
        else:
            print(f"   ↳ 🗑️ 过滤掉 (不感兴趣)")
            return False
    except Exception as e:
        print(f"⚠️ 筛选出错: {e}，默认保留")
        return True

def get_ai_summary(title, content):
    """AI 总结器"""
    try:
        prompt = f"""
        任务：你是一个科技主编。请用中文一句话总结核心看点（50字内）。
        标题: {title}
        摘要: {content[:800]}
        总结:
        """
        response = model.generate_content(prompt)
        return response.text.strip()
    except:
        return "（AI 暂时无法总结，请阅读原文）"

def send_lark_card(cards):
    url = os.environ["LARK_WEBHOOK"]
    headers = {"Content-Type": "application/json"}
    today = datetime.now().strftime("%Y-%m-%d")
    
    payload = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "template": "blue",
                "title": {
                    "content": f"📅 AI 精选日报 ({today})", 
                    "tag": "plain_text"
                }
            },
            "elements": cards
        }
    }
    requests.post(url, headers=headers, data=json.dumps(payload))

def main():
    print("🚀 智能筛选任务启动...")
    cards = []
    has_news = False
    
    # 遍历所有 RSS 源
    for url in RSS_URLS:
        print(f"📡 正在抓取: {url}")
        try:
            feed = feedparser.parse(url)
            # 这里的 [:5] 表示每个源只取最新的 5 条给 AI 挑
            # 如果想看更多，可以改成 [:10]
            for entry in feed.entries[:5]: 
                title = entry.title
                link = entry.link
                summary_raw = entry.get('summary', entry.get('description', ''))
                
                # 1. AI 筛选
                if check_if_interesting(title, summary_raw):
                    # 2. AI 总结
                    ai_text = get_ai_summary(title, summary_raw)
                    
                    cards.append({
                        "tag": "div",
                        "text": {
                            "content": f"**📌 {title}**\n{ai_text}",
                            "tag": "lark_md"
                        }
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
            print(f"⚠️ RSS 读取错误: {url} -> {e}")

    if has_news:
        cards.append({
            "tag": "note",
            "elements": [{"content": "Powered by Gemini Smart Filter", "tag": "plain_text"}]
        })
        send_lark_card(cards)
        print("✅ 精选日报已发送！")
    else:
        print("📭 今天没有符合你口味的新闻。")

if __name__ == "__main__":
    main()
