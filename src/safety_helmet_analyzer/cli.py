import argparse
import sys
from pathlib import Path

from .config import load_config
from .detectors import DetectorError
from .video import VideoAnalysisError, VideoAnalyzer


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "analyze":
        return _run_analyze(args)
    if args.command == "web":
        return _run_web(args)

    parser.print_help()
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="safety-helmet-analyzer",
        description="Offline analysis of missing safety helmets in worksite videos.",
    )
    subparsers = parser.add_subparsers(dest="command")

    analyze = subparsers.add_parser("analyze", help="Analyze one local video file")
    analyze.add_argument("video", help="Path to input video")
    analyze.add_argument("--config", default="config/default.json", help="Path to JSON config")
    analyze.add_argument("--output", default=None, help="Output directory for report files")
    analyze.add_argument("--backend", choices=["onnx", "color"], help="Detector backend override")
    analyze.add_argument("--model", help="ONNX model path override")
    analyze.add_argument("--labels", help="Labels file path override")
    analyze.add_argument("--sample-fps", type=float, help="Video sampling FPS override")

    web = subparsers.add_parser("web", help="Start local upload web interface")
    web.add_argument("--config", default="config/default.json", help="Path to JSON config")
    web.add_argument("--host", default="127.0.0.1", help="Bind host")
    web.add_argument("--port", type=int, default=8080, help="Bind port")
    web.add_argument("--backend", choices=["onnx", "color"], help="Detector backend override")
    web.add_argument("--model", help="ONNX model path override")
    web.add_argument("--labels", help="Labels file path override")
    web.add_argument("--sample-fps", type=float, help="Video sampling FPS override")

    return parser


def _run_analyze(args) -> int:
    try:
        config = _load_and_apply_overrides(args)
        output = args.output or _default_output_dir(args.video)
        analyzer = VideoAnalyzer(config)
        result = analyzer.analyze(args.video, output)
    except (DetectorError, VideoAnalysisError, FileNotFoundError) as exc:
        print("Ошибка: %s" % exc, file=sys.stderr)
        return 2

    summary = result.get("summary", {})
    print("Анализ завершен.")
    print("Видео: %s" % result.get("video", {}).get("name"))
    print("Отчет: %s" % Path(result.get("output_dir", output)).joinpath("report.html"))
    print("Подтвержденных эпизодов: %s" % summary.get("episode_count", 0))
    if summary.get("violations_found"):
        print("Результат: обнаружены нарушения отсутствия каски.")
    else:
        print("Результат: подтвержденных нарушений не обнаружено.")
    return 0


def _run_web(args) -> int:
    try:
        config = _load_and_apply_overrides(args)
        from .web import serve

        serve(config=config, host=args.host, port=args.port)
        return 0
    except (DetectorError, FileNotFoundError) as exc:
        print("Ошибка: %s" % exc, file=sys.stderr)
        return 2


def _load_and_apply_overrides(args):
    config = load_config(args.config)
    detector = config.setdefault("detector", {})
    video = config.setdefault("video", {})
    if getattr(args, "backend", None):
        detector["backend"] = args.backend
    if getattr(args, "model", None):
        detector["model_path"] = args.model
    if getattr(args, "labels", None):
        detector["labels_path"] = args.labels
    if getattr(args, "sample_fps", None):
        video["sample_fps"] = args.sample_fps
    return config


def _default_output_dir(video_path: str) -> str:
    stem = Path(video_path).stem or "video"
    return str(Path("reports") / stem)
