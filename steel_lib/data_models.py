from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Any, Literal, Union
from enum import Enum,auto
from .si_units import si
import math
from pydantic import BaseModel, ConfigDict
from typing import Dict
from .materials import Material, BoltGrade
def get_component_from_string(component_str: str):
    """
    Safely retrieves a ConnectionComponent enum member from its string value.
    """
    try:
        # The core of the solution: pass the string directly to the class.
        enum_member = ConnectionComponent(component_str)
        return enum_member
    except ValueError:
        print(f"Unknown component: {component_str}")
        # This block runs if the string does not match any enum value.
        return None


class ConnectionComponent(Enum):
    """Defines the specific part of a member that is being connected."""
    TOTAL = "total"
    WEB = "web"
    FLANGE = "flange"
    GUSSET_LENGTH = "gusset_length"
    GUSSET_WIDTH = "gusset_width"
    FLANGE_TOP = "flange_top"
    FLANGE_BOTTOM = "flange_bottom"
    PLATE_FACE = "plate_face"


@dataclass(frozen=True)
class GeometricProperties:
    """
    A container for the pre-calculated gross area (Ag) of a member's various components.
    This makes the properties easy to access and prevents repeated calculations.
    """
    total: Optional[float] = None
    web: Optional[float] = None
    flange: Optional[float] = None
    along_length: Optional[float] = None
    along_width: Optional[float] = None




@dataclass
class Plate:
    """
    Represents a custom plate member. Includes loading_condition as an
    intrinsic property, defaulting to 1.
    """
    t: si.inch
    material: Material
    loading_condition: int = 1
    length: Any = 0 * si.inch
    width: Any = 0 * si.inch
    clipping: Any = 0 * si.inch
    type: str = "PL"
    geometry: "GeometricProperties" = field(init=False)
    role: str = "PLATE"
    angle: float = 0.0  # Angle in radians, default to 0 (horizontal)

    def __post_init__(self):
        """
        Post-initialization hook to automatically calculate and assign the
        geometric properties for the plate.
        """
        self.geometry = GeometricProperties(
            along_length=self.gross_area_length,
            along_width=self.gross_area_width,
            total=self.gross_area_length or self.gross_area_width # Default total
        )

    @classmethod
    def from_dimensions(
        cls,
        dimensions: "PlateDimensions",
        material: "Material",
        loading_condition: int = 1,
        clipping: Any = 0 * si.inch,
    ) -> "Plate":
        """
        Creates a Plate member from a PlateDimensions object. The geometry
        is calculated automatically after instantiation.
        """
        return cls(
            t=dimensions.thickness, # Already has units
            material=material,
            loading_condition=loading_condition,
            length=dimensions.vertical, # Already has units
            width=dimensions.horizontal, # Already has units
            clipping=clipping,
        )
    def set_dimensions(self, dimensions: "PlateDimensions"):
        """
        Updates the plate's dimensions from a PlateDimensions object.

        This method allows dimensions to be set or updated after the plate
        has been instantiated.

        Args:
            dimensions: A PlateDimensions object containing the geometric properties.
        """
        self.width = dimensions.vertical - self.clipping
        self.length = dimensions.horizontal - self.clipping
        # After updating dimensions, we must also update the geometry dataclass
        self.geometry = GeometricProperties(
            along_length=self.gross_area_length,
            along_width=self.gross_area_width,
            total=self.gross_area_length or self.gross_area_width
        )

    @property
    def Fy(self) -> si.ksi: return self.material.Fy
    @property
    def Fu(self) -> si.ksi: return self.material.Fu
    @property
    def E(self) -> si.ksi: return self.material.E
    @property
    def gross_area_length(self) :
        """Calculates the gross area of the plate."""
        return (self.length ) * self.t if self.length else None
    @property
    def gross_area_width(self):
        """Calculates the gross area of the plate."""
        return (self.width) * self.t if self.width else None


