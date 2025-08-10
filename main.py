import math
import traceback
from steel_lib.si_units import si
from steelpy import aisc

from steel_lib.data_models import (
    Plate,
    ConnectionFactory,
    ConnectionComponent,
    DesignLoads,
    AppliedLoads,
)
from steel_lib.materials import MATERIALS, BOLT_GRADES, WELD_ELECTRODES
from steel_lib.member_factory import MemberFactory
from steel_lib.calculations import (
    BoltShearCalculator,
    BlockShearCalculator,
    ConnectionCapacityCalculator,
    TensileYieldingCalculator,
    TensileRuptureCalculator,
    TensileYieldWhitmore,
    CompressionBucklingCalculator,
    UFMCalculator,
    PlateTensileYieldingCalculator,
    WebLocalYieldingCalculator,
    WebLocalCrippingCalculator,
    ShearYieldingCalculator,
    PryingActionCalculator,
)

# --- 1. Define Members, Connections, and Initial Loads ---

try:
    # Create and enrich steelpy members using the consolidated factory
    beam = MemberFactory.create_steelpy_member(
        section_class=aisc.W_shapes,
        section_name="W21X83",
        material=MATERIALS["a992"],
        shape_type="W"
    )

    support = MemberFactory.create_steelpy_member(
        section_class=aisc.W_shapes,
        section_name="W14X90",
        material=MATERIALS["a992"],
        shape_type="W"
    )

    # End Plate for Column Connection
    end_plate_column = Plate(
        t=5/8 * si.inch,
        material=MATERIALS["a572_gr50"],
        width=10 * si.inch,
    )

    # Gusset Plate for Bracing Connection
    gusset_plate_bracing = Plate(
        t=1 * si.inch,
        material=MATERIALS["a572_gr50"],
        clipping=3/4 * si.inch,
    )

    # --- Define Connection Configurations ---
    # A dummy member for the other side of the bracing connection
    dummy_member = Plate(t=1 * si.inch, material=MATERIALS["a572_gr50"])

    bracing_connection = ConnectionFactory.create_bolted_connection(
        member_a=gusset_plate_bracing,
        member_b=dummy_member,
        component_a=ConnectionComponent.TOTAL,
        row_spacing=3.0 * si.inch,
        column_spacing=3.0 * si.inch,
        n_rows=2,
        n_columns=7,
        edge_distance_vertical=2 * si.inch,
        edge_distance_horizontal=1.5 * si.inch,
        bolt_diameter=7/8 * si.inch,
        bolt_grade=BOLT_GRADES["a325_x"],
        material=MATERIALS["a572_gr50"],
        angle=47.2 * math.pi / 180
    )

    column_endplate_connection = ConnectionFactory.create_bolted_connection(
        member_a=end_plate_column,
        member_b=support,
        component_b=ConnectionComponent.FLANGE,
        row_spacing=5.5 * si.inch,
        column_spacing=3.0 * si.inch,
        n_rows=7,
        n_columns=2,
        edge_distance_vertical=3 * si.inch,
        edge_distance_horizontal=1.5 * si.inch,
        bolt_diameter=7/8 * si.inch,
        bolt_grade=BOLT_GRADES["a325_x"],
        material=MATERIALS["a572_gr50"],
    )
    endpl_gusset_bolted_connection = ConnectionFactory.create_bolted_connection(
        member_a=end_plate_column,
        member_b=gusset_plate_bracing,
        row_spacing=3.0 * si.inch,
        column_spacing=3.0 * si.inch,
        n_rows=2,
        n_columns=7,
        edge_distance_vertical=3 * si.inch,
        edge_distance_horizontal=1.5 * si.inch,
        bolt_diameter=7/8 * si.inch,
        bolt_grade=BOLT_GRADES["a325_x"],
        material=MATERIALS["a572_gr50"],
    )
    # --- Define Initial Design Loads (from Design Guide Example 5.1) ---
    initial_loads = DesignLoads(
        Pu=840 * si.kip,
        Vu=50.0 * si.kip,
        Aub=100 * si.kip
    )

    # --- 2. Perform Calculations ---
    print("--- Starting Steel Connection Design Verification ---")

    # a) Calculate UFM Geometric Multipliers
    print("\n1. Calculating UFM Geometric Multipliers...")
    ufm_checker = UFMCalculator(
        beam=beam,
        support=support,
        endplate=end_plate_column,
        connection=column_endplate_connection
    )
    final_multipliers = ufm_checker.get_loads_multipliers()
    print(f"   Calculated Load Multipliers: {final_multipliers}")

    # b) Calculate Applied Loads using the Factory
    print("\n2. Calculating Applied Interface Forces via Factory...")
    applied_loads = AppliedLoads.from_ufm(initial_loads, final_multipliers)
    print(f"   Brace Axial Load: {applied_loads.initial_brace_load:.2f}")
    print(f"   Gusset-to-Column Shear (Vuc): {applied_loads.gusset_to_column_shear:.2f}")
    print(f"   Gusset-to-Column Normal (Huc): {applied_loads.gusset_to_column_normal:.2f}")
    print(f"   Gusset-to-Beam Shear (Hub): {applied_loads.gusset_to_beam_shear:.2f}")
    print(f"   Gusset-to-Beam Normal (Vub): {applied_loads.gusset_to_beam_normal:.2f}")

    # c) Set Gusset Plate Dimensions
    final_dimensions = ufm_checker.get_dimensions()
    gusset_plate_bracing.set_dimensions(final_dimensions)
    print(f"\n3. Set Gusset Plate Dimensions: {final_dimensions}")

    # Create weld connections now that gusset dimensions are known
    beam_gusset_connection = ConnectionFactory.create_welded_connection(
        member_a=gusset_plate_bracing,
        member_b=beam,
        component_a=ConnectionComponent.LENGTH,
        component_b=ConnectionComponent.WEB,
        weld_size=0.3125 * si.inch,
        length=gusset_plate_bracing.length,
        electrode=WELD_ELECTRODES["e70xx"]
    )
    endpl_gusset_connection = ConnectionFactory.create_welded_connection(
        member_a=end_plate_column,
        member_b=gusset_plate_bracing,
        component_a=ConnectionComponent.WIDTH,
        weld_size=0.3125 * si.inch,
        length=gusset_plate_bracing.width,
        electrode=WELD_ELECTRODES["e70xx"]
    )

    # --- 3. Perform Demand vs. Capacity (DCR) Checks ---
    print("\n--- Performing DCR Checks ---")

    # a) Whitmore Section Tensile Yielding
    print("\nCHECK: Whitmore Section Tensile Yielding...")
    whitmore_checker = TensileYieldWhitmore(bracing_connection.member_a, bracing_connection)
    dcr_whitmore = whitmore_checker.check_dcr(demand_force=applied_loads.initial_brace_load)
    print(f"   DCR = {dcr_whitmore:.2f} {'(OK)' if dcr_whitmore <= 1.0 else '(FAIL)'}")

    # b) Compression Buckling
    print("\nCHECK: Gusset Compression Buckling...")
    comp_buckling_checker = CompressionBucklingCalculator(bracing_connection.member_a, bracing_connection)
    try:
        dcr_comp_buckling = comp_buckling_checker.check_dcr(demand_force=applied_loads.initial_brace_load)
        print(f"   DCR = {dcr_comp_buckling:.2f} {'(OK)' if dcr_comp_buckling <= 1.0 else '(FAIL)'}")
    except ValueError as e:
        print(f"   CHECK FAILED: {e}")

    # c) Gusset-to-Beam Interface: Shear Yielding
    print("\nCHECK: Gusset-to-Beam Shear Yielding...")
    gusset_beam_shear_checker = ShearYieldingCalculator(beam_gusset_connection.member_a, beam_gusset_connection)
    dcr_gusset_beam_shear = gusset_beam_shear_checker.check_dcr(demand_force=applied_loads.gusset_to_beam_shear)
    print(f"   DCR = {dcr_gusset_beam_shear:.2f} {'(OK)' if dcr_gusset_beam_shear <= 1.0 else '(FAIL)'}")

    # d) Gusset-to-Beam Interface: Tensile Yielding (Normal Force)
    print("\nCHECK: Gusset-to-Beam Tensile Yielding...")
    gusset_beam_tensile_checker = PlateTensileYieldingCalculator(beam_gusset_connection.member_a)
    # Note: The capacity is calculated along the horizontal length of the plate here
    dcr_gusset_beam_tensile = gusset_beam_tensile_checker.check_dcr_horizontal(demand_force=applied_loads.gusset_to_beam_normal)
    print(f"   DCR = {dcr_gusset_beam_tensile:.2f} {'(OK)' if dcr_gusset_beam_tensile <= 1.0 else '(FAIL)'}")

    # e) Beam Web Local Yielding
    print("\nCHECK: Beam Web Local Yielding...")
    web_yield_checker = WebLocalYieldingCalculator(beam_gusset_connection.member_b, beam_gusset_connection, end_plate_column)
    dcr_web_yield = web_yield_checker.check_dcr(demand_force=applied_loads.gusset_to_beam_normal)
    print(f"   DCR = {dcr_web_yield:.2f} {'(OK)' if dcr_web_yield <= 1.0 else '(FAIL)'}")

    # f) Beam Web Local Crippling
    print("\nCHECK: Beam Web Local Crippling...")
    web_crippling_checker = WebLocalCrippingCalculator(beam_gusset_connection.member_b, beam_gusset_connection, end_plate_column)
    dcr_web_crippling = web_crippling_checker.check_dcr(demand_force=applied_loads.gusset_to_beam_normal)
    print(f"   DCR = {dcr_web_crippling:.2f} {'(OK)' if dcr_web_crippling <= 1.0 else '(FAIL)'}")

    # g) Gusset-to-Column Interface: Bolt Shear
    print("\nCHECK: Gusset-to-Column Bolt Shear...")
    bolt_shear_checker = BoltShearCalculator(column_endplate_connection)
    # Check against the shear force component on the column interface
    dcr_bolt_shear = bolt_shear_checker.check_dcr_fnv(
        demand_force=applied_loads.gusset_to_column_shear / (column_endplate_connection.configuration.n_rows * column_endplate_connection.configuration.n_columns),
        number_of_shear_planes=1
    )
    bolt_modified_fnt = bolt_shear_checker.calculate_capacity_fnt_modified(
        demand_force_shear=302 * si.kip,
        debug=True
    )
    print(f"   DCR (per bolt) = {dcr_bolt_shear:.2f} {'(OK)' if dcr_bolt_shear <= 1.0 else '(FAIL)'}")

    # # h) Gusset-to-Column Interface: Prying Action
    # print("\nCHECK: Gusset-to-Column Prying Action...")
    # prying_checker = PryingActionCalculator(end_plate_column, column_endplate_connection)
    # # Check against the normal force component on the column interface
    # tension_per_bolt = applied_loads.gusset_to_column_normal / (column_endplate_connection.configuration.n_rows * column_endplate_connection.configuration.n_columns)
    # dcr_prying = prying_checker.check_dcr(required_tension_per_bolt=tension_per_bolt, debug=True)
    # print(f"   DCR (per bolt) = {dcr_prying:.2f} {'(OK)' if dcr_prying <= 1.0 else '(FAIL)'}")
    print("\n--- All DCR Checks Completed ---")
    asdd = PryingActionCalculator(end_plate_column, gusset_plate_bracing,column_endplate_connection)
    asdsad = asdd.check_dcr( debug=True)

    asdaff = ConnectionCapacityCalculator(column_endplate_connection.member_a,column_endplate_connection,"Axial")
    asdaff.calculate_capacity(number_of_shear_planes=1, debug=True)

    # print("\n\nScript finished successfully.")

except Exception as e:
    print("\n--- SCRIPT FAILED WITH AN ERROR ---")
    print(f"Error Type: {type(e).__name__}")
    print(f"Error Message: {e}")
    print("Traceback:")
    traceback.print_exc()