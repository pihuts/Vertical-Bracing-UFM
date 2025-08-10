import pytest
import math
from steel_lib.calculations import PryingActionCalculator
from steel_lib.data_models import Plate, BoltConfiguration, Connection, BoltGrade, ConnectionComponent, Material
from steel_lib.si_units import si

def test_prying_action_from_design_guide():
    """
    Test case based on AISC Design Guide 29, Example 5.1.
    "Check prying action on bolts at the end plate"
    """
    # 1. Define Materials
    A572_50 = Material(Fy=50 * si.ksi, Fu=65 * si.ksi, E=29000 * si.ksi)
    A36 = Material(Fy=36 * si.ksi, Fu=58 * si.ksi, E=29000 * si.ksi)
    
    plate_material = A572_50
    gusset_material = A36

    # 2. Define Geometry from the design guide
    end_plate = Plate(
        width=8.5 * si.inch,
        length=24.0 * si.inch,
        t=1.0 * si.inch,
        material=plate_material
    )

    gusset = Plate(
        width=8.5 * si.inch,
        length=24.0 * si.inch,
        t=1.0 * si.inch,
        material=gusset_material
    )

    # 3. Define Bolt Configuration
    bolt_config = BoltConfiguration(
        bolt_diameter=0.875 * si.inch,
        bolt_grade=BoltGrade(name="A325-X", Fnt=90 * si.ksi, Fnv=68 * si.ksi),
        n_rows=7,
        n_columns=2,
        row_spacing=5.5 * si.inch,
        column_spacing=3.0 * si.inch,
        edge_distance_horizontal=1.5 * si.inch,
        edge_distance_vertical=1.5 * si.inch,
        angle=math.radians(47.2),
        material=plate_material
    )

    # 4. Define Connection
    connection = Connection(
        member_a=end_plate,
        member_b=gusset,
        connection_type="bolted",
        configuration=bolt_config
    )

    # 5. Instantiate the Calculator
    prying_calculator = PryingActionCalculator(
        member_1=end_plate,
        member_2=gusset,
        connection=connection
    )

    # 6. Calculate the DCR
    # The required tension is now handled internally by the calculator based on hardcoded values
    dcr = prying_calculator.check_dcr(
        debug=True
    )

    # 8. Assertions
    assert dcr < 1.0
