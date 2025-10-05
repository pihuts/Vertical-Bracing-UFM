"""
Unified Load Transfer Functions
================================

Higher-level convenience functions that combine the core load_transfer operations.
These functions simplify common workflows by bundling operations together using
pure functions (no classes).

Key Features:
- create_connection_interface: Bundle connection matrix with data
- Auto-extraction of all available properties
- Single function to build complete connection chains
- Purely functional API
- AISC member generation with role-based selection

Author: steel_lib integration
Date: October 2025
"""

import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Union
from .load_transfer import (
    generate_connection_combinations,
    chain_connections,
    extract_connection_properties,
    apply_eccentricity_moments
)

# ============================================================================
# GLOBAL NAMING SYSTEM
# ============================================================================
# Type code ranges:
#   001-099: Members (beams, columns, braces, etc.)
#   100-199: Bolts
#   200-299: Welds  
#   300-399: Plates
#   400-499: Other connectors

# Member type codes (001-099)
MEMBER_TYPE_MAP = {
    1: 'beam',
    2: 'column',
    3: 'brace',
    4: 'girder',
    5: 'joist',
    6: 'truss_chord',
    7: 'truss_web',
    8: 'strut',
    9: 'tie',
    10: 'gusset_member'
}

# Bolt type codes (100-199)
BOLT_TYPE_MAP = {
    100: 'bolts',
    101: 'bolts_shear',
    102: 'bolts_tension',
    103: 'bolts_combined',
    104: 'anchor_bolts',
    105: 'hsfg_bolts'  # High strength friction grip
}

# Weld type codes (200-299)
WELD_TYPE_MAP = {
    200: 'weld',
    201: 'weld_fillet',
    202: 'weld_groove',
    203: 'weld_plug',
    204: 'weld_slot',
    205: 'weld_partial_penetration'
}

# Plate type codes (300-399)
PLATE_TYPE_MAP = {
    300: 'plate',
    301: 'plate_shear',
    302: 'plate_flange',
    303: 'plate_stiffener',
    304: 'plate_gusset',
    305: 'plate_base',
    306: 'plate_doubler'
}

# Reverse mappings for lookup
MEMBER_TYPE_TO_INT = {v: k for k, v in MEMBER_TYPE_MAP.items()}
BOLT_TYPE_TO_INT = {v: k for k, v in BOLT_TYPE_MAP.items()}
WELD_TYPE_TO_INT = {v: k for k, v in WELD_TYPE_MAP.items()}
PLATE_TYPE_TO_INT = {v: k for k, v in PLATE_TYPE_MAP.items()}

# Combined mapping for name extraction
GLOBAL_TYPE_MAP = {}
GLOBAL_TYPE_MAP.update(MEMBER_TYPE_MAP)
GLOBAL_TYPE_MAP.update(BOLT_TYPE_MAP)
GLOBAL_TYPE_MAP.update(WELD_TYPE_MAP)
GLOBAL_TYPE_MAP.update(PLATE_TYPE_MAP)

# Legacy support - map old role integers to new system
ROLE_TO_MEMBER_TYPE = {
    0: 1,  # beam
    1: 2,  # column
    2: 3,  # brace
    3: 4,  # girder
    4: 5,  # joist
    5: 6,  # truss_chord
    6: 7,  # truss_web
    7: 8,  # strut
    8: 9   # tie
}

# Global AISC database cache
_AISC_DATABASE = None


def extract_type_name(data: Dict[str, np.ndarray]) -> Optional[str]:
    """
    Extract the type name from a data dictionary using the global naming system.
    
    Checks for 'type_id' key and looks up the corresponding name.
    
    Args:
        data: Dictionary with properties (must contain 'type_id' array)
    
    Returns:
        String name (e.g., 'beam', 'bolts', 'weld_fillet', 'plate_shear') or None
    
    Example:
        beams = generate_aisc_members(designations=['W14X68'], type_id=1)
        name = extract_type_name(beams)  # Returns 'beam'
    """
    if 'type_id' not in data:
        return None
    
    # Get first type_id value (all should be same in a config set)
    type_id = int(data['type_id'][0]) if isinstance(data['type_id'], np.ndarray) else int(data['type_id'])
    
    return GLOBAL_TYPE_MAP.get(type_id, None)


