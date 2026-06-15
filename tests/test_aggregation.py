import unittest

from safety_helmet_analyzer.aggregation import aggregate_violations
from safety_helmet_analyzer.domain import BBox, FrameAnalysis, Violation


class AggregationTest(unittest.TestCase):
    def test_groups_adjacent_violation_frames(self):
        frames = [
            _frame(10, 1.0, True, "evidence/a.jpg"),
            _frame(20, 1.5, True, "evidence/b.jpg"),
            _frame(30, 2.0, True, "evidence/c.jpg"),
        ]

        episodes = aggregate_violations(
            frames,
            max_gap_seconds=1.0,
            min_hits=2,
            min_duration_seconds=0.0,
            max_evidence_frames=2,
        )

        self.assertEqual(len(episodes), 1)
        self.assertEqual(episodes[0].start_time, 1.0)
        self.assertEqual(episodes[0].end_time, 2.0)
        self.assertEqual(episodes[0].hit_count, 3)
        self.assertEqual(episodes[0].evidence_paths, ["evidence/a.jpg", "evidence/b.jpg"])

    def test_splits_episode_when_gap_is_too_large(self):
        frames = [
            _frame(10, 1.0, True),
            _frame(20, 1.5, True),
            _frame(90, 5.0, True),
            _frame(100, 5.4, True),
        ]

        episodes = aggregate_violations(
            frames,
            max_gap_seconds=1.0,
            min_hits=2,
            min_duration_seconds=0.0,
            max_evidence_frames=3,
        )

        self.assertEqual(len(episodes), 2)
        self.assertEqual(episodes[0].start_time, 1.0)
        self.assertEqual(episodes[1].start_time, 5.0)

    def test_filters_short_single_frame_noise(self):
        frames = [
            _frame(10, 1.0, True),
            _frame(20, 2.0, False),
        ]

        episodes = aggregate_violations(
            frames,
            max_gap_seconds=1.0,
            min_hits=2,
            min_duration_seconds=0.0,
            max_evidence_frames=3,
        )

        self.assertEqual(episodes, [])


def _frame(index, timestamp, has_violation, evidence_path=None):
    violations = []
    if has_violation:
        violations = [
            Violation(
                timestamp=timestamp,
                confidence=0.8,
                reason="person_without_detected_helmet",
                person_box=BBox(0, 0, 100, 200),
            )
        ]
    return FrameAnalysis(
        frame_index=index,
        timestamp=timestamp,
        violations=violations,
        evidence_path=evidence_path,
    )


if __name__ == "__main__":
    unittest.main()
