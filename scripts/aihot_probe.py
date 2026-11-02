#!/usr/bin/env python3
"""One-time test of AIHOT public APIs; save public titles and status only."""
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

def clean(x, n=250):
    return re.sub(r"[\r\n|<>\[\]]+", " ", str(x or "")).strip()[:n]

terms = ["创业","小团队","商业化","收入","营收","变现","订阅","设计","视觉","创意","电商","营销","获客","内容","视频","客户","企业","销售","工具","Agent","AI产品","自动化","服务"]
lines = ["# AIHOT 实际接口测试", "", "检测时间：" + datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"), "", "|窗口|类别|状态|本页文章数|错误|", "|---|---|---|---:|---|"]
articles = {}
for window in ("24h","7d"):
    for category in ("ai-products","tip","industry"):
        params = urllib.parse.urlencode({"mode":"selected","window":window,"category":category,"limit":40})
        url = "https://aihot.news/api/v1/items?" + params
        request = urllib.request.Request(url, headers={"User-Agent":"aihot-api/2.0.0","Accept":"application/json"})
        status, obj, err = "ERR", {}, ""
        try:
            with urllib.request.urlopen(request, timeout=18) as resp:
                status = resp.status
                obj = json.loads(resp.read(1500000))
        except urllib.error.HTTPError as e:
            status = e.code
            err = clean(e.read(350).decode("utf-8", errors="replace"))
        except Exception as e:
            err = clean(type(e).__name__ + ": " + str(e))
        items = obj.get("items", []) if isinstance(obj,dict) else []
        if not isinstance(items,list):
            items = []
        lines.append(f"|{window}|{category}|{status}|{len(items)}|{err}|")
        for entry in items:
            if not isinstance(entry,dict):
                continue
            title = clean(entry.get("title") or entry.get("originalTitle"))
            summary = clean(entry.get("summary") or entry.get("reason") or entry.get("description"))
            links = entry.get("links") or {}
            if not isinstance(links,dict):
                links = {}
            link = links.get("original") or links.get("aihot") or ""
            if not isinstance(link,str) or not link.startswith("https://"):
                link = ""
            src = entry.get("source") or {}
            if isinstance(src,dict):
                src = src.get("name","")
            date = clean(entry.get("publishedAt") or entry.get("createdAt"),40)
            score = sum(2 if t.lower() in title.lower() else 1 for t in terms if t.lower() in (title+" "+summary).lower())
            if title:
                articles[link or title] = (score,title,link,summary,date,category,clean(src,80))
        time.sleep(0.45)
lines += ["", f"## 候选条目：{len(articles)}（根据关键词排序，尚未核实原文）", ""]
for index, (score,title,link,summary,date,category,source) in enumerate(sorted(articles.values(),key=lambda x:x[0],reverse=True)[:35],1):
    label = f"[{title}]({link})" if link else title
    lines += [f"{index}. **{label}**", f"   {date or '日期未知'} · {category} · {source} · 匹配分 {score}", f"   {summary}", ""]
Path("aihot-test.md").write_text("\n".join(lines),encoding="utf-8")
print("AIHOT test completed:",len(articles),"candidates")