@dataclass(slots=True, kw_only=True)
class BoltConfiguration:
    """Defines the geometry and properties of a bolted connection."""
    row_spacing: float
    column_spacing: float
    edge_distance_vertical: float
    edge_distance_horizontal: float
    bolt_diameter: float
    bolt_grade: BoltGrade
    n_rows: int = 1
    n_columns: int = 1
    connection_type: Literal["bolted"] = "bolted"
    name:str = "pets"
    id:str = "pets"

    def __post_init__(self):
        if isinstance(self.row_spacing, (int, float)):
            self.row_spacing = self.row_spacing * si.inch
        if isinstance(self.column_spacing, (int, float)):
            self.column_spacing = self.column_spacing * si.inch
        if isinstance(self.edge_distance_vertical, (int, float)):
            self.edge_distance_vertical = self.edge_distance_vertical * si.inch
        if isinstance(self.edge_distance_horizontal, (int, float)):
            self.edge_distance_horizontal = self.edge_distance_horizontal * si.inch
        if isinstance(self.bolt_diameter, (int, float)):
            self.bolt_diameter = self.bolt_diameter * si.inch

        # Check if the provided bolt_grade is a string
        BOLT_GRADES: Dict[str, BoltGrade] = {
        "a325_n": BoltGrade(name="A325-N", Fnt=90.0 * si.ksi, Fnv=54.0 * si.ksi), # Threads included
        "a325_x": BoltGrade(name="A325-X", Fnt=90.0 * si.ksi, Fnv=68.0 * si.ksi), # Threads excluded
        "a490_n": BoltGrade(name="A490-N", Fnt=113.0 * si.ksi, Fnv=68.0 * si.ksi), # Threads included
        "a490_x": BoltGrade(name="A490-X", Fnt=113.0 * si.ksi, Fnv=84.0 * si.ksi), # Threads excluded
    }
        if isinstance(self.bolt_grade, str):
            grade_key = self.bolt_grade.lower() # Make it case-insensitive
            
            # Look up the string in our catalog
            grade_object = BOLT_GRADES.get(grade_key)
            
            # If the key is invalid, raise a helpful error
            if grade_object is None:
                raise ValueError(
                    f"Invalid bolt grade string: '{self.bolt_grade}'. "
                    f"Valid options are: {list(BOLT_GRADES.keys())}"
                )
            self.bolt_grade = grade_object
    @property
    def length(self):
        if self.n_columns > 1:
            return self.column_spacing * (self.n_columns - 1) + 2 * self.edge_distance_horizontal
        else:
            return 2 * self.edge_distance_vertical
from steelpy import aisc
from typing import Any, Type

# @dataclass(frozen=True)
# class WeldElectrode:
#     """
#     Represents the properties of a weld electrode. It's frozen because
#     these are standard, immutable values.
#     """
#     Fexx: float  # Nominal strength of the weld electrode (e.g., 70 ksi for E70XX)

WeldType = Literal["fillet", "groove"]


@dataclass(slots=True, kw_only=True)
class WeldConfiguration:
    """
    Defines the geometry and properties of a specific weld line in a connection.
    """
    weld_size: float
    electrode: Literal["e60xx", "e70xx", "e80xx"] = "e70xx"  # Link to the WeldElectrode object
    weld_type: WeldType = "fillet" # Default to fillet, the most common type
    connection_type: Literal["welded"] = "welded"
    length: float = None
    
    def __post_init__(self):
        # Convert units for dimensional attributes
        if isinstance(self.weld_size, (int, float)):
            self.weld_size *= si.inch
        if isinstance(self.length, (int, float)):
            self.length *= si.inch
        
        # Validate and convert electrode string to strength value
        if isinstance(self.electrode, str):
            electrode_key = self.electrode.lower()
            weld_electrodes = {
                "e60xx": 60.0 * si.ksi,
                "e70xx": 70.0 * si.ksi,
                "e80xx": 80.0 * si.ksi,
            }
            if electrode_key not in weld_electrodes:
                raise ValueError(
                    f"Invalid weld electrode: '{self.electrode}'. Valid options: {list(weld_electrodes.keys())}"
                )
            self.electrode = weld_electrodes[electrode_key]

@dataclass(frozen=True)
class PlateDimensions:
    vertical: float; horizontal: float; thickness: float

@dataclass(frozen=True)
class LoadMultipliers:
    vertical_force_column_interface: float; vertical_force_beam_interface: float
    horizontal_force_column_interface: float; horizontal_force_beam_interface: float

