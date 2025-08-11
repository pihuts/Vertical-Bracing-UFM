import unittest
from steel_lib.si_units import si
from steel_lib.data_models import DesignLoads, LoadMultipliers, AppliedLoads

class TestDataModels(unittest.TestCase):

    def test_from_ufm_factory(self):
        """
        Test the AppliedLoads.from_ufm factory method to ensure it correctly
        calculates and combines interface forces.
        """
        # 1. Define Inputs
        design_loads = DesignLoads(
            Pu=840 * si.kip,
            Vu=50.0 * si.kip,
            Aub=100 * si.kip
        )
        
        # These multipliers are taken directly from the successful `main.py` run
        multipliers = LoadMultipliers(
            shear_force_column_interface=0.359176,
            shear_force_beam_interface=0.320265,
            normal_force_column=0.209519,
            normal_force_beam=0.524210
        )

        # 2. Expected Outputs (based on design_guide.md and hand calcs)
        expected_gusset_to_column_shear = ((0.359176 * 840) + 50.0) * si.kip
        expected_gusset_to_column_normal = ((0.209519 * 840) + 100.0) * si.kip
        expected_gusset_to_beam_shear = (0.320265 * 840) * si.kip
        expected_gusset_to_beam_normal = (0.524210 * 840) * si.kip

        # 3. Create AppliedLoads object via the factory
        applied_loads = AppliedLoads.from_ufm(design_loads, multipliers)

        # 4. Assertions
        self.assertAlmostEqual(applied_loads.gusset_to_column_shear.to('kip').value, expected_gusset_to_column_shear, places=1)
        self.assertAlmostEqual(applied_loads.gusset_to_column_normal.to('kip').value, expected_gusset_to_column_normal, places=1)
        self.assertAlmostEqual(applied_loads.gusset_to_beam_shear.to('kip').value, expected_gusset_to_beam_shear, places=1)
        self.assertAlmostEqual(applied_loads.gusset_to_beam_normal.to('kip').value, expected_gusset_to_beam_normal, places=1)

if __name__ == '__main__':
    unittest.main()
