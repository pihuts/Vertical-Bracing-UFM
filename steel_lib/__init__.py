# This file makes the `steel_lib` directory a Python package.
from .debugging import DebugLogger

# Plate generator imports
from .plate_generator import (
    generate_plate_configurations,
    generate_shear_plates,
    generate_flange_plates,
    generate_stiffener_plates,
    generate_gusset_plates,
    get_plate_mapping_info,
    PLATE_TYPE_MAP,
    PLATE_GRADE_MAP,
    STANDARD_PLATE_THICKNESSES
)

# Weld generator imports
from .weld_generator import (
    generate_weld_configurations,
    generate_fillet_welds,
    generate_groove_welds,
    generate_plug_slot_welds,
    get_weld_mapping_info,
    calculate_weld_length_required,
    WELD_TYPE_MAP,
    ELECTRODE_MAP,
    ELECTRODE_PROPERTIES,
    STANDARD_FILLET_SIZES,
    WELD_POSITION_MAP
)