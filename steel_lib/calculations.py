import math
from typing import Any, Literal, Union, Dict, Optional, Type
from dataclasses import dataclass, field
from .si_units import si
from .data_models import (
    BoltConfiguration,
    Plate,
    PlateDimensions,
    LoadMultipliers,
    WeldConfiguration,
    Connection,
    ConnectionComponent,
    AppliedLoads
)
from .debugging import DebugLogger

# Define a type hint for numbers for clarity
Numeric = Union[int, float]


def get_applicable_gross_area(endpoint: "ConnectionEndpoint", connection: Connection) -> float:
    """
    Determines the applicable gross area (Ag) based on the connection endpoint.

    This function acts as the single source of truth for area selection. It prioritizes
    a manual override from the main connection object, otherwise it uses the endpoint's
    specified component to look up the pre-calculated area from the member's geometry.

    Args:
        endpoint (ConnectionEndpoint): The specific connection endpoint to analyze.
        connection (Connection): The parent connection object for context (e.g., override_Ag).

    Returns:
        float: The applicable gross area for the calculation.

    Raises:
        AttributeError: If the member is missing the `.geometry` attribute or the
                        required pre-calculated area within it.
        ValueError: If the specified connection component does not have a corresponding
                    area in the member's geometry.
    """
    # 1. Prioritize the manual override from the parent connection
    if connection.override_Ag is not None:
        return connection.override_Ag

    member = endpoint.member
    # 2. Check for the mandatory geometry attribute on the member
    if not hasattr(member, 'geometry'):
        raise AttributeError("The provided 'member' object must be enriched with a '.geometry' attribute.")

    # 3. Look up the area based on the connection component
    component_name = endpoint.component.value
    applicable_area = getattr(member.geometry, component_name, None)

    if applicable_area is None:
        raise ValueError(
            f"The area for component '{component_name}' is not available in the "
            f"member's geometry. Available areas: {member.geometry}"
        )

    return applicable_area


def get_applicable_thickness(endpoint: "ConnectionEndpoint") -> float:
    """
    Determines the applicable thickness based on the connection endpoint.
    This ensures that calculations like net area are based on the correct
    thickness for the connected part (e.g., web vs. flange).

    Args:
        endpoint (ConnectionEndpoint): The specific connection endpoint to analyze.

    Returns:
        float: The applicable thickness for the calculation.

    Raises:
        AttributeError: If the member lacks the required thickness attribute
                        (e.g., 'tw' for a web connection).
    """
    member = endpoint.member
    component = endpoint.component
    thickness = 0.0

    if component == ConnectionComponent.WEB:
        if not hasattr(member, 'tw'): raise AttributeError("Member lacks 'tw' for web thickness.")
        thickness = member.tw
    elif component == ConnectionComponent.FLANGE:
        if not hasattr(member, 'tf'): raise AttributeError("Member lacks 'tf' for flange thickness.")
        thickness = member.tf
    elif component in [ConnectionComponent.TOTAL, ConnectionComponent.LENGTH, ConnectionComponent.WIDTH]:
        # For plates or total sections, 't' is the primary attribute.
        # Fallback to 'tw' for other section types where 't' isn't defined.
        if hasattr(member, 't'):
            thickness = member.t
        elif hasattr(member, 'tw'):
            thickness = member.tw # A reasonable default for non-plate members
        else:
            raise AttributeError("Member has no recognizable thickness attribute ('t' or 'tw').")
    else:
        raise ValueError(f"Unknown connection component '{component}' for thickness lookup.")

    # Ensure units are applied if it's a raw number
    if isinstance(thickness, (int, float)) and not hasattr(thickness, 'units'):
        return thickness * si.inch
    return thickness


def round_to_interval(number: Numeric, interval: Numeric) -> Numeric:
    """
    Rounds a number to the nearest specified interval.
    """
    if interval == 0:
        raise ValueError("Interval cannot be zero.")
    return round(number / interval) * interval


def round_up_to_interval(number: Numeric, interval: Numeric) -> Numeric:
    """
    Rounds a number UP to the nearest specified interval (ceiling).
    """
    if interval == 0:
        raise ValueError("Interval cannot be zero.")
    return math.ceil(number / interval) * interval


def check_dcr(capacity, demand):
    return demand / capacity  # Returns the ratio of demand to capacity


class BoltShearCalculator:
    """
    Calculates the shear strength of a single bolt based on its properties.
    """
    def __init__(self, connection: Connection):
        """
        Initializes the calculator with a Connection object.
        Assumes a 'bolted' connection configuration.
        """
        self.bolt_config: BoltConfiguration = connection.configuration
        self.bolt_diameter = self.bolt_config.bolt_diameter
        self.bolt_area = self._calculate_bolt_area()
        self.fnv = self.bolt_config.bolt_grade.Fnv
        self.no_bolts = self.bolt_config.n_rows * self.bolt_config.n_columns
        self.no_bolts = self.bolt_config.n_rows * self.bolt_config.n_columns

    def _calculate_bolt_area(self) -> float:
        """Calculates the gross area of the bolt."""
        return (self.bolt_diameter**2 / 4) * math.pi

    def calculate_capacity_fnv(
        self,
        number_of_shear_planes: int,
        resistance_factor: float = 0.75,
        debug: bool = False,
    ) -> float:
        """
        Calculates the design shear strength of the bolt.
        """
        logger = DebugLogger("Bolt Shear Strength", debug)
        logger.add_input("Nominal Shear Stress (Fnv)", self.fnv)
        logger.add_input("Bolt Diameter (d)", self.bolt_diameter)
        logger.add_input("Bolt Area (Ab)", self.bolt_area)
        logger.add_input("Number of Shear Planes", number_of_shear_planes)
        logger.add_input("Resistance Factor (phi)", resistance_factor)

        # Nominal strength (Rn) = Fnv * Ab * Ns
        nominal_strength = self.fnv * self.bolt_area * number_of_shear_planes
        logger.add_calculation("Nominal Strength (Rn = Fnv * Ab * Ns)", nominal_strength)

        # Design strength (phiRn) = phi * Rn
        design_strength = resistance_factor * nominal_strength
        logger.add_output("Design Strength (phiRn)", design_strength)

        logger.display()
        return design_strength

    def check_dcr_fnv(self, demand_force: si.kip, **kwargs) -> float:
        """Calculates the demand-to-capacity ratio for Fnv."""
        capacity = self.calculate_capacity_fnv(**kwargs)
        if capacity == 0: return float('inf')
        return abs(demand_force / capacity)
        
    def calculate_capacity_fnt(
        self,
        number_of_shear_planes: int,
        resistance_factor: float = 0.75,
        debug: bool = False,
    ) -> float:
        """
        Calculates the design tensile strength of the bolt.
        """
        logger = DebugLogger("Bolt Tensile Strength", debug)
        fnt = self.bolt_config.bolt_grade.Fnt
        logger.add_input("Nominal Tensile Stress (Fnt)", fnt)
        logger.add_input("Bolt Area (Ab)", self.bolt_area)
        logger.add_input("Number of Shear Planes", number_of_shear_planes)
        logger.add_input("Resistance Factor (phi)", resistance_factor)

        # Nominal strength (Rn) = Fnt * Ab * Ns
        nominal_strength = fnt * self.bolt_area * number_of_shear_planes
        logger.add_calculation("Nominal Strength (Rn = Fnt * Ab * Ns)", nominal_strength)

        # Design strength (phiRn) = phi * Rn
        design_strength = resistance_factor * nominal_strength
        logger.add_output("Design Strength (phiRn)", design_strength)

        logger.display()
        return design_strength

    def check_dcr_fnt(self, demand_force: si.kip, **kwargs) -> float:
        """Calculates the demand-to-capacity ratio for Fnt."""
        capacity = self.calculate_capacity_fnt(**kwargs)
        if capacity == 0: return float('inf')
        return abs(demand_force / capacity)
    def calculate_capacity_fnt_modified(
        self,demand_force_shear: si.kip,
        resistance_factor: float = 0.75,
        debug: bool = False,
    ):
        """
        Calculates the modified design tensile strength of the bolt, considering interaction with shear.
        """
        logger = DebugLogger("Modified Bolt Tensile Strength (Interaction)", debug)
        
        fnv = self.bolt_config.bolt_grade.Fnv
        fnt = self.bolt_config.bolt_grade.Fnt
        
        logger.add_input("Total Demand Shear Force (V)", demand_force_shear)
        logger.add_input("Number of Bolts (n_bolts)", self.no_bolts)
        logger.add_input("Nominal Tensile Stress (Fnt)", fnt)
        logger.add_input("Nominal Shear Stress (Fnv)", fnv)
        logger.add_input("Bolt Area (Ab)", self.bolt_area)
        logger.add_input("Resistance Factor (phi)", resistance_factor)

        # Per AISC J3.3a, the available tensile stress F'nt is a function of the applied shear stress frv
        # F'nt = 1.3 * Fnt - (Fnt / (phi * Fnv)) * frv <= Fnt
        
        # frv is the required shear stress per unit area
        shear_per_bolt = demand_force_shear / self.no_bolts
        frv = shear_per_bolt / self.bolt_area
        logger.add_calculation("Shear per Bolt (V / n_bolts)", shear_per_bolt)
        logger.add_calculation("Required Shear Stress (frv = V_per_bolt / Ab)", frv)

        # The term (Fnt / (phi * Fnv)) is the interaction coefficient
        interaction_coefficient = fnt / (resistance_factor * fnv)
        logger.add_calculation("Interaction Coefficient (Fnt / (phi * Fnv))", interaction_coefficient)
        
        # Calculate the nominal modified tensile stress
        modified_fnt_nominal = 1.3 * fnt - interaction_coefficient * frv
        logger.add_calculation("Modified F'nt (Nominal, before cap)", modified_fnt_nominal)

        # The result cannot be greater than the nominal tensile stress Fnt
        final_fnt_modified = min(modified_fnt_nominal, fnt)
        logger.add_output("Final Modified Tensile Stress (F'nt)", final_fnt_modified)
        final_fnt_modified
        
        logger.display()
        return final_fnt_modified
