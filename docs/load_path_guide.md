# Load Path System Guide

## Overview

The **Load Path System** models how loads transfer through structural connections from one member to another. It tracks forces through each element (bolts, plates, welds, members) and identifies the critical capacity in the load transfer chain.

## Concept

```
LOAD PATH: Beam → Bolts → Plate → Welds → Column
           [50k]  [45k]   [48k]   [42k]   [100k]
                           Critical! ←
```

Each element in the path is evaluated, and the weakest link governs the connection capacity.

## Key Classes

### 1. `LoadVector`
Represents forces and moments at a connection point.

```python
from steel_lib.load_path import LoadVector

load = LoadVector(
    P=10.0,      # Axial force (kips)
    V_x=5.0,     # Shear in x-direction (kips)
    V_y=40.0,    # Shear in y-direction (kips) - primary
    M_y=120.0    # Moment (kip-in)
)

# Utility methods
load.magnitude()         # Total resultant force
load.shear_resultant()   # Combined shear
load.to_dict()          # Convert to dictionary
```

### 2. `ConnectionElement`
Represents a single element in the load path (bolt group, plate, weld, member).

```python
from steel_lib.load_path import ConnectionElement, LoadPathElement, ConnectionType

element = ConnectionElement(
    element_id="PLATE_001",
    element_type=LoadPathElement.PLATE,
    connection_type=ConnectionType.HYBRID,
    geometry={'thickness': 0.375, 'width': 5.5, 'length': 18.0},
    material={'F_y': 50.0, 'F_u': 65.0},
    load=load
)

# After evaluation:
element.capacities           # Dict of all limit state capacities
element.governing_capacity   # Critical capacity
element.utilization         # Demand/Capacity ratio
```

### 3. `LoadPath`
Complete load path from source to target member.

```python
from steel_lib.load_path import LoadPath

path = LoadPath(
    path_id="SC001",
    source_member="W18X35",
    target_member="W14X90",
    applied_load=load,
    eccentricity=3.0  # inches
)

# Add elements
path.add_element(beam_element)
path.add_element(bolt_element)
path.add_element(plate_element)
path.add_element(weld_element)
path.add_element(column_element)

# Evaluate
path.evaluate()
print(f"Is adequate: {path.is_valid}")
print(f"Critical: {path.critical_element}")
print(f"Utilization: {path.max_utilization:.2f}")
```

### 4. `LoadPathGenerator`
Main class for creating and evaluating load paths.

```python
from steel_lib.load_path import LoadPathGenerator, LoadVector

generator = LoadPathGenerator()

# Create a simple shear connection load path
path = generator.create_simple_shear_connection(
    connection_id="SC001",
    beam_section=beam_dict,
    column_section=column_dict,
    plate_config=plate_dict,
    bolt_config=bolt_dict,
    applied_load=LoadVector(V_y=40.0),
    eccentricity=3.0,
    weld_size=0.3125  # 5/16" fillet weld
)

# Evaluate the complete load path
results = generator.evaluate_load_path(path)
```

## Usage Examples

### Example 1: Simple Shear Connection

```python
import numpy as np
from steel_lib.section_properties import create_aisc_section_selector
from steel_lib.plate_generator import generate_shear_plates
from steel_lib.generator_combination import generate_bolt_configurations
from steel_lib.load_path import LoadPathGenerator, LoadVector

# 1. Get beam and column sections
aisc = create_aisc_section_selector('aisc-shapes-database-v16.0.xlsx')

beam = aisc['get_properties']('W18X35')
column = aisc['get_properties']('W14X90')

# 2. Generate connection plate
plates = generate_shear_plates(
    plate_grade_id=[1],              # A572_50
    thickness=[0.375],
    width=[5.5],
    length=[18.0]
)
plate = {key: val[0] for key, val in plates.items()}

# 3. Generate bolt pattern
bolts = generate_bolt_configurations(
    bolt_size=np.array([0.875], dtype=np.float64),
    bolt_grade_id=np.array([0], dtype=np.int64),
    member_a_BHT_id=np.array([0], dtype=np.int64),
    member_b_BHT_id=np.array([0], dtype=np.int64),
    N_r=np.array([4], dtype=np.int64),
    S_r=np.array([3.0], dtype=np.float64),
    N_c=np.array([1], dtype=np.int64),
    S_c=np.array([3.0], dtype=np.float64),
    L_ev=np.array([1.25], dtype=np.float64),
    L_eh=np.array([1.5], dtype=np.float64),
    Ga=np.array([0.0], dtype=np.float64)
)
bolt = {key: val[0] for key, val in bolts.items()}

# 4. Create load path
generator = LoadPathGenerator()

path = generator.create_simple_shear_connection(
    connection_id="SC001",
    beam_section=beam,
    column_section=column,
    plate_config=plate,
    bolt_config=bolt,
    applied_load=LoadVector(V_y=40.0),  # 40 kip shear
    eccentricity=3.0,                    # 3" eccentricity
    weld_size=0.3125                     # 5/16" weld to column
)

# 5. Evaluate load path
results = generator.evaluate_load_path(path)

# 6. Print results
print(f"Connection: {path.source_member} → {path.target_member}")
print(f"Applied Load: {path.applied_load.V_y:.1f} kips")
print(f"\nIs Adequate: {results['is_adequate']}")
print(f"Critical Element: {results['critical_element']}")
print(f"Governing Capacity: {results['governing_capacity']:.1f} kips")
print(f"Max Utilization: {results['max_utilization']:.2f}")

print(f"\nLoad Path Elements:")
for elem_id, elem_results in results['elements'].items():
    print(f"\n{elem_id}:")
    print(f"  Type: {elem_results['element_type']}")
    print(f"  Demand: {elem_results['demand']:.1f} kips")
    print(f"  Capacity: {elem_results.get('governing_capacity', 0):.1f} kips")
    print(f"  Utilization: {elem_results.get('utilization', 0):.2f}")
    print(f"  Governing: {elem_results.get('governing_limit_state', 'N/A')}")
    
    # Show all capacities
    if 'capacities' in elem_results:
        print(f"  All Limit States:")
        for ls_name, capacity in elem_results['capacities'].items():
            print(f"    {ls_name}: {capacity:.1f} kips")
```

