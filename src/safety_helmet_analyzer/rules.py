from typing import Dict, Iterable, List, Sequence, Set

from .domain import Detection, Violation


def detect_helmet_violations(
    detections: Sequence[Detection],
    detector_config: Dict,
    timestamp: float,
) -> List[Violation]:
    person_labels = _labels(detector_config.get("person_labels", []))
    helmet_labels = _labels(detector_config.get("helmet_labels", []))
    no_helmet_labels = _labels(detector_config.get("no_helmet_labels", []))
    flag_missing = bool(detector_config.get("flag_person_without_detected_helmet", True))

    persons = [d for d in detections if d.label_key() in person_labels]
    helmets = [d for d in detections if d.label_key() in helmet_labels]
    no_helmets = [d for d in detections if d.label_key() in no_helmet_labels]

    violations: List[Violation] = []
    matched_no_helmet_indexes: Set[int] = set()

    for person in persons:
        head_zone = person.box.upper_fraction()
        matching_no_helmet = [
            (index, candidate)
            for index, candidate in enumerate(no_helmets)
            if _is_related_to_head_zone(candidate, head_zone)
        ]

        if matching_no_helmet:
            index, candidate = max(matching_no_helmet, key=lambda item: item[1].confidence)
            matched_no_helmet_indexes.add(index)
            violations.append(
                Violation(
                    timestamp=timestamp,
                    confidence=min(1.0, max(person.confidence, candidate.confidence)),
                    reason="explicit_no_helmet",
                    person_box=person.box,
                    evidence_box=candidate.box,
                )
            )
            continue

        if not flag_missing:
            continue

        has_helmet = any(_is_related_to_head_zone(helmet, head_zone) for helmet in helmets)
        if not has_helmet:
            violations.append(
                Violation(
                    timestamp=timestamp,
                    confidence=person.confidence,
                    reason="person_without_detected_helmet",
                    person_box=person.box,
                    evidence_box=head_zone,
                )
            )

    for index, candidate in enumerate(no_helmets):
        if index in matched_no_helmet_indexes:
            continue
        violations.append(
            Violation(
                timestamp=timestamp,
                confidence=candidate.confidence,
                reason="standalone_no_helmet_detection",
                evidence_box=candidate.box,
            )
        )

    return violations


def _labels(values: Iterable[str]) -> Set[str]:
    return {value.strip().lower() for value in values if value.strip()}


def _is_related_to_head_zone(detection: Detection, head_zone) -> bool:
    if head_zone.contains_center_of(detection.box):
        return True
    if head_zone.intersection(detection.box) > 0:
        smaller_area = max(1.0, min(head_zone.area, detection.box.area))
        return head_zone.intersection(detection.box) / smaller_area >= 0.2
    return False