class TensileYieldingCalculator:
    """
    Calculates the tensile yielding capacity of a member.
    """
    def __init__(self, endpoint: "ConnectionEndpoint", connection: Connection):
        self.endpoint = endpoint
        self.member = endpoint.member
        self.connection = connection
        self.Fy = self.member.Fy
        self.Ag = get_applicable_gross_area(endpoint, connection)
        self.loading_condition = getattr(self.member, 'loading_condition', 1)

    def calculate_capacity(self, resistance_factor: float = 0.9, debug: bool = False) -> float:
        """
        Calculates the design tensile yielding strength.
        """
        nominal_strength = self.Fy * self.Ag
        design_strength = resistance_factor * nominal_strength * self.loading_condition

        logger = DebugLogger(f"Tensile Yielding ({self.endpoint.component.name})", debug)
        logger.add_input("Yield Strength (Fy)", self.Fy)
        logger.add_input(f"Applicable Gross Area (Ag) for {self.endpoint.component.name}", self.Ag)
        logger.add_input("Loading Condition", self.loading_condition)
        logger.add_input("Resistance Factor (phi)", resistance_factor)
        logger.add_calculation("Nominal Strength (Rn = Fy * Ag)", nominal_strength)
        logger.add_output("Design Strength (phiRn)", design_strength)
        logger.display()

        return design_strength

    def check_dcr(self, demand_force: si.kip, **kwargs) -> float:
        """Calculates the demand-to-capacity ratio."""
        capacity = self.calculate_capacity(**kwargs)
        if capacity == 0: return float('inf')
        return abs(demand_force / capacity)

class TensileRuptureCalculator:
    """
    Calculates the tensile rupture capacity of a member.
    """
    def __init__(self, endpoint: "ConnectionEndpoint", connection: Connection):
        self.endpoint = endpoint
        self.member = endpoint.member
        self.connection = connection
        self.bolt_config = connection.configuration
        self.Fu = self.member.Fu
        self.loading_condition = getattr(self.member, 'loading_condition', 1)

    def calculate_capacity(self, resistance_factor: float = 0.75, debug: bool = False) -> float:
        """
        Calculates the design tensile rupture strength with detailed logging.
        """
        logger = DebugLogger(f"Tensile Rupture ({self.endpoint.component.name})", debug)

        # --- Inputs ---
        t = get_applicable_thickness(self.endpoint)
        S_c = self.bolt_config.column_spacing
        N_c = self.bolt_config.n_columns
        dbolt = self.bolt_config.bolt_diameter
        Ag = get_applicable_gross_area(self.endpoint, self.connection)
        n_rows = self.bolt_config.n_rows
        
        logger.add_input("Ultimate Strength (Fu)", self.Fu)
        logger.add_input("Applicable Thickness (t)", t)
        logger.add_input("Gross Area (Ag)", Ag)
        logger.add_input("Bolt Diameter (d_bolt)", dbolt)
        logger.add_input("Bolt Columns (N_c)", N_c)
        logger.add_input("Bolt Rows (n_rows)", n_rows)
        logger.add_input("Column Spacing (S_c)", S_c)
        logger.add_input("Loading Condition", self.loading_condition)
        logger.add_input("Resistance Factor (phi)", resistance_factor)

        # --- Shear Lag Factor (Ubs) Calculation ---
        l = S_c * (N_c - 1)
        logger.add_calculation("Connection Length (l = S_c * (N_c - 1))", l)

        x_bar = 0
        if self.endpoint.component == ConnectionComponent.TOTAL and hasattr(self.member, 'x'):
            x_bar = self.member.x
        logger.add_input("Eccentricity (x_bar)", x_bar)

        Ubs = 1 - (x_bar / l) if l > 0 else 1.0
        logger.add_calculation("Shear Lag Factor (Ubs = 1 - x_bar / l)", Ubs)

        # --- Net Area (An) Calculation ---
        dhole = dbolt + (1/8) * si.inch
        logger.add_calculation("Hole Diameter (d_hole = d_bolt + 1/8)", dhole)
        
        area_deduction = dhole * n_rows * t
        logger.add_calculation("Area Deduction for Holes (d_hole * n_rows * t)", area_deduction)

        An_gross = Ag - area_deduction
        logger.add_calculation("Net Area (An = Ag - deduction)", An_gross)

        # --- Effective Net Area (Ae) ---
        Ae = An_gross * Ubs
        logger.add_calculation("Effective Net Area (Ae = An * Ubs)", Ae)

        # --- Final Capacity Calculation ---
        nominal_strength = self.Fu * Ae
        design_strength = resistance_factor * nominal_strength * self.loading_condition

        logger.add_calculation("Nominal Strength (Rn = Fu * Ae)", nominal_strength)
        logger.add_output("Design Strength (phiRn)", design_strength)
        logger.display()

        return design_strength

    def check_dcr(self, demand_force: si.kip, **kwargs) -> float:
        """Calculates the demand-to-capacity ratio."""
        capacity = self.calculate_capacity(**kwargs)
        if capacity == 0: return float('inf')
        return abs(demand_force / capacity)

MemberType = Any # Use 'Any' for robust compatibility with steelpy objects
LoadingOrientation = Literal["Axial", "Shear"]

