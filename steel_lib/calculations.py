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
    
    ConnectionComponent,
    DesignLoads,
    BeamColumnTransferredForce,result,Connection,ConnectionEndpoint
)
from .debugging import DebugLogger
from abc import ABC, abstractmethod
from handcalcs.decorator import handcalc
# Define a type hint for numbers for clarity
Numeric = Union[int, float]
jupyter_format = "long"
jupyter_display = True
pi = math.pi
def get_applicable_gross_area(endpoint: "ConnectionEndpoint") -> float:
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
    connection = endpoint.connection_configuration
    # # 1. Prioritize the manual override from the parent connection
    # if connection.override_Ag is not None:
    #     return connection.override_Ag

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

def get_load(member: "Connection", load_type: str) -> si:
    """
    Retrieves the specified load type from the connection's members.
    If the load is not defined or the loads attribute is missing, it defaults to zero.

    Args:
        connection (Connection): The connection object containing loads.
        load_type (str): The type of load to retrieve (e.g., "Vu", "Pu", "Mu").

    Returns:
        dict[str, float]: A dictionary with the specified loads for the primary and secondary members.
    """
    def safe_get_load(member, load_type) -> float:
        """Safely retrieves the specified load from a member's loads, defaulting to zero if not available."""
        if hasattr(member, "loads") and hasattr(member.loads, load_type):
            return getattr(member.loads, load_type, 0.0)
        return 0.0

    return safe_get_load(member, load_type)

   
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
        return thickness
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


def check_dcr(capacity: float, demand: float, limit_state_name: str, debug: bool = False) -> float:
    """
    Calculates the demand-to-capacity ratio (DCR) and provides detailed logging.

    Args:
        capacity (float): The calculated capacity of the component.
        demand (float): The applied demand on the component.
        limit_state_name (str): The name of the limit state being checked (for logging).
        debug (bool): If True, detailed debug information will be printed.

    Returns:
        float: The demand-to-capacity ratio.
    """
    logger = DebugLogger(f"DCR Check: {limit_state_name}", debug)
    logger.add_input("Demand", demand)
    logger.add_input("Capacity", capacity)

    if capacity == 0:
        dcr = float('inf')
        logger.add_output("DCR", "Infinity (capacity is zero)")
    else:
        dcr = demand / capacity
        logger.add_output("DCR (Demand / Capacity)", dcr)
    
    logger.display()
    dcr = result(demand=demand, capacity=capacity, dcr=dcr, name=limit_state_name)
    return dcr

# @dataclass(frozen=True)
# class AppliedLoads:
#     """
#     A single, immutable container for all initial and calculated loads.
#     Should be constructed using one of its factory classmethods.
#     """
#     # Initial Design Loads
#     initial_brace_load: si.kip
#     initial_beam_shear: si.kip
#     initial_transfer_force: si.kip

#     # Calculated Interface Forces
#     gusset_to_column_shear: si.kip
#     gusset_to_column_normal: si.kip
#     gusset_to_beam_shear: si.kip
#     gusset_to_beam_normal: si.kip

#     gusset_beam_interface: DesignLoads
#     gusset_endplate_interface: DesignLoads
#     beam_column_interface:DesignLoads

#     @classmethod
#     def from_ufm(
#         cls,
#         design_loads: "DesignLoads", # We'll define this helper next
#         multipliers: "LoadMultipliers"
#     ) :
#         """
#         Factory method to create an AppliedLoads object using the
#         Uniform Force Method calculations.
#         """
#         # Perform the load distribution calculations here
#         vuc = multipliers.vertical_force_column_interface * design_loads.Pu
#         vub = multipliers.vertical_force_beam_interface * design_loads.Pu
#         huc = multipliers.horizontal_force_column_interface * design_loads.Pu
#         hub = multipliers.horizontal_force_beam_interface * design_loads.Pu
        
#         # Add Aub and Vu to the column interface forces
#         total_column_shear = huc + design_loads.Vu
#         total_column_normal = vuc + design_loads.Aub
#         total_column_shear = huc 
#         total_column_normal = vuc 
#         # Calculate gusset to beam forces
#         gusset_beam_interface = DesignLoads(
#             Pu=vub,
#             Vu=hub,
#         )
#         # Calculate gusset to endplate forces
#         gusset_endplate_interface = DesignLoads(
#             Pu=total_column_shear,
#             Vu=total_column_normal,
#         )
#         # Calculate beam-column interface forces

#         return cls(
#             initial_brace_load=design_loads.Pu,
#             initial_beam_shear=design_loads.Vu,
#             initial_transfer_force=design_loads.Aub,
#             gusset_to_column_shear=total_column_shear,
#             gusset_to_column_normal=total_column_normal,
#             gusset_to_beam_shear=hub,
#             gusset_to_beam_normal=vub,
#         )
    
class LimitState(ABC):
    """
    Abstract base class for all capacity calculators.
    Enforces the implementation of calculate_capacity and check_dcr methods.
    """

    @abstractmethod
    def calculate_capacity(self, *args, **kwargs) -> float:
        """
        Abstract method to calculate the design capacity.
        Must be implemented by all subclasses.
        """
        pass

    @abstractmethod
    def check_dcr(self, *args, **kwargs) -> float:
        """
        Abstract method to calculate the demand-to-capacity ratio (DCR).
        Must be implemented by all subclasses.
        """
        pass
@handcalc(jupyter_display=True, precision=3, override=jupyter_format)
def area_circular_bolt(diameter: si.inch) :
    """Calculates the gross area of a circular bolt."""
    A_bolt = diameter**2 / 4 * pi
    return A_bolt

class BoltShearCalculator(LimitState):
    """
    Calculates the shear strength of a single bolt based on its properties.
    """
    def __init__(self, endpoint:ConnectionEndpoint,debug: bool = False):
        """
        Initializes the calculator with a Connection object.
        Assumes a 'bolted' connection configuration.
        """
        self.name = "Bolt Shear Strength"
        self.endpoint = endpoint
        self.bolt_config: BoltConfiguration = endpoint.connection_configuration
        print(self.bolt_config)
        self.bolt_area = area_circular_bolt(self.bolt_config.bolt_diameter)
        self.fnv = self.bolt_config.bolt_grade.Fnv
        self.no_bolts = self.bolt_config.n_rows * self.bolt_config.n_columns
        self.design_method = endpoint.design_method
        self._debug = debug

    @property
    def demand_loads(self) -> float:
        """Returns the shear demand on the bolt."""
        self.loads_vu = get_load(self.endpoint, "Vu")
        self.loads_pu = get_load(self.endpoint, "Pu")
        return ((self.loads_vu**2 + self.loads_pu**2) **0.5).to("kip")/self.no_bolts
    @property
    def resistance_factor(self) -> float:
        """Returns the resistance factor for bolt shear."""
        if self.design_method == "LRFD":
            return 0.75
        elif self.design_method == "ASD":
            return 2
        
    @handcalc(jupyter_display=jupyter_display, precision=3, override=jupyter_format)
    def calculations(self,F_nv: float,A_bolt: float,N_shear_planes: int,phi: float):
        nominal_strength = F_nv * A_bolt * N_shear_planes
        design_strength = phi * nominal_strength
        return design_strength
    def calculate_capacity(self
    ) -> float:
        """
        Calculates the design shear strength of the bolt.
        """
        debug = self._debug
        logger = DebugLogger("Bolt Shear Strength", debug)
        logger.add_input("Nominal Shear Stress (Fnv)", self.fnv)
        logger.add_input("Bolt Area (Ab)", self.bolt_area)
        
        number_of_shear_planes = self.endpoint.shear_condition
        resistance_factor = self.resistance_factor
        logger.add_input("Number of Shear Planes", number_of_shear_planes)
        logger.add_input("Resistance Factor (phi)", resistance_factor)
        # Nominal strength (Rn) = Fnv * Ab * Ns
        design_strength = self.calculations(self.fnv,self.bolt_area,number_of_shear_planes,resistance_factor)

        # Design strength (phiRn) = phi * Rn

        logger.add_output("Design Strength (phiRn)", design_strength)

        logger.display()
        return design_strength

    def check_dcr(self) -> float:
        """Calculates the demand-to-capacity ratio for Fnv."""
        demand_force = self.demand_loads
        capacity = self.calculate_capacity()
        return check_dcr(capacity, abs(demand_force), self.name)
        
    # def calculate_capacity_fnt(
    #     self,
    #     number_of_shear_planes: int = 1,
    #     resistance_factor: float = 0.75,
    #     debug: bool = False,
    # ) -> float:
    #     """
    #     Calculates the design tensile strength of the bolt.
    #     """
    #     logger = DebugLogger("Bolt Tensile Strength", debug)
    #     fnt = self.bolt_config.bolt_grade.Fnt
    #     logger.add_input("Nominal Tensile Stress (Fnt)", fnt)
    #     logger.add_input("Bolt Area (Ab)", self.bolt_area)
    #     logger.add_input("Number of Shear Planes", number_of_shear_planes)
    #     logger.add_input("Resistance Factor (phi)", resistance_factor)

    #     # Nominal strength (Rn) = Fnt * Ab * Ns
    #     nominal_strength = fnt * self.bolt_area * number_of_shear_planes
    #     logger.add_calculation("Nominal Strength (Rn = Fnt * Ab * Ns)", nominal_strength)

    #     # Design strength (phiRn) = phi * Rn
    #     design_strength = resistance_factor * nominal_strength
    #     logger.add_output("Design Strength (phiRn)", design_strength)

    #     logger.display()
    #     return design_strength


