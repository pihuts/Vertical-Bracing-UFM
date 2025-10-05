"""
Plate Member Configuration Generator
====================================

High-performance plate configuration generator for structural steel connections.
Generates combinations of plate geometries for:
- Shear plates (simple shear connections)
- Flange plates (moment connections)
- Stiffener plates (web/column stiffeners)
- Gusset plates (bracing connections)

Follows the same pattern as bolt_configuration generator for consistency.

Author: steel_lib integration
Date: October 2025
"""

import itertools
import numpy as np
from typing import Dict, List, Union, Optional

# Plate type mappings (integer codes for efficiency)
PLATE_TYPE_MAP = {
    0: 'SHEAR',      # Shear plate / simple connection plate
    1: 'FLANGE',     # Flange plate / moment connection
    2: 'STIFFENER',  # Web or column stiffener
    3: 'GUSSET',     # Gusset plate for bracing
    4: 'BASE',       # Base plate
    5: 'DOUBLER'     # Doubler plate
}

# Steel grade mappings for plates
PLATE_GRADE_MAP = {
    0: 'A36',        # F_y = 36 ksi, F_u = 58 ksi
    1: 'A572_50',    # F_y = 50 ksi, F_u = 65 ksi
    2: 'A992',       # F_y = 50 ksi, F_u = 65 ksi
    3: 'A588',       # F_y = 50 ksi, F_u = 70 ksi
    4: 'A514'        # F_y = 100 ksi, F_u = 110 ksi
}

# Material properties lookup
PLATE_MATERIAL_PROPERTIES = {
    'A36': {'F_y': 36.0, 'F_u': 58.0, 'E': 29000.0},
    'A572_50': {'F_y': 50.0, 'F_u': 65.0, 'E': 29000.0},
    'A992': {'F_y': 50.0, 'F_u': 65.0, 'E': 29000.0},
    'A588': {'F_y': 50.0, 'F_u': 70.0, 'E': 29000.0},
    'A514': {'F_y': 100.0, 'F_u': 110.0, 'E': 29000.0}
}

# Standard plate thickness options (inches)
STANDARD_PLATE_THICKNESSES = np.array([
    0.1875, 0.25, 0.3125, 0.375, 0.4375, 0.5, 0.5625, 0.625, 0.6875, 0.75,
    0.875, 1.0, 1.125, 1.25, 1.375, 1.5, 1.75, 2.0, 2.25, 2.5, 3.0, 4.0
], dtype=np.float64)


def generate_combinations_dict(**kwargs):
    """
    Generates a single dictionary containing all combinations as columnar arrays.
    Shared utility function for all plate generators.

    Args:
        **kwargs: Keyword arguments with array-like values

    Returns:
        Dictionary with all combinations as columnar NumPy arrays
    """
    keys = list(kwargs.keys())
    value_arrays = list(kwargs.values())

    if not value_arrays:
        return {}
        
    combinations_iterator = itertools.product(*value_arrays)
    combinations_array = np.array(list(combinations_iterator))

    if combinations_array.size == 0:
        return {key: np.array([]) for key in keys}

    transposed_array = combinations_array.T
    
    return dict(zip(keys, transposed_array))