class BlockShearCalculator:
    """
    Calculates block shear capacity with correct unit handling and debug mode.
    """
    def __init__(
        self,
        endpoint: "ConnectionEndpoint",
        connection: Connection,
        loading_orientation: LoadingOrientation,
        loading_condition: int = 1,
        thickness: float = None,
    ):
        self.endpoint = endpoint
        self.member = endpoint.member
        self.bolt_config: BoltConfiguration = connection.configuration
        self.loading_orientation = loading_orientation
        self.loading_condition = loading_condition

        # CORRECTED: _get_member_thickness now always returns a unit-aware value
        self.thickness = thickness if thickness is not None else get_applicable_thickness(endpoint)
        self.bolt_hole_diameter = self.bolt_config.bolt_diameter + (1/8) * si.inch

        if self.loading_orientation == "Shear" or self.member.Type == "L":
            self.failure_pattern = "L"
        else:
            self.failure_pattern = "U"

    # --- Calculation methods now correctly include loading_condition ---
    def _calculate_l_shear_yield_path(self) -> float:
        spacing, rows , edge_dist = (self.bolt_config.row_spacing, self.bolt_config.n_rows, self.bolt_config.edge_distance_vertical) if self.loading_orientation == "Shear" else (self.bolt_config.column_spacing, self.bolt_config.n_columns, self.bolt_config.edge_distance_horizontal)
        length = spacing * (rows - 1) + edge_dist
        # Apply loading_condition to the area calculation as in the original code
        return length * self.thickness * self.loading_condition

    def _calculate_l_shear_rupture_path(self) -> float:
        gross_area = self._calculate_l_shear_yield_path()
        rows = self.bolt_config.n_rows if self.loading_orientation == "Shear" else self.bolt_config.n_columns
        # Hole deduction must also be scaled by loading_condition
        hole_area_deduction = (rows - 0.5) * self.bolt_hole_diameter * self.thickness * self.loading_condition
        return gross_area - hole_area_deduction

    def _calculate_l_tension_rupture_path(self) -> float:
        if self.loading_orientation == "Axial":
            spacing, rows, edge_dist = self.bolt_config.row_spacing, self.bolt_config.n_rows, self.bolt_config.edge_distance_vertical
        else:
            spacing, rows, edge_dist = self.bolt_config.column_spacing, self.bolt_config.n_columns, self.bolt_config.edge_distance_horizontal

        net_length = (spacing * (rows - 1) + edge_dist) - ((rows - 0.5) * self.bolt_hole_diameter)
        return net_length * self.thickness * self.loading_condition

    def _calculate_u_tension_rupture_path(self) -> float:
        spacing, rows = self.bolt_config.row_spacing, self.bolt_config.n_rows
        net_length = (spacing * (rows - 1)) - ((rows - 1) * self.bolt_hole_diameter)
        return net_length * self.thickness * self.loading_condition

    def calculate_capacity(self, resistance_factor: float = 0.75, debug: bool = False) -> float:
        Ubs = 1.0
        Fu, Fy = self.member.Fu, self.member.Fy
        tension_rupture_component = 0.0

        if self.failure_pattern == "L":
            shear_yield_component = self._calculate_l_shear_yield_path()
            shear_rupture_component = self._calculate_l_shear_rupture_path()
            tension_rupture_component = self._calculate_l_tension_rupture_path()
            # ... (debug print statements)

        elif self.failure_pattern == "U":
            shear_yield_component = self._calculate_l_shear_yield_path() * 2
            shear_rupture_component = self._calculate_l_shear_rupture_path() * 2
            tension_rupture_component = self._calculate_u_tension_rupture_path()
            # ... (debug print statements)

        shear_force = 0.60 * min(shear_yield_component * Fy, shear_rupture_component * Fu)
        tension_force = Ubs * Fu * tension_rupture_component

        nominal_capacity = tension_force + shear_force
        design_capacity = resistance_factor * nominal_capacity

        logger = DebugLogger(f"Block Shear {self.failure_pattern}-Pattern", debug)
        logger.add_input("Gross Shear Area (Agv)", shear_yield_component)
        logger.add_input("Net Shear Area (Anv)", shear_rupture_component)
        logger.add_input("Net Tension Area (Ant)", tension_rupture_component)
        logger.add_input("Resistance Factor (phi)", resistance_factor)
        logger.add_calculation("Shear Yielding (0.6*Fy*Agv)", (0.6 * Fy * shear_yield_component))
        logger.add_calculation("Shear Rupture (0.6*Fu*Anv)", (0.6 * Fu * shear_rupture_component))
        logger.add_calculation("Tension Rupture (Ubs*Fu*Ant)", tension_force)
        logger.add_calculation("Nominal Capacity (Rn)", nominal_capacity)
        logger.add_output("Design Capacity (phiRn)", design_capacity)
        logger.display()

        return design_capacity

    def check_dcr(self, demand_force: si.kip, **kwargs) -> float:
        """Calculates the demand-to-capacity ratio."""
        capacity = self.calculate_capacity(**kwargs)
        if capacity == 0: return float('inf')
        return abs(demand_force / capacity)