class BoltTensileCalculator(LimitState):
    """
    Calculates the shear strength of a single bolt based on its properties.
    """
    def __init__(self, endpoint:ConnectionEndpoint,debug: bool = False):
        """
        Initializes the calculator with a Connection object.
        Assumes a 'bolted' connection configuration.
        """
        self.name = "Bolt Tensile Strength"
        self.endpoint = endpoint
        self.bolt_config: BoltConfiguration = endpoint.connection_configuration
        self.bolt_area = area_circular_bolt(self.bolt_config.bolt_diameter)
        self.fnv = self.bolt_config.bolt_grade.Fnv
        self.no_bolts = self.bolt_config.n_rows * self.bolt_config.n_columns
        self.design_method = endpoint.design_method
        self._debug = debug

    @property
    def demand_loads_shear(self) -> float:
        """Returns the shear demand on the bolt."""
        self.loads_vu = get_load(self.endpoint, "Vu")
        self.loads_pu = get_load(self.endpoint, "Pu")
        return ((self.loads_vu**2 + self.loads_pu**2) **0.5).to("kip")
    
    @property
    def resistance_factor(self) -> float:
        """Returns the resistance factor for bolt shear."""
        if self.design_method == "LRFD":
            return 0.75
        elif self.design_method == "ASD":
            return 2

    @handcalc(jupyter_display=jupyter_display, precision=3, override="params")
    def parameters(self,Vu,no_bolts,F_nv,F_nt,A_bolt,phi):
        Vu = Vu
        no_bolts = no_bolts
        F_nv = F_nv
        F_nt = F_nt
        A_bolt = A_bolt
        phi = phi
    @handcalc(jupyter_display=jupyter_display, precision=3, override=jupyter_format)
    def calculations(self,Vu,no_bolts,F_nv,F_nt_,A_bolt,phi):
        shear_bolt = Vu / no_bolts
        F_rv = shear_bolt/A_bolt
        interaction_coefficient = F_rv / (phi * F_nv) # Ratio of required shear stress to available shear stress
        F_prime_nt = 1.3 * F_nt_ - F_nt_ * interaction_coefficient 
        F_nt = min(F_prime_nt, F_nt_) * A_bolt * phi
        return F_nt

    def calculate_capacity(
        self
    ):
        """
        Calculates the modified design tensile strength of the bolt, considering interaction with shear.
        """
        debug = self._debug
        logger = DebugLogger("Modified Bolt Tensile Strength (Interaction)", debug)
        demand_force_shear = self.demand_loads_shear
        fnv = self.bolt_config.bolt_grade.Fnv
        fnt = self.bolt_config.bolt_grade.Fnt
        print(fnt)
        resistance_factor = self.resistance_factor
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
        print(demand_force_shear)
        frv = shear_per_bolt / self.bolt_area
        logger.add_calculation("Shear per Bolt (V / n_bolts)", shear_per_bolt)
        logger.add_calculation("Required Shear Stress (frv = V_per_bolt / Ab)", frv)

        # The term (Fnt / (phi * Fnv)) is the interaction coefficient
        interaction_coefficient = frv / (resistance_factor * fnv)
        logger.add_calculation("Interaction Coefficient (Fnt / (phi * Fnv))", interaction_coefficient)
        
        # Calculate the nominal modified tensile stress
        print(fnt,frv,interaction_coefficient)
        modified_fnt_nominal = 1.3 * fnt - fnt * interaction_coefficient 
        logger.add_calculation("Modified F'nt (Nominal, before cap)", modified_fnt_nominal)

        # The result cannot be greater than the nominal tensile stress Fnt
        final_fnt_modified = min(modified_fnt_nominal, fnt) * self.bolt_area * resistance_factor
        logger.add_output("Final Modified Tensile Stress (F'nt)", final_fnt_modified)        
        logger.display()
        paramssad = self.parameters(Vu=demand_force_shear,no_bolts=self.no_bolts,F_nv=fnv,F_nt=fnt,A_bolt=self.bolt_area,phi=resistance_factor)
        
        self.calculations(Vu=demand_force_shear,no_bolts=self.no_bolts,F_nv=fnv,F_nt_=self.bolt_config.bolt_grade.Fnt,A_bolt=self.bolt_area,phi=resistance_factor)
        return final_fnt_modified
    
    def check_dcr(self) -> float:
        """Calculates the demand-to-capacity ratio for Fnt."""
        demand_load = get_load(self.endpoint, "out_of_plane_force")
        capacity = self.calculate_capacity()
        return check_dcr(capacity, abs(demand_load)/self.no_bolts, "Bolt Tensile Strength")
    
    

class TensileYieldingCalculator:
    """
    Calculates the tensile yielding capacity of a member.
    """
    def __init__(self, endpoint: "ConnectionEndpoint",debug:bool = False):
        self.endpoint = endpoint
        self.member = endpoint.member
        self.connection = endpoint.connection_configuration
        self.Fy = self.member.Fy
        self.Ag = get_applicable_gross_area(endpoint)
        self.loading_condition = getattr(self.member, 'loading_condition', 1)
        self.load = endpoint.loads
    @handcalc(jupyter_display=jupyter_display, precision=3, override=jupyter_format)
    def calculations(self,F_y,A_g,load_condition,phi):
        P_n = F_y * A_g
        P_u = phi * P_n * load_condition
        return P_u
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
        self.calculations(F_y = self.Fy,A_g = self.Ag,load_condition = self.loading_condition,phi =resistance_factor)
        return design_strength

    def check_dcr(self, **kwargs) -> float:
        """Calculates the demand-to-capacity ratio."""
        capacity = self.calculate_capacity(**kwargs)
        return check_dcr(capacity, abs(self.load.Pu), f"Tensile Yielding ({self.endpoint.component.name})", **kwargs)

class TensileRuptureCalculator:
    """
    Calculates the tensile rupture capacity of a member.
    """
    def __init__(self, endpoint: "ConnectionEndpoint",debug:bool = False):
        self.endpoint = endpoint
        self.member = endpoint.member
        self.bolt_config = endpoint.connection_configuration
        self.Fu = self.member.Fu
        self.loading_condition = getattr(self.member, 'loading_condition', 1)
        self.loads = self.endpoint.loads
    @handcalc(jupyter_display=jupyter_display, precision=3, override=jupyter_format)
    def ubs(self,S_c,N_c,x_bar) -> float:
        l = S_c * (N_c - 1)
        Ubs = 1 - (x_bar / l) if l > 0 else 1.0
        return Ubs
    @handcalc(jupyter_display=jupyter_display, precision=3, override=jupyter_format)
    def A_net(self,dbolt,n_rows,t,A_g,ubs):
        dhole = dbolt + 1/8 * si.inch
        A_deduction = dhole * n_rows * t
        A_n_gross = A_g - A_deduction
        A_e = A_n_gross * ubs
        return A_e
    @handcalc(jupyter_display=jupyter_display, precision=3, override=jupyter_format)
    def strength_calculations(self,F_u, A_e, phi, load_condition):
        P_n = F_u * A_e
        P_u = phi * P_n * load_condition
        return P_u

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
        Ag = get_applicable_gross_area(self.endpoint)
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
        dhole = dbolt + 1/8
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
        a = self.ubs(S_c=S_c,N_c=N_c,x_bar=x_bar)
        b = self.A_net(dbolt=dbolt,n_rows=n_rows,t=t,A_g=Ag,ubs=Ubs)
        c = self.strength_calculations(F_u=self.Fu, A_e=Ae, phi=resistance_factor, load_condition=self.loading_condition)
        return design_strength

    def check_dcr(self, **kwargs) -> float:
        """Calculates the demand-to-capacity ratio."""
        capacity = self.calculate_capacity(**kwargs)
        return check_dcr(capacity, abs(self.loads.Pu), f"Tensile Rupture ({self.endpoint.component.name})", **kwargs)