def generate_plate_configurations(
    plate_type_id,
    plate_grade_id,
    t,
    w=None,
    l=None,
    height=None,
    a=None,
    include_material_props=True
):
    """
    Generate all combinations of plate configurations with automatic material properties.
    
    This is the main general-purpose plate generator that works for all plate types.
    
    Args:
        plate_type_id: Array-like of plate type IDs (0=SHEAR, 1=FLANGE, 2=STIFFENER, 3=GUSSET, etc.)
        plate_grade_id: Array-like of steel grade IDs (0=A36, 1=A572_50, 2=A992, etc.)
        thickness: Array-like of plate thicknesses in inches
        width: Array-like of plate widths in inches (optional, plate-dependent)
        length: Array-like of plate lengths in inches (optional, plate-dependent)
        height: Array-like of plate heights in inches (optional, stiffener plates)
        include_material_props: If True, adds F_y, F_u, E to output (default: True)
    
    Returns:
        Dictionary with all plate configuration combinations as columnar arrays
    """
    # Build input dictionary dynamically
    input_dict = {
        'plate_type_id': plate_type_id,
        'plate_grade_id': plate_grade_id,
        't': t,
    }
    
    if w is not None:
        input_dict['w'] = w
    if l is not None:
        input_dict['l'] = l
    if a is not None:
        input_dict['a'] = a
    if height is not None:
        input_dict['height'] = height
    
    # Generate base combinations
    combinations = generate_combinations_dict(**input_dict)
    
    if not combinations:
        return {}
    
    # Add derived values
    grade_ids = combinations['plate_grade_id']
    type_ids = combinations['plate_type_id']
    
    # Map to string names
    combinations['plate_type'] = np.array([PLATE_TYPE_MAP[tid] for tid in type_ids])
    combinations['plate_grade'] = np.array([PLATE_GRADE_MAP[gid] for gid in grade_ids])
    
    # Add material properties if requested
    if include_material_props:
        grade_names = [PLATE_GRADE_MAP[gid] for gid in grade_ids]
        combinations['F_y'] = np.array([PLATE_MATERIAL_PROPERTIES[gn]['F_y'] for gn in grade_names])
        combinations['F_u'] = np.array([PLATE_MATERIAL_PROPERTIES[gn]['F_u'] for gn in grade_names])
        combinations['E'] = np.array([PLATE_MATERIAL_PROPERTIES[gn]['E'] for gn in grade_names])

    return combinations


def generate_shear_plates(
    plate_grade_id,
    t,
    w = None,
    l = None,
    a = None,
    type_id = 301
):
    """
    Generate shear plate configurations for simple shear connections.
    
    Shear plates are typically used in beam-to-column or beam-to-girder connections
    and are bolted to the web of the supported beam.
    
    **GLOBAL NAMING SYSTEM**: Includes 'type_id' (300-399) for automatic naming in interfaces.
    
    Args:
        plate_grade_id: Array-like of steel grade IDs
            0=A36 (F_y=36 ksi, F_u=58 ksi)
            1=A572_50 (F_y=50 ksi, F_u=65 ksi)
            2=A992 (F_y=50 ksi, F_u=65 ksi)
            3=A588 (F_y=50 ksi, F_u=70 ksi)
            4=A514 (F_y=100 ksi, F_u=110 ksi)
        t: Array-like of plate thicknesses (typically 1/4" to 5/8")
        w: Array-like of plate widths (typically 3" to 8") (optional)
        l: Array-like of plate lengths (typically 6" to 24") (optional)
        a: Array-like of edge distances or other dimension (optional)
        type_id: Type code for automatic naming (300-399 range):
            300='plate', 301='plate_shear', 302='plate_flange', 303='plate_stiffener',
            304='plate_gusset', 305='plate_base', 306='plate_doubler'
    
    Returns:
        Dictionary with shear plate configurations including material properties,
        plus 'type_id' and 'type_name' for automatic interface naming
    """
    plate_type_id = np.array([0], dtype=np.int64)  # 0 = SHEAR type
    
    input_dict = {
        'plate_type_id': plate_type_id,
        'plate_grade_id': plate_grade_id,
        't': t,
        'a':a
    }
    
    if w is not None:
        input_dict['w'] = w
    if l is not None:
        input_dict['l'] = l
    if a is not None:
        input_dict['a'] = a
    
    plates = generate_plate_configurations(**input_dict, include_material_props=True)
    
    # Remove string fields, keep only integer IDs
    plates.pop('plate_type', None)
    plates.pop('plate_grade', None)
    
    # Add type information for automatic naming (global naming system)
    if plates and 't' in plates:
        n_configs = len(plates['t'])
        plates['type_id'] = np.full(n_configs, type_id, dtype=np.int32)
        
        # Type name mapping (300-399 for plates)
        type_names = {
            300: 'plate', 301: 'plate_shear', 302: 'plate_flange',
            303: 'plate_stiffener', 304: 'plate_gusset',
            305: 'plate_base', 306: 'plate_doubler'
        }
        type_name = type_names.get(type_id, 'plate_shear')
        plates['type_name'] = np.full(n_configs, type_name, dtype='<U20')

    return plates


