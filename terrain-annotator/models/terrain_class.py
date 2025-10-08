from dataclasses import dataclass

@dataclass
class TerrainClass:
    """
    Represents a terrain classification.
    Corresponds to the 'terrain_classes' table in the database.
    """
    id: int
    class_name: str
    class_id: int
    color: str
    description: str = ""