"""
Weld Configuration Generator
============================

High-performance weld configuration generator for structural steel connections.
Generates combinations of weld specifications for:
- Fillet welds (most common)
- Groove welds (full penetration, partial penetration)
- Plug/slot welds
- Combined weld configurations

Follows the same pattern as bolt_configuration and plate generators for consistency.

Features:
- Integer mapping for efficiency (weld types, electrode grades)
- Columnar NumPy arrays for Numba compatibility
- Auto material properties (F_EXX, strength)
- Pre-computed capacities
- Integration with load path system

Author: steel_lib integration
Date: October 2025
"""

import itertools
import numpy as np
from typing import Dict, List, Union, Optional, Tuple

# Weld type mappings (integer codes for efficiency)
WELD_TYPE_MAP = {
    0: 'FILLET',           # Fillet weld (most common)
    1: 'CJP',              # Complete Joint Penetration (groove weld)
    2: 'PJP',              # Partial Joint Penetration (groove weld)
    3: 'PLUG',             # Plug weld
    4: 'SLOT',             # Slot weld
    5: 'FILLET_BOTH',      # Fillet both sides
    6: 'FILLET_INTERMITTENT' # Intermittent fillet
}

# Electrode grade mappings
ELECTRODE_MAP = {
    0: 'E60XX',   # 60 ksi electrode
    1: 'E70XX',   # 70 ksi electrode (most common)
    2: 'E80XX',   # 80 ksi electrode
    3: 'E90XX',   # 90 ksi electrode
    4: 'E100XX',  # 100 ksi electrode
    5: 'E110XX'   # 110 ksi electrode
}

# Electrode properties
ELECTRODE_PROPERTIES = {
    'E60XX': {'F_EXX': 60.0, 'F_w': 60.0 * 0.6},  # F_w = 0.60*F_EXX
    'E70XX': {'F_EXX': 70.0, 'F_w': 70.0 * 0.6},
    'E80XX': {'F_EXX': 80.0, 'F_w': 80.0 * 0.6},
    'E90XX': {'F_EXX': 90.0, 'F_w': 90.0 * 0.6},
    'E100XX': {'F_EXX': 100.0, 'F_w': 100.0 * 0.6},
    'E110XX': {'F_EXX': 110.0, 'F_w': 110.0 * 0.6}
}

# Standard fillet weld sizes (inches)
STANDARD_FILLET_SIZES = np.array([
    0.1875,  # 3/16"
    0.25,    # 1/4"
    0.3125,  # 5/16"
    0.375,   # 3/8"
    0.4375,  # 7/16"
    0.5,     # 1/2"
    0.5625,  # 9/16"
    0.625,   # 5/8"
    0.6875,  # 11/16"
    0.75,    # 3/4"
    0.875,   # 7/8"
    1.0      # 1"
], dtype=np.float64)

# Weld position codes
WELD_POSITION_MAP = {
    0: 'FLAT',      # Flat (1F, 1G)
    1: 'HORIZONTAL', # Horizontal (2F, 2G)
    2: 'VERTICAL',   # Vertical (3F, 3G)
    3: 'OVERHEAD'    # Overhead (4F, 4G)
}