@dataclass(frozen=True)
class DesignLoads:
    """A simple container for the initial load inputs."""
    Pu: si.kip = 0 * si.kip
    Vu: si.kip = 0 * si.kip
    Aub: si.kip = 0 * si.kip
    out_of_plane_force: si.kip = 0 * si.kip
    Peq: si.kip = 0 * si.kip  # Equivalent force from moments
    Rw: si.kip = 0 * si.kip  # Resultant weld force


@dataclass(frozen=True)
class GlobalLoads:
    """Represents a generalized 6-component load vector."""
    id: str = "pets"
    name:str = "pets"
    fx: float = 0.0
    fy: float = 0.0
    fz: float = 0.0
    mx: float = 0.0
    my: float = 0.0
    mz: float = 0.0
    direct_load : float = 0.0
    fxeq: float = 0.0
    rw: float = 0.0

    def __post_init__(self):
        object.__setattr__(self, 'fx', self.fx * si.kip if isinstance(self.fx, (int, float)) else self.fx)
        object.__setattr__(self, 'fy', self.fy * si.kip if isinstance(self.fy, (int, float)) else self.fy)
        object.__setattr__(self, 'fz', self.fz * si.kip if isinstance(self.fz, (int, float)) else self.fz)
        object.__setattr__(self, 'mx', self.mx * si.kip if isinstance(self.mx, (int, float)) else self.mx)
        object.__setattr__(self, 'my', self.my * si.kip if isinstance(self.my, (int, float)) else self.my)
        object.__setattr__(self, 'mz', self.mz * si.kip if isinstance(self.mz, (int, float)) else self.mz)
        object.__setattr__(self, 'direct_load', self.direct_load * si.kip if isinstance(self.direct_load, (int, float)) else self.direct_load)
        object.__setattr__(self, 'fxeq', self.fxeq * si.kip if isinstance(self.fxeq, (int, float)) else self.fxeq)
        object.__setattr__(self, 'rw', self.rw * si.kip if isinstance(self.rw, (int, float)) else self.rw)

@dataclass(frozen=True)
class BeamColumnTransferredForce:
    """
    Represents the transferred force from a beam to a column.
    This is a simple container for the force value.
    """
    shear: si.kip
    normal: si.kip




from typing import Union, Literal

@dataclass(slots=True)
class ConnectionEndpoint:
    """
    Represents one side of a connection, defining which member and which specific
    part of that member is being connected. The loads attribute is populated
    after the Connection is initialized.
    """
    member: Any
    component: ConnectionComponent = ConnectionComponent.TOTAL
    role: Optional[Literal['BEAM', 'COLUMN', 'GIRDER', 'END_PLATE', 'SHEAR_PLATE', 'FLANGE_PLATE','GUSSET_PLATE']] = None
    loads: DesignLoads = field(default_factory=DesignLoads, init=False)
    connection_configuration: Optional[Union[BoltConfiguration, WeldConfiguration]] = None
    design_method: str = "LRFD"  # Default design method
    shear_condition: int = 1  # Default to single shear
class remarks(Enum):
    PASS = auto()
    FAIL = auto()

@dataclass
class result:
    """
    A simple container for the results of a limit state check.
    """
    name: str
    demand: float
    capacity: float
    dcr: float
    remarks: str = "WIP"
    details: Optional[str] = None
    def __post_init__(self):
        self.remarks = remarks.PASS if self.dcr <= 1.0 else remarks.FAIL 


# @dataclass
# class Connection:
#     """
#     A unified connection class that explicitly defines the two members and their
#     respective components being joined.
#     """
#     member_a: ConnectionEndpoint
#     member_b: ConnectionEndpoint
#     configuration: Union["BoltConfiguration", "WeldConfiguration"]
#     global_loads: Optional[GlobalLoads] = None
#     override_Ag: Optional[float] = None  # Allow manual override of gross area

#     def __post_init__(self):
#         """
#         Automatically transforms and assigns global loads to the respective
#         connection endpoints after the connection is initialized.
#         """
#         if self.global_loads:
#             self._transform_and_assign_loads()