def generate_aisc_members(
    designations: Optional[List[str]] = None,
    filters: Optional[Dict[str, Any]] = None,
    type_id: Union[int, str] = 1,
    material: str = 'A992',
    database_path: str = 'aisc-shapes-database-v16.0.xlsx'
) -> Dict[str, np.ndarray]:
    """
    Generate AISC member configurations with automatic naming.
    
    This function works like generate_bolt_configurations and generate_shear_plates,
    but for AISC steel members (beams, columns, braces, etc.).
    
    **GLOBAL NAMING SYSTEM**: Includes 'type_id' (001-099) for automatic naming in interfaces.
    
    Args:
        designations: List of AISC designations (e.g., ['W14X68', 'W14X53'])
        filters: Dictionary of property filters for selection
        type_id: Member type as integer (001-099) or string:
            1 or 'beam': Beam member
            2 or 'column': Column member
            3 or 'brace': Brace member
            4 or 'girder': Girder member
            5 or 'joist': Joist member
            6 or 'truss_chord': Truss chord member
            7 or 'truss_web': Truss web member
            8 or 'strut': Strut member
            9 or 'tie': Tie member
        material: Material grade (default: 'A992')
        database_path: Path to AISC database Excel file
    
    Returns:
        Dictionary with all AISC properties as arrays, plus:
            'type_id': Type integer ID array (001-099)
            'type_name': Type name string array
    
    Example:
        # Generate beam configurations
        beams = generate_aisc_members(
            designations=['W14X68', 'W14X53'],
            type_id=1  # or type_id='beam'
        )
        
        # Generate column configurations with filters
        columns = generate_aisc_members(
            filters={'W': {'min': 10.0, 'max': 15.0}},
            type_id=2  # or type_id='column'
        )
        
        # Use in interface creation (automatic naming!)
        interface = create_connection_interface(
            member_a_data=beams,     # Auto-extracts 'beam'
            member_b_data=plates,    # Auto-extracts 'plate_shear'
            connector_data=bolts     # Auto-extracts 'bolts'
        )
    """
    global _AISC_DATABASE
    
    # Load AISC database (cached)
    if _AISC_DATABASE is None:
        try:
            from .section_properties import create_aisc_section_selector
            _AISC_DATABASE = create_aisc_section_selector(database_path)
        except Exception as e:
            raise RuntimeError(f"Failed to load AISC database from '{database_path}': {e}")
    
    # Convert type_id string to integer if needed
    if isinstance(type_id, str):
        # String name -> type_id integer
        type_id = MEMBER_TYPE_TO_INT.get(type_id.lower(), 1)
    
    # Get type name from mapping
    type_name = MEMBER_TYPE_MAP.get(type_id, 'beam')
    
    # Build selection criteria
    selection_dict = {}
    
    if designations is not None:
        selection_dict['designation'] = designations
    
    if filters is not None:
        selection_dict.update(filters)
    
    # Add material filter
    selection_dict['Type'] = [material]
    
    # Select from database
    result = _AISC_DATABASE['select_by_properties'](selection_dict, material=material)
    
    if result['count'] == 0:
        raise ValueError(f"No AISC members found matching criteria: {selection_dict}")
    
    # Add type information (global naming system)
    result['type_id'] = np.full(result['count'], type_id, dtype=np.int32)
    result['type_name'] = np.full(result['count'], type_name, dtype='<U20')
    
    # Legacy support: also include role/role_name
    result['role'] = np.full(result['count'], type_id, dtype=np.int32)
    result['role_name'] = np.full(result['count'], type_name, dtype='<U20')
    
    return result


