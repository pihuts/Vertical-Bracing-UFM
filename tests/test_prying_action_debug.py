import pytest
import math
from steel_lib.calculations import PryingActionCalculator, BoltShearCalculator
from steel_lib.data_models import (
    Plate, 
    BoltConfiguration, 
    Connection, 
    BoltGrade, 
    ConnectionComponent, 
    Material,
    AppliedLoads,
    DesignLoads,
    LoadMultipliers
)
from steel_lib.si_units import si

@pytest.fixture
def design_loads():
    return DesignLoads(
        Pu=840 * si.kip,
        Vu=50 * si.kip,
        Aub=100 * si.kip
    )

@pytest.fixture
def ufm_multipliers():
    # These values are taken from the AISC Design Guide 29, Example 5.1
    return LoadMultipliers(
        vertical_force_column_interface=12.0/33.4,
        vertical_force_beam_interface=17.5/33.4,
        horizontal_force_column_interface=7.0/33.4,
        horizontal_force_beam_interface=10.7/33.4
    )

@pytest.fixture
def applied_loads(design_loads, ufm_multipliers):
    return AppliedLoads.from_ufm(design_loads, ufm_multipliers)

def test_prying_action_from_design_guide(applied_loads):
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

    # 6. Print debug values
    print(f"\n--- DEBUG: Prying Action ---")
    print(f"  Inputs:")
    print(f"    Required Tension per Bolt (T_req)  : {prying_calculator.tension_force / prying_calculator.n_bolts:.3f}")
    print(f"    Plate Width (w)                    : {prying_calculator.width:.3f}")
    print(f"    Plate Thickness (t)                : {prying_calculator.t:.3f}")
    print(f"    Plate Fu                           : {prying_calculator.plate_Fu:.3f}")
    print(f"    Gusset Thickness                   : {prying_calculator.gusset_thickness:.3f}")
    print(f"    Bolt Diameter                      : {prying_calculator.bolt_diameter:.3f}")
    print(f"    Bolt Fnt                           : {prying_calculator.bolt_grade.Fnt:.3f}")
    print(f"    Tributary Length (p)               : {prying_calculator.p:.3f}")
    print(f"    Gage (g)                           : {prying_calculator.g:.3f}")
    print(f"  Calculations:")
    print(f"    Distance 'a'                       : {prying_calculator.a:.3f}")
    print(f"    Distance 'b'                       : {prying_calculator.b:.3f}")
    print(f"    Effective Hole Diameter (d')       : {prying_calculator.d_prime:.3f}")
    print(f"    b'                                 : {prying_calculator.b_prime:.3f}")
    print(f"    a'                                 : {prying_calculator.a_prime:.3f}")
    print(f"    rho (b'/a')                        : {prying_calculator.p_:.4f}")
    print(f"    delta (1 - d'/p)                   : {prying_calculator.delta:.4f}")
    print(f"    Bolt Area (Ab)                     : {prying_calculator.bolt_area:.3f}")
    
    Fnt_modified = BoltShearCalculator(connection).calculate_capacity_fnt_modified(prying_calculator.shear_force)
    B = Fnt_modified * prying_calculator.bolt_area
    print(f"    Bolt Nominal Strength (B)          : {B:.3f}")
    
    t_req = prying_calculator._calculate_t_req()
    print(f"    Required Thickness (t_req)         : {float(t_req.to('inch')):.3f} inch")
    
    alpha_prime = prying_calculator._calculate_alpha_prime()
    print(f"    Alpha Prime (alpha')               : {float(alpha_prime):.4f}")
    
    Q = prying_calculator.calculate_Q()
    print(f"    Prying Force Factor (Q)            : {Q:.4f}")
    
    available_strength = prying_calculator.calculate_bolt_tension_with_prying()
    print(f"    Available Bolt Strength with Prying (B*Q): {available_strength:.3f}")
    
    design_capacity = 0.75 * available_strength
    print(f"  Output:")
    print(f"                                         --------------------")
    print(f"    Available Design Strength (phi*B*Q): {design_capacity:.3f}")
    print(f"--- END DEBUG: Prying Action ---\n")

    # 7. Calculate the DCR
    dcr = prying_calculator.check_dcr()

    # 8. Assertions
    assert dcr < 1.0