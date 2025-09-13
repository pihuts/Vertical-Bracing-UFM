from typing import Any, Type, Literal, Optional
from .data_models import Plate, GeometricProperties, Material
from .si_units import si
from steelpy import aisc
from steel_lib.materials import MATERIALS, BOLT_GRADES
import math
class MemberFactory:
    """
    A factory class responsible for creating and enriching member objects.

    This factory ensures that any member object used in calculations has a
    standardized 'geometry' attribute, which contains all the pre-calculated
    gross areas for its various components. This centralizes the geometric
    calculations and decouples the calculators from the member's specific shape.
    """
    @staticmethod
    def create_member(
        type: Literal["steelpy", "plate"],
        **kwargs: Any
    ) -> Any:
        member_type = type
        if member_type == "steelpy":
            return MemberFactory.create_steelpy_member(**kwargs)
        elif member_type == "plate":
            return MemberFactory.create_plate_member(**kwargs)

    @staticmethod
    def create_plate_member(
        thickness: float,
        material: Literal["a36", "a572_gr50", "a992"],
        role: Literal["END_PLATE", "SHEAR_PLATE", "GUSSET_PLATE"],
        loading_condition: int = 1,
        length: Optional[float] = 0,
        width: Optional[float] = 0,
        angle: Optional[float] = 0,
        **kwargs: Any
    ) -> Plate:
        """
        Creates a Plate member with the specified dimensions and material properties.
        The Plate is enriched with geometric properties for its components.
        """
        if isinstance(angle, (int, float)):
            angle = angle * math.pi / 180.0 # Convert degrees to radians
        material = MATERIALS[material]
        plate = Plate(width=width, length=length, t=thickness, angle=angle, material=material, loading_condition=loading_condition, Role=role)
        return plate

    @staticmethod
    def create_steelpy_member(
        section_class: Literal["C_shapes", "DBL_L_shapes", "HP_shapes", "HSS_R_shapes", "HSS_shapes", "L_shapes", "M_shapes", "MC_shapes", "MT_shapes", "PIPE_shapes", "S_shapes", "ST_shapes", "W_shapes", "WT_shapes"],
        section_name: str,
        material: Literal["a36", "a572_gr50", "a992"],
        shape_type: str,
        role: Literal["BEAM", "COLUMN", "GIRDER", "BRACE"],
        loading_condition: int = 1,
        length: Optional[float] = 0,
        angle: Optional[float] = 0,
        **kwargs: Any
    ) -> Any:
        """
        Creates a steelpy member, assigns material and loading properties,
        and enriches it with the GeometricProperties dataclass.
        """
        SHAPE_CATALOG_MAP = {
            "C_shapes": aisc.C_shapes,
            "DBL_L_shapes": aisc.DBL_L_shapes,
            "HP_shapes": aisc.HP_shapes,
            "HSS_R_shapes": aisc.HSS_R_shapes,
            "HSS_shapes": aisc.HSS_shapes,
            "L_shapes": aisc.L_shapes,
            "M_shapes": aisc.M_shapes,
            "MC_shapes": aisc.MC_shapes,
            "MT_shapes": aisc.MT_shapes,
            "PIPE_shapes": aisc.PIPE_shapes,
            "S_shapes": aisc.S_shapes,
            "ST_shapes": aisc.ST_shapes,
            "W_shapes": aisc.W_shapes,
            "WT_shapes": aisc.WT_shapes,
        }
        if isinstance(angle, (int, float)):
            angle = angle * math.pi / 180.0 # Convert degrees to radians
        material = MATERIALS[material]
        # 1. Create the basic steelpy section object
        section = getattr(SHAPE_CATALOG_MAP[section_class], section_name)

        # 2. Enrich the raw steelpy object with units for all relevant attributes
        MemberFactory._enrich_member_with_units(section)

        # 3. Add the necessary material and type properties
        section.add_property("material", material)
        section.add_property("Type", shape_type)
        section.add_property("Role", role)
        section.add_property("angle", angle)
        if length is not None:
            section.add_property("length", length * si.inch)
        section.loading_condition = loading_condition

        # 4. Now that units and type exist, enrich it with geometric properties
        section.geometry = MemberFactory._create_geometric_properties(section)
        
        return section

    @staticmethod
    def _enrich_member_with_units(member: Any) -> None:
        """
        Iterates through a member's attributes and applies units based on a
        predefined mapping. This ensures that all downstream calculations
        can rely on unit-aware quantities.
        """
        # This mapping defines the expected units for common steelpy attributes.
        # It can be extended as needed for other section types.
        unit_map = {
            # Linear dimensions
            "d": si.inch, "bf": si.inch, "tf": si.inch, "tw": si.inch,
            "k": si.inch, "k_det": si.inch, "x": si.inch, "y": si.inch,
            "T": si.inch, "b": si.inch, "t": si.inch,
            # Area properties
            "area": si.inch**2,
            # Section moduli & moments of inertia
            "Zx": si.inch**3, "Zy": si.inch**3, "Sx": si.inch**3, "Sy": si.inch**3,
            "Ix": si.inch**4, "Iy": si.inch**4,
        }

        for attr, unit in unit_map.items():
            if hasattr(member, attr):
                raw_value = getattr(member, attr)
                # Ensure we don't re-apply units to a value that already has them
                if isinstance(raw_value, (int, float)):
                    setattr(member, attr, raw_value * unit)

    @staticmethod
    def _create_geometric_properties(member: Any) -> GeometricProperties:
        """
        Private helper to calculate and assemble the GeometricProperties for any member.
        """
        # For W-shapes and other standard sections from steelpy
        total_area = getattr(member, 'area', None)
        web_area = getattr(member, 'd', 0) * getattr(member, 'tw', 0) if hasattr(member, 'd') else None
        flange_area = getattr(member, 'bf', 0) * getattr(member, 'tf', 0) if hasattr(member, 'bf') else None

        # For Plate objects, this function is not needed as they self-populate.
        # This logic is now exclusively for external (e.g., steelpy) members.
        return GeometricProperties(
            total=total_area,
            web=web_area if web_area else None,
            flange=flange_area if flange_area else None
        )