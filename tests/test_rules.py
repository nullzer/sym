import unittest

from safety_helmet_analyzer.domain import BBox, Detection
from safety_helmet_analyzer.rules import detect_helmet_violations


CONFIG = {
    "person_labels": ["person"],
    "helmet_labels": ["helmet"],
    "no_helmet_labels": ["no_helmet"],
    "flag_person_without_detected_helmet": True,
}


class RulesTest(unittest.TestCase):
    def test_person_with_helmet_has_no_violation(self):
        detections = [
            Detection("person", 0.9, BBox(10, 10, 110, 210)),
            Detection("helmet", 0.8, BBox(35, 15, 85, 55)),
        ]

        violations = detect_helmet_violations(detections, CONFIG, timestamp=3.0)

        self.assertEqual(violations, [])

    def test_person_without_helmet_is_violation(self):
        detections = [
            Detection("person", 0.9, BBox(10, 10, 110, 210)),
        ]

        violations = detect_helmet_violations(detections, CONFIG, timestamp=3.0)

        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].reason, "person_without_detected_helmet")

    def test_explicit_no_helmet_detection_is_attached_to_person(self):
        detections = [
            Detection("person", 0.9, BBox(10, 10, 110, 210)),
            Detection("no_helmet", 0.75, BBox(35, 15, 85, 55)),
        ]

        violations = detect_helmet_violations(detections, CONFIG, timestamp=3.0)

        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].reason, "explicit_no_helmet")
        self.assertIsNotNone(violations[0].person_box)


if __name__ == "__main__":
    unittest.main()
