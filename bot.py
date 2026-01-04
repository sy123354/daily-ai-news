import os
import feedparser
import google.generativeai as genai
import requests
import json
from datetime import datetime

# --- 配置 ---
RSS_URLS = [
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "https://openai.com/blog/rss.xml", 
]

# --- 验证 Key 是否存在 ---
if "GEMINI_API_KEY" not in os.environ:
    print("❌ 严重错误：GitHub Secrets 里没有 GEMINI_API_KEY！")
else:
    # 打印 Key 的前几位验证是否复制多了空格
    key = os.environ["GEMINI_API_KEY"]
    print(f"🔍 检查 API Key: {key[:5]}...{key[-5:]} (长度: {len(key)})")
    genai.configure(api_key=key)
    model = genai.GenerativeModel('gemini-1.5-flash')

def get_ai_summary(text):
    print("🤖 正在尝试调用 Gemini...")
    try:
        # 这里的 prompt 稍微改简单点，测试连通性
        prompt = f"请用中文总结这段话(50字内): {text[:500]}"
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        # 🔥 关键点：把错误打印出来！
        print(f"❌ Gemini 调用失败，错误详情: {e}")
        return f"AI报错: {str(e)}"

def send_lark_message(content):
    url = os.environ["LARK_WEBHOOK"]
    headers = {"Content-Type": "application/json"}
    payload = {
        "msg_type": "text",
        "content": {"text": content}
    }
    requests.post(url, headers=headers, data=json.dumps(payload))

def main():
    print("🚀 开始诊断 AI...")
    
    # 1. 直接用一句简单的测试语测试 AI，不依赖 RSS
    test_summary = get_ai_summary("Google DeepMind is a British-American artificial intelligence research laboratory which serves as a subsidiary of Google.")
    
    # 2. 发送诊断结果给飞书
    msg = f"🧪 AI 诊断报告:\n测试结果: {test_summary}\n(包含关键词'日报')"
    send_lark_message(msg)
    print("✅ 诊断报告已发送")

if __name__ == "__main__":
    main()