class ConnectionCapacityCalculator:
    """
    Calculates the governing bolt capacity for an entire connection, considering
    bolt shear and bolt bearing/tearout for inner and outer bolts.
    """
    def __init__(self, endpoint: "ConnectionEndpoint", connection: Connection, loading_orientation: Literal["Axial", "Shear"]):
        self.endpoint = endpoint
        self.connection = connection
        self.member = endpoint.member
        self.bolt_config: BoltConfiguration = connection.configuration
        self.loading_orientation = loading_orientation

        # Extract common properties
        self.Fu = self.member.Fu
        self.thickness = get_applicable_thickness(endpoint)
        self.bolt_diameter = self.bolt_config.bolt_diameter
        self.bolt_diameter_nominal = self.bolt_config.bolt_diameter + (1/16) * si.inch

        # Per AISC, standard hole diameter is bolt diameter + 1/8"
        self.hole_diameter = self.bolt_config.bolt_diameter + (1/8) * si.inch

        # Determine geometry based on loading orientation (DRY principle)
        if self.loading_orientation == "Axial":
            self.longitudinal_spacing = self.bolt_config.column_spacing
            self.longitudinal_edge_dist = self.bolt_config.edge_distance_horizontal
            self.bolts_per_line = self.bolt_config.n_columns
            self.num_lines = self.bolt_config.n_rows
        else: # Shear
            self.longitudinal_spacing = self.bolt_config.row_spacing
            self.longitudinal_edge_dist = self.bolt_config.edge_distance_vertical
            self.bolts_per_line = self.bolt_config.n_rows
            self.num_lines = self.bolt_config.n_columns


    def _calculate_lc_inner(self) -> float:
        """Calculates clear distance for an inner bolt."""
        return self.longitudinal_spacing - self.bolt_diameter_nominal

    def _calculate_lc_outer(self) -> float:
        """Calculates clear distance for an edge bolt."""
        return self.longitudinal_edge_dist - (self.bolt_diameter_nominal / 2)

    def calculate_capacity(
        self,
        number_of_shear_planes: int,
        resistance_factor: float = 0.75,
        debug: bool = False,
    ) -> float:
        """
        Calculates the total design capacity of the bolted connection.
        """
        # 1. Get the shear capacity of a single bolt (this is an upper limit)
        # Create a new Connection object to pass to the shear checker
        shear_checker = BoltShearCalculator(self.connection)
        bolt_shear_strength = shear_checker.calculate_capacity_fnv(number_of_shear_planes, resistance_factor=0.75) # Use nominal for comparison

        # 2. Calculate clear distances
        lc_in = self._calculate_lc_inner()
        lc_out = self._calculate_lc_outer()

        # 3. Calculate nominal bearing/tearout capacities per bolt
        # Based on AISC J3-6a for standard holes where deformation is a consideration
        bearing_limit = 2.4 * self.bolt_diameter * self.thickness * self.Fu  * resistance_factor
        tearout_inner = 1.2 * lc_in * self.thickness * self.Fu * resistance_factor
        tearout_outer = 1.2 * lc_out * self.thickness * self.Fu *  resistance_factor

        # 4. Determine the governing nominal strength for inner and outer bolts
        r_nominal_inner = min(bolt_shear_strength, bearing_limit, tearout_inner)
        r_nominal_outer = min(bolt_shear_strength, bearing_limit, tearout_outer)

        # 5. Sum the capacities for all bolts in the connection
        total_nominal_capacity = (r_nominal_inner * (self.bolts_per_line - 1) + r_nominal_outer) * self.num_lines

        # 6. Apply resistance factor and loading condition for the final design strength
        # The member's loading_condition (e.g., 2 for double angle) scales the final result
        loading_condition = getattr(self.member, 'loading_condition', 1)
        design_capacity = total_nominal_capacity  * loading_condition

        logger = DebugLogger("Connection Capacity", debug)
        logger.add_input("Member Fu", self.Fu)
        logger.add_input("Member Thickness", self.thickness)
        logger.add_input("Bolt Diameter", self.bolt_diameter)
        logger.add_input("Hole Diameter", self.hole_diameter)
        logger.add_input("Longitudinal Spacing", self.longitudinal_spacing)
        logger.add_input("Longitudinal Edge Dist", self.longitudinal_edge_dist)
        logger.add_input("Bolts per Line", self.bolts_per_line)
        logger.add_input("Number of Lines", self.num_lines)
        logger.add_input("Resistance Factor (phi)", resistance_factor)
        logger.add_input("Loading Condition Multiplier", loading_condition)
        logger.add_calculation("Inner Bolt Clear Distance (lc_in)", lc_in)
        logger.add_calculation("Outer Bolt Clear Distance (lc_out)", lc_out)
        logger.add_calculation("Bolt Shear Strength", bolt_shear_strength)
        logger.add_calculation("Bearing Limit (2.4*d*t*Fu)", bearing_limit)
        logger.add_calculation("Tearout (Inner Bolt)", tearout_inner)
        logger.add_calculation("Tearout (Outer Bolt)", tearout_outer)
        logger.add_calculation("Governing Strength (Inner)", r_nominal_inner)
        logger.add_calculation("Governing Strength (Outer)", r_nominal_outer)
        logger.add_calculation("Total Nominal Strength (Rn)", total_nominal_capacity)
        logger.add_output("Final Design Capacity (phiRn)", design_capacity)
        logger.display()

        return design_capacity

    def check_dcr(self, demand_force: si.kip, **kwargs) -> float:
        """Calculates the demand-to-capacity ratio."""
        capacity = self.calculate_capacity(**kwargs)
        if capacity == 0: return float('inf')
        return abs(demand_force / capacity)


class TensileYieldWhitmore:
    """
    Calculates the tensile yielding capacity based on the Whitmore section.
    """

    def __init__(self, endpoint: "ConnectionEndpoint", connection: Connection):
        """Initializes the calculator with the member and connection objects."""
        self.endpoint = endpoint
        self.member = endpoint.member
        self.bolt_config: BoltConfiguration = connection.configuration
        self.Fy = self.member.Fy
        self.loading_condition = getattr(self.member, "loading_condition", 1)
        self.n_cols = self.bolt_config.n_columns
        self.spacing_col = self.bolt_config.column_spacing
        self.spacing_row = self.bolt_config.row_spacing
        self.t = self._get_member_thickness()

    def _get_member_thickness(self) -> float:
        """Determines thickness from various member types and ensures it has units."""
        if hasattr(self.member, "t"):
            t_val = self.member.t
            if hasattr(t_val, 'units'):
                return t_val
            if isinstance(t_val, (int, float)):
                return t_val * si.inch
            return t_val
        elif hasattr(self.member, "tw"):
            tw_val = self.member.tw
            if isinstance(tw_val, (int, float)):
                return tw_val * si.inch
            return tw_val
        raise AttributeError("Member does not have a recognizable thickness attribute.")

    @property
    def length_whitmore(self) -> float:
        """Calculates the effective width of the Whitmore section."""
        bolt_group_length = (self.n_cols - 1) * self.spacing_col
        spread_width = 2 * (bolt_group_length * math.tan(math.radians(30)))
        return self.spacing_row + spread_width

    @property
    def area_whitmore(self) -> float:
        """Calculates the area of the Whitmore section."""
        return (
            self.length_whitmore - 4.7 * si.inch
        ) * self.t + 4.7 * si.inch * 0.515 * si.inch

    def calculate_capacity(
        self, resistance_factor: float = 0.9, debug: bool = False
    ) -> float:
        """
        Calculates the design tensile yield strength of the Whitmore section.
        """
        nominal_capacity = self.Fy * self.area_whitmore
        design_capacity = (
            nominal_capacity * resistance_factor * self.loading_condition
        )
        logger = DebugLogger("Whitmore Section Tensile Yield", debug)
        logger.add_input("Yield Strength (Fy)", self.Fy)
        logger.add_input("Member Thickness (t)", self.t)
        logger.add_input("Resistance Factor (phi)", resistance_factor)
        logger.add_input("Loading Condition Multiplier", self.loading_condition)
        logger.add_calculation("Effective Length (Lw)", self.length_whitmore)
        logger.add_calculation("Effective Area (Aw)", self.area_whitmore)
        logger.add_calculation("Nominal Capacity (Rn)", nominal_capacity)
        logger.add_output("Final Design Capacity (phiRn)", design_capacity)
        logger.display()
        return design_capacity

    def check_dcr(self, demand_force: si.kip, **kwargs) -> float:
        """Calculates the demand-to-capacity ratio."""
        capacity = self.calculate_capacity(**kwargs)
        if capacity == 0: return float('inf')
        return abs(demand_force / capacity)


class CompressionBucklingCalculator:
    """
    Calculates the compression buckling capacity of a member.
    """

    def __init__(self, endpoint: "ConnectionEndpoint", connection: Connection):
        """Initializes the calculator with the member and connection."""
        self.endpoint = endpoint
        self.member = endpoint.member
        self.bolt_config: BoltConfiguration = connection.configuration
        self.Fy = self.member.Fy
        self.t = self._get_member_thickness()

    def _get_member_thickness(self) -> float:
        """Determ-ines thickness from various member types and ensures it has units."""
        if hasattr(self.member, "t"):
            t_val = self.member.t
            if hasattr(t_val, 'units'):
                return t_val
            if isinstance(t_val, (int, float)):
                return t_val * si.inch
            return t_val
        elif hasattr(self.member, "tw"):
            tw_val = self.member.tw
            if isinstance(tw_val, (int, float)):
                return tw_val * si.inch
            return tw_val
        raise AttributeError("Member does not have a recognizable thickness attribute.")

    @property
    def k(self) -> float:
        # This calculator is specific to bracing connections, so k is fixed.
        # A more advanced implementation might take this as an argument.
        return 0.5

    @property
    def r(self):
        return self.t / math.sqrt(12)

    @property
    def slenderness_ratio(self):
        return (self.k * 9.76 * si.inch) / (self.r)

    def calculate_capacity(self, resistance_factor=0.9, debug: bool = False) -> float:
        """
        Calculates the design compression buckling strength of the member.
        """
        logger = DebugLogger("Compression Buckling", debug)
        logger.add_input("k", self.k)
        logger.add_input("r", self.r)
        logger.add_input("Slenderness Ratio", self.slenderness_ratio)
        logger.add_input("Fy", self.Fy)
        logger.add_input("Resistance Factor (phi)", resistance_factor)

        if self.slenderness_ratio <= 25:
            capacity = self.Fy * 20.9 * si.inch**2 * resistance_factor
            logger.add_output("Design Capacity (phiRn)", capacity)
            logger.display()
            return capacity
        else:
            raise ValueError(
                "Member is not slender enough for compression buckling calculation."
            )

    def check_dcr(self, demand_force: si.kip, **kwargs) -> float:
        """Calculates the demand-to-capacity ratio."""
        capacity = self.calculate_capacity(**kwargs)
        if capacity == 0: return float('inf')
        return abs(demand_force / capacity)


