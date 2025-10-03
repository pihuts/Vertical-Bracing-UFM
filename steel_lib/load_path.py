"""
Load Path System for Steel Connections
======================================

Models load transfer through structural connections from member to member.
Handles:
- Load decomposition (forces/moments to connection forces)
- Load path tracking (beam → plate → column)
- Connection element evaluation (bolts, welds, plates)
- Limit state checking at each transfer point
- Critical capacity identification

Integrates with:
- section_properties (member definitions)
- plate_generator (connection plates)
- generator_combination (bolt patterns)
- aisc_14th (limit state functions)

Author: steel_lib integration
Date: October 2025
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Union, Any
from dataclasses import dataclass, field
from enum import IntEnum

# Connection type definitions
class ConnectionType(IntEnum):
    """Connection types for load transfer."""
    BOLTED = 0
    WELDED = 1
    HYBRID = 2  # Bolted on one side, welded on other


class MemberType(IntEnum):
    """Structural member types."""
    BEAM = 0
    COLUMN = 1
    BRACE = 2
    GIRDER = 3
    PLATE = 4


class LoadPathElement(IntEnum):
    """Elements in the load path."""
    MEMBER_A = 0       # Source member (e.g., beam)
    BOLTS_A = 1        # Bolts connecting to member A
    PLATE = 2          # Connection plate
    WELDS_B = 3        # Welds connecting to member B
    BOLTS_B = 4        # Bolts connecting to member B
    MEMBER_B = 5       # Target member (e.g., column)


@dataclass
class LoadVector:
    """
    Represents forces and moments at a connection point.
    All forces in kips, moments in kip-in.
    """
    # Forces
    P: float = 0.0      # Axial force (tension +, compression -)
    V_x: float = 0.0    # Shear in x-direction
    V_y: float = 0.0    # Shear in y-direction (primary shear for typical connections)
    
    # Moments
    M_x: float = 0.0    # Moment about x-axis
    M_y: float = 0.0    # Moment about y-axis
    M_z: float = 0.0    # Torsion about z-axis
    
    def magnitude(self) -> float:
        """Calculate resultant force magnitude."""
        return np.sqrt(self.P**2 + self.V_x**2 + self.V_y**2)
    
    def shear_resultant(self) -> float:
        """Calculate resultant shear force."""
        return np.sqrt(self.V_x**2 + self.V_y**2)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'P': self.P, 'V_x': self.V_x, 'V_y': self.V_y,
            'M_x': self.M_x, 'M_y': self.M_y, 'M_z': self.M_z
        }


@dataclass
class ConnectionElement:
    """
    Represents a single element in the load path (bolt group, weld, plate, etc.).
    """
    element_id: str                    # Unique identifier
    element_type: LoadPathElement      # Type from enum
    connection_type: ConnectionType    # Bolted/welded/hybrid
    
    # Geometric properties
    geometry: Dict[str, Any] = field(default_factory=dict)
    
    # Material properties
    material: Dict[str, Any] = field(default_factory=dict)
    
    # Load at this element
    load: LoadVector = field(default_factory=LoadVector)
    
    # Capacities (calculated)
    capacities: Dict[str, float] = field(default_factory=dict)
    
    # Critical limit state
    governing_limit_state: Optional[str] = None
    governing_capacity: Optional[float] = None
    utilization: Optional[float] = None  # Demand/Capacity ratio


@dataclass
class LoadPath:
    """
    Complete load path from one member to another through connection elements.
    Example: Beam → Bolts → Plate → Welds → Column
    """
    path_id: str
    source_member: str              # Member A (e.g., "W18X35")
    target_member: str              # Member B (e.g., "W14X90")
    
    # Applied loads at connection
    applied_load: LoadVector = field(default_factory=LoadVector)
    
    # Connection elements in order
    elements: List[ConnectionElement] = field(default_factory=list)
    
    # Overall connection properties
    connection_type: ConnectionType = ConnectionType.HYBRID
    eccentricity: float = 0.0  # inches
    
    # Analysis results
    is_valid: bool = False
    critical_element: Optional[str] = None
    critical_capacity: Optional[float] = None
    max_utilization: Optional[float] = None
    
    def add_element(self, element: ConnectionElement):
        """Add an element to the load path."""
        self.elements.append(element)
    
    def get_element(self, element_type: LoadPathElement) -> Optional[ConnectionElement]:
        """Get element by type."""
        for elem in self.elements:
            if elem.element_type == element_type:
                return elem
        return None
    
    def evaluate(self) -> bool:
        """
        Evaluate the complete load path and find critical element.
        Returns True if connection is adequate.
        """
        if not self.elements:
            return False
        
        max_util = 0.0
        critical_elem = None
        critical_cap = np.inf
        
        for elem in self.elements:
            if elem.utilization is not None and elem.utilization > max_util:
                max_util = elem.utilization
                critical_elem = elem.element_id
                critical_cap = elem.governing_capacity
        
        self.max_utilization = max_util
        self.critical_element = critical_elem
        self.critical_capacity = critical_cap
        self.is_valid = max_util <= 1.0
        
        return self.is_valid


class LoadPathGenerator:
    """
    Main class for creating and evaluating load paths through connections.
    """
    
    def __init__(self):
        """Initialize load path generator."""
        self.load_paths: List[LoadPath] = []
        self.limit_state_functions = None  # Reference to imported functions
    
    def create_simple_shear_connection(
        self,
        connection_id: str,
        beam_section: Dict,
        column_section: Dict,
        plate_config: Dict,
        bolt_config: Dict,
        applied_load: LoadVector,
        eccentricity: float = 0.0,
        weld_size: Optional[float] = None,
        weld_config: Optional[Dict] = None
    ) -> LoadPath:
        """
        Create a simple shear connection load path.
        
        Typical configuration:
        Beam → Bolts (to beam web) → Plate → Welds (to column flange) → Column
        
        Args:
            connection_id: Unique identifier
            beam_section: Dictionary with beam properties from AISC selector
            column_section: Dictionary with column properties
            plate_config: Dictionary from plate generator
            bolt_config: Dictionary from bolt generator
            applied_load: LoadVector with connection forces
            eccentricity: Load eccentricity in inches
            weld_size: Fillet weld size (if welded to column) - deprecated, use weld_config
            weld_config: Dictionary from weld generator (preferred over weld_size)
        
        Returns:
            LoadPath object with all elements
        """
        # Create load path
        path = LoadPath(
            path_id=connection_id,
            source_member=beam_section.get('designation', 'BEAM'),
            target_member=column_section.get('designation', 'COLUMN'),
            applied_load=applied_load,
            connection_type=ConnectionType.HYBRID if weld_size else ConnectionType.BOLTED,
            eccentricity=eccentricity
        )
        
        # Element 1: Source beam
        beam_elem = ConnectionElement(
            element_id=f"{connection_id}_BEAM",
            element_type=LoadPathElement.MEMBER_A,
            connection_type=ConnectionType.BOLTED,
            geometry={
                'designation': beam_section.get('designation'),
                'd': beam_section.get('d'),
                'tw': beam_section.get('tw'),
                'bf': beam_section.get('bf'),
                'tf': beam_section.get('tf')
            },
            material={
                'F_y': beam_section.get('F_y', 50.0),
                'F_u': beam_section.get('F_u', 65.0)
            },
            load=applied_load
        )
        path.add_element(beam_elem)
        
        # Element 2: Bolts to beam web
        bolts_beam = ConnectionElement(
            element_id=f"{connection_id}_BOLTS_BEAM",
            element_type=LoadPathElement.BOLTS_A,
            connection_type=ConnectionType.BOLTED,
            geometry={
                'bolt_size': bolt_config.get('bolt_size'),
                'bolt_grade': bolt_config.get('bolt_grade'),
                'N_r': bolt_config.get('N_r'),
                'N_c': bolt_config.get('N_c'),
                'S_r': bolt_config.get('S_r'),
                'S_c': bolt_config.get('S_c'),
                'n_bolts': bolt_config.get('N_r', 1) * bolt_config.get('N_c', 1)
            },
            material={
                'F_nv': bolt_config.get('F_nv'),
                'F_nt': bolt_config.get('F_nt')
            },
            load=self._distribute_load_to_bolts(applied_load, bolt_config, eccentricity)
        )
        path.add_element(bolts_beam)
        
        # Element 3: Connection plate
        plate_elem = ConnectionElement(
            element_id=f"{connection_id}_PLATE",
            element_type=LoadPathElement.PLATE,
            connection_type=ConnectionType.HYBRID if weld_size else ConnectionType.BOLTED,
            geometry={
                'thickness': plate_config.get('thickness'),
                'width': plate_config.get('width'),
                'length': plate_config.get('length'),
                'area': plate_config.get('area')
            },
            material={
                'F_y': plate_config.get('F_y'),
                'F_u': plate_config.get('F_u'),
                'grade': plate_config.get('plate_grade')
            },
            load=applied_load
        )
        path.add_element(plate_elem)
        
        # Element 4: Welds to column (if welded)
        if weld_config or weld_size:
            # Use weld_config from weld generator if provided
            if weld_config:
                weld_elem = ConnectionElement(
                    element_id=f"{connection_id}_WELDS_COLUMN",
                    element_type=LoadPathElement.WELDS_B,
                    connection_type=ConnectionType.WELDED,
                    geometry={
                        'weld_type': weld_config.get('weld_type', 'FILLET'),
                        'weld_size': weld_config.get('weld_size', 0.25),
                        'weld_length': weld_config.get('weld_length', plate_config.get('length', 18.0)),
                        'throat': weld_config.get('throat', 0.707 * weld_config.get('weld_size', 0.25)),
                        'both_sides': weld_config.get('both_sides', True),
                        'electrode': weld_config.get('electrode', 'E70XX'),
                        'phi_R_n': weld_config.get('phi_R_n'),  # Use calculated capacity
                        'R_n': weld_config.get('R_n'),
                        'strength_per_inch': weld_config.get('strength_per_inch'),
                        'phi_strength_per_inch': weld_config.get('phi_strength_per_inch')
                    },
                    material={
                        'F_EXX': weld_config.get('F_EXX', 70.0),
                        'F_w': weld_config.get('F_w', 42.0)
                    },
                    load=applied_load
                )
            else:
                # Legacy support - use simple weld_size parameter
                weld_elem = ConnectionElement(
                    element_id=f"{connection_id}_WELDS_COLUMN",
                    element_type=LoadPathElement.WELDS_B,
                    connection_type=ConnectionType.WELDED,
                    geometry={
                        'weld_size': weld_size,
                        'weld_length': plate_config.get('length', 18.0),
                        'weld_type': 'FILLET',
                        'both_sides': True
                    },
                    material={
                        'F_EXX': 70.0  # E70XX electrode
                    },
                    load=applied_load
                )
            path.add_element(weld_elem)
        
        # Element 5: Target column
        column_elem = ConnectionElement(
            element_id=f"{connection_id}_COLUMN",
            element_type=LoadPathElement.MEMBER_B,
            connection_type=ConnectionType.WELDED if weld_size else ConnectionType.BOLTED,
            geometry={
                'designation': column_section.get('designation'),
                'd': column_section.get('d'),
                'tw': column_section.get('tw'),
                'bf': column_section.get('bf'),
                'tf': column_section.get('tf')
            },
            material={
                'F_y': column_section.get('F_y', 50.0),
                'F_u': column_section.get('F_u', 65.0)
            },
            load=applied_load
        )
        path.add_element(column_elem)
        
        return path
    
    def _distribute_load_to_bolts(
        self,
        applied_load: LoadVector,
        bolt_config: Dict,
        eccentricity: float
    ) -> LoadVector:
        """
        Distribute applied load to bolt group considering eccentricity.
        Returns load vector for critical bolt.
        """
        # Simple distribution - for accurate use instantaneous center of rotation
        n_bolts = bolt_config.get('N_r', 4) * bolt_config.get('N_c', 1)
        
        # Shear per bolt (uniform distribution)
        V_per_bolt = applied_load.V_y / n_bolts if n_bolts > 0 else 0.0
        
        # Additional shear due to moment from eccentricity
        if eccentricity > 0 and applied_load.V_y > 0:
            M_ecc = applied_load.V_y * eccentricity
            # This is simplified - proper calculation needs bolt coordinates
            V_moment = M_ecc / (n_bolts * bolt_config.get('S_r', 3.0))
            V_per_bolt += V_moment
        
        # Tension per bolt (if any)
        P_per_bolt = applied_load.P / n_bolts if n_bolts > 0 else 0.0
        
        return LoadVector(P=P_per_bolt, V_y=V_per_bolt)
    
    def evaluate_load_path(
        self,
        load_path: LoadPath,
        limit_state_functions: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Evaluate all elements in the load path and determine critical capacity.
        
        Args:
            load_path: LoadPath object to evaluate
            limit_state_functions: Dict of imported limit state functions
        
        Returns:
            Dictionary with evaluation results for each element
        """
        results = {
            'path_id': load_path.path_id,
            'elements': {},
            'is_adequate': False,
            'critical_element': None,
            'governing_capacity': None,
            'max_utilization': None
        }
        
        # Evaluate each element
        for elem in load_path.elements:
            elem_results = self._evaluate_element(elem, load_path, limit_state_functions)
            results['elements'][elem.element_id] = elem_results
            
            # Update element with results
            elem.capacities = elem_results.get('capacities', {})
            elem.governing_limit_state = elem_results.get('governing_limit_state')
            elem.governing_capacity = elem_results.get('governing_capacity')
            elem.utilization = elem_results.get('utilization')
        
        # Find critical element
        load_path.evaluate()
        results['is_adequate'] = load_path.is_valid
        results['critical_element'] = load_path.critical_element
        results['governing_capacity'] = load_path.critical_capacity
        results['max_utilization'] = load_path.max_utilization
        
        return results
    
    def _evaluate_element(
        self,
        element: ConnectionElement,
        load_path: LoadPath,
        limit_state_functions: Optional[Dict]
    ) -> Dict[str, Any]:
        """
        Evaluate a single element in the load path.
        Returns capacities and critical limit state.
        """
        results = {
            'element_type': element.element_type.name,
            'capacities': {},
            'governing_limit_state': None,
            'governing_capacity': None,
            'utilization': None,
            'demand': element.load.magnitude()
        }
        
        # Different evaluation based on element type
        if element.element_type == LoadPathElement.BOLTS_A:
            results = self._evaluate_bolts(element, load_path, limit_state_functions)
        
        elif element.element_type == LoadPathElement.PLATE:
            results = self._evaluate_plate(element, load_path, limit_state_functions)
        
        elif element.element_type == LoadPathElement.WELDS_B:
            results = self._evaluate_welds(element, load_path, limit_state_functions)
        
        elif element.element_type in [LoadPathElement.MEMBER_A, LoadPathElement.MEMBER_B]:
            results = self._evaluate_member(element, load_path, limit_state_functions)
        
        return results
    
    def _evaluate_bolts(
        self,
        element: ConnectionElement,
        load_path: LoadPath,
        limit_state_functions: Optional[Dict]
    ) -> Dict:
        """Evaluate bolt group limit states."""
        capacities = {}
        
        # Get properties
        geom = element.geometry
        mat = element.material
        load = element.load
        
        # Placeholder capacities (use actual limit state functions)
        n_bolts = geom.get('n_bolts', 4)
        F_nv = mat.get('F_nv', 54.0)
        d_bolt = geom.get('bolt_size', 0.875)
        A_bolt = np.pi * (d_bolt/2)**2
        
        # Bolt shear capacity
        capacities['bolt_shear'] = 0.75 * F_nv * A_bolt * n_bolts  # Simplified
        
        # Bearing capacity (needs plate thickness and F_u)
        # Would call actual bolt_bearing() function here
        capacities['bearing'] = 100.0  # Placeholder
        
        # Block shear
        # Would call actual block_shear() function here
        capacities['block_shear'] = 80.0  # Placeholder
        
        # Find governing
        governing_capacity = min(capacities.values())
        governing_limit_state = min(capacities, key=capacities.get)
        
        # Utilization
        demand = load.shear_resultant()
        utilization = demand / governing_capacity if governing_capacity > 0 else np.inf
        
        return {
            'element_type': 'BOLTS',
            'capacities': capacities,
            'governing_limit_state': governing_limit_state,
            'governing_capacity': governing_capacity,
            'utilization': utilization,
            'demand': demand
        }
    
    def _evaluate_plate(
        self,
        element: ConnectionElement,
        load_path: LoadPath,
        limit_state_functions: Optional[Dict]
    ) -> Dict:
        """Evaluate plate limit states."""
        capacities = {}
        
        geom = element.geometry
        mat = element.material
        load = element.load
        
        # Shear yielding (gross section)
        F_y = mat.get('F_y', 50.0)
        A_g = geom.get('area', 1.0)
        capacities['shear_yielding'] = 1.0 * 0.6 * F_y * A_g
        
        # Shear rupture (net section) - needs hole info
        # Would call actual shear_yielding_rupture() function
        capacities['shear_rupture'] = 75.0  # Placeholder
        
        # Block shear (if applicable)
        capacities['block_shear'] = 85.0  # Placeholder
        
        # Flexure (if moment present)
        if abs(load.M_y) > 0.1:
            # Would call flexural_14th() or flexural_15th()
            capacities['flexure'] = 60.0  # Placeholder
        
        governing_capacity = min(capacities.values())
        governing_limit_state = min(capacities, key=capacities.get)
        
        demand = load.shear_resultant()
        utilization = demand / governing_capacity if governing_capacity > 0 else np.inf
        
        return {
            'element_type': 'PLATE',
            'capacities': capacities,
            'governing_limit_state': governing_limit_state,
            'governing_capacity': governing_capacity,
            'utilization': utilization,
            'demand': demand
        }
    
    def _evaluate_welds(
        self,
        element: ConnectionElement,
        load_path: LoadPath,
        limit_state_functions: Optional[Dict]
    ) -> Dict:
        """
        Evaluate weld capacity using AISC provisions.
        
        Handles:
        - Fillet welds (most common)
        - Groove welds (CJP/PJP)
        - Single or double-sided welds
        - Longitudinal and transverse configurations
        
        Per AISC 360 J2: φ = 0.75, F_w = 0.60 × F_EXX
        """
        capacities = {}
        
        geom = element.geometry
        mat = element.material
        load = element.load
        
        # Extract weld properties
        weld_type = geom.get('weld_type', 'FILLET')
        w = geom.get('weld_size', 0.25)  # inches (leg size for fillet)
        L = geom.get('weld_length', 36.0)  # inches
        F_EXX = mat.get('F_EXX', 70.0)  # ksi
        both_sides = geom.get('both_sides', False)
        
        # Calculate F_w per AISC J2.4
        F_w = 0.60 * F_EXX  # ksi
        phi = 0.75  # Resistance factor for welds
        
        # Calculate effective throat
        if weld_type == 'FILLET':
            # For equal leg fillet: throat = 0.707 × leg size
            throat = geom.get('throat', 0.707 * w)  # inches
        elif weld_type in ['CJP', 'GROOVE']:
            # For complete joint penetration: throat = plate thickness
            throat = geom.get('throat', w)  # Use weld_size as throat
        elif weld_type == 'PJP':
            # For partial joint penetration: use specified effective throat
            throat = geom.get('throat', 0.5 * w)
        else:
            throat = geom.get('throat', 0.707 * w)
        
        # Calculate effective weld area
        A_we = throat * L  # in²
        
        # Account for both sides if applicable
        if both_sides:
            A_we *= 2
        
        # Base weld shear capacity per AISC J2-3
        # R_n = F_w × A_we (for shear on weld)
        R_n_shear = F_w * A_we  # kips
        capacities['weld_shear'] = phi * R_n_shear
        
        # Base metal shear capacity (AISC J2-4)
        # Check if base metal governs (usually for matching weld)
        if 'base_thickness' in geom and 'base_F_y' in mat:
            t_base = geom['base_thickness']
            F_y_base = mat['base_F_y']
            A_base = t_base * L
            if both_sides:
                A_base *= 2
            R_n_base = 0.6 * F_y_base * A_base
            capacities['base_metal_shear'] = 1.0 * R_n_base  # φ = 1.0 for base metal shear
        
        # For longitudinal welds, check for length effects per AISC J2.2b
        # Reduction factor for long welds (L > 100w)
        if L > 100 * w:
            reduction = 1.2 - 0.002 * (L / w)
            reduction = max(reduction, 0.6)  # Minimum 60%
            capacities['weld_shear_long'] = capacities['weld_shear'] * reduction
        
        # Check for directional effects if load angle is specified
        load_angle = geom.get('load_angle', 90.0)  # degrees from weld axis
        if load_angle != 90.0:
            # AISC J2.4: No increase for load angle, use base equation
            # (Some codes allow increase for transverse loads)
            angle_factor = 1.0
            capacities['weld_shear_directional'] = capacities['weld_shear'] * angle_factor
        
        # If actual weld generator output is provided, use it directly
        if 'phi_R_n' in geom:
            capacities['weld_capacity_provided'] = geom['phi_R_n']
        
        # Determine governing capacity
        governing_capacity = min(capacities.values()) if capacities else 0.0
        governing_limit_state = min(capacities, key=capacities.get) if capacities else 'weld_shear'
        
        # Calculate demand and utilization
        demand = load.shear_resultant()
        
        # For moment loading on weld group (if M_z present)
        if abs(load.M_z) > 0.01:
            # Add moment demand (simplified - proper analysis needs weld group properties)
            # M = f × I_p / r_max, where f is force at max distance
            demand_moment = abs(load.M_z) / L  # Simplified
            demand = max(demand, demand_moment)
        
        utilization = demand / governing_capacity if governing_capacity > 0 else np.inf
        
        # Add detailed weld info to results
        weld_info = {
            'weld_type': weld_type,
            'weld_size': w,
            'weld_length': L,
            'throat': throat,
            'F_EXX': F_EXX,
            'F_w': F_w,
            'both_sides': both_sides,
            'effective_area': A_we
        }
        
        return {
            'element_type': 'WELDS',
            'capacities': capacities,
            'governing_limit_state': governing_limit_state,
            'governing_capacity': governing_capacity,
            'utilization': utilization,
            'demand': demand,
            'weld_info': weld_info
        }
    
    def _evaluate_member(
        self,
        element: ConnectionElement,
        load_path: LoadPath,
        limit_state_functions: Optional[Dict]
    ) -> Dict:
        """Evaluate member local effects (web shear, etc.)."""
        capacities = {}
        
        geom = element.geometry
        mat = element.material
        load = element.load
        
        # Web shear capacity
        if 'd' in geom and 'tw' in geom:
            d = geom['d']
            tw = geom['tw']
            F_y = mat.get('F_y', 50.0)
            A_w = d * tw
            capacities['web_shear'] = 1.0 * 0.6 * F_y * A_w
        
        # Web local yielding/crippling (if concentrated load)
        # Would call actual limit state functions
        
        governing_capacity = min(capacities.values()) if capacities else np.inf
        governing_limit_state = min(capacities, key=capacities.get) if capacities else 'none'
        
        demand = load.shear_resultant()
        utilization = demand / governing_capacity if governing_capacity > 0 else 0.0
        
        return {
            'element_type': 'MEMBER',
            'capacities': capacities,
            'governing_limit_state': governing_limit_state,
            'governing_capacity': governing_capacity,
            'utilization': utilization,
            'demand': demand
        }