### Example 2: Batch Evaluation for Optimization

```python
from steel_lib.load_path import generate_load_paths_batch

# Generate design space
beams = aisc['select_by_properties']({'designation': ['W18X35', 'W21X44']})

plates = generate_shear_plates(
    plate_grade_id=[0, 1],
    thickness=[0.25, 0.375, 0.5],
    width=[5.0, 5.5],
    length=[15.0, 18.0]
)

bolts = generate_bolt_configurations(
    bolt_size=np.array([0.75, 0.875], dtype=np.float64),
    bolt_grade_id=np.array([0], dtype=np.int64),
    member_a_BHT_id=np.array([0], dtype=np.int64),
    member_b_BHT_id=np.array([0], dtype=np.int64),
    N_r=np.array([3, 4], dtype=np.int64),
    S_r=np.array([3.0], dtype=np.float64),
    N_c=np.array([1], dtype=np.int64),
    S_c=np.array([3.0], dtype=np.float64),
    L_ev=np.array([1.25], dtype=np.float64),
    L_eh=np.array([1.5], dtype=np.float64),
    Ga=np.array([0.0], dtype=np.float64)
)

# Generate load paths for all combinations
applied_loads = np.array([30.0, 40.0, 50.0])  # kips
eccentricities = np.array([2.0, 3.0, 4.0])    # inches

load_paths = generate_load_paths_batch(
    beam_sections=beams,
    column_sections=beams,  # Use same sections
    plate_configs=plates,
    bolt_configs=bolts,
    applied_loads=applied_loads,
    eccentricities=eccentricities
)

print(f"Generated {len(load_paths)} load path combinations")

# Evaluate all
generator = LoadPathGenerator()
results_list = []

for path in load_paths[:10]:  # First 10 for example
    result = generator.evaluate_load_path(path)
    results_list.append(result)

# Find optimal (adequate and minimum weight)
adequate_paths = [r for r in results_list if r['is_adequate']]
print(f"\nAdequate connections: {len(adequate_paths)}/{len(results_list)}")

if adequate_paths:
    # Sort by utilization (closer to 1.0 is more efficient)
    optimal = min(adequate_paths, key=lambda r: abs(1.0 - r['max_utilization']))
    print(f"\nMost efficient connection:")
    print(f"  Path ID: {optimal['path_id']}")
    print(f"  Utilization: {optimal['max_utilization']:.2f}")
    print(f"  Critical: {optimal['critical_element']}")
```

### Example 3: Custom Load Path with Multiple Plates