class UFMCalculator:
    """
    Calculates UFM endplate dimensions and load multipliers with a
    comprehensive debug mode to show all intermediate values.
    """

    def __init__(self, beam: Any, support: Any, endplate: Any, connection: Connection):
        config: BoltConfiguration = connection.configuration

        self._beam_depth = self._get_attribute(beam, ["d", "depth"])
        self._support_depth = self._get_attribute(support, ["d", "depth"])
        self._end_plate_thickness = self._get_attribute(endplate, ["t", "thickness"])
        self._edge_dist = config.edge_distance_horizontal
        self._col_spacing = config.column_spacing
        self._n_col = config.n_columns
        self._angle_rad = config.angle

    def _get_attribute(self, obj: Any, potential_names: list[str]) -> float:
        for name in potential_names:
            if hasattr(obj, name):
                value = getattr(obj, name)
                if hasattr(value, 'units'):
                    return value
                # Check if the value is a number before applying units
                if isinstance(value, (int, float)):
                    return value * si.inch
                return value # Return as is if it's not a number and has no units
        raise AttributeError(
            f"Object does not have any of the expected attributes: {potential_names}"
        )

    @property
    def _beam_half_depth(self) -> float:
        return self._beam_depth / 2

    @property
    def _support_half_depth(self) -> float:
        return self._support_depth / 2

    @property
    def _beta(self) -> float:
        return self._edge_dist + ((self._n_col - 1) * self._col_spacing) / 2

    @property
    def _alpha(self) -> float:
        return (
            (self._beam_half_depth + self._beta) * math.tan(self._angle_rad)
            - self._support_half_depth
        )

    @property
    def _r(self) -> float:
        return (
            (self._alpha + self._support_half_depth) ** 2
            + (self._beam_half_depth + self._beta) ** 2
        ) ** 0.5

    @property
    def _horizontal_plate_length(self) -> float:
        k_line_clearance = 0.75 * si.inch
        return 2 * self._alpha - 2 * self._end_plate_thickness - k_line_clearance

    def get_dimensions(self, debug: bool = False) -> PlateDimensions:
        """Calculates and returns the final, rounded plate dimensions."""
        logger = DebugLogger("UFM Plate Dimensions", debug)
        logger.add_input("Beam Depth", self._beam_depth)
        logger.add_input("Support Depth", self._support_depth)
        logger.add_input("End Plate Thickness", self._end_plate_thickness)
        logger.add_input("Edge Distance (vert)", self._edge_dist)
        logger.add_input("Row Spacing", self._col_spacing)
        logger.add_input("Number of Rows", self._n_col)
        logger.add_input("Connection Angle", f"{math.degrees(self._angle_rad):.2f} degrees")

        logger.add_calculation("_beta", self._beta)
        logger.add_calculation("_alpha", self._alpha)
        logger.add_calculation("Horizontal Plate Length (unrounded)", self._horizontal_plate_length)

        unrounded_vertical = (
            self._edge_dist * 2
            + ((self._n_col - 1) * self._col_spacing)
            + 0.5 * si.inch
        )
        logger.add_calculation("Vertical Plate Length (unrounded)", unrounded_vertical)

        vertical_dim = round_up_to_interval(
            number=unrounded_vertical, interval=0.25 * si.inch
        )
        horizontal_dim = round_up_to_interval(
            number=self._horizontal_plate_length, interval=0.25 * si.inch
        )

        logger.add_output("Final Vertical Dimension", vertical_dim)
        logger.add_output("Final Horizontal Dimension", horizontal_dim)
        logger.display()

        return PlateDimensions(
            vertical=vertical_dim,
            horizontal=horizontal_dim,
            thickness=self._end_plate_thickness,
        )

    def get_loads_multipliers(self, debug: bool = False) -> LoadMultipliers:
        """Calculates and returns the load multipliers for the UFM interfaces."""
        logger = DebugLogger("UFM Load Multipliers", debug)
        logger.add_input("Beam Depth", self._beam_depth)
        logger.add_input("Support Depth", self._support_depth)
        logger.add_input("Edge Distance (vert)", self._edge_dist)
        logger.add_input("Row Spacing", self._col_spacing)
        logger.add_input("Number of Rows", self._n_col)
        logger.add_input("Connection Angle", f"{math.degrees(self._angle_rad):.2f} degrees")

        logger.add_calculation("_beta", self._beta)
        logger.add_calculation("_alpha", self._alpha)
        logger.add_calculation("_r", self._r)

        multipliers = LoadMultipliers(
            vertical_force_column_interface=self._beta / self._r,
            vertical_force_beam_interface=self._beam_half_depth / self._r,
            horizontal_force_column_interface=self._support_half_depth / self._r,
            horizontal_force_beam_interface=self._alpha / self._r,
        )

        logger.add_output("Shear Force (Column Interface)", multipliers.vertical_force_column_interface)
        logger.add_output("Shear Force (Beam Interface)", multipliers.vertical_force_beam_interface)
        logger.add_output("Normal Force (Column)", multipliers.horizontal_force_column_interface)
        logger.add_output("Normal Force (Beam)", multipliers.horizontal_force_beam_interface)
        logger.display()

        return multipliers


class PlateTensileYieldingCalculator:
    """
    Calculates design tensile strength based on gross section yielding (AISC J4.1a).
    This calculator expects to be initialized with a member object that has a
    '.dimensions' attribute containing a PlateDimensions object.
    """

    def __init__(self, endpoint: "ConnectionEndpoint"):
        """
        Initializes the calculator by extracting required data from the endpoint's member object.
        """
        member = endpoint.member
        if not all(hasattr(member, attr) for attr in ['length', 'width', 't']):
            raise AttributeError(
                "The provided Plate object must have 'length', 'width', and 't' attributes."
            )
        self.member = member
        self.Fy = self.member.Fy
        self.loading_condition = getattr(self.member, "loading_condition", 1)
        self._thickness = self.member.t

    def _calculate_capacity_for_path(
        self,
        gross_length: float,
        interface_name: str,
        resistance_factor: float,
        debug: bool,
    ) -> float:
        """A private helper to perform the core calculation, avoiding code duplication."""
        effective_length = gross_length
        gross_area = effective_length * self._thickness
        nominal_capacity = self.Fy * gross_area
        design_capacity = (
            nominal_capacity * resistance_factor * self.loading_condition
        )
        logger = DebugLogger(f"Plate Tensile Yielding ({interface_name})", debug)
        logger.add_input("Yield Strength (Fy)", self.Fy)
        logger.add_input("Gross Length", gross_length)
        logger.add_input("Thickness", self._thickness)
        logger.add_input("Resistance Factor (phi)", resistance_factor)
        logger.add_input("Loading Condition", self.loading_condition)
        logger.add_calculation("Effective Length", effective_length)
        logger.add_calculation("Gross Area (Ag)", gross_area)
        logger.add_calculation("Nominal Capacity (Pn)", nominal_capacity)
        logger.add_output("Final Design Capacity (phiPn)", design_capacity)
        logger.display()
        return design_capacity

    def check_dcr_horizontal(self, demand_force: si.kip, **kwargs) -> float:
        """Calculates the demand-to-capacity ratio for the horizontal path."""
        capacity = self.calculate_capacity_horizontal(**kwargs)
        if capacity == 0: return float('inf')
        return abs(demand_force / capacity)

    def check_dcr_vertical(self, demand_force: si.kip, **kwargs) -> float:
        """Calculates the demand-to-capacity ratio for the vertical path."""
        capacity = self.calculate_capacity_vertical(**kwargs)
        if capacity == 0: return float('inf')
        return abs(demand_force / capacity)

    def calculate_capacity_horizontal(
        self, resistance_factor: float = 0.9, debug: bool = False
    ) -> float:
        """Calculates the design tensile yield strength along the HORIZONTAL path."""
        return self._calculate_capacity_for_path(
            gross_length=self.member.width,
            interface_name="Horizontal",
            resistance_factor=resistance_factor,
            debug=debug,
        )

    def calculate_capacity_vertical(
        self, resistance_factor: float = 0.9, debug: bool = False
    ) -> float:
        """Calculates the design tensile yield strength along the VERTICAL path."""
        return self._calculate_capacity_for_path(
            gross_length=self.member.length,
            interface_name="Vertical",
            resistance_factor=resistance_factor,
            debug=debug,
        )


