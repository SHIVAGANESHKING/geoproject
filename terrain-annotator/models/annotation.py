from dataclasses import dataclass, field
from datetime import datetime, timezone

@dataclass
class Annotation:
    """
    Represents a terrain annotation.
    Corresponds to the 'terrain_annotations' table in the database.
    """
    id: int = None
    geom: str = None  # WKT representation of the geometry
    class_name: str = None
    class_id: int = None
    area_sqm: float = 0.0
    perimeter_m: float = 0.0
    elevation_min: float = None
    elevation_max: float = None
    elevation_mean: float = None
    slope_mean: float = None
    annotator: str = "default_user"
    notes: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))