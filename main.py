#!/usr/bin/env python3
"""
YouTube Shorts Auto Generator — CLI entry point.

Usage:
    python main.py                              # 1本生成
    python main.py --count 5                    # 5本まとめて生成
    python main.py --topic "AIの未来"           # トピック手動指定
    python main.py --no-trends                  # RSS のみ（Google Trends スキップ）
    python main.py --upload                     # YouTube に非公開でアップロード
    python main.py --upload --privacy public    # 公開でアップロード
    python main.py --dry-run                    # AI 呼び出しなしで動作確認
    python main.py --count 5 --upload           # 5本生成して全部アップロード
"""
import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent
SRC = ROOT / "src"
for _p in (str(SRC), str(ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import config


def setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
        level=level,
        handlers=[logging.StreamHandler()],
    )


def make_run_dir(base: Path, title: str) -> Path:
    safe = "".join(c if c.isalnum() or c in "._-" else "_" for c in title)[:30]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = base / f"{ts}_{safe}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def build_dummy_topic(title: str) -> dict:
    return {"title": title, "summary": "", "source": "manual", "url": "", "ai_reason": "手動指定"}


def build_dummy_script(topic: dict) -> dict:
    title = topic["title"]
    return {
        "topic_title": title,
        "slides": [
            {"type": "hook",    "headline": f"{title}って知ってた?", "narration": f"{title}について、衝撃の事実をお届けします！", "duration": 8},
            {"type": "content", "headline": "ポイント①", "narration": f"{title}の基本情報です。とても重要です。", "duration": 10},
            {"type": "content", "headline": "ポイント②", "narration": "実は多くの人が知らない事実があります。", "duration": 10},
            {"type": "content", "headline": "ポイント③", "narration": "データで見るとこんな結果が出ています。", "duration": 10},
            {"type": "content", "headline": "ポイント④", "narration": "専門家もこう言っています。", "duration": 10},
            {"type": "outro",   "headline": "まとめ", "narration": "いかがでしたか？フォロー&いいねをお忘れなく！", "duration": 8},
        ],
        "full_narration": f"{title}について衝撃の事実があります。ポイント1つ目。基本情報です。ポイント2つ目。知らない事実があります。ポイント3つ目。データの結果です。ポイント4つ目。専門家の意見です。まとめ。フォロー&いいねをお忘れなく！",
    }


def build_dummy_metadata(topic: dict) -> dict:
    return {
        "title": f"【衝撃】{topic['title']}の真実がヤバすぎた...",
        "description": f"{topic['title']}について60秒でわかりやすく解説！\n\n#Shorts #{topic['title'].replace(' ', '')} #知識 #トレンド #雑学",
        "tags": [topic["title"], "Shorts", "知識", "雑学", "トレンド"],
        "category_id": "27",
        "default_language": "ja",
    }


def generate_one(topic: dict, args: argparse.Namespace, client) -> dict:
    """
    Run the full pipeline for a single topic.
    Returns a result dict with keys: topic, run_dir, metadata, upload_result, error.
    """
    log = logging.getLogger(__name__)
    result = {"topic": topic, "run_dir": None, "metadata": None, "upload_result": None, "error": None}

    try:
        # Script
        if args.dry_run:
            script = build_dummy_script(topic)
        else:
            from pipeline.script import generate_script
            script = generate_script(topic, client, num_slides=config.NUM_SLIDES)

        # Run directory
        out_base = Path(args.output_dir)
        run_dir = make_run_dir(out_base, topic["title"])
        slides_dir = run_dir / "slides"
        slides_dir.mkdir(exist_ok=True)
        result["run_dir"] = run_dir

        (run_dir / "script.json").write_text(
            json.dumps(script, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        # TTS
        from pipeline.tts import generate_tts
        audio_path = generate_tts(
            text=script["full_narration"],
            output_path=run_dir / "audio.mp3",
        )

        # Slides
        from pipeline.slides import generate_slides
        slide_paths = generate_slides(
            script=script,
            output_dir=slides_dir,
            width=config.VIDEO_WIDTH,
            height=config.VIDEO_HEIGHT,
        )

        # Video
        from pipeline.video import create_video
        video_path = create_video(
            slide_paths=slide_paths,
            audio_path=audio_path,
            output_path=run_dir / "final.mp4",
            width=config.VIDEO_WIDTH,
            height=config.VIDEO_HEIGHT,
            fps=config.VIDEO_FPS,
        )

        # Metadata
        if args.dry_run:
            metadata = build_dummy_metadata(topic)
        else:
            from pipeline.metadata import generate_metadata
            metadata = generate_metadata(topic, script, client)

        (run_dir / "metadata.json").write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        result["metadata"] = metadata

        # Upload
        if args.upload:
            from pipeline.uploader import upload_video
            upload_result = upload_video(
                video_path=video_path,
                metadata=metadata,
                client_secrets=ROOT / "client_secrets.json",
                token_path=ROOT / "token.json",
                privacy=args.privacy,
            )
            (run_dir / "upload_result.json").write_text(
                json.dumps(upload_result, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            result["upload_result"] = upload_result

    except Exception as e:
        log.error(f"[{topic['title']}] 失敗: {e}")
        result["error"] = str(e)

    return result


def print_final_summary(results: list[dict]):
    width = 70
    ok_count = sum(1 for r in results if not r["error"])

    print("\n" + "=" * width)
    print(f"  完了: {ok_count}/{len(results)} 本")
    print("=" * width)
    for i, r in enumerate(results, 1):
        topic_title = r["topic"]["title"]
        if r["error"]:
            print(f"  [{i}] ✗ {topic_title}")
            print(f"       エラー: {r['error']}")
        else:
            meta_title = r["metadata"]["title"] if r["metadata"] else "-"
            run_dir = r["run_dir"]
            upload = r["upload_result"]
            print(f"  [{i}] ✓ {topic_title}")
            print(f"       タイトル : {meta_title}")
            print(f"       動画     : {run_dir / 'final.mp4'}")
            if upload:
                print(f"       YouTube  : {upload['url']}  [{upload['privacy']}]")
    print("=" * width + "\n")


def run(args: argparse.Namespace):
    log = logging.getLogger(__name__)

    # API client
    if not args.dry_run:
        if not config.ANTHROPIC_API_KEY:
            log.error("ANTHROPIC_API_KEY が設定されていません。export ANTHROPIC_API_KEY=... を実行してください。")
            sys.exit(1)
        import anthropic
        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    else:
        client = None
        log.info("Dry-run モード: AI呼び出しをスキップします")

    count = args.count

    # ── Topic selection ───────────────────────────────────────────────────────
    if args.topic:
        # 手動指定: 同じトピックを count 回生成
        selected_topics = [build_dummy_topic(args.topic) for _ in range(count)]
    else:
        from pipeline.fetch import fetch_all_topics
        all_topics = fetch_all_topics(include_trends=not args.no_trends)
        if not all_topics:
            log.error("トピックを取得できませんでした。--topic でトピックを指定してください。")
            sys.exit(1)
        log.info(f"{len(all_topics)} 件のトピック候補を取得しました")

        if args.dry_run:
            selected_topics = []
            for i, t in enumerate(all_topics[:count]):
                t = dict(t)
                t["ai_reason"] = f"dry-run: {i+1}番目を選択"
                selected_topics.append(t)
        else:
            from pipeline.score import score_and_select_topics
            selected_topics = score_and_select_topics(all_topics, client, n=count)

    log.info(f"{len(selected_topics)} 本の動画を生成します")

    # ── Generate each video ───────────────────────────────────────────────────
    results = []
    for i, topic in enumerate(selected_topics, 1):
        log.info(f"\n{'─' * 50}")
        log.info(f"[{i}/{len(selected_topics)}] {topic['title']}")
        log.info(f"{'─' * 50}")
        result = generate_one(topic, args, client)
        results.append(result)

    print_final_summary(results)


def main():
    parser = argparse.ArgumentParser(
        description="YouTube Shorts 自動生成ツール",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--topic", "-t", metavar="TOPIC",
                        help="手動でトピックを指定（フェッチ・スコアリングをスキップ）")
    parser.add_argument("--count", "-n", type=int, default=1, metavar="N",
                        help="生成する動画の本数 (default: 1)")
    parser.add_argument("--output-dir", "-o", default=str(config.OUTPUT_DIR),
                        metavar="DIR", help=f"出力ディレクトリ (default: {config.OUTPUT_DIR})")
    parser.add_argument("--no-trends", action="store_true",
                        help="Google Trends を使わない（RSS のみ）")
    parser.add_argument("--dry-run", action="store_true",
                        help="AI 呼び出しをスキップし、ダミーデータで動作確認")
    parser.add_argument("--upload", "-u", action="store_true",
                        help="生成後に YouTube へ自動アップロード（client_secrets.json が必要）")
    parser.add_argument("--privacy", choices=["private", "unlisted", "public"],
                        default="private",
                        help="アップロード時の公開設定 (default: private)")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="詳細ログを表示")
    args = parser.parse_args()

    if args.count < 1:
        parser.error("--count は 1 以上を指定してください")

    setup_logging(args.verbose)
    run(args)


if __name__ == "__main__":
    main()