class WebLocalYieldingCalculator:
    """
    Calculates the web local yielding capacity based on AISC Specification J10.2,
    with a clear separation between input and calculation debugging.
    """

    def __init__(self, endpoint: "ConnectionEndpoint", connection: Connection, end_plate: Plate):
        """
        Initializes the calculator by extracting all necessary primitive values.
        The end_plate thickness is now derived directly from the end_plate object.
        """
        config: WeldConfiguration = connection.configuration
        member = endpoint.member
        self._Fy = member.Fy
        self._tw = self._get_attribute(member, ["tw"])
        self._k = self._get_attribute(member, ["k", "k_det"])
        self._d = self._get_attribute(member, ["d", "depth"])
        self._connection_length = config.length
        self._end_plate_thickness = end_plate.t # Simplified: get thickness directly
        self._loading_condition = getattr(member, "loading_condition", 1)

    def _get_attribute(self, obj: Any, potential_names: list[str]) -> float:
        """Safely gets a numeric attribute from an object and ensures it has units."""
        for name in potential_names:
            if hasattr(obj, name):
                value = getattr(obj, name)
                return value if hasattr(value, "units") else value
        raise AttributeError(
            f"Object does not have any of the expected attributes: {potential_names}"
        )

    def calculate_capacity(self, resistance_factor: float = 1.0, debug: bool = False) -> float:
        """
        Calculates the design web local yielding strength (phiRn).
        """
        logger = DebugLogger("Web Local Yielding", debug)
        try:
            logger.add_input("Yield Strength (Fy)", self._Fy)
            logger.add_input("Web Thickness (tw)", self._tw)
            logger.add_input("Detailing Distance (k)", self._k)
            logger.add_input("Member Depth (d)", self._d)
            logger.add_input("Connection Length (lb)", self._connection_length)
            logger.add_input("End Plate Thickness (tpl)", self._end_plate_thickness)
            logger.add_input("Resistance Factor (phi)", resistance_factor)
            logger.add_input("Loading Condition", self._loading_condition)

            clip_dist = 3 / 4 * si.inch
            
            # Log inputs before calculation
            logger.add_calculation("Input: self._connection_length", self._connection_length)
            logger.add_calculation("Input: clip_dist", clip_dist)
            logger.add_calculation("Input: self._end_plate_thickness", self._end_plate_thickness)

            connection_load_centroid = (
                self._connection_length / 2 + clip_dist + self._end_plate_thickness
            )
            
            # Log output of calculation
            logger.add_calculation("Output: Connection Load Centroid", connection_load_centroid)

            # Log values for comparison
            logger.add_calculation("Comparison Input: self._d", self._d)
            try:
                logger.add_calculation("DEBUG: connection_load_centroid units", connection_load_centroid.units)
                logger.add_calculation("DEBUG: self._d units", self._d.units)
            except AttributeError:
                logger.add_calculation("DEBUG: One of the values does not have units.", "N/A")

            if connection_load_centroid <= self._d:
                multiplier_k = 2.5
            else:
                multiplier_k = 5.0
            logger.add_calculation("Multiplier (k)", multiplier_k)

            bearing_length = (multiplier_k * self._k) + self._connection_length
            logger.add_calculation("Bearing Length", bearing_length)

            nominal_capacity = self._Fy * self._tw * bearing_length
            logger.add_calculation("Nominal Capacity (Pn)", nominal_capacity)

            design_capacity = (
                nominal_capacity * resistance_factor * self._loading_condition
            )
            logger.add_output("Design Capacity (phiRn)", design_capacity)
            
            return design_capacity
        finally:
            logger.display()

    def check_dcr(self, demand_force: si.kip, **kwargs) -> float:
        """Calculates the demand-to-capacity ratio."""
        capacity = self.calculate_capacity(**kwargs)
        if capacity == 0: return float('inf')
        return abs(demand_force / capacity)
    