#     def _transform_and_assign_loads(self):
#         """
#         Determines member roles and assigns the appropriate DesignLoads.
#         It prioritizes explicit roles and falls back to a heuristic based
#         on connection topology if roles are not provided.
#         """
#         # Step 1: Define transformation rules for each role
#         transformation_rules = {
#             'BEAM':       {'Pu': self.global_loads.fx, 'Vu': self.global_loads.fy},
#             'COLUMN':     {'Pu': self.global_loads.fy, 'Vu': self.global_loads.fx},
#             'GIRDER':     {'Pu': self.global_loads.fx, 'Vu': self.global_loads.fy},
#             'END_PLATE':  {'Pu': self.global_loads.fy, 'Vu': self.global_loads.fx},
#             'SHEAR_PLATE':{'Pu': self.global_loads.fx, 'Vu': self.global_loads.fy},
#             'BRACE':   {'Pu': self.global_loads.direct_load, 'Vu': 0 * si.kip},
#         }

#         # Step 2: Assign loads based on explicit roles if they exist
#         # Check member_a
#         if self.member_a.role in transformation_rules:
#             self.member_a.loads = DesignLoads(**transformation_rules[self.member_a.role])
#         # Check member_b
#         if self.member_b.role in transformation_rules:
#             self.member_b.loads = DesignLoads(**transformation_rules[self.member_b.role])

#         # If both roles were provided and handled, the job is done.
#         if self.member_a.role and self.member_b.role:
#             return

#         # Step 3: Fallback to heuristic if one or both explicit roles are not provided
#         if not (self.member_a.role and self.member_b.role):
#             if self.member_a.component in [ConnectionComponent.WEB, ConnectionComponent.FLANGE]:
#                 primary_member_endpoint = self.member_a
#                 secondary_member_endpoint = self.member_b
#             elif self.member_b.component in [ConnectionComponent.WEB, ConnectionComponent.FLANGE]:
#                 primary_member_endpoint = self.member_b
#                 secondary_member_endpoint = self.member_a
#             else:
#                 primary_member_endpoint = self.member_a
#                 secondary_member_endpoint = self.member_b

#             # Apply transformations based on inferred roles, only if not explicitly set
#             if not primary_member_endpoint.role:
#                 primary_member_endpoint.loads = DesignLoads(Pu=self.global_loads.fy, Vu=self.global_loads.fx)
#             if not secondary_member_endpoint.role:
#                 secondary_member_endpoint.loads = DesignLoads(Pu=self.global_loads.fx, Vu=self.global_loads.fy)

# @dataclass
# class ConnectionFactory:
#     """Factory for creating Connection objects."""

#     @staticmethod
#     def create_bolted_connection(
#         member_a: Any,
#         member_b: Any,
#         component_a: ConnectionComponent = ConnectionComponent.TOTAL,
#         component_b: ConnectionComponent = ConnectionComponent.TOTAL,
#         *args, **kwargs
#     ) -> Connection:
#         """
#         Creates a bolted connection, explicitly defining the two members and their
#         connected components.
#         """
#         override_ag = kwargs.pop('override_Ag', None)
#         global_loads = kwargs.pop('global_loads', None)
#         role_a = member_a.Role 
#         role_b = member_b.Role 
#         endpoint_a = ConnectionEndpoint(member=member_a, component=component_a, role=role_a)
#         endpoint_b = ConnectionEndpoint(member=member_b, component=component_b, role=role_b)

#         return Connection(
#             member_a=endpoint_a,
#             member_b=endpoint_b,
#             configuration=BoltConfiguration(*args, **kwargs),
#             override_Ag=override_ag,
#             global_loads=global_loads
#         )

#     @staticmethod
#     def create_welded_connection(
#         member_a: Any,
#         member_b: Any,
#         component_a: ConnectionComponent = ConnectionComponent.TOTAL,
#         component_b: ConnectionComponent = ConnectionComponent.TOTAL,
#         role_a: Optional[str] = None,
#         role_b: Optional[str] = None,
#         *args, **kwargs
#     ) -> Connection:
#         """
#         Creates a welded connection, explicitly defining the two members and their
#         connected components.
#         """
#         override_ag = kwargs.pop('override_Ag', None)
#         global_loads = kwargs.pop('global_loads', None)
#         endpoint_a = ConnectionEndpoint(member=member_a, component=component_a, role=role_a)
#         endpoint_b = ConnectionEndpoint(member=member_b, component=component_b, role=role_b)

#         return Connection(
#             member_a=endpoint_a,
#             member_b=endpoint_b,
#             configuration=WeldConfiguration(*args, **kwargs),
#             override_Ag=override_ag,
#             global_loads=global_loads
#         )

