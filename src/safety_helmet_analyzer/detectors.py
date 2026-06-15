from pathlib import Path
from typing import Dict, List, Optional, Sequence

from .domain import BBox, Detection


class DetectorError(RuntimeError):
    pass


class BaseDetector:
    def detect(self, frame) -> List[Detection]:
        raise NotImplementedError


def create_detector(detector_config: Dict, backend_override: Optional[str] = None) -> BaseDetector:
    backend = (backend_override or detector_config.get("backend") or "onnx").strip().lower()
    if backend == "onnx":
        return OnnxYoloDetector(detector_config)
    if backend == "color":
        return ColorHelmetDetector(detector_config)
    raise DetectorError("Unknown detector backend: %s" % backend)


class OnnxYoloDetector(BaseDetector):
    """YOLO-like ONNX detector using OpenCV DNN."""

    def __init__(self, detector_config: Dict):
        cv2, np = _require_cv2()
        self.cv2 = cv2
        self.np = np
        self.model_path = Path(detector_config.get("model_path", "models/helmet_detector.onnx"))
        if not self.model_path.exists():
            raise DetectorError(
                "ONNX model not found: %s. Put the model into models/ or use --backend color."
                % self.model_path
            )

        self.labels = _load_labels(detector_config.get("labels_path"))
        if not self.labels:
            self.labels = ["person", "helmet", "no_helmet"]

        self.input_size = int(detector_config.get("input_size", 640))
        self.confidence_threshold = float(detector_config.get("confidence_threshold", 0.35))
        self.nms_threshold = float(detector_config.get("nms_threshold", 0.45))
        self.net = cv2.dnn.readNetFromONNX(str(self.model_path))

    def detect(self, frame) -> List[Detection]:
        height, width = frame.shape[:2]
        blob = self.cv2.dnn.blobFromImage(
            frame,
            scalefactor=1.0 / 255.0,
            size=(self.input_size, self.input_size),
            mean=(0, 0, 0),
            swapRB=True,
            crop=False,
        )
        self.net.setInput(blob)
        output = self.net.forward()
        rows = self._normalize_output(output)

        boxes: List[List[int]] = []
        scores: List[float] = []
        class_ids: List[int] = []

        for row in rows:
            parsed = self._parse_row(row, width, height)
            if parsed is None:
                continue
            class_id, score, box = parsed
            boxes.append([int(box.x1), int(box.y1), int(box.width), int(box.height)])
            scores.append(score)
            class_ids.append(class_id)

        if not boxes:
            return []

        indexes = self.cv2.dnn.NMSBoxes(
            boxes,
            scores,
            self.confidence_threshold,
            self.nms_threshold,
        )
        indexes = _flatten_indexes(indexes)

        detections: List[Detection] = []
        for index in indexes:
            x, y, w, h = boxes[index]
            class_id = class_ids[index]
            label = self.labels[class_id] if class_id < len(self.labels) else "class_%d" % class_id
            detections.append(
                Detection(
                    label=label,
                    confidence=float(scores[index]),
                    box=BBox(
                        max(0, x),
                        max(0, y),
                        min(width - 1, x + w),
                        min(height - 1, y + h),
                    ),
                )
            )
        return detections

    def _normalize_output(self, output):
        array = output[0] if isinstance(output, (list, tuple)) else output
        array = self.np.asarray(array)
        if array.ndim == 3:
            array = array[0]
        if array.ndim != 2:
            raise DetectorError("Unsupported ONNX output shape: %s" % (array.shape,))

        expected_values = 4 + len(self.labels)
        if array.shape[0] == expected_values or array.shape[0] == expected_values + 1:
            array = array.T
        elif array.shape[0] < array.shape[1] and array.shape[0] <= 512:
            array = array.T

        return array

    def _parse_row(self, row, frame_width: int, frame_height: int):
        values = row.astype("float32")
        if len(values) < 5:
            return None

        if len(values) == 4 + len(self.labels):
            objectness = 1.0
            class_scores = values[4:]
        else:
            objectness = float(values[4])
            class_scores = values[5:]

        if len(class_scores) == 0:
            return None

        class_id = int(class_scores.argmax())
        score = float(class_scores[class_id]) * objectness
        if score < self.confidence_threshold:
            return None

        cx, cy, bw, bh = [float(v) for v in values[:4]]
        if max(abs(cx), abs(cy), abs(bw), abs(bh)) <= 2.0:
            cx *= self.input_size
            cy *= self.input_size
            bw *= self.input_size
            bh *= self.input_size

        scale_x = float(frame_width) / float(self.input_size)
        scale_y = float(frame_height) / float(self.input_size)
        x1 = (cx - bw / 2.0) * scale_x
        y1 = (cy - bh / 2.0) * scale_y
        x2 = (cx + bw / 2.0) * scale_x
        y2 = (cy + bh / 2.0) * scale_y

        return class_id, score, BBox(x1, y1, x2, y2)