def generate_load_paths_batch(
    beam_sections: Dict,
    column_sections: Dict,
    plate_configs: Dict,
    bolt_configs: Dict,
    applied_loads: np.ndarray,
    eccentricities: Optional[np.ndarray] = None,
    weld_sizes: Optional[np.ndarray] = None
) -> List[LoadPath]:
    """
    Generate multiple load paths for batch evaluation.
    
    Useful for optimization/parametric studies where you want to evaluate
    many different connection configurations.
    
    Args:
        beam_sections: Dict from AISC selector with multiple beams
        column_sections: Dict from AISC selector with multiple columns
        plate_configs: Dict from plate generator
        bolt_configs: Dict from bolt generator
        applied_loads: Array of shear forces (kips)
        eccentricities: Array of eccentricities (inches)
        weld_sizes: Array of weld sizes (inches) or None for bolted
    
    Returns:
        List of LoadPath objects
    """
    generator = LoadPathGenerator()
    load_paths = []
    
    # Get counts
    n_beams = beam_sections.get('count', len(beam_sections.get('designations', [])))
    n_plates = len(plate_configs.get('thickness', []))
    n_bolts = len(bolt_configs.get('bolt_size', []))
    n_loads = len(applied_loads) if hasattr(applied_loads, '__len__') else 1
    
    if eccentricities is None:
        eccentricities = np.zeros(n_loads)
    if weld_sizes is None:
        weld_sizes = np.full(n_loads, 0.25)  # Default 1/4" weld
    
    # Generate all combinations
    idx = 0
    for i_beam in range(n_beams):
        for i_plate in range(n_plates):
            for i_bolt in range(n_bolts):
                for i_load in range(n_loads):
                    # Extract individual configs
                    beam = {key: vals[i_beam] for key, vals in beam_sections.items() 
                           if key != 'count' and hasattr(vals, '__getitem__')}
                    
                    plate = {key: vals[i_plate] for key, vals in plate_configs.items()
                            if hasattr(vals, '__getitem__')}
                    
                    bolt = {key: vals[i_bolt] for key, vals in bolt_configs.items()
                           if hasattr(vals, '__getitem__')}
                    
                    # Create load vector
                    load = LoadVector(V_y=applied_loads[i_load])
                    
                    # Assume column is same for all (or modify as needed)
                    column = beam.copy()  # Placeholder
                    
                    # Create load path
                    path = generator.create_simple_shear_connection(
                        connection_id=f"PATH_{idx:06d}",
                        beam_section=beam,
                        column_section=column,
                        plate_config=plate,
                        bolt_config=bolt,
                        applied_load=load,
                        eccentricity=eccentricities[i_load],
                        weld_size=weld_sizes[i_load]
                    )
                    
                    load_paths.append(path)
                    idx += 1
    
    return load_paths


