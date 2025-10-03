"""
Load Path System V2 - Numba-Compatible, Performance-Focused
============================================================

A modular system for calculating load transfer through connection interfaces.
Designed for vectorized operations and numba JIT compilation.

Architecture:
    1. Interface definitions (bolt group, weld, plate, etc.)
    2. Load transfer calculations per interface
    3. Composable load paths connecting multiple interfaces
    4. Batch evaluation with vectorized operations

Variable naming follows: docs/variable_naming_protocol.ipynb
- AISC symbols preserved (F_y, L_ev, etc.)
- Result arrays prefixed with 'results_'
- Lengths in inches, forces in kips, stresses in ksi

Focus: Simple shear connections for now
Example: Beam web → Weld → Plate → Bolts → Column web
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from numba import njit

# =============================================================================
# INTERFACE TYPES - Simple Shear Connection
# =============================================================================

# Interface 1: Weld connection (Beam web to Plate)
# Interface 2: Bolt connection (Plate to Column web)
# Interface 3: Plate strength checks
# Interface 4: Beam web strength checks
# Interface 5: Column web strength checks


# =============================================================================
# LOAD TRANSFER FUNCTIONS (Numba-compatible)
# =============================================================================

@njit
def transfer_weld_to_plate(
    V_u: float,
    weld_size: float,
    weld_length: float,
    electrode_strength: float,
    both_sides: bool
) -> Tuple[float, float]:
    """
    Calculate load transfer through fillet weld.
    
    Interface: Beam web → Weld → Plate
    
    Args:
        V_u: Applied shear force (kips)
        weld_size: Fillet weld size (in)
        weld_length: Total weld length per side (in)
        electrode_strength: Electrode strength FEXX (ksi)
        both_sides: True if weld on both sides
        
    Returns:
        capacity: Weld capacity (kips)
        utilization: V_u / capacity
        
    Note: Placeholder calculation - update with actual AISC J2 equations
    """
    # PLACEHOLDER - Simplified calculation
    # TODO: Use actual AISC 360 Table J2.5 calculations
    phi = 0.75
    n_welds = 2.0 if both_sides else 1.0
    
    # Simplified: capacity per inch of weld
    capacity_per_inch = 0.707 * weld_size * electrode_strength * 0.6 * phi
    capacity = capacity_per_inch * weld_length * n_welds
    
    utilization = V_u / capacity if capacity > 0 else 999.0
    
    return capacity, utilization


@njit
def transfer_bolts_shear(
    V_u: float,
    d_bolt: float,
    F_nv: float,
    N_r: int,
    N_c: int,
    N_shear_planes: int
) -> Tuple[float, float]:
    """
    Calculate bolt group shear capacity.
    
    Interface: Plate → Bolts → Column web
    
    Args:
        V_u: Applied shear force (kips)
        d_bolt: Bolt diameter (in)
        F_nv: Bolt shear strength (ksi)
        N_r: Number of bolt rows
        N_c: Number of bolt columns
        N_shear_planes: Number of shear planes (1 or 2)
        
    Returns:
        capacity: Bolt group shear capacity (kips)
        utilization: V_u / capacity
        
    Note: Placeholder - update with actual AISC J3 equations
    """
    # PLACEHOLDER - Simplified calculation
    # TODO: Use actual AISC 360 J3.6 bolt shear equations
    phi = 0.75
    n_bolts = N_r * N_c
    A_bolt = np.pi * (d_bolt ** 2) / 4.0
    
    # Simplified bolt shear
    capacity = phi * F_nv * A_bolt * N_shear_planes * n_bolts
    
    utilization = V_u / capacity if capacity > 0 else 999.0
    
    return capacity, utilization


@njit
def check_bolt_bearing(
    V_u: float,
    d_bolt: float,
    t: float,
    F_u: float,
    L_ev: float,
    L_eh: float,
    S_r: float,
    S_c: float,
    N_r: int,
    N_c: int
) -> Tuple[float, float]:
    """
    Check bolt bearing on plate or member.
    
    Args:
        V_u: Applied shear force (kips)
        d_bolt: Bolt diameter (in)
        t: Plate/member thickness (in)
        F_u: Ultimate strength (ksi)
        L_ev: Vertical edge distance (in)
        L_eh: Horizontal edge distance (in)
        S_r: Row spacing (in)
        S_c: Column spacing (in)
        N_r: Number of bolt rows
        N_c: Number of bolt columns
        
    Returns:
        capacity: Bearing capacity (kips)
        utilization: V_u / capacity
        
    Note: Placeholder - update with actual AISC J3 equations
    """
    # PLACEHOLDER - Simplified calculation
    # TODO: Use actual AISC 360 J3.10 bearing equations
    phi = 0.75
    n_bolts = N_r * N_c
    
    # Simplified bearing - 2.4*d*t*Fu per bolt
    capacity_per_bolt = phi * 2.4 * d_bolt * t * F_u
    capacity = capacity_per_bolt * n_bolts
    
    utilization = V_u / capacity if capacity > 0 else 999.0
    
    return capacity, utilization


@njit
def check_plate_shear_yielding(
    V_u: float,
    t: float,
    width: float,
    F_y: float,
    F_u: float
) -> Tuple[float, float, float]:
    """
    Check plate shear yielding and rupture.
    
    Args:
        V_u: Applied shear force (kips)
        t: Plate thickness (in)
        width: Plate width perpendicular to shear (in)
        F_y: Yield strength (ksi)
        F_u: Ultimate strength (ksi)
        
    Returns:
        capacity_yielding: Shear yielding capacity (kips)
        capacity_rupture: Shear rupture capacity (kips)
        utilization: V_u / min(capacity)
        
    Note: Placeholder - update with actual AISC J4 equations
    """
    # PLACEHOLDER - Simplified calculation
    # TODO: Use actual AISC 360 J4.2 shear yielding/rupture equations
    phi_y = 1.0
    phi_u = 0.75
    
    # Gross area
    A_g = t * width
    
    # Yielding: 0.6*Fy*Ag
    capacity_yielding = phi_y * 0.6 * F_y * A_g
    
    # Rupture: 0.6*Fu*Anv (simplified - no hole deduction for now)
    capacity_rupture = phi_u * 0.6 * F_u * A_g
    
    capacity = min(capacity_yielding, capacity_rupture)
    utilization = V_u / capacity if capacity > 0 else 999.0
    
    return capacity_yielding, capacity_rupture, utilization


@njit
def check_block_shear(
    V_u: float,
    t: float,
    F_y: float,
    F_u: float,
    L_ev: float,
    L_eh: float,
    S_r: float,
    N_r: int,
    d_v: float
) -> Tuple[float, float]:
    """
    Check block shear rupture along bolt pattern.
    
    Args:
        V_u: Applied shear force (kips)
        t: Plate thickness (in)
        F_y: Yield strength (ksi)
        F_u: Ultimate strength (ksi)
        L_ev: Vertical edge distance (in)
        L_eh: Horizontal edge distance (in)
        S_r: Row spacing (in)
        N_r: Number of rows
        d_v: Hole diameter vertical (in)
        
    Returns:
        capacity: Block shear capacity (kips)
        utilization: V_u / capacity
        
    Note: Placeholder - update with actual AISC J4 equations
    """
    # PLACEHOLDER - Simplified calculation
    # TODO: Use actual AISC 360 J4.3 block shear equations
    phi = 0.75
    
    # Tension plane length
    L_t = L_eh
    A_nt = (L_t - 0.5 * d_v) * t
    
    # Shear plane length
    L_v = L_ev + (N_r - 1) * S_r
    A_nv = (L_v - (N_r - 0.5) * d_v) * t
    A_gv = L_v * t
    
    # Block shear capacity
    term1 = 0.6 * F_u * A_nv + 1.0 * F_u * A_nt
    term2 = 0.6 * F_y * A_gv + 1.0 * F_u * A_nt
    
    capacity = phi * min(term1, term2)
    utilization = V_u / capacity if capacity > 0 else 999.0
    
    return capacity, utilization


# =============================================================================
# INTERFACE DEFINITIONS (Data Structures)
# =============================================================================

class WeldInterface:
    """
    Weld connection interface.
    
    Attributes aligned with variable_naming_protocol.ipynb:
        electrode_id, weld_size, weld_length, both_sides
    """
    def __init__(self, weld_config: Dict):
        self.weld_size = weld_config['weld_size']
        self.weld_length = weld_config['weld_length']
        self.electrode_id = weld_config['electrode_id']
        self.both_sides = weld_config.get('both_sides', True)
        
        # Electrode strength mapping
        electrode_map = {
            0: 60.0,  # E60XX
            1: 70.0,  # E70XX
            2: 80.0,  # E80XX
        }
        self.electrode_strength = electrode_map.get(self.electrode_id, 70.0)
    
    def evaluate(self, V_u: float) -> Dict:
        """Evaluate weld capacity for given load."""
        capacity, utilization = transfer_weld_to_plate(
            V_u=V_u,
            weld_size=self.weld_size,
            weld_length=self.weld_length,
            electrode_strength=self.electrode_strength,
            both_sides=self.both_sides
        )
        
        return {
            'interface_type': 'weld',
            'capacity': capacity,
            'utilization': utilization,
            'is_adequate': utilization <= 1.0,
            'limit_state': 'weld_shear'
        }


class BoltInterface:
    """
    Bolt connection interface.
    
    Attributes aligned with variable_naming_protocol.ipynb:
        d_bolt, F_nv, N_r, N_c, S_r, S_c, L_ev, L_eh, etc.
    """
    def __init__(self, bolt_config: Dict, plate_config: Dict, support_config: Dict):
        # Bolt properties
        self.d_bolt = bolt_config['bolt_size']
        self.F_nv = bolt_config['F_nv']
        self.F_nt = bolt_config['F_nt']
        self.N_r = bolt_config['N_r']
        self.N_c = bolt_config['N_c']
        self.S_r = bolt_config['S_r']
        self.S_c = bolt_config.get('S_c', 3.0)
        self.L_ev = bolt_config['L_ev']
        self.L_eh = bolt_config['L_eh']
        self.d_v = bolt_config['d_v']
        self.d_h = bolt_config['d_h']
        self.N_shear_planes = 1  # Simple shear - single shear plane
        
        # Plate properties
        self.plate_t = plate_config['thickness']
        self.plate_F_y = plate_config['F_y']
        self.plate_F_u = plate_config['F_u']
        self.plate_width = plate_config['width']
        
        # Support properties (column web)
        self.support_t = support_config.get('tw', 0.5)
        self.support_F_u = support_config.get('F_u', 65.0)
    
    def evaluate(self, V_u: float) -> Dict:
        """Evaluate bolt connection capacity for given load."""
        
        # Check 1: Bolt shear
        cap_bolt_shear, util_bolt_shear = transfer_bolts_shear(
            V_u=V_u,
            d_bolt=self.d_bolt,
            F_nv=self.F_nv,
            N_r=self.N_r,
            N_c=self.N_c,
            N_shear_planes=self.N_shear_planes
        )
        
        # Check 2: Bolt bearing on plate
        cap_bearing_plate, util_bearing_plate = check_bolt_bearing(
            V_u=V_u,
            d_bolt=self.d_bolt,
            t=self.plate_t,
            F_u=self.plate_F_u,
            L_ev=self.L_ev,
            L_eh=self.L_eh,
            S_r=self.S_r,
            S_c=self.S_c,
            N_r=self.N_r,
            N_c=self.N_c
        )
        
        # Check 3: Bolt bearing on support (column web)
        cap_bearing_support, util_bearing_support = check_bolt_bearing(
            V_u=V_u,
            d_bolt=self.d_bolt,
            t=self.support_t,
            F_u=self.support_F_u,
            L_ev=self.L_ev,
            L_eh=self.L_eh,
            S_r=self.S_r,
            S_c=self.S_c,
            N_r=self.N_r,
            N_c=self.N_c
        )
        
        # Check 4: Plate shear yielding/rupture
        cap_yield, cap_rupture, util_plate_shear = check_plate_shear_yielding(
            V_u=V_u,
            t=self.plate_t,
            width=self.plate_width,
            F_y=self.plate_F_y,
            F_u=self.plate_F_u
        )
        
        # Check 5: Block shear on plate
        cap_block, util_block = check_block_shear(
            V_u=V_u,
            t=self.plate_t,
            F_y=self.plate_F_y,
            F_u=self.plate_F_u,
            L_ev=self.L_ev,
            L_eh=self.L_eh,
            S_r=self.S_r,
            N_r=self.N_r,
            d_v=self.d_v
        )
        
        # Find controlling limit state
        capacities = {
            'bolt_shear': cap_bolt_shear,
            'bearing_plate': cap_bearing_plate,
            'bearing_support': cap_bearing_support,
            'plate_shear': min(cap_yield, cap_rupture),
            'block_shear': cap_block
        }
        
        utilizations = {
            'bolt_shear': util_bolt_shear,
            'bearing_plate': util_bearing_plate,
            'bearing_support': util_bearing_support,
            'plate_shear': util_plate_shear,
            'block_shear': util_block
        }
        
        # Find controlling (highest utilization)
        controlling_state = max(utilizations, key=utilizations.get)
        max_utilization = utilizations[controlling_state]
        min_capacity = capacities[controlling_state]
        
        return {
            'interface_type': 'bolt',
            'capacity': min_capacity,
            'utilization': max_utilization,
            'is_adequate': max_utilization <= 1.0,
            'limit_state': controlling_state,
            'all_capacities': capacities,
            'all_utilizations': utilizations
        }


# =============================================================================
# LOAD PATH - Composable Connection Sequence
# =============================================================================

class SimpleShearConnection:
    """
    Simple shear connection load path.
    
    Sequence: Beam web → Weld → Plate → Bolts → Column web
    
    This represents the complete load transfer path for a simple
    shear connection (e.g., shear tab, single angle).
    """
    
    def __init__(
        self,
        beam_section: Dict,
        plate_config: Dict,
        weld_config: Dict,
        bolt_config: Dict,
        column_section: Dict
    ):
        """
        Initialize simple shear connection.
        
        Args:
            beam_section: Dict with beam properties (d, tw, F_y, F_u, etc.)
            plate_config: Dict with plate properties (thickness, width, F_y, F_u, etc.)
            weld_config: Dict with weld properties (weld_size, weld_length, electrode_id, etc.)
            bolt_config: Dict with bolt properties (bolt_size, N_r, N_c, F_nv, etc.)
            column_section: Dict with column properties (d, tw, F_y, F_u, etc.)
        """
        self.beam_section = beam_section
        self.plate_config = plate_config
        self.weld_config = weld_config
        self.bolt_config = bolt_config
        self.column_section = column_section
        
        # Create interfaces
        self.weld_interface = WeldInterface(weld_config)
        self.bolt_interface = BoltInterface(bolt_config, plate_config, column_section)
        
        # Store interface sequence
        self.interfaces = [self.weld_interface, self.bolt_interface]
    
    def evaluate(self, V_u: float) -> Dict:
        """
        Evaluate complete load path for applied shear load.
        
        Args:
            V_u: Applied shear force (kips)
            
        Returns:
            Dict with:
                - is_adequate: Boolean, True if all interfaces pass
                - max_utilization: Maximum utilization across all interfaces
                - controlling_interface: Which interface controls
                - controlling_limit_state: Which limit state controls
                - interface_results: List of results for each interface
        """
        results = []
        
        # Evaluate each interface in sequence
        for interface in self.interfaces:
            result = interface.evaluate(V_u)
            results.append(result)
        
        # Find controlling interface (highest utilization)
        max_util = max(r['utilization'] for r in results)
        controlling_idx = next(i for i, r in enumerate(results) if r['utilization'] == max_util)
        controlling_result = results[controlling_idx]
        
        return {
            'is_adequate': all(r['is_adequate'] for r in results),
            'max_utilization': max_util,
            'controlling_interface': controlling_result['interface_type'],
            'controlling_limit_state': controlling_result['limit_state'],
            'interface_results': results,
            'applied_load': V_u
        }


# =============================================================================
# BATCH EVALUATION - Vectorized Processing
# =============================================================================

def evaluate_simple_shear_batch(
    beam_sections: Dict,
    plate_configs: Dict,
    weld_configs: Dict,
    bolt_configs: Dict,
    column_section: Dict,
    V_u: float
) -> Dict:
    """
    Batch evaluation of multiple simple shear connection configurations.
    
    This function evaluates all combinations of plates, welds, and bolts
    for given beam and column sections.
    
    Args:
        beam_sections: Dict with beam properties (can be single or batch)
        plate_configs: Dict with arrays of plate configurations
        weld_configs: Dict with arrays of weld configurations
        bolt_configs: Dict with arrays of bolt configurations
        column_section: Dict with column properties
        V_u: Applied shear force (kips)
        
    Returns:
        Dict with arrays of results for all configurations:
            - results_adequate: Boolean array
            - results_utilization: Utilization array
            - results_controlling_state: Array of controlling limit states
            - count: Total number of configurations evaluated
    """
    n_plates = len(plate_configs['thickness'])
    n_welds = len(weld_configs['weld_size'])
    n_bolts = len(bolt_configs['bolt_size'])
    n_total = n_plates * n_welds * n_bolts
    
    # Initialize result arrays
    results_adequate = np.zeros(n_total, dtype=bool)
    results_utilization = np.zeros(n_total)
    results_controlling_state = []
    
    idx = 0
    for i_plate in range(n_plates):
        plate_config = {
            'thickness': plate_configs['thickness'][i_plate],
            'width': plate_configs['width'][i_plate],
            'length': plate_configs['length'][i_plate],
            'F_y': plate_configs['F_y'][i_plate],
            'F_u': plate_configs['F_u'][i_plate],
        }
        
        for i_weld in range(n_welds):
            weld_config = {
                'weld_size': weld_configs['weld_size'][i_weld],
                'weld_length': weld_configs['weld_length'][i_weld],
                'electrode_id': weld_configs['electrode_id'][i_weld],
                'both_sides': weld_configs['both_sides'][i_weld],
            }
            
            for i_bolt in range(n_bolts):
                bolt_config = {
                    'bolt_size': bolt_configs['bolt_size'][i_bolt],
                    'F_nv': bolt_configs['F_nv'][i_bolt],
                    'F_nt': bolt_configs['F_nt'][i_bolt],
                    'N_r': bolt_configs['N_r'][i_bolt],
                    'N_c': bolt_configs['N_c'][i_bolt],
                    'S_r': bolt_configs['S_r'][i_bolt],
                    'L_ev': bolt_configs['L_ev'][i_bolt],
                    'L_eh': bolt_configs['L_eh'][i_bolt],
                    'd_v': bolt_configs['d_v'][i_bolt],
                    'd_h': bolt_configs['d_h'][i_bolt],
                }
                
                # Create and evaluate connection
                connection = SimpleShearConnection(
                    beam_section=beam_sections,
                    plate_config=plate_config,
                    weld_config=weld_config,
                    bolt_config=bolt_config,
                    column_section=column_section
                )
                
                result = connection.evaluate(V_u)
                
                results_adequate[idx] = result['is_adequate']
                results_utilization[idx] = result['max_utilization']
                results_controlling_state.append(result['controlling_limit_state'])
                
                idx += 1
    
    return {
        'count': n_total,
        'results_adequate': results_adequate,
        'results_utilization': results_utilization,
        'results_controlling_state': results_controlling_state,
        'V_u': V_u
    }


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def find_optimal_design(batch_results: Dict) -> Dict:
    """
    Find optimal design from batch results.
    
    Args:
        batch_results: Results from evaluate_simple_shear_batch
        
    Returns:
        Dict with optimal design index and properties
    """
    adequate_mask = batch_results['results_adequate']
    
    if not np.any(adequate_mask):
        return {'found': False, 'message': 'No adequate designs found'}
    
    # Among adequate designs, find minimum utilization
    adequate_utils = np.where(adequate_mask, batch_results['results_utilization'], np.inf)
    optimal_idx = np.argmin(adequate_utils)
    
    return {
        'found': True,
        'index': optimal_idx,
        'utilization': batch_results['results_utilization'][optimal_idx],
        'controlling_state': batch_results['results_controlling_state'][optimal_idx],
        'is_adequate': True
    }
