import unittest
import math
from steel_lib.si_units import si
from steel_lib.data_models import (
    Plate,
    ConnectionFactory,
    ConnectionComponent,
)
from steel_lib.member_factory import MemberFactory
from steelpy import aisc
from steel_lib.calculations import (
    TensileYieldWhitmore,
    CompressionBucklingCalculator,
    ShearYieldingCalculator,
    UFMCalculator,
    PlateTensileYieldingCalculator,
    WebLocalYieldingCalculator,
    WebLocalCrippingCalculator,
    BoltShearCalculator,
)
from steel_lib.materials import MATERIALS, BOLT_GRADES, WELD_ELECTRODES

class TestCalculations(unittest.TestCase):

    def setUp(self):
        """Set up common objects for the tests."""
        self.beam = MemberFactory.create_steelpy_member(
            section_class=aisc.W_shapes,
            section_name="W21X83",
            material=MATERIALS["a992"],
            shape_type="W"
        )
        self.support = MemberFactory.create_steelpy_member(
            section_class=aisc.W_shapes,
            section_name="W14X90",
            material=MATERIALS["a992"],
            shape_type="W"
        )
        self.end_plate_column = Plate(
            t=1 * si.inch,
            material=MATERIALS["a572_gr50"]
        )
        self.gusset_plate_bracing = Plate(
            t=1 * si.inch,
            material=MATERIALS["a572_gr50"],
            clipping=3/4 * si.inch,
        )
        self.bracing_connection = ConnectionFactory.create_bolted_connection(
            component=ConnectionComponent.TOTAL,
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
        self.column_endplate_connection = ConnectionFactory.create_bolted_connection(
            component=ConnectionComponent.FLANGE,
            row_spacing=3.0 * si.inch,
            column_spacing=3.0 * si.inch,
            n_rows=7,
            n_columns=2,
            edge_distance_vertical=3 * si.inch,
            edge_distance_horizontal=1.5 * si.inch,
            bolt_diameter=7/8 * si.inch,
            bolt_grade=BOLT_GRADES["a490_x"],
            material=MATERIALS["a572_gr50"],
            angle=47.2 * math.pi / 180
        )
        ufm_checker = UFMCalculator(
            beam=self.beam,
            support=self.support,
            endplate=self.end_plate_column,
            connection=self.column_endplate_connection
        )
        final_dimensions = ufm_checker.get_dimensions()
        self.gusset_plate_bracing.set_dimensions(final_dimensions)
        self.demand_force = 840 * si.kip
        self.beam_gusset_connection = ConnectionFactory.create_welded_connection(
            component=ConnectionComponent.LENGTH,
            weld_size=0.3125 * si.inch,
            length=self.gusset_plate_bracing.length,
            electrode=WELD_ELECTRODES["e70xx"]
        )

    def test_tensile_yield_whitmore_dcr(self):
        """
        Test the check_dcr method of the TensileYieldWhitmore calculator.
        """
        # Expected Output from design_guide.md, page 51
        expected_dcr = 0.87

        # Create Calculator and run DCR check
        whitmore_checker = TensileYieldWhitmore(self.gusset_plate_bracing, self.bracing_connection)
        dcr = whitmore_checker.check_dcr(demand_force=self.demand_force)

        # Assertion
        self.assertAlmostEqual(dcr, expected_dcr, places=2)

    def test_compression_buckling_dcr(self):
        """
        Test the check_dcr method of the CompressionBucklingCalculator.
        """
        # Expected Output from design_guide.md, page 51
        expected_dcr = 0.89

        # Create Calculator and run DCR check
        buckling_checker = CompressionBucklingCalculator(self.gusset_plate_bracing, self.bracing_connection)
        dcr = buckling_checker.check_dcr(demand_force=self.demand_force)

        # Assertion
        self.assertAlmostEqual(dcr, expected_dcr, places=2)

    def test_shear_yielding_dcr(self):
        """
        Test the check_dcr method of the ShearYieldingCalculator.
        """
        # Correct demand force is Hub = 440.34 kips
        # Capacity is 945 kips
        # DCR = 440.34 / 945 = 0.466
        expected_dcr = 0.466

        # Create Calculator and run DCR check
        shear_checker = ShearYieldingCalculator(self.gusset_plate_bracing, self.beam_gusset_connection)
        dcr = shear_checker.check_dcr(demand_force=440.34 * si.kip)

        # Assertion
        self.assertAlmostEqual(dcr, expected_dcr, places=2)

    def test_plate_tensile_yielding_dcr(self):
        """
        Test the check_dcr method of the PlateTensileYieldingCalculator.
        """
        # Correct demand force is Vub = 269.02 kips
        # Capacity is 1428.75 kips
        # DCR = 269.02 / 1428.75 = 0.188
        expected_dcr = 0.19

        # Create Calculator and run DCR check
        tensile_checker = PlateTensileYieldingCalculator(self.gusset_plate_bracing)
        dcr = tensile_checker.check_dcr_vertical(demand_force=269.02 * si.kip)

        # Assertion
        self.assertAlmostEqual(dcr, expected_dcr, places=2)

    def test_web_local_yielding_dcr(self):
        """
        Test the check_dcr method of the WebLocalYieldingCalculator.
        """
        # Expected Output from design_guide.md, page 58
        # phi*Rn = 897 kips
        # Vub = 269 kips
        # DCR = 269 / 897 = 0.299
        expected_dcr = 0.30

        # Create Calculator and run DCR check
        web_yielding_checker = WebLocalYieldingCalculator(self.beam, self.beam_gusset_connection, self.end_plate_column)
        dcr = web_yielding_checker.check_dcr(demand_force=269.02 * si.kip)

        # Assertion
        self.assertAlmostEqual(dcr, expected_dcr, places=2)

    def test_web_local_crippling_dcr(self):
        """
        Test the check_dcr method of the WebLocalCrippingCalculator.
        """
        # Expected Output from design_guide.md, page 59
        # phi*Rn = 766 kips
        # Vub = 269 kips
        # DCR = 269 / 766 = 0.351
        expected_dcr = 0.35

        # Create Calculator and run DCR check
        web_crippling_checker = WebLocalCrippingCalculator(self.beam, self.beam_gusset_connection, self.end_plate_column)
        dcr = web_crippling_checker.check_dcr(demand_force=269.02 * si.kip)

        # Assertion
        self.assertAlmostEqual(dcr, expected_dcr, places=2)

    def test_bolt_modified_tensile_strength(self):
        """
        Test the calculate_capacity_fnt_modified method against the AISC Design Guide 29.
        """
        # Values from Design Guide Example 5.1, page 61.
        # The guide uses 7/8" ASTM A325-X bolts for this check.
        # Total shear force on the interface (Vuc) is 302 kips across 14 bolts.
        connection_a325 = ConnectionFactory.create_bolted_connection(
            component=ConnectionComponent.FLANGE,
            row_spacing=3.0 * si.inch,
            column_spacing=3.0 * si.inch,
            n_rows=7,
            n_columns=2,
            edge_distance_vertical=3 * si.inch,
            edge_distance_horizontal=1.5 * si.inch,
            bolt_diameter=7/8 * si.inch,
            bolt_grade=BOLT_GRADES["a325_x"],
            material=MATERIALS["a572_gr50"],
            angle=47.2 * math.pi / 180
        )
        
        shear_calculator = BoltShearCalculator(connection_a325)
        
        # Total required shear strength for the connection (Vuc from the guide)
        total_demand_shear = 302 * si.kip
        
        # Expected modified tensile stress (F'nt) from the guide
        expected_fnt_modified = 53.6 * si.ksi

        # Calculate the modified tensile strength
        fnt_modified = shear_calculator.calculate_capacity_fnt_modified(
            demand_force_shear=total_demand_shear,
            resistance_factor=0.75,
            debug=True
        )

        # Assert that the calculated value matches the guide's value
        self.assertAlmostEqual(fnt_modified, expected_fnt_modified, delta=0.1 * si.ksi)


if __name__ == '__main__':
    unittest.main()