if __name__ == "__main__":
    # Example usage
    print("Load Path System")
    print("=" * 70)
    
    # Create a simple load path
    generator = LoadPathGenerator()
    
    # Mock beam and column
    beam = {'designation': 'W18X35', 'd': 17.7, 'tw': 0.300, 'bf': 6.0, 'tf': 0.425}
    column = {'designation': 'W14X90', 'd': 14.02, 'tw': 0.440, 'bf': 14.5, 'tf': 0.710}
    
    # Mock plate
    plate = {
        'thickness': 0.375,
        'width': 5.5,
        'length': 18.0,
        'area': 2.0625,
        'F_y': 50.0,
        'F_u': 65.0,
        'plate_grade': 'A572_50'
    }
    
    # Mock bolts
    bolts = {
        'bolt_size': 0.875,
        'bolt_grade': 'A325-N',
        'N_r': 4,
        'N_c': 1,
        'S_r': 3.0,
        'S_c': 3.0,
        'F_nv': 54.0,
        'F_nt': 90.0
    }
    
    # Applied load
    load = LoadVector(V_y=40.0)  # 40 kip shear
    
    # Create load path
    path = generator.create_simple_shear_connection(
        connection_id="SC001",
        beam_section=beam,
        column_section=column,
        plate_config=plate,
        bolt_config=bolts,
        applied_load=load,
        eccentricity=3.0,
        weld_size=0.3125  # 5/16" weld
    )
    
    print(f"\nLoad Path: {path.source_member} → {path.target_member}")
    print(f"Applied Load: V = {path.applied_load.V_y:.1f} kips")
    print(f"Eccentricity: {path.eccentricity:.2f} in")
    print(f"\nLoad Path Elements:")
    for i, elem in enumerate(path.elements, 1):
        print(f"  {i}. {elem.element_type.name:15s} - {elem.element_id}")
    
    # Evaluate load path
    print(f"\nEvaluating load path...")
    results = generator.evaluate_load_path(path)
    
    print(f"\nResults:")
    print(f"  Is Adequate: {results['is_adequate']}")
    print(f"  Critical Element: {results['critical_element']}")
    print(f"  Governing Capacity: {results.get('governing_capacity', 0):.1f} kips")
    print(f"  Max Utilization: {results.get('max_utilization', 0):.2f}")
    
    print(f"\nElement Details:")
    for elem_id, elem_results in results['elements'].items():
        print(f"  {elem_id}:")
        print(f"    Demand: {elem_results.get('demand', 0):.1f} kips")
        print(f"    Capacity: {elem_results.get('governing_capacity', 0):.1f} kips")
        print(f"    Utilization: {elem_results.get('utilization', 0):.2f}")
        print(f"    Governing: {elem_results.get('governing_limit_state', 'N/A')}")