class WebLocalCrippingCalculator:
    """
    Calculates the web local crippling capacity based on AISC Specification J10.2,
    with a clear separation between input and calculation debugging.
    """

    def __init__(self, endpoint: "ConnectionEndpoint", connection: Connection, end_plate: Plate):
        """
        Initializes the calculator by extracting all necessary primitive values.
        The end_plate thickness is now derived directly from the end_plate object.
        """
        config: WeldConfiguration = connection.configuration
        member = endpoint.member
        self._Fy = member.Fy
        self._tw = self._get_attribute(member, ["tw"])
        self._k = self._get_attribute(member, ["k", "k_det"])
        self._d = self._get_attribute(member, ["d", "depth"])
        self._connection_length = config.length
        self._end_plate_thickness = end_plate.t # Simplified: get thickness directly
        self._loading_condition = getattr(member, "loading_condition", 1)
        self._E = member.E if hasattr(member, 'E') else 29000 * si.ksi
        self._tf = self._get_attribute(member, ["tf", "thickness_flange"])


    def _get_attribute(self, obj: Any, potential_names: list[str]) -> float:
        """Safely gets a numeric attribute from an object and ensures it has units."""
        for name in potential_names:
            if hasattr(obj, name):
                value = getattr(obj, name)
                return value if hasattr(value, "units") else value * si.inch
        raise AttributeError(
            f"Object does not have any of the expected attributes: {potential_names}"
        )

    def calculate_capacity(self, resistance_factor: float = 0.75, debug: bool = False) -> float:
        """
        Calculates the design web local crippling strength (phiRn) based on AISC J10.3.
        """
        logger = DebugLogger("Web Local Crippling", debug)
        logger.add_input("Yield Strength (Fy)", self._Fy)
        logger.add_input("Web Thickness (tw)", self._tw)
        logger.add_input("Flange Thickness (tf)", self._tf)
        logger.add_input("Modulus of Elasticity (E)", self._E)
        logger.add_input("Member Depth (d)", self._d)
        logger.add_input("Connection Length (lb)", self._connection_length)
        logger.add_input("End Plate Thickness (tpl)", self._end_plate_thickness)
        logger.add_input("Resistance Factor (phi)", resistance_factor)
        logger.add_input("Loading Condition", self._loading_condition)

        # Common term in AISC J10.3 equations
        ef_term = ((self._E * self._Fy * self._tf) / self._tw) ** 0.5
        ef_term = ef_term.to('ksi')
        logger.add_calculation("EF Term ((E*Fy*tf)/tw)^0.5", ef_term)

        # Determine which case of J10.3 applies
        clip_dist = 3 / 4 * si.inch
        connection_load_centroid = (
            self._connection_length / 2 + clip_dist + self._end_plate_thickness
        )
        logger.add_calculation("Connection Load Centroid", connection_load_centroid)

        # Ratio of bearing length to member depth
        lb_d_ratio = self._connection_length / self._d
        logger.add_calculation(
            "Bearing Length to Depth Ratio (lb/d)", lb_d_ratio
        )

        # Ratio of web thickness to flange thickness
        tw_tf_ratio = self._tw / self._tf
        logger.add_calculation(
            "Web to Flange Thickness Ratio (tw/tf)", tw_tf_ratio
        )

        nominal_capacity = 0.0

        # Case 1: Load is applied at a distance from the member end >= d
        if connection_load_centroid >= self._d/2:
            formula_part = 1 + 3 * (lb_d_ratio) * (tw_tf_ratio**1.5)
            nominal_capacity = 0.80 * self._tw**2 * formula_part * ef_term
            logger.add_calculation(
                "Formula Part (1 + 3*(lb/d)*(tw/tf)^1.5)", formula_part
            )
            logger.add_calculation(
                "Nominal Capacity (Rn) - Eq. J10-4", nominal_capacity
            )

        # Case 2: Load is applied at a distance from the member end < d
        else:
            # Subcase a: lb/d <= 0.2
            if lb_d_ratio <= 0.2:
                formula_part = 1 + 3 * (lb_d_ratio) * (tw_tf_ratio**1.5)
                nominal_capacity = 0.40 * self._tw**2 * formula_part * ef_term
                logger.add_calculation(
                    "Formula Part (1 + 3*(lb/d)*(tw/tf)^1.5)", formula_part
                )
                logger.add_calculation(
                    "Nominal Capacity (Rn) - Eq. J10-5a", nominal_capacity
                )
            # Subcase b: lb/d > 0.2
            else:
                formula_part = 1 + (4 * lb_d_ratio - 0.2) * (tw_tf_ratio**1.5)
                nominal_capacity = 0.40 * self._tw**2 * formula_part * ef_term
                logger.add_calculation(
                    "Formula Part (1 + (4*lb/d - 0.2)*(tw/tf)^1.5)",
                    formula_part,
                )
                logger.add_calculation(
                    "Nominal Capacity (Rn) - Eq. J10-5b", nominal_capacity
                )

        design_capacity = (
            nominal_capacity * resistance_factor * self._loading_condition
        )
        logger.add_output("Design Capacity (phiRn)", design_capacity)
        logger.display()

        return design_capacity

    def check_dcr(self, demand_force: si.kip, **kwargs) -> float:
        """Calculates the demand-to-capacity ratio."""
        capacity = self.calculate_capacity(**kwargs)
        if capacity == 0: return float('inf')
        return abs(demand_force / capacity)
class ShearYieldingCalculator:
    """
    Calculates the shear yielding capacity of a member based on AISC Specification J3.2.
    This class is designed to handle both L and U patterns for block shear calculations.
    """

    def __init__(self, endpoint: "ConnectionEndpoint", connection: Connection):
        self.endpoint = endpoint
        self.member = endpoint.member
        self.connection = connection # Keep the full connection for context
        self.config: Union[BoltConfiguration, WeldConfiguration] = connection.configuration
        self.connection_type = connection.connection_type
 
        # Extract common properties
        self.Fy = self.member.Fy
        self.Fu = self.member.Fu
        self.thickness = self._get_member_thickness()


    def _get_member_thickness(self) -> float:
        """Determines thickness from various member types and ensures it has units."""
        if hasattr(self.member, "t"):
            t_val = self.member.t
            if hasattr(t_val, 'units'):
                return t_val
            if isinstance(t_val, (int, float)):
                return t_val * si.inch
            return t_val
        elif hasattr(self.member, "tw"):
            tw_val = self.member.tw
            if isinstance(tw_val, (int, float)):
                return tw_val * si.inch
            return tw_val
        raise AttributeError("Member does not have a recognizable thickness attribute.")

    def calculate_capacity(self, resistance_factor: float = 1.0, debug: bool = False) -> float:
        """
        Calculates the design shear yielding strength (phiRn).
        """
        logger = DebugLogger(f"Shear Yielding ({self.endpoint.component.name})", debug)
        
        gross_area = get_applicable_gross_area(self.endpoint, self.connection)
        loading_condition = getattr(self.member, "loading_condition", 1)
        
        logger.add_input("Member Type", getattr(self.member, "Type", "N/A"))
        logger.add_input("Connection Type", self.connection_type)
        logger.add_input("Yield Strength (Fy)", self.Fy)
        logger.add_input("Ultimate Strength (Fu)", self.Fu)
        logger.add_input("Member Thickness (t)", self.thickness)
        logger.add_input(f"Applicable Gross Area (Ag) for {self.endpoint.component.name}", gross_area)
        logger.add_input("Loading Condition (Informational)", loading_condition)
        logger.add_input("Resistance Factor (phi)", resistance_factor)

        # Per AISC J4.2(a), the nominal strength for shear yielding is 0.6 * Fy * Ag
        nominal_capacity = 0.6 * self.Fy * gross_area
        design_capacity = resistance_factor * nominal_capacity

        logger.add_calculation("Nominal Capacity (0.6 * Fy * Ag)", nominal_capacity)
        logger.add_output("Design Capacity (phiRn)", design_capacity)
        logger.display()

        return design_capacity

    def check_dcr(self, demand_force: si.kip, **kwargs) -> float:
        """Calculates the demand-to-capacity ratio."""
        capacity = self.calculate_capacity(**kwargs)
        if capacity == 0: return float('inf')
        return abs(demand_force / capacity)


