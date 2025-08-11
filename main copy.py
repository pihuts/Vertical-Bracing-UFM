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
    AdmissableDistortionForces,
    WeldCalculator
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
        t=5/8 * si.inch,
        material=MATERIALS["a572_gr50"],
        width=10 * si.inch,
    )
    end_plate_beam = Plate(
        t=3/4 * si.inch,
        material=MATERIALS["a572_gr50"],
        width=10 * si.inch,
        length = beam.d + 1 * si.inch,  # Assuming the end plate length is equal to the beam depth plus some extra
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
        member_b=gusset_plate,
        component_a=ConnectionComponent.TOTAL,
        component_b=ConnectionComponent.TOTAL,
        row_spacing=5.50 * si.inch,
        column_spacing=3.0 * si.inch,
        n_rows=2,
        n_columns=7,
        edge_distance_vertical=1.75 * si.inch,
        edge_distance_horizontal=3 * si.inch,
        bolt_diameter=7/8 * si.inch,
        bolt_grade=BOLT_GRADES["a325_x"],
        material=MATERIALS["a572_gr50"],
        angle=47.2 * math.pi / 180
    )
    endpl_column_connection = ConnectionFactory.create_bolted_connection(
        member_a=end_plate_column,
        member_b=support,
        component_a=ConnectionComponent.TOTAL,
        component_b=ConnectionComponent.TOTAL,
        row_spacing=5.50 * si.inch,
        column_spacing=3.0 * si.inch,
        n_rows=2,
        n_columns=7,
        edge_distance_vertical=1.75 * si.inch,
        edge_distance_horizontal=1.75 * si.inch,
        bolt_diameter=7/8 * si.inch,
        bolt_grade=BOLT_GRADES["a325_x"],
        material=MATERIALS["a572_gr50"],
        angle=47.2 * math.pi / 180
    )

    beam_column_connection = ConnectionFactory.create_bolted_connection(
        member_a=beam,
        member_b=end_plate_beam,
        component_a=ConnectionComponent.TOTAL,
        component_b=ConnectionComponent.TOTAL,
        row_spacing=5.5 * si.inch,
        column_spacing=3.0 * si.inch,
        n_rows=2,
        n_columns=6,
        edge_distance_vertical=1.75 * si.inch,
        edge_distance_horizontal=end_plate_beam.length - (6*3*si.inch),
        bolt_diameter=7/8 * si.inch,
        bolt_grade=BOLT_GRADES["a490_x"],
        material=MATERIALS["a572_gr50"],
        angle=47.2 * math.pi / 180
    )
    beam_column_connection1 = ConnectionFactory.create_bolted_connection(
        member_a=beam,
        member_b=support,
        component_a=ConnectionComponent.WEB,
        component_b=ConnectionComponent.FLANGE,
        row_spacing=5.5 * si.inch,
        column_spacing=3.0 * si.inch,
        n_rows=2,
        n_columns=6,
        edge_distance_vertical=1.75 * si.inch,
        edge_distance_horizontal=end_plate_beam.length - (6*3*si.inch),
        bolt_diameter=7/8 * si.inch,
        bolt_grade=BOLT_GRADES["a490_x"],
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
        length=gusset_plate.length - gusset_plate.clipping,
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

    test_4_prying = PryingActionCalculator(
        member_1=end_plate_column,
        member_2= gusset_plate,
        connection=endpl_gusset_connection,
    )
    test_4_prying.check_dcr(debug=True)

    print(applied_loads)
    # print(BoltShearCalculator(endpl_gusset_connection).calculate_capacity_fnt_modified(302 * si.kip,debug=True)* 0.601 *si.inch**2)   # Example of how to use the modified shear capacity
    # test_3_web_local_yield.calculate_capacity(debug=True)
    test_4_connection_capacity = ConnectionCapacityCalculator(
        endpoint=endpl_gusset_connection.member_a,
        connection=endpl_gusset_connection,
        loading_orientation="Axial",
        

    )
    test_4_connection_capacity.calculate_capacity(debug=True,number_of_shear_planes=2)
    test_4_blockshear = BlockShearCalculator(endpoint = endpl_column_connection.member_a, connection=endpl_column_connection,loading_orientation="Axial")
    test_4_blockshear.calculate_capacity(debug=True)
    test_4_prying = PryingActionCalculator(
        member_1=support,
        member_2=end_plate_column,
        connection=endpl_column_connection,
    )
    test_4_prying.check_dcr(debug=True),

    test_5_adf = AdmissableDistortionForces(beam=beam,support=support,brace = bracing, loads=initial_loads,connection=endpl_column_connection,lb = 25*si.ft)
    test_5_adf.calculate_admissible_distortion_forces(debug=True)
    beam_column_transferred_forces = test_5_adf.from_adf(test_2_ufm,applied_loads,debug=True)
    test_5_bolt_shear = BoltShearCalculator(
        connection=beam_column_connection)
    test_5_bolt_shear.calculate_capacity_fnt_modified(beam_column_transferred_forces.shear,debug=True)
    test_5_prying_endpl = PryingActionCalculator(
        member_1=end_plate_beam,
        member_2=beam,
        connection=beam_column_connection,
    )
    test_5_prying_endpl.check_dcr(debug=True)
    test_5_prying_column = PryingActionCalculator(
        member_1=support,
        member_2=end_plate_column,
        connection=beam_column_connection,
    )
    test_5_prying_column.check_dcr(debug=True)
    test_5_bearing = ConnectionCapacityCalculator(
        endpoint=beam_column_connection.member_b,connection=beam_column_connection,
        loading_orientation="Axial",)
    test_5_bearing.calculate_capacity(debug=True,number_of_shear_planes=1)
    test_5_blockshear = BlockShearCalculator(endpoint = beam_column_connection.member_b, connection=beam_column_connection,loading_orientation="Axial")
    test_5_blockshear.calculate_capacity(debug=True)
    test_6_beam_shear = ShearYieldingCalculator(endpoint=beam_column_connection1.member_a, connection=beam_column_connection)
    test_6_beam_shear.calculate_capacity(debug=True)
    test_7_column_shear = ShearYieldingCalculator(endpoint=beam_column_connection1.member_b, connection=beam_column_connection)
    test_7_column_shear.calculate_capacity(debug=True)
    loads_checking = DesignLoads(Pu = 269 * si.kip, Vu = 440 * si.kip)
    test_8_plate = WeldCalculator(beam_gusset_connection,loads_checking)
    test_8_plate.calculate_min_thickness(debug=True)

except Exception as e:
    print("\n--- SCRIPT FAILED WITH AN ERROR ---")
    print(f"Error Type: {type(e).__name__}")
    print(f"Error Message: {e}")
    print("Traceback:")
    traceback.print_exc()