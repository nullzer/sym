from dataclasses import dataclass, field
from typing import List, Optional, Set, Tuple


@dataclass(frozen=True)
class BBox:
    """Bounding box in image coordinates."""

    x1: float
    y1: float
    x2: float
    y2: float

    @property
    def width(self) -> float:
        return max(0.0, self.x2 - self.x1)

    @property
    def height(self) -> float:
        return max(0.0, self.y2 - self.y1)

    @property
    def area(self) -> float:
        return self.width * self.height

    @property
    def center(self) -> Tuple[float, float]:
        return ((self.x1 + self.x2) / 2.0, (self.y1 + self.y2) / 2.0)

    def intersection(self, other: "BBox") -> float:
        x1 = max(self.x1, other.x1)
        y1 = max(self.y1, other.y1)
        x2 = min(self.x2, other.x2)
        y2 = min(self.y2, other.y2)
        return max(0.0, x2 - x1) * max(0.0, y2 - y1)

    def iou(self, other: "BBox") -> float:
        union = self.area + other.area - self.intersection(other)
        if union <= 0.0:
            return 0.0
        return self.intersection(other) / union

    def contains_point(self, x: float, y: float) -> bool:
        return self.x1 <= x <= self.x2 and self.y1 <= y <= self.y2

    def contains_center_of(self, other: "BBox") -> bool:
        x, y = other.center
        return self.contains_point(x, y)

    def upper_fraction(self, fraction: float = 0.45) -> "BBox":
        fraction = min(1.0, max(0.05, fraction))
        return BBox(self.x1, self.y1, self.x2, self.y1 + self.height * fraction)

    def to_xyxy(self) -> List[float]:
        return [round(self.x1, 2), round(self.y1, 2), round(self.x2, 2), round(self.y2, 2)]


@dataclass(frozen=True)
class Detection:
    label: str
    confidence: float
    box: BBox

    def label_key(self) -> str:
        return self.label.strip().lower()

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "confidence": round(float(self.confidence), 4),
            "box": self.box.to_xyxy(),
        }


@dataclass(frozen=True)
class Violation:
    timestamp: float
    confidence: float
    reason: str
    person_box: Optional[BBox] = None
    evidence_box: Optional[BBox] = None

    def to_dict(self) -> dict:
        payload = {
            "timestamp": round(float(self.timestamp), 3),
            "confidence": round(float(self.confidence), 4),
            "reason": self.reason,
        }
        if self.person_box is not None:
            payload["person_box"] = self.person_box.to_xyxy()
        if self.evidence_box is not None:
            payload["evidence_box"] = self.evidence_box.to_xyxy()
        return payload


@dataclass
class FrameAnalysis:
    frame_index: int
    timestamp: float
    detections: List[Detection] = field(default_factory=list)
    violations: List[Violation] = field(default_factory=list)
    evidence_path: Optional[str] = None

    @property
    def has_violation(self) -> bool:
        return bool(self.violations)


@dataclass
class ViolationEpisode:
    start_time: float
    end_time: float
    hit_count: int
    max_confidence: float
    reasons: Set[str] = field(default_factory=set)
    evidence_paths: List[str] = field(default_factory=list)

    @property
    def duration_seconds(self) -> float:
        return max(0.0, self.end_time - self.start_time)

    def to_dict(self) -> dict:
        return {
            "start_time": round(float(self.start_time), 3),
            "end_time": round(float(self.end_time), 3),
            "duration_seconds": round(float(self.duration_seconds), 3),
            "hit_count": int(self.hit_count),
            "max_confidence": round(float(self.max_confidence), 4),
            "reasons": sorted(self.reasons),
            "evidence_paths": list(self.evidence_paths),
        }
