from dataclasses import dataclass
from typing import Dict
import forallpeople as si

@dataclass(frozen=True)
class BoltGrade:
    """Represents the nominal strength properties of a bolt material."""
    name: str      # e.g., "A325"
    Fnt: si.ksi  # Nominal tensile stress
    Fnv: si.ksi  # Nominal shear stress

si.environment('structural', top_level=False)
@dataclass(frozen=True)
class Material:
    """Represents the engineering properties of a steel material."""
    Fy: si.ksi
    Fu: si.ksi
    E: si.ksi
MATERIALS: Dict[str, Material] = {
    "a36": Material(Fy=36.0 * si.ksi, Fu=58.0 * si.ksi, E=29000.0 * si.ksi),
    "a572_gr50": Material(Fy=50.0 * si.ksi, Fu=65.0 * si.ksi, E=29000.0 * si.ksi),
    "a992": Material(Fy=50.0 * si.ksi, Fu=65.0 * si.ksi, E=29000.0 * si.ksi),
}

BOLT_GRADES: Dict[str, BoltGrade] = {
    "a325_n": BoltGrade(name="A325-N", Fnt=90.0 * si.ksi, Fnv=54.0 * si.ksi), # Threads included
    "a325_x": BoltGrade(name="A325-X", Fnt=90.0 * si.ksi, Fnv=68.0 * si.ksi), # Threads excluded
    "a490_n": BoltGrade(name="A490-N", Fnt=113.0 * si.ksi, Fnv=68.0 * si.ksi), # Threads included
    "a490_x": BoltGrade(name="A490-X", Fnt=113.0 * si.ksi, Fnv=84.0 * si.ksi), # Threads excluded
}

WELD_ELECTRODES: Dict[str, si.Physical] = {
    "e60xx": 60.0 * si.ksi,
    "e70xx": 70.0 * si.ksi,
    "e80xx": 80.0 * si.ksi,
}