import unittest
from steel_lib.data_models import (
    ConnectionFactory,
    GlobalLoads,
    Plate,
    Material,
    ConnectionComponent,
    DesignLoads,
)
from steel_lib.si_units import si

class TestLoadTransformation(unittest.TestCase):
    def setUp(self):
        """Set up common materials and members for tests."""
        self.steel_material = Material(Fy=50 * si.ksi, Fu=65 * si.ksi, E=29000 * si.ksi)
        self.beam = Plate(t=0.5 * si.inch, material=self.steel_material, length=10 * si.inch, width=5 * si.inch)
        self.column = Plate(t=0.75 * si.inch, material=self.steel_material, length=12 * si.inch, width=12 * si.inch)
        self.plate = Plate(t=0.375 * si.inch, material=self.steel_material, length=8 * si.inch, width=4 * si.inch)

    def test_explicit_roles_beam_to_column(self):
        """
        Tests the transformation using explicit 'BEAM' and 'COLUMN' roles.
        """
        print("\n--- Running Test: Explicit Roles - Beam to Column ---")
        loads = GlobalLoads(fx=10 * si.kip, fy=50 * si.kip)
        print(f"Applied Global Loads: fx={loads.fx}, fy={loads.fy}")

        connection = ConnectionFactory.create_bolted_connection(
            member_a=self.beam,
            role_a='BEAM',
            member_b=self.column,
            role_b='COLUMN',
            global_loads=loads,
            # Dummy bolt config
            row_spacing=3*si.inch, column_spacing=3*si.inch, edge_distance_vertical=1.5*si.inch,
            edge_distance_horizontal=1.5*si.inch, bolt_diameter=0.75*si.inch, bolt_grade=None, material=self.steel_material
        )

        beam_loads = connection.member_a.loads
        column_loads = connection.member_b.loads

        print(f"Transformed Beam Loads: Pu={beam_loads.Pu}, Vu={beam_loads.Vu}")
        print(f"Transformed Column Loads: Pu={column_loads.Pu}, Vu={column_loads.Vu}")

        # Verify Beam (Pu=fx, Vu=fy)
        self.assertEqual(beam_loads.Pu, loads.fx)
        self.assertEqual(beam_loads.Vu, loads.fy)

        # Verify Column (Pu=fy, Vu=fx)
        self.assertEqual(column_loads.Pu, loads.fy)
        self.assertEqual(column_loads.Vu, loads.fx)
        print("Verification successful.")

    def test_fallback_heuristic_beam_to_column(self):
        """
        Tests the fallback heuristic when no roles are provided.
        """
        print("\n--- Running Test: Fallback Heuristic - Beam to Column Web ---")
        loads = GlobalLoads(fx=15 * si.kip, fy=60 * si.kip)
        print(f"Applied Global Loads: fx={loads.fx}, fy={loads.fy}")

        # No roles are provided, so it should use the component to infer roles
        connection = ConnectionFactory.create_bolted_connection(
            member_a=self.beam,
            member_b=self.column,
            component_b=ConnectionComponent.WEB, # This makes column the primary member
            global_loads=loads,
            # Dummy bolt config
            row_spacing=3*si.inch, column_spacing=3*si.inch, edge_distance_vertical=1.5*si.inch,
            edge_distance_horizontal=1.5*si.inch, bolt_diameter=0.75*si.inch, bolt_grade=None, material=self.steel_material
        )

        beam_loads = connection.member_a.loads   # Secondary
        column_loads = connection.member_b.loads # Primary

        print(f"Inferred Beam Loads (Secondary): Pu={beam_loads.Pu}, Vu={beam_loads.Vu}")
        print(f"Inferred Column Loads (Primary): Pu={column_loads.Pu}, Vu={column_loads.Vu}")

        # Verify Beam (Secondary: Pu=fx, Vu=fy)
        self.assertEqual(beam_loads.Pu, loads.fx)
        self.assertEqual(beam_loads.Vu, loads.fy)

        # Verify Column (Primary: Pu=fy, Vu=fx)
        self.assertEqual(column_loads.Pu, loads.fy)
        self.assertEqual(column_loads.Vu, loads.fx)
        print("Verification successful.")

    def test_shear_plate_role(self):
        """
        Tests that a SHEAR_PLATE gets the same loads as a BEAM.
        """
        print("\n--- Running Test: Shear Plate Role ---")
        loads = GlobalLoads(fx=5 * si.kip, fy=25 * si.kip)
        print(f"Applied Global Loads: fx={loads.fx}, fy={loads.fy}")

        # The shear plate (member_a) connects the beam to the column.
        # We test the plate's loads directly.
        connection = ConnectionFactory.create_bolted_connection(
            member_a=self.plate,
            role_a='SHEAR_PLATE',
            member_b=self.column,
            role_b='COLUMN',
            global_loads=loads,
            # Dummy bolt config
            row_spacing=3*si.inch, column_spacing=3*si.inch, edge_distance_vertical=1.5*si.inch,
            edge_distance_horizontal=1.5*si.inch, bolt_diameter=0.75*si.inch, bolt_grade=None, material=self.steel_material
        )

        plate_loads = connection.member_a.loads
        column_loads = connection.member_b.loads

        print(f"Transformed Plate Loads: Pu={plate_loads.Pu}, Vu={plate_loads.Vu}")
        print(f"Transformed Column Loads: Pu={column_loads.Pu}, Vu={column_loads.Vu}")

        # Verify Shear Plate (Pu=fx, Vu=fy, same as a beam)
        self.assertEqual(plate_loads.Pu, loads.fx)
        self.assertEqual(plate_loads.Vu, loads.fy)
        
        # Verify Column (Pu=fy, Vu=fx)
        self.assertEqual(column_loads.Pu, loads.fy)
        self.assertEqual(column_loads.Vu, loads.fx)
        print("Verification successful.")

if __name__ == '__main__':
    unittest.main()