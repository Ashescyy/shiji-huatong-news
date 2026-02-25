#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
世纪华通新闻简报机器人
"""

import os
import json
import requests
import datetime
import time

# 配置
STOCK_CODE = "002602"
STOCK_NAME = "世纪华通"
KIMI_API_KEY = os.environ.get("KIMI_API_KEY")
DINGTALK_WEBHOOK = os.environ.get("DINGTALK_WEBHOOK")

def get_news_from_eastmoney():
    """从东方财富获取新闻"""
    try:
        url = f"https://searchapi.eastmoney.com/api/suggest/get?input={STOCK_NAME}&type=14&count=10"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        news_list = []
        if 'QuotationCodeTable' in data and 'Data' in data['QuotationCodeTable']:
            for item in data['QuotationCodeTable']['Data'][:5]:
                news_list.append({
                    'title': item.get('Name', ''),
                    'content': item.get('Code', '')
                })
        return news_list
    except Exception as e:
        print(f"获取新闻失败: {e}")
        return []

def generate_briefing_with_kimi(news_list):
    """使用Kimi API生成简报"""
    print("正在调用Kimi API...")
    
    # 准备新闻文本
    news_text = "\n".join([
        f"{i+1}. {n.get('title', '无标题')}"
        for i, n in enumerate(news_list[:5])
    ]) if news_list else "今日暂无重大新闻"
    
    # 构建Prompt
    prompt = f"""你是专业财经分析师，请根据世纪华通(002602)的以下信息生成简报：

【最新动态】：
{news_text}

请生成简洁的简报，包含：
1. 重点新闻（带利好/利空/中性判断）
2. 股价影响评估（短期/中期）
3. 风险提示

格式用Markdown，总字数300字以内。"""

    # 调用Kimi API
    headers = {
        "Authorization": f"Bearer {KIMI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "moonshot-v1-8k",
        "messages": [
            {"role": "system", "content": "你是专业股票分析师"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }
    
    try:
        response = requests.post(
            "https://api.moonshot.cn/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        result = response.json()
        return result['choices'][0]['message']['content']
    except Exception as e:
        print(f"Kimi API错误: {e}")
        return f"""## 📊 世纪华通简报（备用）

**时间**：{datetime.datetime.now().strftime("%m月%d日 %H:%M")}

**最新动态**：
{news_text}

**简要分析**：今日需关注主力资金流向和板块轮动情况。

⚠️ 注：Kimi API调用失败，以上为备用简报。"""

def send_to_dingtalk(content):
    """发送到钉钉"""
    print("正在推送到钉钉...")
    
    message = {
        "msgtype": "markdown",
        "markdown": {
            "title": f"{STOCK_NAME}新闻简报",
            "text": content + f"\n\n---\n🕐 生成时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n🤖 自动推送"
        }
    }
    
    try:
        response = requests.post(
            DINGTALK_WEBHOOK,
            json=message,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print(f"钉钉推送成功: {response.json()}")
        return True
    except Exception as e:
        print(f"钉钉推送失败: {e}")
        return False

def main():
    print(f"=== 开始生成 {STOCK_NAME} 简报 ===")
    print(f"时间：{datetime.datetime.now()}")
    
    # 获取新闻
    news = get_news_from_eastmoney()
    print(f"获取到 {len(news)} 条新闻")
    
    # 生成简报
    briefing = generate_briefing_with_kimi(news)
    print("\n生成的简报：")
    print(briefing)
    
    # 推送
    if DINGTALK_WEBHOOK:
        send_to_dingtalk(briefing)
    else:
        print("未配置钉钉Webhook，跳过推送")
    
    # 保存文件
    filename = f"briefing_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(briefing)
    
    print(f"=== 完成，已保存到 {filename} ===")

if __name__ == "__main__":
    main()