def create_connection_interface(
    member_a_data: Dict[str, np.ndarray],
    member_b_data: Dict[str, np.ndarray],
    connector_data: Dict[str, np.ndarray],
    filter_fn: Optional[callable] = None,
    member_a_name: Optional[str] = None,
    member_b_name: Optional[str] = None,
    connector_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a connection interface that bundles connection matrix with data.
    
    This generates all possible combinations of member_a × member_b × connector
    and stores everything in a dictionary for easy passing to other functions.
    
    **AUTOMATIC NAMING**: If name parameters are None, automatically extracts
    names from 'type_id' field using the global naming system (001-099 members,
    100-199 bolts, 200-299 welds, 300-399 plates).
    
    Args:
        member_a_data: Dictionary of first member properties (e.g., beams)
        member_b_data: Dictionary of second member properties (e.g., plates)
        connector_data: Dictionary of connector properties (e.g., bolts)
        filter_fn: Optional function to filter invalid combinations
        member_a_name: Optional override name (auto-extracted if None)
        member_b_name: Optional override name (auto-extracted if None)
        connector_name: Optional override name (auto-extracted if None)
    
    Returns:
        Dictionary containing:
            'connection_matrix': The index mapping
            'member_a_data': First member data
            'member_b_data': Second member data
            'connector_data': Connector data
            'n_connections': Total number of combinations
            'member_a_name': Name for member_a (auto or manual)
            'member_b_name': Name for member_b (auto or manual)
            'connector_name': Name for connector (auto or manual)
    
    Example:
        # Automatic naming from type_id
        beams = generate_aisc_members(designations=['W14X68'], type_id=1)  # 'beam'
        plates = generate_shear_plates(..., type_id=301)  # 'plate_shear'
        bolts = generate_bolt_configurations(..., type_id=100)  # 'bolts'
        
        interface = create_connection_interface(
            member_a_data=beams,
            member_b_data=plates,
            connector_data=bolts
            # Names auto-extracted! No manual naming needed!
        )
        
        # Properties automatically use names: 'm0_beam', 'm1_plate_shear', 'c0_bolts'
    """
    # Determine counts from first array in each dict
    member_a_count = len(next(iter(member_a_data.values())))
    member_b_count = len(next(iter(member_b_data.values())))
    connector_count = len(next(iter(connector_data.values())))
    
    # Generate all combinations
    connection_matrix = generate_connection_combinations(
        member_a_count=member_a_count,
        member_b_count=member_b_count,
        connector_count=connector_count,
        filter_fn=filter_fn
    )
    
    interface = {
        'connection_matrix': connection_matrix,
        'member_a_data': member_a_data,
        'member_b_data': member_b_data,
        'connector_data': connector_data,
        'n_connections': connection_matrix['n_connections']
    }
    
    # Auto-extract names if not provided (uses global naming system)
    if member_a_name is None:
        member_a_name = extract_type_name(member_a_data)
    if member_b_name is None:
        member_b_name = extract_type_name(member_b_data)
    if connector_name is None:
        connector_name = extract_type_name(connector_data)
    
    # Add names to interface (may be None if type_id not present)
    if member_a_name is not None:
        interface['member_a_name'] = member_a_name
    if member_b_name is not None:
        interface['member_b_name'] = member_b_name
    if connector_name is not None:
        interface['connector_name'] = connector_name
    
    return interface


def extract_all_properties(
    connection_matrix: Dict[str, np.ndarray],
    *member_connector_data: Dict[str, np.ndarray]
) -> Dict[str, np.ndarray]:
    """
    Extract ALL available properties from members and connectors.
    
    This is a convenience wrapper that automatically extracts every property
    from the data dictionaries without needing to specify them.
    
    Args:
        connection_matrix: The connection chain or matrix with index mappings
        *member_connector_data: Data dictionaries in order (member0, connector0, member1, ...)
    
    Returns:
        Dictionary with all extracted properties using prefixes:
        - m0_*, m1_*, m2_* for members
        - c0_*, c1_* for connectors
    
    Example:
        # Extract everything
        props = extract_all_properties(
            full_chain,
            beams, bolts, plates, welds, columns
        )
        
        # Access any property
        beam_tw = props['m0_tw']
        bolt_size = props['c0_bolt_size']
    """
    # Determine number of members and connectors
    n_members = connection_matrix.get('n_members')
    n_connectors = connection_matrix.get('n_connectors')
    
    if n_members is None:
        # Legacy 2-member connection
        n_members = 2
        n_connectors = 1
    
    # Verify we have the right amount of data
    expected_count = n_members + n_connectors
    if len(member_connector_data) != expected_count:
        raise ValueError(
            f"Expected {expected_count} data dicts "
            f"({n_members} members + {n_connectors} connectors), "
            f"got {len(member_connector_data)}"
        )
    
    # Build properties_to_extract dict by scanning all keys
    # Data order is: member_0, connector_0, member_1, connector_1, member_2, ...
    # Filter out scalar values - only extract array properties
    properties_to_extract = {}
    
    # Extract from members (at positions 0, 2, 4, 6...)
    for i in range(n_members):
        data_idx = i * 2  # member_0 at 0, member_1 at 2, member_2 at 4...
        if data_idx < len(member_connector_data):
            member_data = member_connector_data[data_idx]
            member_key = f'member_{i}'
            # Only include array properties (skip scalars like 'count')
            properties_to_extract[member_key] = [
                key for key, val in member_data.items()
                if isinstance(val, np.ndarray)
            ]
    
    # Extract from connectors (at positions 1, 3, 5...)
    for i in range(n_connectors):
        data_idx = i * 2 + 1  # connector_0 at 1, connector_1 at 3, connector_2 at 5...
        if data_idx < len(member_connector_data):
            connector_data = member_connector_data[data_idx]
            connector_key = f'connector_{i}'
            # Only include array properties
            properties_to_extract[connector_key] = [
                key for key, val in connector_data.items()
                if isinstance(val, np.ndarray)
            ]
    
    # Call the standard extract function
    return extract_connection_properties(
        connection_matrix,
        *member_connector_data,
        properties_to_extract=properties_to_extract
    )


def build_connection_chain_from_interfaces(
    *interfaces: Dict[str, Any],
    extract_properties: bool = True,
    track_relationships: bool = True
) -> Dict[str, Any]:
    """
    Build a complete connection chain from multiple interfaces and extract properties.
    
    This function supports:
    1. Linear chains: m0 → c0 → m1 → c1 → m2
    2. Branching connections: Multiple interfaces connecting to the same member
    3. Relationship tracking: Know what members/connectors are connected to each member
    
    Args:
        *interfaces: Connection interface dicts (from create_connection_interface)
        extract_properties: If True, automatically extract all properties (default: True)
        track_relationships: If True, build relationship map (default: True)
    
    Returns:
        Dictionary containing:
            'chain': The chained connection matrix
            'properties': Dict organized by member/connector (if extract_properties=True)
            'relationships': Dict mapping each member to its connections (if track_relationships=True):
                {
                    'm0': {
                        'connected_to': ['c0'],           # Connectors attached to this member
                        'connected_members': ['m1']        # Members connected via those connectors
                    },
                    'm1': {
                        'connected_to': ['c0', 'c1'],      # Connected to both c0 and c1
                        'connected_members': ['m0', 'm2']  # Connected to m0 and m2
                    },
                    ...
                }
            'topology': Human-readable connection description
    
    Example - Linear Chain:
        beam_plate = create_connection_interface(beams, plates, bolts)
        plate_column = create_connection_interface(plates, columns, welds)
        
        result = build_connection_chain_from_interfaces(beam_plate, plate_column)
        
        # Check what's connected to the plate (m1)
        plate_connections = result['relationships']['m1']
        # {'connected_to': ['c0', 'c1'], 'connected_members': ['m0', 'm2']}
        # Plate is connected to beam via c0 and to column via c1
    
    Example - Branching:
        # plate_1 connects to multiple members
        interface_a = create_connection_interface(beam, plate_1, bolts_a)    # beam → plate_1
        interface_b = create_connection_interface(plate_1, column_b, welds_b) # plate_1 → column_b
        interface_c = create_connection_interface(plate_1, column_c, welds_c) # plate_1 → column_c
        
        result = build_connection_chain_from_interfaces(interface_a, interface_b, interface_c)
        
        # Check plate_1 connections (m1)
        plate_connections = result['relationships']['m1']
        # {'connected_to': ['c0', 'c1', 'c2'], 'connected_members': ['m0', 'm2', 'm3']}
        # Plate connects to beam + 2 columns
    """
    if len(interfaces) == 0:
        raise ValueError("Must provide at least one connection interface")
    
    # Extract connection matrices for chaining
    connection_matrices = [iface['connection_matrix'] for iface in interfaces]
    
    # Chain them together
    chained = chain_connections(*connection_matrices)
    
    # Build ordered list of data dictionaries
    # For chaining: member_0, connector_0, member_1, connector_1, member_2, ...
    data_order = []
    
    # Collect custom names for members and connectors
    member_names = []
    connector_names = []
    
    # Add first interface fully
    data_order.append(interfaces[0]['member_a_data'])
    member_names.append(interfaces[0].get('member_a_name'))
    
    data_order.append(interfaces[0]['connector_data'])
    connector_names.append(interfaces[0].get('connector_name'))
    
    data_order.append(interfaces[0]['member_b_data'])
    member_names.append(interfaces[0].get('member_b_name'))
    
    # Add subsequent interfaces (skip member_a as it matches previous member_b)
    for iface in interfaces[1:]:
        data_order.append(iface['connector_data'])
        connector_names.append(iface.get('connector_name'))
        
        data_order.append(iface['member_b_data'])
        member_names.append(iface.get('member_b_name'))
    
    result = {
        'chain': chained,
        'member_names': member_names,      # Store for later use
        'connector_names': connector_names  # Store for later use
    }
    
    # Build relationship tracking
    if track_relationships:
        relationships = {}
        
        # Calculate number of members and connectors
        n_members = chained['n_members']
        n_connectors = chained['n_connectors']
        
        # Helper to create key with optional name
        def make_member_key(idx, name=None):
            if name:
                return f'm{idx}_{name}'
            return f'm{idx}'
        
        def make_connector_key(idx, name=None):
            if name:
                return f'c{idx}_{name}'
            return f'c{idx}'
        
        # Build adjacency information
        # Structure: member_0 → connector_0 → member_1 → connector_1 → member_2 → ...
        for i in range(n_members):
            member_key = make_member_key(i, member_names[i])
            relationships[member_key] = {
                'connected_to': [],        # Connector IDs
                'connected_members': [],    # Member IDs
                'index': i,                 # Numeric index
                'name': member_names[i]     # Custom name (if any)
            }
            
            # Check connector before this member (if exists)
            if i > 0:
                prev_connector = make_connector_key(i-1, connector_names[i-1])
                prev_member = make_member_key(i-1, member_names[i-1])
                relationships[member_key]['connected_to'].append(prev_connector)
                relationships[member_key]['connected_members'].append(prev_member)
            
            # Check connector after this member (if exists)
            if i < n_connectors:
                next_connector = make_connector_key(i, connector_names[i])
                next_member = make_member_key(i+1, member_names[i+1])
                relationships[member_key]['connected_to'].append(next_connector)
                relationships[member_key]['connected_members'].append(next_member)
        
        # Add connector relationships
        for i in range(n_connectors):
            connector_key = make_connector_key(i, connector_names[i])
            m_before = make_member_key(i, member_names[i])
            m_after = make_member_key(i+1, member_names[i+1])
            
            relationships[connector_key] = {
                'connects': [m_before, m_after],  # Members this connector joins
                'between': f'{m_before} and {m_after}',  # Human readable
                'index': i,                 # Numeric index
                'name': connector_names[i]  # Custom name (if any)
            }
        
        result['relationships'] = relationships
        
        # Build topology description
        topology_parts = []
        for i in range(n_members):
            topology_parts.append(make_member_key(i, member_names[i]))
            if i < n_connectors:
                topology_parts.append(make_connector_key(i, connector_names[i]))
        result['topology'] = ' → '.join(topology_parts)
    
    # Extract all properties if requested
    if extract_properties:
        # Get flat extracted properties (m0_tw, c0_bolt_size, etc.)
        flat_props = extract_all_properties(chained, *data_order)
        
        # Reorganize into nested structure using custom names if available
        organized_props = {}
        n_members = chained['n_members']
        n_connectors = chained['n_connectors']
        
        for flat_key, value in flat_props.items():
            # Parse key like "m0_tw" -> prefix="m0", prop_name="tw"
            # Or "c0_bolt_size" -> prefix="c0", prop_name="bolt_size"
            parts = flat_key.split('_', 1)  # Split on first underscore only
            if len(parts) == 2:
                prefix, prop_name = parts
                
                # Determine if it's a member or connector and build custom key
                if prefix.startswith('m'):
                    idx = int(prefix[1:])
                    if idx < len(member_names) and member_names[idx]:
                        custom_key = f'm{idx}_{member_names[idx]}'
                    else:
                        custom_key = prefix
                elif prefix.startswith('c'):
                    idx = int(prefix[1:])
                    if idx < len(connector_names) and connector_names[idx]:
                        custom_key = f'c{idx}_{connector_names[idx]}'
                    else:
                        custom_key = prefix
                else:
                    custom_key = prefix
                
                # Create nested dict if doesn't exist
                if custom_key not in organized_props:
                    organized_props[custom_key] = {}
                
                # Add property to the nested dict
                organized_props[custom_key][prop_name] = value
        
        result['properties'] = organized_props
    
    return result


def get_member_connections(result: Dict[str, Any], member_id: str) -> Dict[str, Any]:
    """
    Get all connections for a specific member.
    
    Args:
        result: Result from build_connection_chain_from_interfaces
        member_id: Member ID to query (e.g., 'm0', 'm1', 'm2')
    
    Returns:
        Dictionary with connection information for the member:
            {
                'member_id': 'm1',
                'connected_to': ['c0', 'c1'],           # Connector IDs
                'connected_members': ['m0', 'm2'],       # Connected member IDs
                'properties': {...}                      # All properties for this member
            }
    
    Example:
        result = build_connection_chain_from_interfaces(iface1, iface2)
        
        # Get what's connected to the plate (m1)
        plate_info = get_member_connections(result, 'm1')
        print(f"Plate connected via: {plate_info['connected_to']}")
        print(f"Plate connected to: {plate_info['connected_members']}")
    """
    if 'relationships' not in result:
        raise ValueError("Result does not contain relationship information. "
                        "Use track_relationships=True when calling build_connection_chain_from_interfaces")
    
    if member_id not in result['relationships']:
        available = [k for k in result['relationships'].keys() if k.startswith('m')]
        raise ValueError(f"Member '{member_id}' not found. Available members: {available}")
    
    info = {
        'member_id': member_id,
        **result['relationships'][member_id]
    }
    
    # Add properties if available
    if 'properties' in result and member_id in result['properties']:
        info['properties'] = result['properties'][member_id]
    
    return info


def get_connector_info(result: Dict[str, Any], connector_id: str) -> Dict[str, Any]:
    """
    Get information about a specific connector.
    
    Args:
        result: Result from build_connection_chain_from_interfaces
        connector_id: Connector ID to query (e.g., 'c0', 'c1')
    
    Returns:
        Dictionary with connector information:
            {
                'connector_id': 'c0',
                'connects': ['m0', 'm1'],      # Members it connects
                'between': 'm0 and m1',        # Human readable
                'properties': {...}             # All properties for this connector
            }
    
    Example:
        result = build_connection_chain_from_interfaces(iface1, iface2)
        
        bolt_info = get_connector_info(result, 'c0')
        print(f"Bolts connect: {bolt_info['connects']}")
    """
    if 'relationships' not in result:
        raise ValueError("Result does not contain relationship information. "
                        "Use track_relationships=True when calling build_connection_chain_from_interfaces")
    
    if connector_id not in result['relationships']:
        available = [k for k in result['relationships'].keys() if k.startswith('c')]
        raise ValueError(f"Connector '{connector_id}' not found. Available connectors: {available}")
    
    info = {
        'connector_id': connector_id,
        **result['relationships'][connector_id]
    }
    
    # Add properties if available
    if 'properties' in result and connector_id in result['properties']:
        info['properties'] = result['properties'][connector_id]
    
    return info


def print_connection_topology(result: Dict[str, Any], show_details: bool = False):
    """
    Print a human-readable description of the connection topology.
    
    Args:
        result: Result from build_connection_chain_from_interfaces
        show_details: If True, show detailed connection information
    
    Example:
        result = build_connection_chain_from_interfaces(iface1, iface2)
        print_connection_topology(result, show_details=True)
    """
    if 'topology' not in result:
        print("No topology information available.")
        return
    
    print("=" * 70)
    print("CONNECTION TOPOLOGY")
    print("=" * 70)
    print(f"Structure: {result['topology']}")
    print(f"Total chains: {result['chain']['n_chains']}")
    
    if show_details and 'relationships' in result:
        print("\n" + "-" * 70)
        print("MEMBER CONNECTIONS:")
        print("-" * 70)
        
        members = [k for k in result['relationships'].keys() if k.startswith('m')]
        for member_id in members:
            rel = result['relationships'][member_id]
            print(f"\n{member_id}:")
            print(f"  Connected via: {', '.join(rel['connected_to']) if rel['connected_to'] else 'None'}")
            print(f"  Connected to: {', '.join(rel['connected_members']) if rel['connected_members'] else 'None'}")
        
        print("\n" + "-" * 70)
        print("CONNECTOR DETAILS:")
        print("-" * 70)
        
        connectors = [k for k in result['relationships'].keys() if k.startswith('c')]
        for connector_id in connectors:
            rel = result['relationships'][connector_id]
            print(f"\n{connector_id}:")
            print(f"  Connects: {rel['between']}")
    
    print("=" * 70)


# Convenience function for quick workflow
def quick_chain(
    *interfaces: Dict[str, Any],
    loads: Optional[Dict[str, float]] = None,
    eccentricity: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Quick workflow: chain + extract + optionally apply loads.
    
    This is the fastest way to go from interfaces to ready-to-analyze data.
    
    Args:
        *interfaces: Connection interface dicts (from create_connection_interface)
        loads: Optional load dictionary to apply to all chains (scalars or arrays)
        eccentricity: Optional eccentricity for load transformation (scalars or arrays)
    
    Returns:
        Dictionary with:
            'chain': Connection chain
            'properties': All extracted properties
            'loads': Applied loads (if provided)
            'n_chains': Total number of configurations
    
    Example:
        # One-liner to get everything
        result = quick_chain(
            beam_plate_interface,
            plate_column_interface,
            loads={'P': 10.0, 'V_y': 40.0},
            eccentricity={'e_x': 3.0}
        )
        
        # Ready to analyze
        props = result['properties']
        loads = result['loads']
    """
    # Build chain and extract properties
    result = build_connection_chain_from_interfaces(*interfaces, extract_properties=True)
    
    n_chains = result['chain']['n_chains']
    result['n_chains'] = n_chains
    
    # Apply loads if provided
    if loads is not None:
        # Convert scalar loads to arrays
        load_arrays = {}
        for key, value in loads.items():
            if np.isscalar(value):
                load_arrays[key] = np.full(n_chains, value)
            else:
                load_arrays[key] = value
        
        # Ensure all load components exist
        for component in ['P', 'V_y', 'V_z', 'M_x', 'M_y', 'M_z']:
            if component not in load_arrays:
                load_arrays[component] = np.zeros(n_chains)
        
        # Apply eccentricity if provided
        if eccentricity is not None:
            # Convert scalar eccentricity to arrays
            ecc_arrays = {}
            for key, value in eccentricity.items():
                if np.isscalar(value):
                    ecc_arrays[key] = np.full(n_chains, value)
                else:
                    ecc_arrays[key] = value
            load_arrays = apply_eccentricity_moments(load_arrays, ecc_arrays)
        
        result['loads'] = load_arrays
    
    return result