@dataclass(slots=True,kw_only=True)
class Connection:
    """
    A unified connection class that explicitly defines the two members and their
    respective components being joined.
    """
    member_a: ConnectionEndpoint
    member_b: ConnectionEndpoint
    global_loads: Optional[GlobalLoads] = None
    override_Ag: Optional[float] = None  # Allow manual override of gross area
    
    def __post_init__(self):
        """
        Automatically transforms and assigns global loads to the respective
        connection endpoints after the connection is initialized.
        """
        if self.global_loads:
            self._transform_and_assign_loads()
        shear_condition = max(self.member_a.member.loading_condition, self.member_b.member.loading_condition)
        self.member_a.shear_condition = shear_condition
        self.member_b.shear_condition = shear_condition


    def _transform_and_assign_loads(self):
        """
        Determines member roles and assigns the appropriate DesignLoads.
        It prioritizes explicit roles and falls back to a heuristic based
        on connection topology if roles are not provided.
        """
        # Step 1: Define transformation rules for each role

        transformation_rules = {
            'BEAM':       {'Pu': self.global_loads.fx, 'Vu': self.global_loads.fy},
            'COLUMN':     {'Pu': self.global_loads.fy, 'Vu': self.global_loads.fx},
            'GIRDER':     {'Pu': self.global_loads.fx, 'Vu': self.global_loads.fy,'out_of_plane_force': self.global_loads.fz},
            ('END_PLATE','plate_face'):  {'Pu': self.global_loads.fx, 'Vu': self.global_loads.fy},
            'SHEAR_PLATE':{'Pu': self.global_loads.fx, 'Vu': self.global_loads.fy},
            'BRACE':   {'Pu': self.global_loads.direct_load, 'Vu': 0 * si.kip},
            ('GUSSET_PLATE','gusset_length'): {'Pu': self.global_loads.fy + self.global_loads.direct_load, 'Vu': self.global_loads.fx, 'Peq': self.global_loads.fxeq, 'Rw': self.global_loads.rw},
            ('GUSSET_PLATE','gusset_width'): {'Pu': self.global_loads.fx + self.global_loads.direct_load, 'Vu': self.global_loads.fy, 'Peq': self.global_loads.fxeq, 'Rw': self.global_loads.rw},
            ('BEAM', 'flange_top'): {'Pu': self.global_loads.fx, 'Vu': self.global_loads.rw if self.global_loads.rw else self.global_loads.fy},
        
        }

        # Step 2: Assign loads based on explicit roles if they exist
        # Check member_a
        print(self.member_a.role,self.member_a.component.value)
        print((self.member_a.role,self.member_a.component.value) in transformation_rules)
        print(self.member_b.role,self.member_b.component.value)
        print((self.member_b.role,self.member_b.component.value) in transformation_rules)
        
        if (self.member_a.role,self.member_a.component.value) in transformation_rules:
            self.member_a.loads = DesignLoads(**transformation_rules[(self.member_a.role,self.member_a.component.value)])
        # Check member_b
        if (self.member_b.role,self.member_b.component.value) in transformation_rules:
            self.member_b.loads = DesignLoads(**transformation_rules[(self.member_b.role,self.member_b.component.value)])

        # If both roles were provided and handled, the job is done.
        if self.member_a.role and self.member_b.role:
            return

        # Step 3: Fallback to heuristic if one or both explicit roles are not provided
        if not (self.member_a.role and self.member_b.role):
            if self.member_a.component in [ConnectionComponent.WEB, ConnectionComponent.FLANGE]:
                primary_member_endpoint = self.member_a
                secondary_member_endpoint = self.member_b
            elif self.member_b.component in [ConnectionComponent.WEB, ConnectionComponent.FLANGE]:
                primary_member_endpoint = self.member_b
                secondary_member_endpoint = self.member_a
            else:
                primary_member_endpoint = self.member_a
                secondary_member_endpoint = self.member_b

            # Apply transformations based on inferred roles, only if not explicitly set
            if not primary_member_endpoint.role:
                primary_member_endpoint.loads = DesignLoads(Pu=self.global_loads.fy, Vu=self.global_loads.fx)
            if not secondary_member_endpoint.role:
                secondary_member_endpoint.loads = DesignLoads(Pu=self.global_loads.fx, Vu=self.global_loads.fy)

