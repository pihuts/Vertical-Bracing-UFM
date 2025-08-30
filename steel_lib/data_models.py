from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Any, Literal, Union
from enum import Enum,auto
from .si_units import si



class ConnectionComponent(Enum):
    """Defines the specific part of a member that is being connected."""
    TOTAL = "total"
    WEB = "web"
    FLANGE = "flange"
    LENGTH = "along_length"
    WIDTH = "along_width"


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


@dataclass(frozen=True)
class Material:
    """Represents the engineering properties of a steel material."""
    Fy: si.ksi
    Fu: si.ksi
    E: si.ksi

@dataclass
class Plate:
    """
    Represents a custom plate member. Includes loading_condition as an
    intrinsic property, defaulting to 1.
    """
    t: si.inch
    material: Material
    loading_condition: int = 1
    length: Any = None
    width: Any = None
    clipping: Any = 0 * si.inch
    Type: str = "PL"
    geometry: "GeometricProperties" = field(init=False)

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
@dataclass(frozen=True)
class BoltGrade:
    """Represents the nominal strength properties of a bolt material."""
    name: str      # e.g., "A325"
    Fnt: si.ksi  # Nominal tensile stress
    Fnv: si.ksi  # Nominal shear stress

@dataclass
class BoltConfiguration:
    """Defines the geometry and properties of a bolted connection."""
    row_spacing: si.inch   # Default to 3 inches if not specified
    column_spacing: si.inch  # Default to 3 inches if not specified
    edge_distance_vertical: si.inch 
    edge_distance_horizontal: si.inch 
    bolt_diameter: si.inch 
    bolt_grade: BoltGrade 
    angle: float = 0.0
    n_rows: int = 1  # Default to 1 row if not specified
    n_columns: int = 1  # Default to 1 column if not specified
    connection_type: Literal["bolted"] = "bolted"
from steelpy import aisc
from typing import Any, Type

@dataclass(frozen=True)
class WeldElectrode:
    """
    Represents the properties of a weld electrode. It's frozen because
    these are standard, immutable values.
    """
    Fexx: float  # Nominal strength of the weld electrode (e.g., 70 ksi for E70XX)

WeldType = Literal["fillet", "groove"]

@dataclass(kw_only=True)
class WeldConfiguration:
    """
    Defines the geometry and properties of a specific weld line in a connection.
    """
    weld_size: float
    length: float
    electrode: WeldElectrode  # Link to the WeldElectrode object
    weld_type: WeldType = "fillet" # Default to fillet, the most common type
    connection_type="welded",
    orientation: Literal["horizontal", "vertical", "overhead"] = "horizontal"

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

@dataclass(frozen=True)
class GlobalLoads:
    """Represents a generalized 6-component load vector."""
    fx: si.kip = 0 * si.kip
    fy: si.kip = 0 * si.kip
    fz: si.kip = 0 * si.kip
    mx: si.kip = 0 * si.kip
    my: si.kip = 0 * si.kip
    mz: si.kip = 0 * si.kip
    direct_load : si.kip = 0 * si.kip # this is for cases like bracing

@dataclass(frozen=True)
class BeamColumnTransferredForce:
    """
    Represents the transferred force from a beam to a column.
    This is a simple container for the force value.
    """
    shear: si.kip
    normal: si.kip




from typing import Union, Literal

@dataclass
class ConnectionEndpoint:
    """
    Represents one side of a connection, defining which member and which specific
    part of that member is being connected. The loads attribute is populated
    after the Connection is initialized.
    """
    member: Any
    component: ConnectionComponent = ConnectionComponent.TOTAL
    role: Optional[Literal['BEAM', 'COLUMN', 'GIRDER', 'END_PLATE', 'SHEAR_PLATE', 'FLANGE_PLATE']] = None
    loads: DesignLoads = field(default_factory=DesignLoads, init=False)
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
    remarks: str
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