MemberType = Any # Use 'Any' for robust compatibility with steelpy objects
LoadingOrientation = Literal["Axial", "Shear"]

class BlockShearCalculator:
    """
    Calculates block shear capacity with correct unit handling and debug mode.
    """
    def __init__(
        self,
        endpoint: "ConnectionEndpoint",debug:bool = False
    ):
        self.loads = endpoint.loads
        self.endpoint = endpoint
        self.member = endpoint.member
        self.bolt_config: BoltConfiguration = endpoint.connection_configuration
        
        self.loading_condition = self.member.loading_condition if hasattr(self.member, 'loading_condition') else 1
        self.row_spacing = self.bolt_config.row_spacing
        self.column_spacing = self.bolt_config.column_spacing
        #check if member have width or d then use which is applicable
        if hasattr(self.member, 'width'):
            self.width = self.member.width
        elif hasattr(self.member, 'd'):
            self.width = self.member.d
        print(f"Member width: {self.width}")


        # CORRECTED: _get_member_thickness now always returns a unit-aware value
        self.thickness = get_applicable_thickness(endpoint)
        self.bolt_hole_diameter = self.bolt_config.bolt_diameter + 1/8 * si.inch
        self.failure_pattern = []
        print(self.loads.Vu,self.member.Type == "L",self.loads.Pu)
        if self.loads.Vu > 0.00001 or self.member.Type == "L":
            self.failure_pattern.append("L")
        if self.loads.Pu > 0.00001 and self.member.Type != "L":
            self.failure_pattern.append("U")
    # --- Calculation methods now correctly include loading_condition ---

    def _calculate_l_shear_yield_path(self, debug=False) -> float:
        logger = DebugLogger("L-Pattern Gross Shear Area (Agv)", debug)
        # spacing, rows, edge_dist = (self.bolt_config.row_spacing, self.bolt_config.n_rows, self.bolt_config.edge_distance_vertical) if self.loading_orientation == "Shear" else (self.bolt_config.column_spacing, self.bolt_config.n_columns, self.bolt_config.edge_distance_horizontal)
        spacing, rows, edge_dist = (self.bolt_config.row_spacing, self.bolt_config.n_rows, self.bolt_config.edge_distance_vertical)
        logger.add_input("Spacing", spacing)
        logger.add_input("Rows/Columns", rows)
        logger.add_input("Edge Distance", edge_dist)
        
        length = spacing * (rows - 1) + edge_dist
        logger.add_calculation("Gross Length (Lgv = spacing * (rows - 1) + edge_dist)", length)
        
        area = length * self.thickness * self.loading_condition
        logger.add_output("Gross Shear Area (Agv = Lgv * t * loading_condition)", area)
        logger.display()
        return area

    def _calculate_l_shear_rupture_path(self, debug=False) -> float:
        logger = DebugLogger("L-Pattern Net Shear Area (Anv)", debug)
        gross_area = self._calculate_l_shear_yield_path(debug=False) # Don't double-log inputs
        # rows = self.bolt_config.n_rows if self.loading_orientation == "Shear" else self.bolt_config.n_columns
        rows = self.bolt_config.n_rows
        logger.add_input("Gross Shear Area (Agv)", gross_area)
        logger.add_input("Rows/Columns", rows)
        logger.add_input("Bolt Hole Diameter", self.bolt_hole_diameter)
        logger.add_input("Thickness", self.thickness)

        hole_area_deduction = (rows - 0.5) * self.bolt_hole_diameter * self.thickness * self.loading_condition
        logger.add_calculation("Hole Deduction ((rows - 0.5) * d_hole * t)", hole_area_deduction)

        net_area = gross_area - hole_area_deduction
        logger.add_output("Net Shear Area (Anv = Agv - deduction)", net_area)
        logger.display()
        return net_area
    
    def _calculate_l_tension_rupture_path(self, debug=False) -> float:
        logger = DebugLogger("L-Pattern Net Tension Area (Ant)", debug)
        # if self.loading_orientation == "Axial":
        #     spacing, rows, edge_dist = self.bolt_config.row_spacing, self.bolt_config.n_rows, self.bolt_config.edge_distance_vertical
        # else:
        #     spacing, rows, edge_dist = self.bolt_config.column_spacing, self.bolt_config.n_columns, self.bolt_config.edge_distance_horizontal
        spacing, rows, edge_dist = self.bolt_config.row_spacing, self.bolt_config.n_rows, self.bolt_config.edge_distance_vertical
        logger.add_input("Spacing", spacing)
        logger.add_input("Rows/Columns", rows)
        logger.add_input("Edge Distance", edge_dist)
        logger.add_input("Bolt Hole Diameter", self.bolt_hole_diameter)
        logger.add_input("Thickness", self.thickness)

        gross_length = spacing * (rows - 1) + edge_dist
        logger.add_calculation("Gross Tension Length", gross_length)
        
        hole_deduction_length = (rows - 0.5) * self.bolt_hole_diameter
        logger.add_calculation("Hole Deduction Length", hole_deduction_length)

        net_length = gross_length - hole_deduction_length
        logger.add_calculation("Net Length (Lnt)", net_length)

        net_area = net_length * self.thickness * self.loading_condition
        logger.add_output("Net Tension Area (Ant = Lnt * t * loading_condition)", net_area)
        logger.display()
        return net_area
    

    def _calculate_u_tension_rupture_path(self, debug=False) -> float:
        logger = DebugLogger("U-Pattern Net Tension Area (Ant)", debug)
        spacing, rows = self.bolt_config.row_spacing, self.bolt_config.n_rows
        
        logger.add_input("Spacing", spacing)
        logger.add_input("Rows", rows)
        logger.add_input("Bolt Hole Diameter", self.bolt_hole_diameter)
        logger.add_input("Thickness", self.thickness)

        gross_length = spacing * (rows - 1)
        logger.add_calculation("Gross Length", gross_length)

        hole_deduction_length = (rows - 1) * self.bolt_hole_diameter
        logger.add_calculation("Hole Deduction Length", hole_deduction_length)

        net_length = gross_length - hole_deduction_length
        logger.add_calculation("Net Length (Lnt)", net_length)
        if self.width:
            net_area0 = net_length * self.thickness * self.loading_condition

            net_area1 = ((self.width - self.row_spacing)/2 - self.bolt_hole_diameter/2) * self.thickness * 2
            net_area = min(net_area0, net_area1)
        else:
            net_area = net_length * self.thickness * self.loading_condition
        
        logger.add_output("Net Tension Area (Ant = Lnt * t * loading_condition)", net_area)
        logger.display()
        return net_area  # Ensure we return the minimum of the two calculated areas
    def get_properties(self,load_type):
        if load_type == "axial":
            N_para,S_para,l_e_para,N_perp,S_perp,L_e_perp = self.bolt_config.n_columns,self.bolt_config.column_spacing,self.bolt_config.edge_distance_horizontal, self.bolt_config.n_rows,self.bolt_config.row_spacing,self.bolt_config.edge_distance_vertical
        elif load_type == "shear":
            N_para,S_para,l_e_para,N_perp,S_perp,L_e_perp = self.bolt_config.n_rows,self.bolt_config.row_spacing,self.bolt_config.edge_distance_vertical, self.bolt_config.n_columns,self.bolt_config.column_spacing,self.bolt_config.edge_distance_horizontal
        return N_para,S_para,l_e_para,N_perp,S_perp,L_e_perp
    def _calculation(self,d_bolt,t,width,load_condition,F_y,F_u):
        @handcalc(jupyter_display=jupyter_display, precision=3, override=jupyter_format)
        def _calculation_l_shear_yield_path(S_r,N_r,L_eh,t,load_condition):
            l = S_r * (N_r - 1) + L_eh
            A_gp = l * t * load_condition
            return A_gp
        @handcalc(jupyter_display=jupyter_display, precision=3, override=jupyter_format)
        def _calculation_l_shear_rupture_path(A_gp,N_r,d_bolt,t,load_condition):
            A_hole = (N_r - 0.5) * d_bolt * t * load_condition
            A_net = A_gp - A_hole
            return A_net
        @handcalc(jupyter_display=jupyter_display, precision=3, override=jupyter_format)
        def _calculation_l_tension_rupture_path(S_r,N_r,L_ev,d_bolt,t,load_condition):
            l_gross = S_r * (N_r - 1) + L_ev
            A_hole = (N_r - 0.5) * d_bolt
            l_net = l_gross - A_hole
            A_net = l_net * t * load_condition
            return A_net
        @handcalc(jupyter_display=jupyter_display, precision=3, override=jupyter_format)
        def _calculation_u_tension_rupture_path(S_r,N_r,d_bolt,t,width) -> float:
            l_g = S_r * (N_r - 1)
            A_hole = (N_r - 1) * d_bolt
            l_net = l_g - A_hole
            A_net_1 = l_net * t * self.loading_condition
            if width > 0.000001 * si.inch :A_net_2 = ((width - S_r)/2 - d_bolt/2) * t * 2;A_net = min(A_net_1, A_net_2)
            else: A_net = A_net_1
            return A_net
