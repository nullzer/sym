import copy
import json
from pathlib import Path
from typing import Any, Dict, Optional


DEFAULT_CONFIG: Dict[str, Any] = {
    "video": {
        "sample_fps": 2.0,
        "max_evidence_frames_per_episode": 3,
    },
    "detector": {
        "backend": "onnx",
        "model_path": "models/helmet_detector.onnx",
        "labels_path": "models/labels.txt",
        "input_size": 640,
        "confidence_threshold": 0.35,
        "nms_threshold": 0.45,
        "person_labels": ["person", "worker"],
        "helmet_labels": ["helmet", "hardhat", "hard_hat", "safety_helmet"],
        "no_helmet_labels": ["no_helmet", "no-hardhat", "head"],
        "flag_person_without_detected_helmet": True,
    },
    "violations": {
        "max_gap_seconds": 1.5,
        "min_hits": 2,
        "min_duration_seconds": 0.0,
    },
}


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    config = copy.deepcopy(DEFAULT_CONFIG)
    candidate = Path(config_path) if config_path else Path("config/default.json")

    if candidate.exists():
        with candidate.open("r", encoding="utf-8") as handle:
            file_config = json.load(handle)
        config = deep_merge(config, file_config)
    elif config_path:
        raise FileNotFoundError("Config file not found: %s" % candidate)

    return config


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    result = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result