class PryingActionCalculator:
    """
    Calculates the effects of prying action on a bolted connection based on
    AISC Manual Part 9.
    """

    def __init__(self, plate: Plate,gusset: Plate , connection: Connection):
        """
        Initializes the calculator with the plate and connection objects.
        """
        if connection.connection_type != "bolted":
            raise ValueError("PryingActionCalculator only supports bolted connections.")
        self.connection = connection
        self.plate = plate
        self.plate_width = plate.width
        self.plate_length = plate.length
        self.gusset = gusset
        self.gusset_thickness = gusset.t
        self.config: BoltConfiguration = connection.configuration
        self.bolt_grade = self.config.bolt_grade
        self.bolt_diameter = self.config.bolt_diameter
        self.t = self.plate.t  # Plate thickness

        # Geometric properties from the connection
        self.p = self.config.column_spacing  # Tributary length per bolt
        self.g = self.config.row_spacing    # Gage distance
        
        # Distances 'a' and 'b' as defined in AISC Manual Part 9
        # 'a' is the distance from the bolt centerline to the edge of the fitting
        self.a = (self.plate_width - self.g) / 2
        # 'b' is the distance from the bolt centerline to the face of the supporting element
        self.b =  (self.g - self.gusset_thickness)/2

        # Derived geometric properties
        self.d_prime = self.bolt_diameter + (1 / 16) * si.inch # Effective hole diameter
        self.b_prime = self.b - self.bolt_diameter / 2
        self.a_prime = min(self.a,1.25 * self.b) + self.bolt_diameter / 2


        # Ratio of b' to a'
        self.p_ = self.b_prime / self.a_prime
        # Delta: ratio of unstiffened to stiffened length
        self.delta = 1 - (self.d_prime / self.p)
        
        # Bolt properties
        self.bolt_area = (self.bolt_diameter**2 / 4) * math.pi

        # Get total number of bolts 
        self.n_rows = self.config.n_rows
        self.n_columns = self.config.n_columns
        self.n_bolts = self.n_rows * self.n_columns

        # This Values are hardcoded and will be updated later 
        self.shear_force = 302 * si.kip
        self.tension_force = 176 * si.kip
        
        self.B = BoltShearCalculator(self.connection).calculate_capacity_fnt_modified(302 * si.kip,debug=True)

    def _calculate_alpha_prime(self, debug: bool = False) -> float:
        """
        Calculates the intermediate variable alpha' (alpha_prime).
        """
        logger = DebugLogger("Alpha Prime Calculation", debug)
        
        if self.B == 0:
            logger.add_calculation("Condition", "B is zero, returning infinity.")
            logger.display()
            return float('inf')
            
        tc = self._calculate_t_req()
        ratio = tc / self.t
        
        logger.add_input("Available Bolt Strength (B)", self.B)
        logger.add_input("Required Thickness (tc)", tc)
        logger.add_input("Plate Thickness (t)", self.t)
        logger.add_input("Delta (1 - d'/p)", self.delta)
        logger.add_input("Rho (b'/a')", self.p_)
        
        logger.add_calculation("Thickness Ratio (tc/t)", ratio)
        logger.add_calculation("Thickness Ratio Squared ((tc/t)^2)", ratio**2)
        logger.add_calculation("Denominator Term (delta * (1 + rho))", self.delta * (1 + self.p_))

        if self.delta == 0:
            logger.add_calculation("Condition", "Delta is zero, returning infinity.")
            logger.display()
            return float('inf')

        alpha_prime = (1 / (self.delta * (1 + self.p_))) * (ratio**2 - 1)
        logger.add_calculation(
            "Alpha Prime Formula",
            f"(1 / ({self.delta:.3f} * (1 + {self.p_:.3f}))) * (({ratio:.3f})^2 - 1)"
        )
        logger.add_output("Calculated Alpha Prime (alpha')", alpha_prime)
        
        logger.display()
        return alpha_prime
    
    def _calculate_t_req(self, debug: bool = False) -> si.inch:
        """
        Calculates the required thickness (t_req) to eliminate prying action.
        """
        logger = DebugLogger("Required Thickness (t_req) Calculation", debug)
        
        numerator = 4 * self.B * self.b_prime
        denominator = self.p * self.plate.Fu * 0.9
        
        logger.add_input("Available Bolt Strength (B)", self.B)
        logger.add_input("Distance b'", self.b_prime)
        logger.add_input("Tributary Length (p)", self.p)
        logger.add_input("Plate Fu", self.plate.Fu)
        
        logger.add_calculation("Numerator (4 * B * b')", numerator)
        logger.add_calculation("Denominator (p * Fy)", denominator)

        if denominator == 0:
            logger.add_calculation("Condition", "Denominator is zero, returning infinity.")
            logger.display()
            return float('inf') * si.inch

        t_req = ((numerator / denominator)**0.5)
        logger.add_calculation("t_req Formula", "sqrt( (4 * B * b') / (p * Fy) )")
        logger.add_output("Required Thickness (t_req)", t_req)
        logger.display()
        return t_req


    def calculate_Q(self, debug: bool = False) -> float:
        """
        Calculates the prying force factor 'Q'. Returns a unitless factor.
        """
        logger = DebugLogger("Prying Factor (Q) Calculation", debug)
        
        # Pass debug flag to dependent calculations
        alpha_prime = self._calculate_alpha_prime(debug=debug)
        tc = self._calculate_t_req(debug=debug)
        
        logger.add_input("Plate Thickness (t)", self.t)
        logger.add_input("Required Thickness (tc)", tc)
        logger.add_input("Alpha Prime (alpha')", alpha_prime)
        logger.add_input("Delta (delta)", self.delta)

        Q = 0.0
        if tc == 0: # Avoid division by zero
            logger.add_calculation("Condition", "tc is zero, Q is set to a large value to indicate failure.")
            Q = float('inf')
        elif alpha_prime < 0:
            Q = 1.0
            logger.add_calculation("Condition: alpha' < 0", "Q is set to 1.0")
        elif 0 <= alpha_prime <= 1:
            ratio_sq = (self.t / tc)**2
            term = (1 + (self.delta * alpha_prime))
            Q = ratio_sq * term
            logger.add_calculation("Thickness Ratio Squared (t/tc)^2", ratio_sq)
            logger.add_calculation("Term (1 + delta*alpha')", term)
            logger.add_calculation("Condition: 0 <= alpha' <= 1", f"Q = {ratio_sq:.3f} * {term:.3f}")
        elif alpha_prime > 1:
            ratio_sq = (self.t / tc)**2
            term = (1 + self.delta)
            Q = ratio_sq * term
            logger.add_calculation("Thickness Ratio Squared (t/tc)^2", ratio_sq)
            logger.add_calculation("Term (1 + delta)", term)
            logger.add_calculation("Condition: alpha' > 1", f"Q = {ratio_sq:.3f} * {term:.3f}")
        
        logger.add_output("Prying Factor (Q)", Q)
        logger.display()
        return Q

    def calculate_bolt_tension_with_prying(self) -> si.kip:
        """
        Calculates the total tension in the bolt, including prying force.
        T_total = T_req + Q
        """
        Q = self.calculate_Q(debug=False) # Debugging is handled in the main check_dcr
        return self.B * Q

    def check_dcr(self,resistance_factor: float = 0.75, debug: bool = False) -> float:
        """
        Calculates the DCR for prying action.
        DCR = (T_req) / (phi * B * Q)
        """
        available_strength = self.calculate_bolt_tension_with_prying()
        design_capacity = (resistance_factor * available_strength).to('kip')
        
        logger = DebugLogger("Prying Action", debug)
        logger.add_input("Required Tension per Bolt (T_req)", self.tension_force/( self.n_bolts))
        logger.add_input("Plate Width (w)", self.plate.width)
        logger.add_input("Plate Thickness (t)", self.plate.t)
        logger.add_input("Plate Fy", self.plate.Fy)
        logger.add_input("Gusset Thickness", self.gusset_thickness)
        logger.add_input("Bolt Diameter", self.bolt_diameter)
        logger.add_input("Bolt Fnt", self.bolt_grade.Fnt)
        logger.add_input("Tributary Length (p)", self.p)
        logger.add_input("Gage (g)", self.g)
        logger.add_input("Resistance Factor (phi)", resistance_factor)
        
        logger.add_calculation("Distance 'a'", self.a)
        logger.add_calculation("Distance 'b'", self.b)
        logger.add_calculation("Effective Hole Diameter (d')", self.d_prime)
        logger.add_calculation("b'", self.b_prime)
        logger.add_calculation("a'", self.a_prime)
        logger.add_calculation("Fnt Modified (Fnt_modified)", self.B)
        logger.add_calculation("rho (b'/a')", self.p_)
        logger.add_calculation("delta (1 - d'/p)", self.delta)
        logger.add_calculation("Bolt Area (Ab)", self.bolt_area)

        # All calculations are now called with the debug flag and log themselves.
        # The main logger just needs to show the final results.
        Q = self.calculate_Q(debug=debug)
        
        logger.add_calculation("Available Bolt Strength with Prying (B*Q)", available_strength)
        logger.add_output("Available Design Strength (phi*B*Q)", design_capacity)
        
        logger.display()

        if design_capacity == 0:
            return float('inf')
            
        return self.tension_force/( self.n_bolts) / design_capacity.to('kip')


3