def generate_flange_plates(
    plate_grade_id,
    thickness,
    width,
    length,
    moment_connection_type_id=None
):
    """
    Generate flange plate configurations for moment connections.
    
    Flange plates are used in fully restrained (FR) moment connections,
    typically bolted to beam flanges.
    
    Args:
        plate_grade_id: Array-like of steel grade IDs
            0=A36 (F_y=36 ksi, F_u=58 ksi)
            1=A572_50 (F_y=50 ksi, F_u=65 ksi)
            2=A992 (F_y=50 ksi, F_u=65 ksi)
            3=A588 (F_y=50 ksi, F_u=70 ksi)
            4=A514 (F_y=100 ksi, F_u=110 ksi)
        thickness: Array-like of plate thicknesses (typically 1/2" to 2")
        width: Array-like of plate widths (typically 6" to 16")
        length: Array-like of plate lengths (typically 10" to 30")
        moment_connection_type_id: Array-like for connection type (0=bolted, 1=welded, 2=hybrid)
    
    Returns:
        Dictionary with flange plate configurations
    """
    plate_type_id = np.array([1], dtype=np.int64)  # 1 = FLANGE type
    
    input_dict = {
        'plate_type_id': plate_type_id,
        'plate_grade_id': plate_grade_id,
        'thickness': thickness,
        'width': width,
        'length': length
    }
    
    if moment_connection_type_id is not None:
        input_dict['moment_connection_type_id'] = moment_connection_type_id
    
    plates = generate_plate_configurations(**input_dict)
    
    # Add flange-specific parameters
    if plates and 'area' in plates:
        F_y = plates['F_y']
        F_u = plates['F_u']
        area = plates['area']
        t = plates['thickness']
        w = plates['width']
        
        # Tensile yielding strength
        plates['P_n_yield'] = F_y * area
        plates['phi_P_n_yield'] = 0.9 * plates['P_n_yield']
        
        # Tensile rupture strength (simplified, assumes no holes)
        plates['P_n_rupture'] = F_u * area
        plates['phi_P_n_rupture'] = 0.75 * plates['P_n_rupture']
        
        # Plastic section modulus (for flexural checks)
        plates['Z_x'] = (w * t**2) / 4.0
    
    return plates


def generate_stiffener_plates(
    plate_grade_id,
    thickness,
    width,
    height,
    stiffener_type_id=None
):
    """
    Generate stiffener plate configurations for web or column stiffeners.
    
    Stiffeners are used to reinforce web or column elements at concentrated loads,
    support reactions, or moment connections.
    
    Args:
        plate_grade_id: Array-like of steel grade IDs
            0=A36 (F_y=36 ksi, F_u=58 ksi)
            1=A572_50 (F_y=50 ksi, F_u=65 ksi)
            2=A992 (F_y=50 ksi, F_u=65 ksi)
            3=A588 (F_y=50 ksi, F_u=70 ksi)
            4=A514 (F_y=100 ksi, F_u=110 ksi)
        thickness: Array-like of plate thicknesses (typically 1/4" to 3/4")
        width: Array-like of stiffener widths (typically 3" to 8")
        height: Array-like of stiffener heights (typically 6" to 36")
        stiffener_type_id: Array-like for type (0=bearing, 1=transverse, 2=diagonal)
    
    Returns:
        Dictionary with stiffener plate configurations
    """
    plate_type_id = np.array([2], dtype=np.int64)  # 2 = STIFFENER type
    
    input_dict = {
        'plate_type_id': plate_type_id,
        'plate_grade_id': plate_grade_id,
        'thickness': thickness,
        'width': width,
        'height': height
    }
    
    if stiffener_type_id is not None:
        input_dict['stiffener_type_id'] = stiffener_type_id
    
    plates = generate_plate_configurations(**input_dict)
    
    # Add stiffener-specific parameters
    if plates and 'area' in plates:
        F_y = plates['F_y']
        t = plates['thickness']
        w = plates['width']
        h = plates['height']
        
        # Bearing strength (two stiffeners, simplified)
        bearing_area = 2 * w * t
        plates['R_n_bearing'] = 1.8 * F_y * bearing_area
        plates['phi_R_n_bearing'] = 0.75 * plates['R_n_bearing']
        
        # Buckling check parameter (width-thickness ratio)
        plates['b_t_ratio'] = (w / 2.0) / t  # for outstanding element
        
        # Limiting b/t for unstiffened elements (E = 29000 ksi)
        plates['b_t_limit'] = 0.56 * np.sqrt(29000.0 / F_y)
        
        # Slenderness ratio for column buckling
        plates['kl_r'] = (0.75 * h) / (t / np.sqrt(12.0))  # k=0.75 for stiffener
    
    return plates