def generate_combinations_dict(**kwargs):
    """
    Generates a single dictionary containing all combinations as columnar arrays.
    Shared utility function for all weld generators.

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


def generate_weld_configurations(
    weld_type_id,
    electrode_id,
    weld_size,
    weld_length=None,
    leg_a=None,
    leg_b=None,
    throat=None,
    include_capacity=True
):
    """
    Generate all combinations of weld configurations with automatic properties.
    
    This is the main general-purpose weld generator that works for all weld types.
    
    Args:
        weld_type_id: Array-like of weld type IDs
            0=FILLET (Fillet weld)
            1=CJP (Complete Joint Penetration)
            2=PJP (Partial Joint Penetration)
            3=PLUG (Plug weld)
            4=SLOT (Slot weld)
            5=FILLET_BOTH (Fillet both sides)
            6=FILLET_INTERMITTENT (Intermittent fillet)
        electrode_id: Array-like of electrode IDs
            0=E60XX (F_EXX=60 ksi, F_w=36.0 ksi)
            1=E70XX (F_EXX=70 ksi, F_w=42.0 ksi)
            2=E80XX (F_EXX=80 ksi, F_w=48.0 ksi)
            3=E90XX (F_EXX=90 ksi, F_w=54.0 ksi)
            4=E100XX (F_EXX=100 ksi, F_w=60.0 ksi)
            5=E110XX (F_EXX=110 ksi, F_w=66.0 ksi)
        weld_size: Array-like of weld sizes in inches (leg size for fillet)
        weld_length: Array-like of weld lengths in inches (optional)
        leg_a: Array-like of leg A dimensions for unequal leg fillets (optional)
        leg_b: Array-like of leg B dimensions for unequal leg fillets (optional)
        throat: Array-like of effective throat dimensions (optional, auto-calculated)
        include_capacity: If True, adds strength calculations to output (default: True)
    
    Returns:
        Dictionary with all weld configuration combinations as columnar arrays
    """
    # Build input dictionary dynamically
    input_dict = {
        'weld_type_id': weld_type_id,
        'electrode_id': electrode_id,
        'weld_size': weld_size
    }
    
    if weld_length is not None:
        input_dict['weld_length'] = weld_length
    if leg_a is not None:
        input_dict['leg_a'] = leg_a
    if leg_b is not None:
        input_dict['leg_b'] = leg_b
    if throat is not None:
        input_dict['throat'] = throat
    
    # Generate base combinations
    combinations = generate_combinations_dict(**input_dict)
    
    if not combinations:
        return {}
    
    # Add derived values
    type_ids = combinations['weld_type_id']
    electrode_ids = combinations['electrode_id']
    
    # Add electrode properties (using integer IDs only)
    electrode_names = [ELECTRODE_MAP[eid] for eid in electrode_ids]
    combinations['F_EXX'] = np.array([ELECTRODE_PROPERTIES[en]['F_EXX'] for en in electrode_names])
    combinations['F_w'] = np.array([ELECTRODE_PROPERTIES[en]['F_w'] for en in electrode_names])
    
    # Calculate effective throat for fillet welds
    weld_sizes = np.asarray(combinations['weld_size'], dtype=np.float64)
    weld_type_ids = type_ids
    
    # For equal leg fillet welds, throat = 0.707 * leg size
    if 'throat' not in combinations:
        throat = np.zeros_like(weld_sizes)
        for i, wtype_id in enumerate(weld_type_ids):
            if wtype_id in [0, 5, 6]:  # FILLET, FILLET_BOTH, FILLET_INTERMITTENT
                if 'leg_a' in combinations and 'leg_b' in combinations:
                    # Unequal leg: throat = smaller leg * 0.707
                    throat[i] = min(combinations['leg_a'][i], combinations['leg_b'][i]) * 0.707
                else:
                    # Equal leg: throat = leg * 0.707
                    throat[i] = weld_sizes[i] * 0.707
            elif wtype_id == 1:  # CJP
                # CJP: throat = plate thickness (will be provided separately)
                throat[i] = weld_sizes[i]  # Placeholder
            elif wtype_id == 2:  # PJP
                # PJP: throat = effective throat depth
                throat[i] = weld_sizes[i]  # Placeholder
        
        combinations['throat'] = throat
    
    # Calculate capacities if requested
    if include_capacity and 'weld_length' in combinations:
        F_w = combinations['F_w']
        throat_arr = combinations['throat']
        length_arr = np.asarray(combinations['weld_length'], dtype=np.float64)
        
        # Base metal strength per inch (for capacity calculations)
        # R_n = F_w * A_we = F_w * throat * length
        nominal_strength = F_w * throat_arr * length_arr  # Total capacity in kips
        
        # AISC J2-3: φ = 0.75 for welds
        combinations['R_n'] = nominal_strength
        combinations['phi_R_n'] = 0.75 * nominal_strength
        
        # Strength per inch of weld
        combinations['strength_per_inch'] = F_w * throat_arr
        combinations['phi_strength_per_inch'] = 0.75 * F_w * throat_arr
    
    return combinations


def generate_fillet_welds(
    electrode_id,
    weld_size,
    weld_length,
    both_sides=None,
    intermittent=None,
    intermittent_pitch=None
):
    """
    Generate fillet weld configurations.
    
    Fillet welds are the most common weld type, used in T-joints, lap joints, and corner joints.
    
    Args:
        electrode_id: Array-like of electrode IDs
            0=E60XX (F_EXX=60 ksi, F_w=36.0 ksi)
            1=E70XX (F_EXX=70 ksi, F_w=42.0 ksi)
            2=E80XX (F_EXX=80 ksi, F_w=48.0 ksi)
            3=E90XX (F_EXX=90 ksi, F_w=54.0 ksi)
            4=E100XX (F_EXX=100 ksi, F_w=60.0 ksi)
            5=E110XX (F_EXX=110 ksi, F_w=66.0 ksi)
        weld_size: Array-like of leg sizes in inches (3/16" to 1")
        weld_length: Array-like of weld lengths in inches
        both_sides: Array-like of boolean flags for double fillet welds (optional)
        intermittent: Array-like of boolean flags for intermittent welds (optional)
        intermittent_pitch: Array-like of pitch for intermittent welds in inches (optional)
    
    Returns:
        Dictionary with fillet weld configurations
    """
    weld_type_id = np.array([0], dtype=np.int64)  # 0 = FILLET type
    
    # Build input dict with all parameters
    input_dict = {
        'weld_type_id': weld_type_id,
        'electrode_id': electrode_id,
        'weld_size': weld_size,
        'weld_length': weld_length
    }
    
    # Add optional parameters before generation
    if both_sides is not None:
        input_dict['both_sides'] = both_sides
    if intermittent is not None:
        input_dict['intermittent'] = intermittent
    if intermittent_pitch is not None:
        input_dict['intermittent_pitch'] = intermittent_pitch
    
    # Generate all combinations at once
    combinations = generate_combinations_dict(**input_dict)
    
    if not combinations:
        return {}
    
    # Add derived values (using integer IDs only)
    type_ids = combinations['weld_type_id']
    electrode_ids = combinations['electrode_id']
    
    # Add electrode properties (no string mappings)
    electrode_names = [ELECTRODE_MAP[eid] for eid in electrode_ids]
    combinations['F_EXX'] = np.array([ELECTRODE_PROPERTIES[en]['F_EXX'] for en in electrode_names])
    combinations['F_w'] = np.array([ELECTRODE_PROPERTIES[en]['F_w'] for en in electrode_names])
    

    

    

    
    return combinations


def generate_groove_welds(
    electrode_id,
    weld_type_id,  # 1=CJP, 2=PJP
    plate_thickness,
    weld_length,
    effective_throat=None
):
    """
    Generate groove weld configurations (CJP and PJP).
    
    Groove welds provide full cross-section strength and are used in butt joints
    and high-capacity connections.
    
    Args:
        electrode_id: Array-like of electrode IDs
            0=E60XX (F_EXX=60 ksi, F_w=36.0 ksi)
            1=E70XX (F_EXX=70 ksi, F_w=42.0 ksi)
            2=E80XX (F_EXX=80 ksi, F_w=48.0 ksi)
            3=E90XX (F_EXX=90 ksi, F_w=54.0 ksi)
            4=E100XX (F_EXX=100 ksi, F_w=60.0 ksi)
            5=E110XX (F_EXX=110 ksi, F_w=66.0 ksi)
        weld_type_id: Array-like with 1=CJP or 2=PJP
        plate_thickness: Array-like of plate thicknesses (base metal)
        weld_length: Array-like of weld lengths
        effective_throat: Array-like of effective throat for PJP welds (optional)
    
    Returns:
        Dictionary with groove weld configurations
    """
    input_dict = {
        'weld_type_id': weld_type_id,
        'electrode_id': electrode_id,
        'weld_size': plate_thickness,  # For groove welds, size relates to plate thickness
        'weld_length': weld_length
    }
    
    if effective_throat is not None:
        input_dict['throat'] = effective_throat
    
    welds = generate_weld_configurations(**input_dict)
    
    # Add groove-specific parameters
    if welds:
        welds['plate_thickness'] = welds['weld_size'].copy()
        
        # For CJP, full plate capacity
        # For PJP, limited by effective throat
        weld_type_ids = welds['weld_type_id']
        F_w = welds['F_w']
        t = welds['plate_thickness']
        L = welds['weld_length']
        
        # Recalculate capacity based on weld type ID
        R_n = np.zeros(len(welds['weld_type_id']))
        for i, wtype_id in enumerate(weld_type_ids):
            if wtype_id == 1:  # CJP
                # CJP: Full plate capacity
                # Use base metal strength (typically lower than weld metal)
                R_n[i] = F_w[i] * t[i] * L[i]
            elif wtype_id == 2:  # PJP
                # PJP: Limited by effective throat
                throat_val = welds['throat'][i]
                R_n[i] = F_w[i] * throat_val * L[i]
        
        welds['R_n'] = R_n
        welds['phi_R_n'] = 0.75 * R_n
    
    return welds


def generate_plug_slot_welds(
    electrode_id,
    weld_type_id,  # 3=PLUG, 4=SLOT
    diameter_or_width,
    length=None,
    thickness=None,
    n_welds=None
):
    """
    Generate plug or slot weld configurations.
    
    Used for lap joints and repair work. Less common than fillet or groove welds.
    
    Args:
        electrode_id: Array-like of electrode IDs
            0=E60XX (F_EXX=60 ksi, F_w=36.0 ksi)
            1=E70XX (F_EXX=70 ksi, F_w=42.0 ksi)
            2=E80XX (F_EXX=80 ksi, F_w=48.0 ksi)
            3=E90XX (F_EXX=90 ksi, F_w=54.0 ksi)
            4=E100XX (F_EXX=100 ksi, F_w=60.0 ksi)
            5=E110XX (F_EXX=110 ksi, F_w=66.0 ksi)
        weld_type_id: Array-like with 3=PLUG or 4=SLOT
        diameter_or_width: Array-like of hole diameter (plug) or width (slot) in inches
        length: Array-like of slot lengths in inches (for slot welds only)
        thickness: Array-like of plate thicknesses
        n_welds: Array-like of number of plugs/slots
    
    Returns:
        Dictionary with plug/slot weld configurations
    """
    input_dict = {
        'weld_type_id': weld_type_id,
        'electrode_id': electrode_id,
        'weld_size': diameter_or_width
    }
    
    if length is not None:
        input_dict['length'] = length
    if thickness is not None:
        input_dict['thickness'] = thickness
    if n_welds is not None:
        input_dict['n_welds'] = n_welds
    
    welds = generate_weld_configurations(**input_dict, include_capacity=False)
    
    # Add plug/slot-specific capacity calculations
    if welds:
        F_w = welds['F_w']
        d_or_w = welds['weld_size']
        weld_type_ids = welds['weld_type_id']
        
        # Per AISC J2.3
        A_eff = np.zeros(len(weld_type_ids))
        
        for i, wtype_id in enumerate(weld_type_ids):
            if wtype_id == 3:  # PLUG
                # Plug weld: A_eff = π * d²/4
                A_eff[i] = np.pi * (d_or_w[i] ** 2) / 4.0
            elif wtype_id == 4:  # SLOT
                # Slot weld: A_eff = width * length
                if 'length' in welds:
                    A_eff[i] = d_or_w[i] * welds['length'][i]
                else:
                    A_eff[i] = d_or_w[i] * d_or_w[i]  # Assume square
        
        # Capacity per weld
        welds['A_effective'] = A_eff
        welds['R_n_per_weld'] = 0.6 * F_w * A_eff
        welds['phi_R_n_per_weld'] = 0.75 * welds['R_n_per_weld']
        
        # Total capacity if number of welds specified
        if 'n_welds' in welds:
            n = np.asarray(welds['n_welds'], dtype=np.float64)
            welds['R_n_total'] = welds['R_n_per_weld'] * n
            welds['phi_R_n_total'] = welds['phi_R_n_per_weld'] * n
    
    return welds


def get_weld_mapping_info():
    """
    Returns mapping information for integer-based weld inputs.
    
    Returns:
        Dictionary with mapping information for weld types and electrodes
    """
    return {
        'weld_types': {id: wtype for id, wtype in WELD_TYPE_MAP.items()},
        'electrodes': {id: elec for id, elec in ELECTRODE_MAP.items()},
        'electrode_properties': ELECTRODE_PROPERTIES,
        'standard_fillet_sizes': STANDARD_FILLET_SIZES,
        'weld_positions': {id: pos for id, pos in WELD_POSITION_MAP.items()}
    }


def calculate_weld_length_required(
    force,
    electrode_grade='E70XX',
    weld_size=0.25,
    safety_factor=0.75,
    both_sides=False
):
    """
    Calculate minimum weld length required for a given force.
    
    Utility function for preliminary design.
    
    Args:
        force: Applied force in kips
        electrode_grade: Electrode designation (default E70XX)
        weld_size: Weld leg size in inches (default 1/4")
        safety_factor: Resistance factor φ (default 0.75)
        both_sides: If True, weld on both sides (default False)
    
    Returns:
        Minimum weld length required in inches
    """
    F_w = ELECTRODE_PROPERTIES[electrode_grade]['F_w']
    throat = weld_size * 0.707
    strength_per_inch = safety_factor * F_w * throat
    
    if both_sides:
        strength_per_inch *= 2
    
    L_required = force / strength_per_inch
    
    return L_required


def example_fillet_weld_configurations():
    """Example usage of fillet weld generator."""
    welds = generate_fillet_welds(
        electrode_id=[1, 1],              # E70XX
        weld_size=[0.25, 0.3125, 0.375],  # 1/4", 5/16", 3/8"
        weld_length=[12.0, 18.0, 24.0],   # 12", 18", 24"
        both_sides=[False, True]          # Single and double fillet
    )
    return welds


def example_groove_weld_configurations():
    """Example usage of groove weld generator."""
    welds = generate_groove_welds(
        electrode_id=[1],                 # E70XX
        weld_type_id=[1, 2],             # CJP and PJP
        plate_thickness=[0.375, 0.5, 0.625],
        weld_length=[12.0, 18.0],
        effective_throat=[0.25, 0.375]   # For PJP
    )
    return welds


if __name__ == "__main__":
    # Show mapping information
    mappings = get_weld_mapping_info()
    print("Weld Configuration System")
    print("=" * 70)
    print(f"Weld Types: {mappings['weld_types']}")
    print(f"Electrodes: {mappings['electrodes']}")
    print(f"Standard Fillet Sizes: {len(mappings['standard_fillet_sizes'])} options")
    print()
    
    # Example: Fillet welds
    print("Example 1: Fillet Welds")
    print("-" * 70)
    fillet_welds = example_fillet_weld_configurations()
    print(f"Generated {len(fillet_welds['weld_size'])} fillet weld configurations")
    print(f"Parameters: {list(fillet_welds.keys())}")
    
    # Show first 3 configurations
    print("\nFirst 3 fillet weld configurations:")
    for i in range(min(3, len(fillet_welds['weld_size']))):
        sides = "both sides" if fillet_welds.get('both_sides', [False])[i % len(fillet_welds.get('both_sides', [False]))] else "one side"
        print(f"  Weld {i+1}: {fillet_welds['electrode'][i]} "
              f"{fillet_welds['weld_size'][i]:.3f}\" fillet, {fillet_welds['weld_length'][i]:.1f}\" long, {sides}")
        print(f"    Throat = {fillet_welds['throat'][i]:.3f}\", "
              f"φR_n = {fillet_welds['phi_R_n'][i]:.1f} kips, "
              f"φR_n/in = {fillet_welds['phi_strength_per_inch'][i]:.2f} k/in")
    
    print("\n" + "=" * 70)
    print("Example 2: Groove Welds")
    print("-" * 70)
    groove_welds = example_groove_weld_configurations()
    print(f"Generated {len(groove_welds['weld_size'])} groove weld configurations")
    
    # Calculate required weld length
    print("\n" + "=" * 70)
    print("Example 3: Weld Length Calculator")
    print("-" * 70)
    force = 40.0  # kips
    weld_size = 0.3125  # 5/16"
    L_req_single = calculate_weld_length_required(force, weld_size=weld_size, both_sides=False)
    L_req_double = calculate_weld_length_required(force, weld_size=weld_size, both_sides=True)
    
    print(f"For {force:.0f} kip force with {weld_size:.4f}\" ({weld_size*16:.0f}/16\") E70XX fillet weld:")
    print(f"  Single side: {L_req_single:.1f}\" required")
    print(f"  Both sides:  {L_req_double:.1f}\" required per side")