# net_area = min(A_net_1, A_net_2)
# return net_area
        @handcalc(jupyter_display=jupyter_display, precision=3, override=jupyter_format)
        def _calculation_block_shear(F_y,F_u,A_gv,A_nv,A_nt):
            U_bs = 1
            V_n_1 = 0.60 * F_y * A_gv
            V_n_2 = 0.60 * F_u * A_nv
            V_n = min(V_n_1, V_n_2)
            P_n = V_n + F_u * A_nt * U_bs
            return P_n
        if "L" in self.failure_pattern  :
            N_para,S_para,l_e_para,N_perp,S_perp,L_e_perp = self.get_properties("axial")
            A_g_shear = _calculation_l_shear_yield_path(S_para,N_para,l_e_para,t,load_condition)
            A_n_shear = _calculation_l_shear_rupture_path(A_g_shear,N_para,d_bolt,t,load_condition)
            A_n_tension = _calculation_l_tension_rupture_path(S_perp,N_perp,L_e_perp,d_bolt,t,load_condition)
            _calculation_block_shear(F_y = F_y,F_u = F_u,A_gv = A_g_shear,A_nv = A_n_shear,A_nt = A_n_tension)
        elif "U" in  self.failure_pattern:
            N_para,S_para,l_e_para,N_perp,S_perp,L_e_perp = self.get_properties("axial")
            A_g_shear = _calculation_l_shear_yield_path(S_r=S_para,N_r=N_para,L_eh=l_e_para,t=t,load_condition = load_condition)* 2
            A_n_shear = _calculation_l_shear_rupture_path(A_g_shear*0.5,N_para,d_bolt,t,load_condition) * 2
            A_n_tension = _calculation_u_tension_rupture_path(S_perp,N_perp,d_bolt,t,width)
            _calculation_block_shear(F_y = F_y,F_u = F_u,A_gv = A_g_shear,A_nv = A_n_shear,A_nt = A_n_tension)
        # A_g_shear = _calculation_l_shear_yield_path(S_r,N_r,L_eh,t,load_condition)
    def calculate_capacity(self, resistance_factor: float = 0.75, debug: bool = False) -> float:
        """
        Calculates the block shear capacity with detailed logging of all inputs and outputs.
        """
        logger = DebugLogger(f"Block Shear {self.failure_pattern}-Pattern", debug)
        
        Ubs = 1.0  # Shear lag factor, typically 1.0 for block shear
        Fu, Fy = self.member.Fu, self.member.Fy
        
        logger.add_input("Member Type", self.member.Type)
        logger.add_input("Failure Pattern", self.failure_pattern)
        logger.add_input("Ultimate Strength (Fu)", Fu)
        logger.add_input("Yield Strength (Fy)", Fy)
        logger.add_input("Thickness (t)", self.thickness)
        logger.add_input("Bolt Hole Diameter", self.bolt_hole_diameter)
        logger.add_input("Shear Lag Factor (Ubs)", Ubs)
        logger.add_input("Resistance Factor (phi)", resistance_factor)
        logger.add_input("Loading Condition Multiplier", self.loading_condition)
        logger.add_input("--- Bolt Configuration ---", "")
        logger.add_input("Bolt Rows (n_rows)", self.bolt_config.n_rows)
        logger.add_input("Bolt Columns (n_columns)", self.bolt_config.n_columns)
        logger.add_input("Row Spacing", self.bolt_config.row_spacing)
        logger.add_input("Column Spacing", self.bolt_config.column_spacing)
        logger.add_input("Vertical Edge Distance", self.bolt_config.edge_distance_vertical)
        logger.add_input("Horizontal Edge Distance", self.bolt_config.edge_distance_horizontal)
        logger.add_input("------------------------", "")

        tension_rupture_component = 0.0

        if "L" in self.failure_pattern:
            shear_yield_component = self._calculate_l_shear_yield_path(debug=debug)
            shear_rupture_component = self._calculate_l_shear_rupture_path(debug=debug)
            tension_rupture_component = self._calculate_l_tension_rupture_path(debug=debug)
        elif "U" in self.failure_pattern:
            shear_yield_component = self._calculate_l_shear_yield_path(debug=debug) * 2
            shear_rupture_component = self._calculate_l_shear_rupture_path(debug=debug) * 2
            tension_rupture_component = self._calculate_u_tension_rupture_path(debug=debug)

        logger.add_calculation("Gross Shear Area (Agv)", shear_yield_component)
        logger.add_calculation("Net Shear Area (Anv)", shear_rupture_component)
        logger.add_calculation("Net Tension Area (Ant)", tension_rupture_component)

        # --- AISC J4.3 ---
        # The available shear strength shall be the lesser of shear yielding and shear rupture
        shear_yield_strength = 0.60 * Fy * shear_yield_component
        shear_rupture_strength = 0.60 * Fu * shear_rupture_component
        governing_shear_strength = min(shear_yield_strength, shear_rupture_strength)
        
        logger.add_calculation("Shear Yielding Strength (0.6 * Fy * Agv)", shear_yield_strength)
        logger.add_calculation("Shear Rupture Strength (0.6 * Fu * Anv)", shear_rupture_strength)
        logger.add_output("Governing Shear Strength", governing_shear_strength)

        # The available tensile strength
        tension_rupture_strength = Ubs * Fu * tension_rupture_component
        logger.add_calculation("Tension Rupture Strength (Ubs * Fu * Ant)", tension_rupture_strength)

        # Nominal capacity is the sum of the tension rupture and the governing shear strength
        nominal_capacity = tension_rupture_strength + governing_shear_strength
        logger.add_calculation("Nominal Capacity (Rn = Tension Strength + Shear Strength)", nominal_capacity)

        # Final design capacity
        design_capacity = resistance_factor * nominal_capacity
        logger.add_output("Design Capacity (phi * Rn)", design_capacity)
        
        logger.display()
        _calculation = self._calculation(d_bolt=self.bolt_hole_diameter,t=self.thickness,width=self.width,load_condition=self.loading_condition,F_y=Fy,F_u=Fu)
        return design_capacity

    def check_dcr(self, **kwargs) -> float:
        """Calculates the demand-to-capacity ratio."""
        capacity = self.calculate_capacity(**kwargs)
        return check_dcr(capacity, abs(self.loads.Pu), f"Block Shear {self.failure_pattern}-Pattern", **kwargs)

