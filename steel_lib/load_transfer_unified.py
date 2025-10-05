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

Author: steel_lib integration
Date: October 2025
"""

import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from .load_transfer import (
    generate_connection_combinations,
    chain_connections,
    extract_connection_properties,
    apply_eccentricity_moments
)


def create_connection_interface(
    member_a_data: Dict[str, np.ndarray],
    member_b_data: Dict[str, np.ndarray],
    connector_data: Dict[str, np.ndarray],
    filter_fn: Optional[callable] = None
) -> Dict[str, Any]:
    """
    Create a connection interface that bundles connection matrix with data.
    
    This generates all possible combinations of member_a × member_b × connector
    and stores everything in a dictionary for easy passing to other functions.
    
    Args:
        member_a_data: Dictionary of first member properties (e.g., beams)
        member_b_data: Dictionary of second member properties (e.g., plates)
        connector_data: Dictionary of connector properties (e.g., bolts)
        filter_fn: Optional function to filter invalid combinations
    
    Returns:
        Dictionary containing:
            'connection_matrix': The index mapping
            'member_a_data': First member data
            'member_b_data': Second member data
            'connector_data': Connector data
            'n_connections': Total number of combinations
    
    Example:
        interface = create_connection_interface(
            member_a_data=beams,
            member_b_data=plates,
            connector_data=bolts
        )
        
        # Later use in chaining
        chain_result = build_connection_chain_from_interfaces(interface1, interface2)
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
    
    return {
        'connection_matrix': connection_matrix,
        'member_a_data': member_a_data,
        'member_b_data': member_b_data,
        'connector_data': connector_data,
        'n_connections': connection_matrix['n_connections']
    }


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
    
    # Add first interface fully
    data_order.append(interfaces[0]['member_a_data'])
    data_order.append(interfaces[0]['connector_data'])
    data_order.append(interfaces[0]['member_b_data'])
    
    # Add subsequent interfaces (skip member_a as it matches previous member_b)
    for iface in interfaces[1:]:
        data_order.append(iface['connector_data'])
        data_order.append(iface['member_b_data'])
    
    result = {
        'chain': chained
    }
    
    # Build relationship tracking
    if track_relationships:
        relationships = {}
        
        # Calculate number of members and connectors
        n_members = chained['n_members']
        n_connectors = chained['n_connectors']
        
        # Build adjacency information
        # Structure: member_0 → connector_0 → member_1 → connector_1 → member_2 → ...
        for i in range(n_members):
            member_key = f'm{i}'
            relationships[member_key] = {
                'connected_to': [],        # Connector IDs
                'connected_members': []     # Member IDs
            }
            
            # Check connector before this member (if exists)
            if i > 0:
                prev_connector = f'c{i-1}'
                prev_member = f'm{i-1}'
                relationships[member_key]['connected_to'].append(prev_connector)
                relationships[member_key]['connected_members'].append(prev_member)
            
            # Check connector after this member (if exists)
            if i < n_connectors:
                next_connector = f'c{i}'
                next_member = f'm{i+1}'
                relationships[member_key]['connected_to'].append(next_connector)
                relationships[member_key]['connected_members'].append(next_member)
        
        # Add connector relationships
        for i in range(n_connectors):
            connector_key = f'c{i}'
            relationships[connector_key] = {
                'connects': [f'm{i}', f'm{i+1}'],  # Members this connector joins
                'between': f'{f"m{i}"} and {f"m{i+1}"}'  # Human readable
            }
        
        result['relationships'] = relationships
        
        # Build topology description
        topology_parts = []
        for i in range(n_members):
            topology_parts.append(f'm{i}')
            if i < n_connectors:
                topology_parts.append(f'c{i}')
        result['topology'] = ' → '.join(topology_parts)
    
    # Extract all properties if requested
    if extract_properties:
        # Get flat extracted properties (m0_tw, c0_bolt_size, etc.)
        flat_props = extract_all_properties(chained, *data_order)
        
        # Reorganize into nested structure: {m0: {tw: array, ...}, c0: {bolt_size: array, ...}}
        organized_props = {}
        
        for flat_key, value in flat_props.items():
            # Parse key like "m0_tw" -> prefix="m0", prop_name="tw"
            # Or "c0_bolt_size" -> prefix="c0", prop_name="bolt_size"
            parts = flat_key.split('_', 1)  # Split on first underscore only
            if len(parts) == 2:
                prefix, prop_name = parts
                
                # Create nested dict if doesn't exist
                if prefix not in organized_props:
                    organized_props[prefix] = {}
                
                # Add property to the nested dict
                organized_props[prefix][prop_name] = value
        
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
