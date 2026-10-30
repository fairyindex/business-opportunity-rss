#!/usr/bin/env python3
"""Fetch configured RSS/Atom feeds and write a compact, public Markdown digest."""
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from pathlib import Path
import re
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "feed-sources.txt"
OUTPUT = ROOT / "feeds.md"
WINDOW_DAYS = 7
MAX_ITEMS = 250
USER_AGENT = "business-opportunity-rss/1.0 (+https://github.com/fairyindex/business-opportunity-rss)"


def local_name(tag):
    return tag.rsplit("}", 1)[-1].lower()


def child_text(element, names):
    for child in element.iter():
        if local_name(child.tag) in names and child.text and child.text.strip():
            return child.text.strip()
    return ""


def entry_link(entry):
    for child in entry:
        if local_name(child.tag) == "link":
            href = child.attrib.get("href")
            if href:
                return href.strip()
            if child.text and child.text.strip():
                return child.text.strip()
    return ""


def parse_date(value):
    if not value:
        return None
    value = value.strip()
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        try:
            parsed = parsedate_to_datetime(value)
        except (TypeError, ValueError, OverflowError):
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def plain_text(value, limit=360):
    value = unescape(value or "")
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    if len(value) > limit:
        value = value[:limit].rsplit(" ", 1)[0] + "…"
    return value


def parse_feed(xml_bytes, cutoff, source_name):
    root = ET.fromstring(xml_bytes)
    items = []
    for element in root.iter():
        kind = local_name(element.tag)
        if kind not in {"item", "entry"}:
            continue
        title = child_text(element, {"title"}) or "(无标题)"
        link = entry_link(element)
        date_value = child_text(element, {"published", "pubdate", "date", "updated"})
        published = parse_date(date_value)
        if not link or not published or published < cutoff:
            continue
        summary = child_text(element, {"summary", "description", "encoded", "content"})
        items.append({
            "title": plain_text(title, 220),
            "link": link,
            "published": published,
            "summary": plain_text(summary),
            "source": source_name,
        })
    return items


def main():
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=WINDOW_DAYS)
    feeds = []
    for raw in SOURCES.read_text(encoding="utf-8").splitlines():
        url = raw.strip()
        if not url or url.startswith("#"):
            continue
        source_name = url.split("//", 1)[-1].split("/", 1)[0]
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/atom+xml, application/rss+xml, application/xml, text/xml"})
        try:
            with urllib.request.urlopen(request, timeout=25) as response:
                items = parse_feed(response.read(), cutoff, source_name)
            feeds.append((source_name, len(items), None))
            feeds.extend(items)
        except (urllib.error.URLError, TimeoutError, ET.ParseError, OSError, ValueError) as exc:
            feeds.append((source_name, 0, str(exc).splitlines()[0][:180]))

    items = [item for item in feeds if isinstance(item, dict)]
    # Keep the newest copy when the same link appears in more than one feed.
    unique = {}
    for item in items:
        unique[item["link"]] = item
    items = sorted(unique.values(), key=lambda item: item["published"], reverse=True)[:MAX_ITEMS]

    status_rows = [entry for entry in feeds if isinstance(entry, tuple)]
    lines = [
        "# RSS 新内容汇总",
        "",
        f"更新时间：{now.strftime('%Y-%m-%d %H:%M UTC')} · 收录最近 {WINDOW_DAYS} 天 · {len(items)} 条",
        "",
        "> 这是 RSS 发现清单。发布日期来自订阅源；摘要可能不完整，阅读时请打开原始链接核实。",
        "",
        "## 信源状态",
        "",
        "| RSS 信源 | 近 7 天条目 | 状态 |",
        "|---|---:|---|",
    ]
    for name, count, error in status_rows:
        state = f"读取失败：{error}" if error else "正常"
        lines.append(f"| {name} | {count} | {state} |")
    lines.extend(["", "## 最新内容", ""])
    if not items:
        lines.append("本次没有成功获取到近 7 天的条目。")
    for item in items:
        date = item["published"].strftime("%Y-%m-%d %H:%M UTC")
        lines.append(f"### [{item['title']}]({item['link']})")
        lines.append(f"**来源：** {item['source']} · **发布时间：** {date}")
        if item["summary"]:
            lines.append("")
            lines.append(item["summary"])
        lines.append("")
    OUTPUT.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
