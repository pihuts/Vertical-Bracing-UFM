from typing import Dict
import forallpeople as si
from .data_models import Material, BoltGrade, WeldElectrode

si.environment('structural', top_level=False)

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

WELD_ELECTRODES: Dict[str, WeldElectrode] = {
    "e60xx": WeldElectrode(Fexx=60.0 * si.ksi),
    "e70xx": WeldElectrode(Fexx=70.0 * si.ksi),
    "e80xx": WeldElectrode(Fexx=80.0 * si.ksi),
}