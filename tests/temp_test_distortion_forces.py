import pytest
import math
from steel_lib.calculations import AdmissableDistortionForces
from steel_lib.data_models import DesignLoads, Connection, BoltConfiguration
from steel_lib.si_units import si
# No change, remove this line

# Mock classes for beam and support with necessary attributes
class MockMember:
    def __init__(self, Ix, area, Type="W"):
        self.Ix = Ix
        self.area = area
        self.Type = Type

class MockConnection:
    def __init__(self, angle_degrees):
        self.configuration = MockBoltConfiguration(angle_degrees)

class MockBoltConfiguration:
    def __init__(self, angle_degrees):
        self.angle = math.radians(angle_degrees)

def test_admissible_distortion_forces_logging(capsys):
    """
    Tests the logging output of the AdmissableDistortionForces calculation.
    """
    beam = MockMember(Ix=100 * si.inch**4, area=10 * si.inch**2)
    support = MockMember(Ix=200 * si.inch**4, area=20 * si.inch**2)
    loads = DesignLoads(Pu=50 * si.kip, Vu=0 * si.kip, Aub=0 * si.kip)
    connection = MockConnection(angle_degrees=45)

    # Test with lb provided
    calculator_lb = AdmissableDistortionForces(
        beam=beam,
        support=support,
        loads=loads,
        connection=connection,
        lb=20 * si.inch,
        lc=None
    )
    result_lb = calculator_lb.calculate_admissible_distortion_forces(debug=True)
    captured_lb = capsys.readouterr()
    print("\n--- Logging Output for lb provided ---")
    print(captured_lb.out)

    assert "Factored Load (Pu)                 : 50.000 kip" in captured_lb.out
    assert "Initial Beam Length (lb_init)      : 20.000 inch" in captured_lb.out
    assert "Initial Support Length (lc_init)   : None" in captured_lb.out
    assert "Effective Beam Length (b = lb/2 or lc*tan(angle)/2): 10.000 inch" in captured_lb.out
    assert "Effective Support Length (c = lc/2 or lb/tan(angle)/2): 5.000 inch" in captured_lb.out
    assert "Admissible Distortion Force        : " in captured_lb.out
    assert "DEBUG: Admissible Distortion Forces Calculation" in captured_lb.out

    # Test with lc provided
    calculator_lc = AdmissableDistortionForces(
        beam=beam,
        support=support,
        loads=loads,
        connection=connection,
        lb=None,
        lc=20 * si.inch
    )
    result_lc = calculator_lc.calculate_admissible_distortion_forces(debug=True)
    captured_lc = capsys.readouterr()
    print("\n--- Logging Output for lc provided ---")
    print(captured_lc.out)

    assert "Factored Load (Pu)                 : 50.000 kip" in captured_lc.out
    assert "Initial Beam Length (lb_init)      : None" in captured_lc.out
    assert "Initial Support Length (lc_init)   : 20.000 inch" in captured_lc.out
    assert "Effective Beam Length (b = lb/2 or lc*tan(angle)/2): 10.000 inch" in captured_lc.out
    assert "Effective Support Length (c = lc/2 or lb/tan(angle)/2): 10.000 inch" in captured_lc.out
    assert "Admissible Distortion Force        : " in captured_lc.out
    assert "DEBUG: Admissible Distortion Forces Calculation" in captured_lc.out

    # Verify the calculated values are reasonable (not a full functional test, just sanity)
    assert isinstance(result_lb, type(si.kip))
    assert isinstance(result_lc, type(si.kip))
    assert result_lb > 0
    assert result_lc > 0