class ConnectionCapacityCalculator:
    """
    Calculates the governing bolt capacity for an entire connection, considering
    bolt shear and bolt bearing/tearout for inner and outer bolts.
    """
    def __init__(self, endpoint: "ConnectionEndpoint", connection: Connection, loads: DesignLoads):
        self.endpoint = endpoint
        self.connection = connection
        self.member = endpoint.member
        self.bolt_config: BoltConfiguration = connection.configuration
        self.loads = loads

        # Extract common properties
        self.Fu = self.member.Fu
        self.thickness = get_applicable_thickness(endpoint)
        self.bolt_diameter = self.bolt_config.bolt_diameter
        self.bolt_diameter_nominal = self.bolt_config.bolt_diameter + 1/16

        # Per AISC, standard hole diameter is bolt diameter + 1/8"
        self.hole_diameter = self.bolt_config.bolt_diameter + 1/8

        # Determine geometry based on loading orientation (DRY principle)
        # if self.loading_orientation == "Axial":
        self.longitudinal_spacing = self.bolt_config.column_spacing
        self.longitudinal_edge_dist = self.bolt_config.edge_distance_horizontal
        self.bolts_per_line = self.bolt_config.n_columns
        self.num_lines = self.bolt_config.n_rows
        # else: # Shear
        #     self.longitudinal_spacing = self.bolt_config.row_spacing
        #     self.longitudinal_edge_dist = self.bolt_config.edge_distance_vertical
        #     self.bolts_per_line = self.bolt_config.n_rows
        #     self.num_lines = self.bolt_config.n_columns


    def _calculate_lc_inner(self) -> float:
        """Calculates clear distance for an inner bolt."""
        return self.longitudinal_spacing - self.bolt_diameter_nominal

    def _calculate_lc_outer(self) -> float:
        """Calculates clear distance for an edge bolt."""
        return self.longitudinal_edge_dist - (self.bolt_diameter_nominal / 2)

    def calculate_capacity(
        self,
        number_of_shear_planes: int = 1,
        resistance_factor: float = 0.75,
        debug: bool = False,
    ) -> float:
        """
        Calculates the total design capacity of the bolted connection.
        """
        # 1. Get the shear capacity of a single bolt (this is an upper limit)
        # Create a new Connection object to pass to the shear checker
        shear_checker = BoltShearCalculator(self.connection,loads=self.loads)
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

    def check_dcr(self, **kwargs) -> float:
        """Calculates the demand-to-capacity ratio."""
        capacity = self.calculate_capacity(**kwargs)
        return check_dcr(capacity, abs(self.loads.Pu), "Connection Capacity", debug = True)


class TensileYieldWhitmore:
    """
    Calculates the tensile yielding capacity based on the Whitmore section.
    """

    def __init__(self, endpoint: "ConnectionEndpoint", connection: Connection,loads : DesignLoads):
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
        self.loads = loads

    def _get_member_thickness(self) -> float:
        """Determines thickness from various member types and ensures it has units."""
        if hasattr(self.member, "t"):
            t_val = self.member.t
            if hasattr(t_val, 'units'):
                return t_val
            if isinstance(t_val, (int, float)):
                return t_val
            return t_val
        elif hasattr(self.member, "tw"):
            tw_val = self.member.tw
            if isinstance(tw_val, (int, float)):
                return tw_val
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
            self.length_whitmore - 4.7
        ) * self.t + 4.7 * 0.515

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

    def check_dcr(self, **kwargs) -> float:
        """Calculates the demand-to-capacity ratio."""
        capacity = self.calculate_capacity(**kwargs)
        return check_dcr(capacity, abs(self.loads.Pu), "Whitmore Section Tensile Yield", **kwargs)


class CompressionBucklingCalculator:
    """
    Calculates the compression buckling capacity of a member.
    """

    def __init__(self, endpoint: "ConnectionEndpoint", connection: Connection, loads: DesignLoads):
        """Initializes the calculator with the member and connection."""
        self.endpoint = endpoint
        self.member = endpoint.member
        self.bolt_config: BoltConfiguration = connection.configuration
        self.Fy = self.member.Fy
        self.t = self._get_member_thickness()
        self.loads = loads

    def _get_member_thickness(self) -> float:
        """Determ-ines thickness from various member types and ensures it has units."""
        if hasattr(self.member, "t"):
            t_val = self.member.t
            if hasattr(t_val, 'units'):
                return t_val
            if isinstance(t_val, (int, float)):
                return t_val
            return t_val
        elif hasattr(self.member, "tw"):
            tw_val = self.member.tw
            if isinstance(tw_val, (int, float)):
                return tw_val
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
        return (self.k * 9.76) / (self.r)

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
            capacity = self.Fy * 20.9 * resistance_factor
            logger.add_output("Design Capacity (phiRn)", capacity)
            logger.display()
            return capacity
        else:
            raise ValueError(
                "Member is not slender enough for compression buckling calculation."
            )

    def check_dcr(self, **kwargs) -> float:
        """Calculates the demand-to-capacity ratio."""
        capacity = self.calculate_capacity(**kwargs)
        return check_dcr(capacity, abs(self.loads.Pu), "Compression Buckling", **kwargs)