```python
# For more complex connections (e.g., extended end plate)

path = LoadPath(
    path_id="MOMENT_001",
    source_member="W21X44",
    target_member="W14X90",
    applied_load=LoadVector(V_y=20.0, M_y=2400.0),  # Shear + moment
    connection_type=ConnectionType.BOLTED
)

# Add beam
beam_elem = ConnectionElement(
    element_id="BEAM",
    element_type=LoadPathElement.MEMBER_A,
    connection_type=ConnectionType.BOLTED,
    geometry=beam,
    material={'F_y': 50.0, 'F_u': 65.0},
    load=path.applied_load
)
path.add_element(beam_elem)

# Add flange plate (top)
flange_plate_top = ConnectionElement(
    element_id="FLANGE_PLATE_TOP",
    element_type=LoadPathElement.PLATE,
    connection_type=ConnectionType.BOLTED,
    geometry={'thickness': 1.0, 'width': 10.0, 'length': 20.0},
    material={'F_y': 50.0, 'F_u': 65.0},
    load=LoadVector(P=50.0)  # Tension flange
)
path.add_element(flange_plate_top)

# Add flange plate (bottom)
flange_plate_bot = ConnectionElement(
    element_id="FLANGE_PLATE_BOT",
    element_type=LoadPathElement.PLATE,
    connection_type=ConnectionType.BOLTED,
    geometry={'thickness': 1.0, 'width': 10.0, 'length': 20.0},
    material={'F_y': 50.0, 'F_u': 65.0},
    load=LoadVector(P=-50.0)  # Compression flange
)
path.add_element(flange_plate_bot)

# Add shear plate/tab
shear_plate = ConnectionElement(
    element_id="SHEAR_TAB",
    element_type=LoadPathElement.PLATE,
    connection_type=ConnectionType.BOLTED,
    geometry={'thickness': 0.5, 'width': 5.5, 'length': 15.0},
    material={'F_y': 50.0, 'F_u': 65.0},
    load=LoadVector(V_y=20.0)
)
path.add_element(shear_plate)

# Add column
column_elem = ConnectionElement(
    element_id="COLUMN",
    element_type=LoadPathElement.MEMBER_B,
    connection_type=ConnectionType.BOLTED,
    geometry=column,
    material={'F_y': 50.0, 'F_u': 65.0},
    load=path.applied_load
)
path.add_element(column_elem)

# Evaluate
path.evaluate()
```

## Load Path Visualization

```python
def print_load_path_diagram(path: LoadPath):
    """Print ASCII diagram of load path."""
    print(f"\nLoad Path: {path.path_id}")
    print(f"Applied Load: V={path.applied_load.V_y:.1f}k, M={path.applied_load.M_y:.1f}k-in")
    print("=" * 70)
    
    for i, elem in enumerate(path.elements):
        # Element name
        print(f"{elem.element_type.name:15s}", end="")
        
        # Capacity if evaluated
        if elem.governing_capacity:
            cap = elem.governing_capacity
            util = elem.utilization
            status = "✓" if util <= 1.0 else "✗"
            print(f" φR_n={cap:6.1f}k  D/C={util:4.2f}  {status}", end="")
        
        print()
        
        # Arrow to next element
        if i < len(path.elements) - 1:
            print("      ↓")
    
    print("=" * 70)
    if path.critical_element:
        print(f"CRITICAL: {path.critical_element}")
        print(f"CAPACITY: {path.critical_capacity:.1f} kips")
        print(f"UTILIZATION: {path.max_utilization:.2f}")
        print(f"STATUS: {'ADEQUATE' if path.is_valid else 'INADEQUATE'}")

# Usage
print_load_path_diagram(path)
```

## Integration with Existing Limit State Functions

The load path system is designed to work with your existing `aisc_14th.py` functions:

```python
from steel_lib.aisc_14th import (
    bolt_bearing, bolt_shear, block_shear, 
    shear_yielding_rupture, flexural_14th, prying_action
)

# In _evaluate_bolts method, replace placeholders with actual calls:
def _evaluate_bolts_with_actual_functions(element, load_path):
    geom = element.geometry
    # Get plate from load path
    plate_elem = load_path.get_element(LoadPathElement.PLATE)
    
    # Call actual bolt_bearing
    bearing_capacity = bolt_bearing(
        F_u=plate_elem.material['F_u'],
        d_bolt=geom['bolt_size'],
        t=plate_elem.geometry['thickness'],
        P_u=element.load.P,
        V_u=element.load.V_y,
        S_r=geom['S_r'],
        N_r=geom['N_r'],
        # ... other parameters
    )
    
    # Call block_shear
    block_capacity = block_shear(
        # ... parameters from element and plate
    )
    
    return {
        'bearing': bearing_capacity,
        'block_shear': block_capacity,
        # ... other limit states
    }
```

## Benefits

1. **Systematic Evaluation**: Every element in the load transfer is checked
2. **Critical Path Identification**: Automatically finds weakest link
3. **Optimization Ready**: Generate thousands of paths, find optimal
4. **Traceability**: Complete load path documentation
5. **Modular**: Easy to add new element types or limit states

## Next Steps

1. **Implement Actual Limit State Calls**: Replace placeholder capacities with actual function calls
2. **Add More Connection Types**: Moment connections, bracing connections, etc.
3. **Add Visualization**: Generate diagrams showing load flow
4. **Database Integration**: Store and query evaluated load paths
5. **Optimization**: Use with scipy.optimize to find optimal connections

## See Also

- `plate_generator.py` - Generate connection plates
- `generator_combination.py` - Generate bolt patterns
- `section_properties.py` - Select steel sections
- `aisc_14th.py` - Limit state functions
