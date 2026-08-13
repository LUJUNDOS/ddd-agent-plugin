#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
transcribe.py —— 短视频/音频 → 转写文本（端侧 ASR）

管线：
  1. 解析来源：URL（抖音/快手/TikTok/B站/YouTube/优酷/腾讯/小红书/直链）或本地音视频文件。
  2. 下载/抽取音频：抖音默认免 Cookie（douyin_resolver SSR 解析分享页公开数据），TikTok/其他走 yt-dlp 拉媒体（TikTok 需登录 Cookie），imageio-ffmpeg 抽 16k 单声道 wav。
  3. 端侧 ASR：faster-whisper（模型首次运行自动从 HuggingFace 下载，约 140MB/base）。
  4. 输出：<slug>.srt + <slug>.txt，并在 [TRANSCRIPT_START] / [TRANSCRIPT_END] 间打印纯文本，供 ingest 捕获。

设计：本脚本由 ingest skill 在识别到「视频/音频来源」时调用，用户不直接调用。
依赖（一次性安装）：pip install yt-dlp faster-whisper imageio-ffmpeg
抖音策略：默认免 Cookie（SSR 解析分享页公开数据，见 douyin_resolver.py）；仅当解析失败才回退 yt-dlp + Cookie（放 --cookie-file 或环境变量 DOUYIN_COOKIE，从浏览器 DevTools 复制视频页请求的 Cookie 请求头）。
版权/ToS：仅用于用户主动导入、自己有权处理的素材。
"""
import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

# 抖音免 Cookie 主路径：优先用同目录 douyin_resolver（SSR 解析分享页公开数据），
# 失败再回退 yt-dlp + Cookie。resolver 懒加载，避免无 requests 时影响其他来源。
import importlib.util


def _load_douyin_resolver():
    spec = importlib.util.spec_from_file_location(
        "douyin_resolver",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "douyin_resolver.py"),
    )
    if spec is None or spec.loader is None:
        raise ImportError("douyin_resolver.py 不存在")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

VIDEO_HOSTS = (
    "douyin.com", "tiktok.com", "bilibili.com", "youtube.com", "youtu.be",
    "v.youku.com", "v.qq.com", "xiaohongshu.com", "kuaishou.com",
)
VIDEO_EXT = (".mp4", ".mov", ".webm", ".mkv", ".flv", ".m4a", ".mp3", ".wav", ".ogg", ".m4v")


def die(msg, code=1):
    print(f"[transcribe] ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


def check_deps():
    missing = []
    for mod in ("yt_dlp", "faster_whisper", "imageio_ffmpeg"):
        try:
            __import__(mod)
        except Exception:
            missing.append(mod)
    return missing


def get_ffmpeg():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception as e:  # pragma: no cover
        die(f"无法定位 ffmpeg（imageio-ffmpeg 未安装？）：{e}")


def is_video_url(url):
    u = url.lower()
    if u.startswith("http"):
        return any(h in u for h in VIDEO_HOSTS) or u.endswith(VIDEO_EXT)
    return False


def slugify(text, maxlen=48):
    text = re.sub(r"[^\w一-龥]+", "-", text or "").strip("-")
    return text[:maxlen] or "video"


def resolve_cookie(cookie_file):
    if cookie_file and os.path.exists(cookie_file):
        return ("file", cookie_file)
    val = os.environ.get("DOUYIN_COOKIE", "")
    if val:
        return ("raw", val)
    return (None, None)


def fmt_ts(s):
    h = int(s // 3600)
    m = int((s % 3600) // 60)
    sec = int(s % 60)
    ms = int(round((s - int(s)) * 1000))
    return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"


def _try_douyin_cookiefree(url, out_dir):
    """抖音免 Cookie 解析 + 下载；成功返回 (media_path, title)，失败返回 (None, "")。"""
    try:
        resolver = _load_douyin_resolver()
    except Exception as e:
        print(f"[transcribe] 抖音免 Cookie 模块加载失败，回退 yt-dlp：{e}", file=sys.stderr)
        return (None, "")
    try:
        meta = resolver.resolve(url)
    except Exception as e:
        print(f"[transcribe] 抖音免 Cookie 解析失败，回退 yt-dlp：{e}", file=sys.stderr)
        return (None, "")
    if meta.get("type") != "video":
        # 图文帖无音频，转写管线暂不支持；回退 yt-dlp 尝试（多半失败，届时 ingest 回退手动字幕）
        print("[transcribe] 检测到抖音图文帖，转写管线暂不支持，回退 yt-dlp 尝试", file=sys.stderr)
        return (None, "")
    dest = out_dir / f"._media_douyin_{meta['aweme_id']}.mp4"
    try:
        n = resolver.download_segmented(meta["video_url"], str(dest))
    except Exception as e:
        print(f"[transcribe] 抖音免 Cookie 下载失败，回退 yt-dlp：{e}", file=sys.stderr)
        return (None, "")
    if not dest.exists() or dest.stat().st_size == 0:
        return (None, "")
    title = (meta.get("desc") or meta.get("author") or "").strip()
    print(f"[transcribe] 抖音免 Cookie 下载成功：{dest.name}（{n} 字节，作者 {meta.get('author','')}）")
    return (str(dest), title)


def _download_via_ytdlp(url, out_dir, cookie_file):
    """原有 yt-dlp 下载（含 Cookie 支持），供非抖音来源与抖音回退使用；返回 (media, title)。"""
    cookie_kind, cookie_val = resolve_cookie(cookie_file)
    ydl_opts = {
        "ffmpeg_location": os.path.dirname(get_ffmpeg()),
        "format": "bestaudio/best",
        "outtmpl": str(out_dir / "._media.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
    }
    tmp_cookie = None
    if cookie_kind == "file":
        ydl_opts["cookiefile"] = cookie_val
    elif cookie_kind == "raw":
        tmp_cookie = out_dir / "._cookie.txt"
        tmp_cookie.write_text(cookie_val, encoding="utf-8")
        ydl_opts["cookiefile"] = str(tmp_cookie)
    try:
        import yt_dlp
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = (info.get("title") or "").strip()
    except Exception as e:
        die(
            f"下载失败（抖音/TikTok 多因缺登录 Cookie，或平台改版）：{e}\n"
            f"→ 解决：浏览器登录后从 DevTools 复制视频页请求的 `Cookie` 请求头，\n"
            f"  存为 --cookie-file 或设环境变量 DOUYIN_COOKIE；\n"
            f"  或改为手动粘贴字幕（ingest 会自动回退到该分支，不卡住）。",
            code=2,
        )
    finally:
        if tmp_cookie is not None:
            try:
                tmp_cookie.unlink()
            except OSError:
                pass
    cands = [c for c in out_dir.glob("._media.*")
             if c.suffix not in (".srt", ".txt", ".vtt", ".cookie.txt")]
    if not cands:
        die("下载完成但未找到媒体文件（可能被合并/命名异常）")
    return (str(cands[0]), title)


def main():
    ap = argparse.ArgumentParser(description="端侧短视频/音频转写（yt-dlp + faster-whisper）")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--url", help="视频/音频 URL（抖音/TikTok/B站/YouTube/直链…）")
    src.add_argument("--file", help="本地音视频文件路径")
    ap.add_argument("--out", default=".", help="输出目录（默认当前目录）")
    ap.add_argument("--model", default="base", help="faster-whisper 模型大小: tiny/base/small/medium/large（默认 base）")
    ap.add_argument("--slug", default="", help="输出文件名 slug（默认取视频标题）")
    ap.add_argument("--cookie-file", default="", help="抖音/TikTok 登录 Cookie 文件路径")
    ap.add_argument("--lang", default="", help="强制语言代码（如 zh/en）；留空=自动检测")
    args = ap.parse_args()

    missing = check_deps()
    if missing:
        die("缺少依赖，请先安装：\n  pip install " + " ".join(missing) +
            "\n（ffmpeg 由 imageio-ffmpeg 提供，无需系统安装）")

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    ffmpeg = get_ffmpeg()
    title = ""

    # 1) 取得媒体文件
    if args.file:
        media = args.file
        if not os.path.exists(media):
            die(f"本地文件不存在：{media}")
    else:
        if not is_video_url(args.url):
            die(f"URL 不像视频来源（主机不在支持列表、且非音视频后缀）：{args.url}")
        media = None
        # 抖音：优先免 Cookie 主路径（SSR 解析分享页公开数据），失败再回退 yt-dlp + Cookie
        if "douyin.com" in args.url.lower():
            media, title = _try_douyin_cookiefree(args.url, out_dir)
        if media is None:
            media, title = _download_via_ytdlp(args.url, out_dir, args.cookie_file)

    # 2) 抽音频（16k 单声道 wav，最适合 Whisper）
    wav = out_dir / "._audio.wav"
    try:
        subprocess.run(
            [ffmpeg, "-y", "-i", media, "-vn", "-ac", "1", "-ar", "16000", str(wav)],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError as e:
        die(f"ffmpeg 抽取音频失败：{e}")

    # 3) 端侧 ASR
    from faster_whisper import WhisperModel
    lang = args.lang if args.lang else None
    model = WhisperModel(args.model, device="cpu", compute_type="int8")
    segments, info = model.transcribe(str(wav), language=lang, beam_size=5)

    slug = args.slug or slugify(title)
    srt_path = out_dir / f"{slug}.srt"
    txt_path = out_dir / f"{slug}.txt"
    lines = []
    with srt_path.open("w", encoding="utf-8") as fs, txt_path.open("w", encoding="utf-8") as ft:
        for i, seg in enumerate(segments, 1):
            text = (seg.text or "").strip()
            if not text:
                continue
            lines.append(text)
            ft.write(text + "\n")
            fs.write(f"{i}\n{fmt_ts(seg.start)} --> {fmt_ts(seg.end)}\n{text}\n\n")

    # 4) 打印纯文本供 ingest 捕获
    print("[transcribe] TRANSCRIPT_START")
    print("\n".join(lines).strip())
    print("[transcribe] TRANSCRIPT_END")
    print(f"[transcribe] written: {srt_path} | {txt_path} | lang={info.language} | model={args.model}")

    # 清理临时媒体/音频
    for t in (media, str(wav)):
        try:
            os.remove(t)
        except OSError:
            pass


if __name__ == "__main__":
    main()
