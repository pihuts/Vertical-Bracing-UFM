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

    bracing = MemberFactory.create_steelpy_member(
        section_class=aisc.L_shapes,
        section_name="L8X6X1",
        material=MATERIALS["a36"],
        shape_type="L",
        loading_condition=2,  # Assuming this is a bracing member
    )

    # End Plate for Column Connection
    end_plate_column = Plate(
        t=1 * si.inch,
        material=MATERIALS["a572_gr50"],
        width=10 * si.inch,
    )
    

    # Gusset Plate for Bracing Connection
    gusset_plate = Plate(
        t=1 * si.inch,
        material=MATERIALS["a572_gr50"],
        clipping=3/4 * si.inch,
    )
    brace_gusset_connection = ConnectionFactory.create_bolted_connection(
        member_a=bracing,
        member_b=gusset_plate,
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

    endpl_gusset_connection = ConnectionFactory.create_bolted_connection(
        member_a=end_plate_column,
        member_b=support,
        component_a=ConnectionComponent.TOTAL,
        component_b=ConnectionComponent.TOTAL,
        row_spacing=3.0 * si.inch,
        column_spacing=3.0 * si.inch,
        n_rows=2,
        n_columns=7,
        edge_distance_vertical=3 * si.inch,
        edge_distance_horizontal=3 * si.inch,
        bolt_diameter=7/8 * si.inch,
        bolt_grade=BOLT_GRADES["a325_x"],
        material=MATERIALS["a572_gr50"],
        angle=47.2 * math.pi / 180
    )

    test_1 = BoltShearCalculator(
        connection=brace_gusset_connection)
    test_1.calculate_capacity_fnt(1,debug=True)
    test_1.calculate_capacity_fnv(2,debug=True)
    test_1_yield = TensileYieldingCalculator(endpoint=brace_gusset_connection.member_a, connection=brace_gusset_connection)
    test_1_yield.calculate_capacity(debug=True)
    test_1_trupture = TensileRuptureCalculator(endpoint=brace_gusset_connection.member_a, connection=brace_gusset_connection)
    test_1_trupture.calculate_capacity(debug=True)
    test_1_blockshear = BlockShearCalculator(endpoint = brace_gusset_connection.member_a, connection=brace_gusset_connection,loading_orientation="Axial",loading_condition=2)
    test_1_blockshear.calculate_capacity(debug=True)
    test_1_blockshear_gussetplate = BlockShearCalculator(endpoint = brace_gusset_connection.member_b, connection=brace_gusset_connection,loading_orientation="Axial")
    test_1_blockshear_gussetplate.calculate_capacity(debug=True)
    test_1_connection_strength = ConnectionCapacityCalculator(endpoint=brace_gusset_connection.member_b, connection=brace_gusset_connection,loading_orientation="Axial")
    test_1_connection_strength.calculate_capacity(debug=True,number_of_shear_planes=2)
    test_1_whitmore = TensileYieldWhitmore(endpoint=brace_gusset_connection.member_b, connection=brace_gusset_connection)
    test_1_whitmore.calculate_capacity(debug=True)
    test_1_compression = CompressionBucklingCalculator(endpoint=brace_gusset_connection.member_b, connection=brace_gusset_connection)#this requires a little update on hardcoded parts
    test_1_compression.calculate_capacity(debug=True)
    test_2_ufm = UFMCalculator(
        beam=beam,
        support=support,
        endplate=end_plate_column,
        connection=endpl_gusset_connection
    )
    dim_ufm = test_2_ufm.get_dimensions(debug = True)
    final_multipliers = test_2_ufm.get_loads_multipliers(debug = True)
    gusset_plate.set_dimensions(dim_ufm)
    beam_gusset_connection = ConnectionFactory.create_welded_connection(
        member_a=gusset_plate,
        member_b=beam,
        component_a=ConnectionComponent.LENGTH,
        component_b=ConnectionComponent.WEB,
        weld_size=0.3125 * si.inch,
        length=gusset_plate.length,
        electrode=WELD_ELECTRODES["e70xx"]
    )
    initial_loads = DesignLoads(
        Pu=840 * si.kip,
        Vu=50.0 * si.kip,
        Aub=100 * si.kip
    )
    applied_loads = AppliedLoads.from_ufm(initial_loads, final_multipliers)
    print(applied_loads)
    test_2_shear_yielding = ShearYieldingCalculator(endpoint=beam_gusset_connection.member_a, connection=beam_gusset_connection)
    test_2_shear_yielding.calculate_capacity(debug=True)
    test_2_plate_yielding = PlateTensileYieldingCalculator(endpoint=beam_gusset_connection.member_a)
    test_2_plate_yielding.calculate_capacity_horizontal(debug=True)
    test_2_plate_yielding.calculate_capacity_vertical(debug=True)

    test_3_web_local_yield = WebLocalYieldingCalculator(endpoint = beam_gusset_connection.member_b, connection = beam_gusset_connection, end_plate=end_plate_column)
    test_3_web_local_yield.calculate_capacity(debug=True)
    test_3_web_local_crippling = WebLocalCrippingCalculator(endpoint = beam_gusset_connection.member_b, connection = beam_gusset_connection, end_plate=end_plate_column)
    test_3_web_local_crippling.calculate_capacity(debug=True)

    # Gusset to Column Connection
    test_4_Fnt_modified = BoltShearCalculator(endpl_gusset_connection)
    test_4_Fnt_modified.calculate_capacity_fnt_modified(applied_loads.gusset_to_column_normal,debug=True) # find a better way to visualize the loads 

    

    print(applied_loads)
    # test_3_web_local_yield.calculate_capacity(debug=True)









except Exception as e:
    print("\n--- SCRIPT FAILED WITH AN ERROR ---")
    print(f"Error Type: {type(e).__name__}")
    print(f"Error Message: {e}")
    print("Traceback:")
    traceback.print_exc()