"""
core/clip_model.py
Simple data class representing a clip project.
"""
from dataclasses import dataclass, field
from typing import Optional
import uuid


@dataclass
class Clip:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    source_path: str = ""
    in_frame: int = 0          # start frame (inclusive)
    out_frame: int = 0         # end frame (inclusive)
    fps: float = 30.0
    label: str = ""
    export_preset: str = "TikTok / Shorts (9:16)"
    output_path: Optional[str] = None

    @property
    def in_seconds(self) -> float:
        return self.in_frame / self.fps if self.fps else 0.0

    @property
    def out_seconds(self) -> float:
        return self.out_frame / self.fps if self.fps else 0.0

    @property
    def duration_seconds(self) -> float:
        return max(0.0, self.out_seconds - self.in_seconds)

    @property
    def duration_str(self) -> str:
        d = self.duration_seconds
        m = int(d // 60)
        s = d % 60
        return f"{m}:{s:05.2f}"

    def is_valid(self) -> bool:
        return (
            bool(self.source_path)
            and self.out_frame > self.in_frame
            and self.duration_seconds >= 0.5
        )

    def display_name(self) -> str:
        if self.label:
            return self.label
        return f"Clip {self.id}"