class ColorHelmetDetector(BaseDetector):
    """Experimental detector based on people HOG and bright helmet colors."""

    def __init__(self, detector_config: Dict):
        cv2, np = _require_cv2()
        self.cv2 = cv2
        self.np = np
        self.confidence_threshold = float(detector_config.get("confidence_threshold", 0.35))
        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

    def detect(self, frame) -> List[Detection]:
        people, weights = self.hog.detectMultiScale(
            frame,
            winStride=(8, 8),
            padding=(8, 8),
            scale=1.05,
        )
        detections: List[Detection] = []
        for index, (x, y, w, h) in enumerate(people):
            person_confidence = float(weights[index]) if len(weights) > index else 0.5
            person_confidence = max(0.4, min(0.99, person_confidence))
            person_box = BBox(float(x), float(y), float(x + w), float(y + h))
            detections.append(Detection("person", person_confidence, person_box))

            head_zone = person_box.upper_fraction()
            has_helmet, helmet_confidence = self._head_zone_has_helmet_color(frame, head_zone)
            label = "helmet" if has_helmet else "no_helmet"
            detections.append(Detection(label, helmet_confidence, head_zone))
        return detections

    def _head_zone_has_helmet_color(self, frame, box: BBox):
        x1 = max(0, int(box.x1))
        y1 = max(0, int(box.y1))
        x2 = min(frame.shape[1], int(box.x2))
        y2 = min(frame.shape[0], int(box.y2))
        if x2 <= x1 or y2 <= y1:
            return False, 0.0

        crop = frame[y1:y2, x1:x2]
        hsv = self.cv2.cvtColor(crop, self.cv2.COLOR_BGR2HSV)

        yellow = self.cv2.inRange(hsv, self.np.array([15, 60, 80]), self.np.array([40, 255, 255]))
        orange = self.cv2.inRange(hsv, self.np.array([5, 80, 80]), self.np.array([20, 255, 255]))
        white = self.cv2.inRange(hsv, self.np.array([0, 0, 175]), self.np.array([180, 70, 255]))
        mask = self.cv2.bitwise_or(self.cv2.bitwise_or(yellow, orange), white)

        ratio = float(self.cv2.countNonZero(mask)) / float(max(1, mask.size))
        has_helmet = ratio >= 0.03
        confidence = min(0.95, max(self.confidence_threshold, ratio * 8.0))
        if not has_helmet:
            confidence = max(self.confidence_threshold, 1.0 - ratio * 10.0)
        return has_helmet, confidence


def _load_labels(labels_path: Optional[str]) -> List[str]:
    if not labels_path:
        return []
    path = Path(labels_path)
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as handle:
        return [line.strip() for line in handle.readlines() if line.strip()]


def _flatten_indexes(indexes) -> List[int]:
    if indexes is None:
        return []
    if hasattr(indexes, "flatten"):
        return [int(index) for index in indexes.flatten()]
    flattened: List[int] = []
    for item in indexes:
        if isinstance(item, Sequence):
            flattened.append(int(item[0]))
        else:
            flattened.append(int(item))
    return flattened


def _require_cv2():
    try:
        import cv2
        import numpy as np
    except ImportError as exc:
        raise DetectorError("OpenCV and NumPy are required. Install requirements.txt first.") from exc
    return cv2, np
