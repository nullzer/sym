from typing import Iterable, List, Optional

from .domain import FrameAnalysis, ViolationEpisode


def aggregate_violations(
    frames: Iterable[FrameAnalysis],
    max_gap_seconds: float,
    min_hits: int,
    min_duration_seconds: float,
    max_evidence_frames: int,
) -> List[ViolationEpisode]:
    """Group adjacent violation frames into stable violation episodes."""

    episodes: List[ViolationEpisode] = []
    current: Optional[ViolationEpisode] = None
    last_timestamp: Optional[float] = None

    for frame in sorted(frames, key=lambda item: item.timestamp):
        if not frame.has_violation:
            continue

        frame_confidence = max(v.confidence for v in frame.violations)
        frame_reasons = {v.reason for v in frame.violations}
        should_start = (
            current is None
            or last_timestamp is None
            or frame.timestamp - last_timestamp > max_gap_seconds
        )

        if should_start:
            _append_if_valid(episodes, current, min_hits, min_duration_seconds)
            current = ViolationEpisode(
                start_time=frame.timestamp,
                end_time=frame.timestamp,
                hit_count=1,
                max_confidence=frame_confidence,
                reasons=set(frame_reasons),
                evidence_paths=[],
            )
        else:
            current.end_time = frame.timestamp
            current.hit_count += 1
            current.max_confidence = max(current.max_confidence, frame_confidence)
            current.reasons.update(frame_reasons)

        if (
            current is not None
            and frame.evidence_path
            and len(current.evidence_paths) < max_evidence_frames
        ):
            current.evidence_paths.append(frame.evidence_path)

        last_timestamp = frame.timestamp

    _append_if_valid(episodes, current, min_hits, min_duration_seconds)
    return episodes


def _append_if_valid(
    episodes: List[ViolationEpisode],
    episode: Optional[ViolationEpisode],
    min_hits: int,
    min_duration_seconds: float,
) -> None:
    if episode is None:
        return
    if episode.hit_count < min_hits:
        return
    if episode.duration_seconds < min_duration_seconds:
        return
    episodes.append(episode)