def generate_gusset_plates(
    plate_grade_id,
    thickness,
    width,
    length,
    angle=None,
    connection_type_id=None
):
    """
    Generate gusset plate configurations for bracing connections.
    
    Gusset plates are used to connect diagonal bracing members to beams and columns
    in lateral force-resisting systems.
    
    Args:
        plate_grade_id: Array-like of steel grade IDs
            0=A36 (F_y=36 ksi, F_u=58 ksi)
            1=A572_50 (F_y=50 ksi, F_u=65 ksi)
            2=A992 (F_y=50 ksi, F_u=65 ksi)
            3=A588 (F_y=50 ksi, F_u=70 ksi)
            4=A514 (F_y=100 ksi, F_u=110 ksi)
        thickness: Array-like of plate thicknesses (typically 3/8" to 1")
        width: Array-like of gusset plate widths (typically 12" to 36")
        length: Array-like of gusset plate lengths (typically 12" to 48")
        angle: Array-like of brace angles in degrees (optional)
        connection_type_id: Array-like for connection type (0=bolted, 1=welded, 2=hybrid)
    
    Returns:
        Dictionary with gusset plate configurations
    """
    plate_type_id = np.array([3], dtype=np.int64)  # 3 = GUSSET type
    
    # Base parameters for plate generator (without angle)
    input_dict = {
        'plate_type_id': plate_type_id,
        'plate_grade_id': plate_grade_id,
        'thickness': thickness,
        'width': width,
        'length': length
    }
    
    # Generate base plate configurations
    plates = generate_plate_configurations(**input_dict)
    
    # Add angle as a separate combination if provided
    if plates and angle is not None:
        # Store original base properties before regenerating
        base_plate_type_id = plates['plate_type_id']
        base_plate_grade_id = plates['plate_grade_id']
        
        # Add angle to combinations
        angle_arr = np.asarray(angle)
        temp_dict = {
            'plate_type_id': base_plate_type_id,
            'plate_grade_id': base_plate_grade_id,
            'thickness': plates['thickness'],
            'width': plates['width'],
            'length': plates['length'],
            'angle': angle
        }
        plates = generate_combinations_dict(**temp_dict)
        
        # Re-add derived values that were lost
        type_ids = plates['plate_type_id']
        grade_ids = plates['plate_grade_id']
        
        plates['plate_type'] = np.array([PLATE_TYPE_MAP[tid] for tid in type_ids])
        plates['plate_grade'] = np.array([PLATE_GRADE_MAP[gid] for gid in grade_ids])
        
        # Add material properties
        grade_names = [PLATE_GRADE_MAP[gid] for gid in grade_ids]
        plates['F_y'] = np.array([PLATE_MATERIAL_PROPERTIES[gn]['F_y'] for gn in grade_names])
        plates['F_u'] = np.array([PLATE_MATERIAL_PROPERTIES[gn]['F_u'] for gn in grade_names])
        plates['density'] = np.array([PLATE_MATERIAL_PROPERTIES[gn]['density'] for gn in grade_names])
        
        # Recalculate geometric properties
        t = np.asarray(plates['thickness'], dtype=np.float64)
        w = np.asarray(plates['width'], dtype=np.float64)
        l = np.asarray(plates['length'], dtype=np.float64)
        
        plates['area'] = w * t
        plates['volume'] = w * l * t
        plates['weight'] = plates['volume'] * plates['density']
    
    # Add connection_type_id if provided
    if plates and connection_type_id is not None:
        conn_arr = np.asarray(connection_type_id)
        temp_dict = {key: val for key, val in plates.items()}
        temp_dict['connection_type_id'] = connection_type_id
        plates = generate_combinations_dict(**temp_dict)
    
    # Add gusset-specific parameters
    if plates:
        F_y = plates['F_y']
        F_u = plates['F_u']
        t = plates['thickness']
        w = plates['width']
        l = plates['length']
        
        # Whitmore width (simplified for brace angle)
        if 'angle' in plates:
            angle_rad = np.radians(plates['angle'])
            # Whitmore effective width = w + 2 * edge_distance * tan(30°)
            # Simplified: use plate width as baseline
            plates['whitmore_width'] = w + 2.0 * 2.0 * np.tan(np.radians(30.0))  # Simplified
        
        # Block shear check parameters (placeholder)
        plates['gross_area'] = w * t
        
        # Buckling strength (simplified)
        plates['slenderness'] = l / t
    
    return plates