class ConnectionAnalysis:
    """
    A unified class to perform all connection analysis calculations, including
    UFM, admissible distortion forces, and final load calculations.
    """

    def __init__(self, beam: Any, support: Any, brace: Any, endplate: Any, connection: Connection, loads: DesignLoads, debug: bool = False):
        """
        Initializes the analysis with all necessary components and runs the calculations.
        """
        self.beam = beam
        self.support = support
        self.brace = brace
        self.endplate = endplate
        self.connection = connection
        self.loads = loads
        self.config: BoltConfiguration = connection.configuration
        self.debug = debug
        self.lb = getattr(beam, 'length', None)
        if self.lb:
            self.lb = self.lb.to('inch')
        self.lc = getattr(support, 'length', None)
        if self.lc:
            self.lc = self.lc.to('inch')



        # Run all calculations
        self.run_analysis()

    def run_analysis(self):
        """
        Executes all calculation steps and stores the results as public attributes.
        """
        logger = DebugLogger("ConnectionAnalysis High-Level", self.debug)
        logger.add_input("Initial Brace Load", self.loads.Pu)
        logger.add_input("Initial Beam Shear", self.loads.Vu)
        logger.add_input("Initial Transfer Force", self.loads.Aub)

        # 1. UFM Calculations
        self.ufm_multipliers = self._calculate_ufm_multipliers(self.debug)
        self.plate_dimensions = self._calculate_plate_dimensions(self.debug)

        # 2. Admissible Distortion Forces
        self.admissible_distortion_force = self._calculate_admissible_distortion_forces(self.debug)

        logger.add_output("UFM Multipliers", self.ufm_multipliers)
        logger.add_output("Plate Dimensions", self.plate_dimensions)
        logger.add_output("Admissible Distortion Force", self.admissible_distortion_force)
        logger.display()

        # 3. Final Load Calculations (can be added here)
        # self.final_loads = self._calculate_final_loads()

    def _get_attribute(self, obj: Any, potential_names: list[str]) -> float:
        for name in potential_names:
            if hasattr(obj, name):
                value = getattr(obj, name)
                if hasattr(value, 'units'):
                    return value
                if isinstance(value, (int, float)):
                    return value
                return value
        raise AttributeError(f"Object does not have any of the expected attributes: {potential_names}")

    # --- UFM Logic (private methods) ---
    def _calculate_ufm_multipliers(self, debug: bool = False) -> LoadMultipliers:
        """Calculates and returns the load multipliers for the UFM interfaces."""
        logger = DebugLogger("UFM Load Multipliers", debug)
        
        beam_depth = self._get_attribute(self.beam, ["d", "depth"]).to('inch')
        support_depth = self._get_attribute(self.support, ["d", "depth"]).to('inch')
        edge_dist = self.config.edge_distance_horizontal
        col_spacing = self.config.column_spacing
        n_col = self.config.n_columns
        angle_rad = self.config.angle

        beam_half_depth = beam_depth / 2
        support_half_depth = support_depth / 2
        beta = edge_dist + ((n_col - 1) * col_spacing) / 2
        alpha = (beam_half_depth + beta) * math.tan(angle_rad) - support_half_depth
        r = ((alpha + support_half_depth)**2 + (beam_half_depth + beta)**2)**0.5

        logger.add_input("Beam Depth", beam_depth)
        logger.add_input("Support Depth", support_depth)
        logger.add_input("Edge Distance (horiz)", edge_dist)
        logger.add_input("Column Spacing", col_spacing)
        logger.add_input("Number of Columns", n_col)
        logger.add_input("Connection Angle", f"{math.degrees(angle_rad):.2f} degrees")
        logger.add_calculation("beta", beta)
        logger.add_calculation("alpha", alpha)
        logger.add_calculation("r", r)

        multipliers = LoadMultipliers(
            vertical_force_column_interface=beta / r,
            vertical_force_beam_interface=beam_half_depth / r,
            horizontal_force_column_interface=support_half_depth / r,
            horizontal_force_beam_interface=alpha / r,
        )

        logger.add_output("Vertical Force (Column Interface)", multipliers.vertical_force_column_interface)
        logger.add_output("Vertical Force (Beam Interface)", multipliers.vertical_force_beam_interface)
        logger.add_output("Horizontal Force (Column)", multipliers.horizontal_force_column_interface)
        logger.add_output("Horizontal Force (Beam)", multipliers.horizontal_force_beam_interface)
        logger.display()

        return multipliers

    def _calculate_plate_dimensions(self, debug: bool = False) -> PlateDimensions:
        """Calculates and returns the final, rounded plate dimensions."""
        logger = DebugLogger("UFM Plate Dimensions", debug)

        beam_depth = self._get_attribute(self.beam, ["d", "depth"])
        support_depth = self._get_attribute(self.support, ["d", "depth"])
        end_plate_thickness = self._get_attribute(self.endplate, ["t", "thickness"])
        edge_dist = self.config.edge_distance_horizontal
        col_spacing = self.config.column_spacing
        n_col = self.config.n_columns
        angle_rad = self.config.angle

        self.beam_half_depth = beam_depth / 2
        self.support_half_depth = support_depth / 2
        self.beta = edge_dist + ((n_col - 1) * col_spacing) / 2
        self.alpha = (self.beam_half_depth + self.beta) * math.tan(angle_rad) - self.support_half_depth
        
        k_line_clearance = 0.75
        horizontal_plate_length = 2 * self.alpha - 2 * end_plate_thickness - k_line_clearance

        logger.add_input("Beam Depth", beam_depth)
        logger.add_input("Support Depth", support_depth)
        logger.add_input("End Plate Thickness", end_plate_thickness)
        logger.add_input("Edge Distance (horiz)", edge_dist)
        logger.add_input("Column Spacing", col_spacing)
        logger.add_input("Number of Columns", n_col)
        logger.add_input("Connection Angle", f"{math.degrees(angle_rad):.2f} degrees")
        logger.add_calculation("beta", self.beta)
        logger.add_calculation("alpha", self.alpha)
        logger.add_calculation("Horizontal Plate Length (unrounded)", horizontal_plate_length)

        unrounded_vertical = (edge_dist * 2 + ((n_col - 1) * col_spacing) + 0.5)
        logger.add_calculation("Vertical Plate Length (unrounded)", unrounded_vertical)

        vertical_dim = round_up_to_interval(number=unrounded_vertical, interval=0.25)
        horizontal_dim = round_up_to_interval(number=horizontal_plate_length, interval=0.25)

        logger.add_output("Final Vertical Dimension", vertical_dim)
        logger.add_output("Final Horizontal Dimension", horizontal_dim)
        logger.display()

        return PlateDimensions(
            vertical=vertical_dim,
            horizontal=horizontal_dim,
            thickness=end_plate_thickness,
        )

    # --- Admissible Distortion Logic (private methods) ---
    def _get_effective_lengths(self, debug: bool = False) -> tuple[float, float]:
        """
        Determines the effective beam (lb) and column (lc) lengths for distortion calculations.
        It prioritizes overrides and calculates missing values based on the connection angle.
        """
        logger = DebugLogger("Effective Length Calculation", debug)
        
        lb = self.lb
        lc = self.lc
        angle = self.config.angle

        logger.add_input("lb_override", lb)
        logger.add_input("lc_override", lc)
        logger.add_input("Connection Angle", angle)


        if lb is not None and lc is None:
            lc = lb / math.tan(angle)
            logger.add_calculation("Calculated lc from lb and angle", lc)
        elif lc is not None and lb is None:
            lb = lc * math.tan(angle)
            logger.add_calculation("Calculated lb from lc and angle", lb)
        
        if lb is None or lc is None:
            raise ValueError("Effective lengths 'lb' and 'lc' could not be determined.")

        logger.add_output("Final lb", lb)
        logger.add_output("Final lc", lc)
        logger.display()
        return lb, lc

    def _calculate_admissible_distortion_forces(self, debug: bool = False) -> si.kip:
        """
        Calculates the admissible distortion forces based on AISC J3.2.
        Returns the calculated force in kip.
        """
        logger = DebugLogger("Admissible Distortion Forces Calculation", debug)
        
        lb, lc = self._get_effective_lengths(debug)

        Pu = self.loads.Pu
        ixb = self.beam.Ix
        ixc = self.support.Ix
        area = self.brace.area * getattr(self.brace, 'loading_condition', 1)
        angle = self.config.angle

        b_val = lb / 2
        c_val = lc / 2

        logger.add_input("Factored Load (Pu)", Pu)
        logger.add_input("Moment of Inertia of Beam (Ix_b)", ixb)
        logger.add_input("Moment of Inertia of Support (Ix_c)", ixc)
        logger.add_input("Cross-sectional Area of Brace", area)
        logger.add_input("Connection Angle (radians)", angle)
        logger.add_input("Effective Beam Length (lb)", lb)
        logger.add_input("Effective Support Length (lc)", lc)
        logger.add_calculation("b (lb/2)", b_val)
        logger.add_calculation("c (lc/2)", c_val)

        if (area * b_val * c_val) == 0 or ((ixb / b_val) + (2 * ixc / c_val)) == 0:
             admissible_force = 0
        else:
            term1 = Pu / (area * b_val * c_val)
            term2_numerator = ixb * ixc
            term2_denominator = (ixb / b_val) + (2 * ixc / c_val)
            term2 = term2_numerator / term2_denominator
            term3_numerator = b_val**2 + c_val**2
            term3_denominator = b_val * c_val
            term3 = term3_numerator / term3_denominator
            admissible_force = 6 * term1 * term2 * term3

        logger.add_output("Admissible Distortion Force", admissible_force)
        logger.display()
        return admissible_force
    def interface_loads(self, debug: bool = False):
        """
        Calculates the final loads on each interface after applying UFM multipliers
        and considering admissible distortion forces.
        """
        logger = DebugLogger("Interface Loads Calculation", debug)
        try:
            m = self.ufm_multipliers
            Pu = self.loads.Pu
            Vu = self.loads.Vu
            Aub = self.loads.Aub
            Padm = self.admissible_distortion_force

            logger.add_input("Factored Load (Pu)", Pu)
            logger.add_input("Beam Shear (Vu)", Vu)
            logger.add_input("Transfer Force (Aub)", Aub)
            logger.add_input("Admissible Distortion Force (Padm)", Padm)
            logger.add_input("Beta (from plate dimensions)", self.beta)
            logger.add_input("Beam Half Depth (from plate dimensions)", self.beam_half_depth)
            logger.add_input("UFM Multiplier: Vertical Force Column Interface", m.vertical_force_column_interface)
            logger.add_input("UFM Multiplier: Vertical Force Beam Interface", m.vertical_force_beam_interface)
            logger.add_input("UFM Multiplier: Horizontal Force Column Interface", m.horizontal_force_column_interface)
            logger.add_input("UFM Multiplier: Horizontal Force Beam Interface", m.horizontal_force_beam_interface)

            # Gusset Beam interface loads
            gb_y_force = Pu * m.vertical_force_beam_interface
            gb_x_force = Pu * m.horizontal_force_beam_interface
            logger.add_calculation("Gusset-Beam Vertical Force (Pu * m.vertical_force_beam_interface)", gb_y_force)
            logger.add_calculation("Gusset-Beam Horizontal Force (Pu * m.horizontal_force_beam_interface)", gb_x_force)

            # Gusset Column interface loads
            gc_y_force = Pu * m.vertical_force_column_interface
            gc_x_force = Pu * m.horizontal_force_column_interface
            logger.add_calculation("Gusset-Column Vertical Force (Pu * m.vertical_force_column_interface)", gc_y_force)
            logger.add_calculation("Gusset-Column Horizontal Force (Pu * m.horizontal_force_column_interface)", gc_x_force)

            # Beam Column interface loads
            bc_x_admissible = Padm / (self.beta + self.beam_half_depth)
            bc_x_force = gc_x_force - bc_x_admissible + Aub
            bc_y_force = gb_y_force + Vu
            logger.add_calculation("Beam-Column Admissible Horizontal Force (Padm / (beta + beam_half_depth))", bc_x_admissible)
            logger.add_calculation("Beam-Column Final Horizontal Force (gc_x_force - bc_x_admissible + Aub)", bc_x_force)
            logger.add_calculation("Beam-Column Vertical Force (m.vertical_force_beam_interface + Vu)", bc_y_force)

            gusset_beam_loads = DesignLoads(Pu=gb_y_force, Vu=gb_x_force)
            gusset_column_loads = DesignLoads(Pu=gc_x_force, Vu=gc_y_force)
            beam_column_interface_loads = DesignLoads(Pu=bc_x_force, Vu=bc_y_force)

            logger.add_output("Gusset-Beam Interface Loads Pu", gusset_beam_loads.Pu)
            logger.add_output("Gusset-Beam Interface Loads Vu", gusset_beam_loads.Vu)
            logger.add_output("Gusset-Column Interface Loads Pu", gusset_column_loads.Pu)
            logger.add_output("Gusset-Column Interface Loads Vu", gusset_column_loads.Vu)
            logger.add_output("Beam-Column Interface Loads Pu", beam_column_interface_loads.Pu)
            logger.add_output("Beam-Column Interface Loads Vu", beam_column_interface_loads.Vu)

            return {
                "Gusset_Beam": gusset_beam_loads,
                "Gusset_Column": gusset_column_loads,
                "Beam_Column_Interface": beam_column_interface_loads,
            }
        finally:
            logger.display()
  

        


