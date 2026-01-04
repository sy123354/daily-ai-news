import os
import feedparser
import google.generativeai as genai
import requests
import json
from datetime import datetime

# --- 配置区域 ---
RSS_URLS = [
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "https://openai.com/blog/rss.xml", 
]

# --- 1. 密钥自检 (帮我们找原因) ---
if "LARK_WEBHOOK" not in os.environ:
    print("❌ 致命错误：LARK_WEBHOOK 根本没找到！")
    exit(1)

webhook_url = os.environ["LARK_WEBHOOK"]
# 打印地址的首尾，检查是否有多余空格
print(f"🔍 正在使用的 Webhook 地址: {webhook_url[:10]} ****** {webhook_url[-5:]}")
if " " in webhook_url or "\n" in webhook_url:
    print("⚠️ 警告：Webhook 地址里好像包含了空格或换行！这会导致发送失败。")

# --- 2. 配置 Gemini ---
if "GEMINI_API_KEY" in os.environ:
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    print("⚠️ 未找到 Gemini Key，将跳过 AI 总结")
    model = None

def get_ai_summary(text):
    if not model: return "AI 未启用"
    try:
        prompt = f"请用中文一句话总结: {text[:500]}"
        response = model.generate_content(prompt)
        return response.text.strip()
    except:
        return "无法总结"

def send_lark_text_message(content):
    """
    👉 降级方案：发送纯文本消息
    完全模拟 curl 命令，排除卡片格式错误的可能性
    """
    headers = {"Content-Type": "application/json"}
    
    # 构造最简单的纯文本 Payload
    payload = {
        "msg_type": "text",
        "content": {
            "text": content
        }
    }
    
    print("📤 正在尝试发送纯文本消息...")
    try:
        resp = requests.post(webhook_url, headers=headers, data=json.dumps(payload))
        print(f"📡 飞书响应状态码: {resp.status_code}")
        print(f"📡 飞书响应内容: {resp.text}")
    except Exception as e:
        print(f"❌ 发送请求直接报错: {e}")

def main():
    print("🚀 开始运行 (调试模式)...")
    
    # 1. 先发一条强制测试消息 (如果这条收到了，说明通信是通的)
    test_msg = "🤖【调试日报】\n这是一条来自 GitHub 的纯文本测试消息。\n如果能看到这条，说明连接成功！"
    send_lark_text_message(test_msg)
    
    # 2. 尝试抓取一条新闻
    try:
        feed = feedparser.parse(RSS_URLS[0])
        if feed.entries:
            entry = feed.entries[0]
            summary = get_ai_summary(entry.summary)
            news_msg = f"📰 新闻测试:\n标题: {entry.title}\nAI总结: {summary}\n(本消息包含关键词'日报')"
            send_lark_text_message(news_msg)
    except Exception as e:
        print(f"抓取测试失败: {e}")

if __name__ == "__main__":
    main()