def get_plate_mapping_info():
    """
    Returns mapping information for integer-based plate inputs.
    
    Returns:
        Dictionary with mapping information for plate types and grades
    """
    return {
        'plate_types': {id: ptype for id, ptype in PLATE_TYPE_MAP.items()},
        'plate_grades': {id: grade for id, grade in PLATE_GRADE_MAP.items()},
        'material_properties': PLATE_MATERIAL_PROPERTIES,
        'standard_thicknesses': STANDARD_PLATE_THICKNESSES
    }


def example_shear_plate_configurations():
    """Example usage of shear plate generator."""
    plates = generate_shear_plates(
        plate_grade_id=[0, 1],           # A36 and A572_50
        t=[0.25, 0.375, 0.5],    # 1/4", 3/8", 1/2"
        w=[3.5, 5.0, 6.0],           # 3.5", 5", 6"
        l=[12.0, 18.0, 24.0]        # 12", 18", 24"
    )
    return plates


def example_flange_plate_configurations():
    """Example usage of flange plate generator."""
    plates = generate_flange_plates(
        plate_grade_id=[1, 2],           # A572_50 and A992
        thickness=[0.75, 1.0, 1.25],     # 3/4", 1", 1-1/4"
        width=[8.0, 10.0, 12.0],         # 8", 10", 12"
        length=[15.0, 18.0, 24.0]        # 15", 18", 24"
    )
    return plates


def example_stiffener_configurations():
    """Example usage of stiffener plate generator."""
    plates = generate_stiffener_plates(
        plate_grade_id=[0, 1],           # A36 and A572_50
        thickness=[0.375, 0.5, 0.625],   # 3/8", 1/2", 5/8"
        width=[4.0, 5.0, 6.0],           # 4", 5", 6"
        height=[12.0, 18.0, 24.0]        # 12", 18", 24"
    )
    return plates


def example_gusset_configurations():
    """Example usage of gusset plate generator."""
    plates = generate_gusset_plates(
        plate_grade_id=[0, 1],           # A36 and A572_50
        thickness=[0.5, 0.625, 0.75],    # 1/2", 5/8", 3/4"
        width=[18.0, 24.0, 30.0],        # 18", 24", 30"
        length=[18.0, 24.0, 36.0],       # 18", 24", 36"
        angle=[35.0, 45.0, 55.0]         # Brace angles
    )
    return plates


if __name__ == "__main__":
    # Show mapping information
    mappings = get_plate_mapping_info()
    print("Plate Configuration System")
    print("=" * 50)
    print(f"Plate Types: {mappings['plate_types']}")
    print(f"Plate Grades: {mappings['plate_grades']}")
    print(f"Standard Thicknesses: {len(mappings['standard_thicknesses'])} options")
    print()
    
    # Example: Shear plates
    print("Example 1: Shear Plates")
    print("-" * 50)
    shear_plates = example_shear_plate_configurations()
    print(f"Generated {len(shear_plates['thickness'])} shear plate configurations")
    print(f"Parameters: {list(shear_plates.keys())}")
    
    # Show first 3 configurations
    print("\nFirst 3 shear plate configurations:")
    for i in range(min(3, len(shear_plates['thickness']))):
        print(f"  Plate {i+1}: {shear_plates['plate_grade'][i]} "
              f"PL {shear_plates['width'][i]:.2f}\"x{shear_plates['thickness'][i]:.3f}\"x{shear_plates['length'][i]:.1f}\" "
              f"(F_y={shear_plates['F_y'][i]:.0f} ksi, φV_n={shear_plates['phi_V_n_gross'][i]:.1f} kips)")
    
    print("\n" + "=" * 50)
    print("Example 2: Flange Plates")
    print("-" * 50)
    flange_plates = example_flange_plate_configurations()
    print(f"Generated {len(flange_plates['thickness'])} flange plate configurations")
    
    print("\n" + "=" * 50)
    print("Example 3: Stiffener Plates")
    print("-" * 50)
    stiffener_plates = example_stiffener_configurations()
    print(f"Generated {len(stiffener_plates['thickness'])} stiffener configurations")
    
    print("\n" + "=" * 50)
    print("Example 4: Gusset Plates")
    print("-" * 50)
    gusset_plates = example_gusset_configurations()
    print(f"Generated {len(gusset_plates['thickness'])} gusset plate configurations")