class PlateTensileYieldingCalculator:
    """
    Calculates design tensile strength based on gross section yielding (AISC J4.1a).
    This calculator expects to be initialized with a member object that has a
    '.dimensions' attribute containing a PlateDimensions object.
    """

    def __init__(self, endpoint: "ConnectionEndpoint",loads : DesignLoads):
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
        return check_dcr(capacity, abs(demand_force), "Plate Tensile Yielding (Horizontal)", **kwargs)

    def check_dcr_vertical(self, demand_force: si.kip, **kwargs) -> float:
        """Calculates the demand-to-capacity ratio for the vertical path."""
        capacity = self.calculate_capacity_vertical(**kwargs)
        return check_dcr(capacity, abs(demand_force), "Plate Tensile Yielding (Vertical)", **kwargs)

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

            clip_dist = 3 / 4
            
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
        return check_dcr(capacity, abs(demand_force), "Web Local Yielding", **kwargs)
    
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
                return value if hasattr(value, "units") else value 
        raise AttributeError(
            f"Object does not have any of the expected attributes: {potential_names}"
        )

    def calculate_capacity(self, resistance_factor: float = 0.75, debug: bool = False) -> float:
        """
        Calculates the design web local crippling strength (phiRn) based on AISC J10.3.
        """
        logger = DebugLogger("Web Local Crippling", debug)
        try:
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
            clip_dist = 3 / 4
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

            return design_capacity
        finally:
            logger.display()

    def check_dcr(self, demand_force: si.kip, **kwargs) -> float:
        """Calculates the demand-to-capacity ratio."""
        capacity = self.calculate_capacity(**kwargs)
        return check_dcr(capacity, abs(demand_force), "Web Local Crippling", **kwargs)
class ShearYieldingCalculator:
    """
    Calculates the shear yielding capacity of a member based on AISC Specification J3.2.
    This class is designed to handle both L and U patterns for block shear calculations.
    """

    def __init__(self, endpoint: "ConnectionEndpoint", connection: Connection,loads : DesignLoads):
        self.endpoint = endpoint
        self.member = endpoint.member
        self.loads = loads
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
                return t_val
            return t_val
        elif hasattr(self.member, "tw"):
            tw_val = self.member.tw
            if isinstance(tw_val, (int, float)):
                return tw_val
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

    def check_dcr(self, **kwargs) -> float:
        """Calculates the demand-to-capacity ratio."""
        capacity = self.calculate_capacity(**kwargs)
        return check_dcr(capacity, abs(self.loads.Vu), f"Shear Yielding ({self.endpoint.component.name})", **kwargs)


