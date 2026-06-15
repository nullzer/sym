import json
from pathlib import Path
from typing import Dict, List, Optional

from .aggregation import aggregate_violations
from .detectors import BaseDetector, DetectorError, create_detector
from .domain import Detection, FrameAnalysis, Violation
from .reporting import write_html_report
from .rules import detect_helmet_violations


class VideoAnalysisError(RuntimeError):
    pass


class VideoAnalyzer:
    def __init__(self, config: Dict, detector: Optional[BaseDetector] = None):
        self.config = config
        self.detector = detector or create_detector(config.get("detector", {}))
        self.cv2 = _require_cv2()

    def analyze(self, video_path: str, output_dir: str) -> Dict:
        video = Path(video_path)
        if not video.exists():
            raise VideoAnalysisError("Video file not found: %s" % video)

        output = Path(output_dir)
        evidence_dir = output / "evidence"
        evidence_dir.mkdir(parents=True, exist_ok=True)

        cap = self.cv2.VideoCapture(str(video))
        if not cap.isOpened():
            raise VideoAnalysisError("Cannot open video file: %s" % video)

        source_fps = float(cap.get(self.cv2.CAP_PROP_FPS) or 0.0)
        frame_count = int(cap.get(self.cv2.CAP_PROP_FRAME_COUNT) or 0)
        sample_fps = float(self.config.get("video", {}).get("sample_fps", 2.0))
        sample_interval = _sample_interval(source_fps, sample_fps)

        frames: List[FrameAnalysis] = []
        processed_frames = 0
        frame_index = 0

        try:
            while True:
                ok, frame = cap.read()
                if not ok:
                    break

                if frame_index % sample_interval != 0:
                    frame_index += 1
                    continue

                timestamp = _timestamp_seconds(cap, frame_index, source_fps)
                detections = self.detector.detect(frame)
                violations = detect_helmet_violations(
                    detections,
                    self.config.get("detector", {}),
                    timestamp,
                )
                evidence_path = None
                if violations:
                    evidence_path = self._save_evidence_frame(
                        frame,
                        detections,
                        violations,
                        evidence_dir,
                        frame_index,
                    )

                frames.append(
                    FrameAnalysis(
                        frame_index=frame_index,
                        timestamp=timestamp,
                        detections=detections,
                        violations=violations,
                        evidence_path=evidence_path,
                    )
                )
                processed_frames += 1
                frame_index += 1
        finally:
            cap.release()

        result = self._build_result(
            video=video,
            output=output,
            source_fps=source_fps,
            sample_fps=sample_fps,
            frame_count=frame_count,
            processed_frames=processed_frames,
            frames=frames,
        )
        self._write_json_report(result, output)
        write_html_report(result, output)
        return result

    def _save_evidence_frame(
        self,
        frame,
        detections: List[Detection],
        violations: List[Violation],
        evidence_dir: Path,
        frame_index: int,
    ) -> str:
        annotated = frame.copy()
        for detection in detections:
            color = (0, 180, 0)
            if detection.label_key() in {"no_helmet", "no-hardhat", "head"}:
                color = (0, 0, 220)
            self._draw_box(annotated, detection.box, color, "%s %.2f" % (detection.label, detection.confidence))

        for violation in violations:
            if violation.person_box is not None:
                self._draw_box(annotated, violation.person_box, (0, 0, 255), "VIOLATION")
            if violation.evidence_box is not None:
                self._draw_box(annotated, violation.evidence_box, (0, 128, 255), violation.reason)

        filename = "frame_%08d.jpg" % frame_index
        path = evidence_dir / filename
        self.cv2.imwrite(str(path), annotated)
        return "evidence/%s" % filename

    def _draw_box(self, frame, box, color, label: str) -> None:
        x1, y1, x2, y2 = [int(v) for v in box.to_xyxy()]
        self.cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        y_text = max(15, y1 - 5)
        self.cv2.putText(
            frame,
            label,
            (x1, y_text),
            self.cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            color,
            1,
            self.cv2.LINE_AA,
        )

    def _build_result(
        self,
        video: Path,
        output: Path,
        source_fps: float,
        sample_fps: float,
        frame_count: int,
        processed_frames: int,
        frames: List[FrameAnalysis],
    ) -> Dict:
        violation_config = self.config.get("violations", {})
        episodes = aggregate_violations(
            frames,
            max_gap_seconds=float(violation_config.get("max_gap_seconds", 1.5)),
            min_hits=int(violation_config.get("min_hits", 2)),
            min_duration_seconds=float(violation_config.get("min_duration_seconds", 0.0)),
            max_evidence_frames=int(
                self.config.get("video", {}).get("max_evidence_frames_per_episode", 3)
            ),
        )

        frame_payload = []
        for frame in frames:
            if frame.has_violation:
                frame_payload.append(
                    {
                        "frame_index": frame.frame_index,
                        "timestamp": round(frame.timestamp, 3),
                        "evidence_path": frame.evidence_path,
                        "violations": [violation.to_dict() for violation in frame.violations],
                    }
                )

        return {
            "video": {
                "path": str(video),
                "name": video.name,
                "source_fps": round(source_fps, 3),
                "frame_count": frame_count,
            },
            "settings": {
                "sample_fps": sample_fps,
                "detector_backend": self.config.get("detector", {}).get("backend"),
            },
            "summary": {
                "processed_frames": processed_frames,
                "frames_with_violations": len(frame_payload),
                "violations_found": bool(episodes),
                "episode_count": len(episodes),
            },
            "episodes": [episode.to_dict() for episode in episodes],
            "violation_frames": frame_payload,
            "output_dir": str(output),
        }

    def _write_json_report(self, result: Dict, output: Path) -> None:
        output.mkdir(parents=True, exist_ok=True)
        with (output / "analysis.json").open("w", encoding="utf-8") as handle:
            json.dump(result, handle, ensure_ascii=False, indent=2)


def _sample_interval(source_fps: float, sample_fps: float) -> int:
    if source_fps <= 0.0:
        return 1
    return max(1, int(round(source_fps / max(0.1, sample_fps))))


def _timestamp_seconds(cap, frame_index: int, source_fps: float) -> float:
    msec = float(cap.get(_require_cv2().CAP_PROP_POS_MSEC) or 0.0)
    if msec > 0.0:
        return msec / 1000.0
    if source_fps > 0.0:
        return float(frame_index) / source_fps
    return float(frame_index)


def _require_cv2():
    try:
        import cv2
    except ImportError as exc:
        raise DetectorError("OpenCV is required. Install requirements.txt first.") from exc
    return cv2
