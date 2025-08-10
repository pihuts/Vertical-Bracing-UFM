from steel_lib.member_factory import MemberFactory
from steel_lib.materials import MATERIALS
from steelpy import aisc
from steel_lib.data_models import Connection, ConnectionComponent, BoltConfiguration, BoltGrade
from steel_lib.calculations import TensileYieldingCalculator, TensileRuptureCalculator

# --- Steel & Connection Properties ---
steel = MATERIALS["a572_gr50"]
bolt_grade = BoltGrade(name="A325", Fnv=68 * 1000, Fnt=90 * 1000)
bolt_config = BoltConfiguration(
    bolt_diameter=7/8,
    bolt_grade=bolt_grade,
    n_rows=2,
    n_columns=7,
    edge_distance_horizontal=1.25,
    edge_distance_vertical=1.25,
    column_spacing=3.0,
    row_spacing=3.0,
    angle=0
)

# --- Member & Connection Setup ---
# Create a double angle member
bracing = MemberFactory.create_steelpy_member(
    section_class=aisc.L_shapes,
    section_name="L6X6X1",
    material=steel,
    shape_type="L",
    loading_condition=2  # Double angle
)

# Define the connection
connection = Connection(
    name="Test Connection",
    connection_type="bolted",
    configuration=bolt_config,
    override_Ag=None
)

# Define the connection endpoint
endpoint = connection.add_endpoint(member=bracing, component=ConnectionComponent.TOTAL)

# --- Calculations & Debugging ---
# Initialize calculators
yielding_calc = TensileYieldingCalculator(endpoint, connection)
rupture_calc = TensileRuptureCalculator(endpoint, connection)

# Calculate and print capacities with debug mode enabled
print("--- Yielding Capacity ---")
yielding_capacity = yielding_calc.calculate_capacity(debug=True)
print(f"Yielding Capacity: {yielding_capacity.to('kip'):.2f}\n")

print("--- Rupture Capacity ---")
rupture_capacity = rupture_calc.calculate_capacity(debug=True)
print(f"Rupture Capacity: {rupture_capacity.to('kip'):.2f}")