class PryingActionCalculator:
    """
    Calculates the effects of prying action on a bolted connection based on
    AISC Manual Part 9.
    """

    def __init__(self, member_1: Any, member_2: Any, connection: Connection, loads: Optional[DesignLoads] = None):
        """
        Initializes the calculator with the plate and connection objects.
        """
        if connection.connection_type != "bolted":
            raise ValueError("PryingActionCalculator only supports bolted connections.")
        
        self.connection = connection
        self.config: BoltConfiguration = connection.configuration

        # Extract properties from the two members
        props_1 = self._get_prying_properties(member_1)
        props_2 = self._get_prying_properties(member_2)

        # Assign properties for the main plate being analyzed
        self.t = props_1['t']
        self.width = props_1['width']
        self.plate_Fu = props_1['Fu'] # Store Fu for later use
        self.loads = loads # Store loads

        self.width_2 = props_2['width']  # Width of the plate

        # Assign thickness for the supporting member (gusset)
        self.member_type = getattr(member_1, 'Type', None)
        self.member_type_2 = getattr(member_2, 'Type', None)
        
        self.bolt_grade = self.config.bolt_grade
        self.bolt_diameter = self.config.bolt_diameter

        # Geometric properties from the connection
        self.p = self.config.column_spacing  # Tributary length per bolt
        self.g = self.config.row_spacing    # Gage distance
        
        # Distances 'a' and 'b' as defined in AISC Manual Part 9
        # 'a' is the distance from the bolt centerline to the edge of the fitting
        self.a = (min(self.width, self.width_2) - self.g) / 2 if self.member_type_2 == "PL" else (self.width - self.g) / 2
        # 'b' is the distance from the bolt centerline to the face of the supporting element

        
        if self.member_type == 'PL':
            if self.member_type_2 == 'W':
                self.t2 = props_2['tw']
            else:
                self.t2 = props_2['t']
            self.b =  (self.g - self.t2)/2
        elif self.member_type == 'W':
            self.t2 = props_1['tw']
            self.b = (self.g - self.t2) / 2 

        # Derived geometric properties
        self.d_prime = self.bolt_diameter + (1 / 16) # Effective hole diameter
        self.b_prime = self.b - self.bolt_diameter / 2
        self.a_prime = min(self.a,1.25 * self.b) + self.bolt_diameter / 2


        # Ratio of b' to a'
        self.p_ = self.b_prime / self.a_prime
        # Delta: ratio of unstiffened to stiffened length
        self.delta = 1 - (self.d_prime / self.p)
        
        # Bolt properties
        self.bolt_area = (self.bolt_diameter**2 / 4) * 3.14

        # Get total number of bolts
        self.n_rows = self.config.n_rows
        self.n_columns = self.config.n_columns
        self.n_bolts = self.n_rows * self.n_columns

        # Initialize shear and tension forces
        self.shear_force = self.loads.Vu if self.loads else None
        self.tension_force = self.loads.Pu if self.loads else None

        # Calculate B only if loads are provided
        self.B = None
        if self.loads:
            self.B = BoltShearCalculator(self.connection, loads=self.loads).calculate_capacity_fnt_modified(self.shear_force, debug=True)
         

    def _get_prying_properties(self, member: Any) -> dict:
        """
        Extracts properties needed for prying calculations from a generic member.
        This acts as an adapter for different member types (Plate, W, L).
        """
        member_type = getattr(member, 'Type', None)

        if member_type == 'PL' or isinstance(member, Plate):
            return {
                't': getattr(member, 't', 0),
                'width': getattr(member, 'width', 0),
                'Fu': getattr(member, 'Fu', 0)
            }
        elif member_type == 'W':
            # Assumption: Prying action occurs on the flange.
            return {
                't': getattr(member, 'tf', 0),      # Flange thickness
                'tw': getattr(member, 'tw', 0), 
                'width': getattr(member, 'bf', 0),  # Flange width
                'Fu': getattr(member, 'Fu', 0)

            }
        elif member_type == 'L':
            return {
                't': getattr(member, 't', 0),       # Leg thickness
                'width': getattr(member, 'd', 0),   # Leg length (used as width)
                'Fu': getattr(member, 'Fu', 0)
            }
        else:
            # Fallback for unknown types or simple objects
            # This maintains backward compatibility if a simple Plate object is passed
            if all(hasattr(member, attr) for attr in ['t', 'width', 'Fu']):
                return {
                    't': member.t,
                    'width': member.width,
                    'Fu': member.Fu
                }
            raise TypeError(f"Unsupported member type for prying calculation: {type(member)}")

    def _calculate_alpha_prime(self, debug: bool = False) -> float:
        """
        Calculates the intermediate variable alpha' (alpha_prime).
        """
        logger = DebugLogger("Alpha Prime Calculation", debug)
        try:
            if self.B is None:
                logger.add_calculation("Condition", "self.B is None, cannot calculate alpha_prime.")
                raise ValueError("Cannot calculate alpha_prime: Bolt strength (B) is not available.")
            if self.B == 0:
                logger.add_calculation("Condition", "B is zero, returning infinity.")
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
                return float('inf')

            alpha_prime = (1 / (self.delta * (1 + self.p_))) * (ratio**2 - 1)
            logger.add_calculation(
                "Alpha Prime Formula",
                f"(1 / ({self.delta:.3f} * (1 + {self.p_:.3f}))) * (({ratio:.3f})^2 - 1)"
            )
            logger.add_output("Calculated Alpha Prime (alpha')", alpha_prime)
            
            return alpha_prime
        finally:
            logger.display()
    
    def _calculate_t_req(self, debug: bool = False):
        """
        Calculates the required thickness (t_req) to eliminate prying action.
        """
        logger = DebugLogger("Required Thickness (t_req) Calculation", debug)
        try:
            if self.B is None:
                logger.add_calculation("Condition", "self.B is None, cannot calculate t_req.")
                raise ValueError("Cannot calculate t_req: Bolt strength (B) is not available.")
            logger.add_input("Available Bolt Strength (B)", self.B)
            logger.add_input("Distance b'", self.b_prime)
            logger.add_input("Distance a'", self.a_prime)
            logger.add_input("Tributary Length (p)", self.p)
            logger.add_input("Plate Fu", self.plate_Fu)
            logger.add_input("Resistance Factor (phi)", 0.9)

            numerator = 4 * self.B * self.b_prime
            logger.add_calculation("Numerator (4 * B * b')", numerator)
            
            denominator = self.p * self.plate_Fu * 0.9
            logger.add_calculation("Denominator (phi * p * Fu)", denominator)

            if denominator == 0:
                logger.add_calculation("Condition", "Denominator is zero, returning infinity.")
                return float('inf')

            t_req = (numerator / denominator)**0.5
            logger.add_calculation("t_req Formula", "sqrt( (4 * B * b') / (p * Fy) )")
            logger.add_output("Required Thickness (t_req)", t_req)
            return t_req
        finally:
            logger.display()


    def calculate_Q(self, debug: bool = False) -> float:
        """
        Calculates the prying force factor 'Q'. Returns a unitless factor.
        """
        logger = DebugLogger("Prying Factor (Q) Calculation", debug)
        try:
            # Pass debug flag to dependent calculations
            alpha_prime = self._calculate_alpha_prime(debug=debug)
            tc = self._calculate_t_req(debug=debug)

            logger.add_input("Plate Thickness (t)", self.t)
            logger.add_input("Required Thickness (tc)", tc)
            logger.add_input("Alpha Prime (alpha')", alpha_prime)
            logger.add_input("Rho (b'/a')", self.p_)
            logger.add_input("Delta (1 - d'/p)", self.delta)

            Q = 0.0
            governing_case = "Unknown"

            if tc == 0:  # Avoid division by zero
                governing_case = "tc is zero, indicates failure"
                logger.add_calculation("Condition", governing_case)
                Q = float('inf')
            elif alpha_prime < 0:
                governing_case = "alpha' < 0"
                Q = 1.0
                logger.add_calculation(f"Condition: {governing_case}", "Q is set to 1.0")
            elif 0 <= alpha_prime <= 1:
                governing_case = "0 <= alpha_prime <= 1"
                logger.add_calculation("Condition", governing_case)
                ratio_sq = (self.t / tc)**2
                logger.add_calculation("(t / tc)^2", f"({self.t:.3f} / {tc:.3f})^2 = {ratio_sq:.3f}")
                term = (1 + (self.delta * alpha_prime))
                logger.add_calculation("(1 + delta * alpha')", f"(1 + {self.delta:.3f} * {alpha_prime:.3f}) = {term:.3f}")
                Q = ratio_sq * term
                logger.add_calculation("Q Formula", "Q = (t/tc)^2 * (1 + delta * alpha')")
            elif alpha_prime > 1:
                governing_case = "alpha_prime > 1"
                logger.add_calculation("Condition", governing_case)
                ratio_sq = (self.t / tc)**2
                logger.add_calculation("(t / tc)^2", f"({self.t:.3f} / {tc:.3f})^2 = {ratio_sq:.3f}")
                term = (1 + self.delta)
                logger.add_calculation("(1 + delta)", f"(1 + {self.delta:.3f}) = {term:.3f}")
                Q = ratio_sq * term
                logger.add_calculation("Q Formula", "Q = (t/tc)^2 * (1 + delta)")

            logger.add_output("Governing Case for Q", governing_case)
            logger.add_output("Prying Factor (Q)", Q)
            return Q
        finally:
            logger.display()

    def calculate_bolt_tension_with_prying(self):
        """
        Calculates the total tension in the bolt, including prying force.
        T_total = T_req + Q
        """
        if self.B is None:
            raise ValueError("Cannot calculate bolt tension: Bolt strength (B) is not available.")
        Q = self.calculate_Q(debug=False) # Debugging is handled in the main check_dcr
        return self.B * Q

    def check_dcr(self, resistance_factor: float = 1, debug: bool = False) -> float:
        """
        Calculates the DCR for prying action.
        DCR = (T_req) / (phi * B * Q)
        """
        # The detailed logging is now handled within the main check_dcr function
        # and the individual calculation methods. We just need to call them.
        t_req = self._calculate_t_req(debug=debug)
        Q = self.calculate_Q(debug=debug)
        
        if self.B is None or self.tension_force is None:
            raise ValueError("Cannot calculate DCR for prying action: Bolt strength (B) or tension force is not available.")

        available_strength = self.B * Q
        design_capacity = (resistance_factor * available_strength).to('kip')
        
        demand_per_bolt = self.tension_force / self.n_bolts
        
        return check_dcr(design_capacity, demand_per_bolt, "Prying Action", debug=debug)

class WeldCalculator:
    def __init__(self,  connection: Connection,loads: DesignLoads):
        """
        Initializes the WeldCalculator with the connection configuration.
        """
        self.shear =  loads.Vu
        self.axial = loads.Pu
        self.connection = connection
        self.config: WeldConfiguration = connection.configuration
        self.weld_size = self.config.weld_size
        self.weld_length = self.config.length
        self.fv = loads.Vu/self.weld_length
        self.fa = loads.Pu/self.weld_length
        self.f_avg = 0.5 * ((self.fa**2+self.fv**2)**0.5 + (self.fv**2+self.fa**2)**0.5)
        self.f_peak = (self.fa**2 + self.fv**2)**0.5
        self.fu_weld = max(self.f_avg *1.25 ,self.f_peak)
        self.angle = math.atan(self.fa/ self.fv) if self.fv != 0 else 0
        self.strength_increase = 1+0.5*math.sin(self.angle)**1.5
    def calculate_min_thickness(self, debug: bool = False):
        """
        Calculates the minimum thickness of the weld based on the shear and axial forces.
        Returns the minimum thickness in inches.
        """
        logger = DebugLogger("Weld Minimum Thickness Calculation", debug)
        try:
            logger.add_input("Shear Force (Vu)", self.shear)
            logger.add_input("Axial Force (Pu)", self.axial)
            logger.add_input("Weld Size", self.weld_size)
            logger.add_input("Weld Length", self.weld_length)
            logger.add_input("Shear Stress (fv)", self.fv)
            logger.add_input("Axial Stress (fa)", self.fa)
            logger.add_input("Average Stress (f_avg)", self.f_avg)
            logger.add_input("Peak Stress (f_peak)", self.f_peak)
            logger.add_input("Angle (radians)", self.angle)
            logger.add_input("Ultimate Weld Strength (fu_weld)", self.fu_weld)
            logger.add_input("Strength Increase Factor", self.strength_increase)
            min_thickness = self.fu_weld / (2 * (1.392 * si.kip / si.inch) * self.strength_increase)
            logger.add_input( "minimum thickness", min_thickness)
            return min_thickness
        finally:
            logger.display()


# aisc_360_14th = [BoltShearCalculator, BoltTensileCalculator,TensileYieldingCalculator,TensileRuptureCalculator,BlockShearCalculator]
aisc_360_14th = [BlockShearCalculator]