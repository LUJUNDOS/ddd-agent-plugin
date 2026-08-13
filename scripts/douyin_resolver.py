#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
douyin_resolver.py — 抖音免 Cookie 解析 + 下载（系统知识库线）

移植 lyxdream/obsidian-douyin-capture 后端方案：抖音分享页 SSR 把公开作品数据
注入 window._ROUTER_DATA（备选 RENDER_DATA），用移动端 UA 直接 GET 即可，无需
登录 Cookie。无水印地址由 play_addr 拼 aweme.snssdk.com 直链得到。

数据流：
  v.douyin.com/xxx  (302) ─► iesdouyin.com/share/video|note/{id}/
       │  GET（移动 UA）  html 含 window._ROUTER_DATA
       ▼
  解析 JSON → item_list[0]
       ├─ 视频：video.play_addr → url_list（playwm→play 无水印）或 uri 拼直链
       └─ 图文：images[].url_list + desc

下载采用分段 Range 续传，规避单连接大文件流被中途打断的问题（实测某些网络环境
单连接 ~522KB 即被截断，分段后可拼满完整文件）。

用法：
  python douyin_resolver.py "<抖音链接或分享文案>" [--out DIR] [--no-download]

依赖：pip install requests
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    sys.stderr.write("缺少依赖 requests：pip install requests\n")
    sys.exit(3)

MOBILE_UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 "
    "Mobile/15E148 Safari/604.1"
)
REFERER = "https://www.iesdouyin.com/"
PLAY_BASE = "https://aweme.snssdk.com/aweme/v1/play/"


def extract_url(text: str) -> str:
    """从分享文案或短链里提取抖音 URL；找不到则原样返回（可能本身就是链接）。"""
    m = re.search(r"https?://[^\s，。、）)]+", text)
    if not m:
        return text.strip()
    return m.group(0).rstrip(".,;)")


def fetch_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": MOBILE_UA,
        "Referer": REFERER,
        "Accept": "text/html,application/xhtml+xml,*/*",
    })
    return s


def get_router_data(html: str) -> dict:
    """从 SSR HTML 提取 window._ROUTER_DATA / RENDER_DATA JSON。"""
    for key in ("_ROUTER_DATA", "RENDER_DATA"):
        pat = r"window\." + key + r"\s*=\s*(\{.*?\})\s*;?\s*</script>"
        m = re.search(pat, html, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(1))
            except json.JSONDecodeError:
                # 末尾可能有尾随字符，从后往前尝试宽松截取
                raw = m.group(1)
                for end in range(len(raw), max(len(raw) - 400, 0), -1):
                    try:
                        return json.loads(raw[:end])
                    except json.JSONDecodeError:
                        continue
    raise ValueError("未在页面中找到 _ROUTER_DATA / RENDER_DATA（可能被风控或页面改版）")


def find_item(data: dict) -> dict:
    """递归查找 item_list[0]。"""
    def walk(node):
        if isinstance(node, dict):
            il = node.get("item_list")
            if isinstance(il, list) and il:
                return il[0]
            for v in node.values():
                r = walk(v)
                if r:
                    return r
        elif isinstance(node, list):
            for v in node:
                r = walk(v)
                if r:
                    return r
        return None
    item = walk(data)
    if not item:
        raise ValueError("解析成功但未找到 item_list（数据结构可能已变化）")
    return item


def build_video_url(item: dict) -> str:
    """从 play_addr 取无水印直链；优先 url_list 中 playwm→play 的地址，退路用 uri 拼直链。"""
    video = item.get("video") or {}
    play_addr = video.get("play_addr") or {}
    for u in play_addr.get("url_list", []):
        if "playwm" in u:
            return u.replace("playwm", "play")
    uri = play_addr.get("uri")
    if uri:
        return f"{PLAY_BASE}?video_id={uri}&ratio=720p&line=0".replace("playwm", "play")
    raise ValueError("未找到可用的视频播放地址")


def resolve(url_or_text: str) -> dict:
    """解析抖音链接，返回元数据 + 媒体地址。"""
    url = extract_url(url_or_text)
    s = fetch_session()
    r = s.get(url, allow_redirects=True, timeout=25)
    r.raise_for_status()
    data = get_router_data(r.text)
    item = find_item(data)
    author = (item.get("author") or {}).get("nickname") or ""
    sec_uid = (item.get("author") or {}).get("sec_uid") or ""
    desc = item.get("desc") or ""
    aweme_id = str(item.get("aweme_id") or item.get("aweme_id_str") or "")
    aweme_type = item.get("aweme_type", 0)
    is_image = (aweme_type == 68) or ("images" in item and item.get("images"))
    result = {
        "aweme_id": aweme_id,
        "author": author,
        "sec_uid": sec_uid,
        "desc": desc,
        "aweme_type": aweme_type,
        "url": r.url,
    }
    if is_image:
        imgs = []
        for im in item.get("images", []):
            for u in (im.get("url_list") or []):
                imgs.append(u)
                break
        result["type"] = "image"
        result["images"] = imgs
    else:
        result["type"] = "video"
        result["video_url"] = build_video_url(item)
    return result


def download_segmented(url: str, dest: str, chunk: int = 512 * 1024) -> int:
    """分段 Range 下载，规避单连接大文件流截断；返回写入字节数。"""
    s = fetch_session()
    head = s.get(url, stream=True, timeout=25)
    total = int(head.headers.get("Content-Length", 0) or 0)
    if head.status_code in (301, 302):
        url = head.headers.get("Location", url)
        head = s.get(url, stream=True, timeout=25)
        total = int(head.headers.get("Content-Length", 0) or 0)
    if total and total < chunk * 4:
        r = s.get(url, timeout=60)
        open(dest, "wb").write(r.content)
        return len(r.content)
    written = 0
    with open(dest, "wb") as f:
        start = 0
        while True:
            end = start + chunk - 1
            h = {"Range": f"bytes={start}-{end}"}
            r = s.get(url, headers=h, timeout=60)
            if r.status_code not in (200, 206) or not r.content:
                break
            f.write(r.content)
            written += len(r.content)
            if total and written >= total:
                break
            if len(r.content) < chunk:
                break
            start = end + 1
    return written


def main():
    ap = argparse.ArgumentParser(description="抖音免 Cookie 解析 + 下载")
    ap.add_argument("url", help="抖音分享链接或含链接的文案")
    ap.add_argument("--out", default=".", help="输出目录")
    ap.add_argument("--no-download", action="store_true", help="只解析不下载")
    args = ap.parse_args()

    meta = resolve(args.url)
    print(json.dumps(meta, ensure_ascii=False, indent=2))
    if args.no_download:
        return
    os.makedirs(args.out, exist_ok=True)
    if meta["type"] == "video":
        dest = os.path.join(args.out, f"{meta['aweme_id']}.mp4")
        n = download_segmented(meta["video_url"], dest)
        print(f"视频已下载：{dest} （{n} 字节）")
    else:
        for i, u in enumerate(meta["images"], 1):
            dest = os.path.join(args.out, f"{meta['aweme_id']}_{i}.jpg")
            n = download_segmented(u, dest)
            print(f"图片已下载：{dest} （{n} 字节）")


if __name__ == "__main__":
    main()
