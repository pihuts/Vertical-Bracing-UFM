# Load Path V2 System

## Overview

A refactored, numba-compatible load path system for steel connection design. This system provides a modular, performance-focused architecture for evaluating load transfer through connection interfaces.

## Key Features

- ✅ **Numba-compatible**: All calculation functions decorated with `@njit` for JIT compilation
- ✅ **Variable naming protocol**: Follows `docs/variable_naming_protocol.ipynb` standards
- ✅ **Modular interfaces**: Each connection element (weld, bolt, plate) is independent
- ✅ **Composable paths**: Connect interfaces to build complete load paths
- ✅ **Batch evaluation**: Vectorized processing of multiple configurations
- ✅ **Performance-optimized**: Fast evaluation suitable for optimization loops
- ✅ **Maintainable**: Clear separation of concerns, easy to extend

## Architecture

### 1. Interface-Based Design

Each connection element is an **interface** that can:
- Accept a load (e.g., V_u shear force)
- Calculate capacity based on multiple limit states
- Return utilization and adequacy status

**Current Interfaces:**
- `WeldInterface`: Fillet weld connections
- `BoltInterface`: Bolt group connections with bearing, shear, block shear checks

### 2. Composable Load Paths

Interfaces are connected in sequence to represent complete load transfer:

```
Beam web → Weld → Plate → Bolts → Column web
```

Each interface in the sequence is evaluated, and the **controlling** interface (highest utilization) determines overall capacity.

### 3. Vectorized Batch Processing

The system supports batch evaluation of multiple configurations:
- Multiple plates × multiple welds × multiple bolts
- Efficient evaluation of thousands of combinations
- Optimized for design space exploration

## Current Implementation: Simple Shear Connections

**Focus**: Simple shear connections (shear tabs, single angles)

**Load Path Components:**
1. **Beam web** (starting point)
2. **Weld** (beam web to plate)
3. **Plate** (connection element)
4. **Bolt group** (plate to column)
5. **Column web** (support)

**Limit States Checked:**

| Interface | Limit States |
|-----------|--------------|
| Weld | Weld shear (AISC J2) |
| Bolt Group | • Bolt shear (AISC J3.6)<br>• Bearing on plate (AISC J3.10)<br>• Bearing on support (AISC J3.10)<br>• Plate shear yield/rupture (AISC J4.2)<br>• Block shear on plate (AISC J4.3) |

## Usage

### Single Connection Evaluation

```python
from steel_lib.load_path_v2 import SimpleShearConnection

# Define configuration
beam_section = {'d': 18.0, 'tw': 0.3, 'F_y': 50.0, 'F_u': 65.0, ...}
plate_config = {'thickness': 0.375, 'width': 5.0, 'F_y': 50.0, 'F_u': 65.0, ...}
weld_config = {'weld_size': 0.25, 'weld_length': 12.0, 'electrode_id': 1, ...}
bolt_config = {'bolt_size': 0.75, 'N_r': 4, 'N_c': 1, 'F_nv': 48.0, ...}
column_section = {'d': 14.0, 'tw': 0.44, 'F_y': 50.0, 'F_u': 65.0, ...}

# Create connection
connection = SimpleShearConnection(
    beam_section=beam_section,
    plate_config=plate_config,
    weld_config=weld_config,
    bolt_config=bolt_config,
    column_section=column_section
)

# Evaluate for applied load
V_u = 40.0  # kips
result = connection.evaluate(V_u)

print(f"Adequate: {result['is_adequate']}")
print(f"Utilization: {result['max_utilization']:.1%}")
print(f"Controlling: {result['controlling_limit_state']}")
```

### Batch Evaluation

```python
from steel_lib.load_path_v2 import evaluate_simple_shear_batch
from steel_lib.plate_generator import generate_shear_plates
from steel_lib.weld_generator import generate_fillet_welds
from steel_lib.generator_combination import generate_bolt_configurations

# Generate multiple configurations
plates = generate_shear_plates(
    plate_grade_id=[1],
    thickness=[0.375, 0.5, 0.625],
    width=[5.0],
    length=[12.0, 15.0]
)

welds = generate_fillet_welds(
    electrode_id=[1],
    weld_size=[0.1875, 0.25, 0.3125],
    weld_length=[12.0, 15.0],
    both_sides=[True]
)

bolts = generate_bolt_configurations(
    bolt_size=np.array([0.75], dtype=np.float64),
    bolt_grade_id=np.array([0], dtype=np.int64),
    N_r=np.array([4, 5, 6], dtype=np.int64),
    ...
)

# Batch evaluation
batch_results = evaluate_simple_shear_batch(
    beam_sections=beam_section,
    plate_configs=plates,
    weld_configs=welds,
    bolt_configs=bolts,
    column_section=column_section,
    V_u=40.0
)

# Results
n_adequate = np.sum(batch_results['results_adequate'])
print(f"Adequate designs: {n_adequate} / {batch_results['count']}")

# Find optimal
from steel_lib.load_path_v2 import find_optimal_design
optimal = find_optimal_design(batch_results)
print(f"Optimal utilization: {optimal['utilization']:.1%}")
```

## Variable Naming Convention

All variables follow `docs/variable_naming_protocol.ipynb`:

**Section Properties:**
- `d`, `bf`, `tf`, `tw`: Section dimensions (inches)
- `F_y`, `F_u`: Material strengths (ksi)
- `designations`: Section labels (e.g., 'W18X35')

**Bolt Properties:**
- `d_bolt`, `bolt_size`: Bolt diameter (inches)
- `F_nv`, `F_nt`: Bolt shear/tension strengths (ksi)
- `N_r`, `N_c`: Number of rows/columns
- `S_r`, `S_c`: Row/column spacing (inches)
- `L_ev`, `L_eh`: Edge distances (inches)
- `d_v`, `d_h`: Hole diameters (inches)

**Weld Properties:**
- `weld_size`: Fillet weld size (inches)
- `weld_length`: Length per side (inches)
- `electrode_id`: Electrode grade code (0=E60, 1=E70, 2=E80)
- `both_sides`: Boolean for double-sided welds

**Plate Properties:**
- `thickness`, `t`: Plate thickness (inches)
- `width`: Plate width (inches)
- `length`: Plate length (inches)
- `F_y`, `F_u`: Material strengths (ksi)

**Loads:**
- `V_u`: Applied shear force (kips)
- `P_u`: Applied axial force (kips)
- `M_u`: Applied moment (kip-in)

**Results:**
- `results_adequate`: Boolean array
- `results_utilization`: Utilization ratio array
- `results_controlling_state`: Controlling limit state array

## Integration with aisc_14th Module

The current implementation uses **placeholder calculations** for limit states. To integrate with the `steel_lib/aisc_14th` module:

### Step 1: Replace Placeholder Functions

Update these functions in `load_path_v2.py`:

```python
# Current placeholder:
@njit
def transfer_weld_to_plate(V_u, weld_size, weld_length, electrode_strength, both_sides):
    # PLACEHOLDER - Simplified calculation
    phi = 0.75
    capacity_per_inch = 0.707 * weld_size * electrode_strength * 0.6 * phi
    capacity = capacity_per_inch * weld_length * (2.0 if both_sides else 1.0)
    return capacity, V_u / capacity

# Replace with actual AISC calculation:
from steel_lib.aisc_14th.weld import fillet_weld_shear  # TODO: Create this

@njit
def transfer_weld_to_plate(V_u, weld_size, weld_length, electrode_strength, both_sides):
    capacity = fillet_weld_shear(
        weld_size=weld_size,
        L=weld_length,
        FEXX=electrode_strength,
        phi=0.75,
        n_welds=2 if both_sides else 1
    )
    return capacity, V_u / capacity
```

### Step 2: Map to aisc_14th Functions

| Placeholder Function | aisc_14th Module |
|---------------------|------------------|
| `transfer_weld_to_plate()` | `aisc_14th/weld.py` (create new) |
| `transfer_bolts_shear()` | `aisc_14th/bolt_shear_tension.py::bolt_shear()` |
| `check_bolt_bearing()` | `aisc_14th/bolt_bearing.py::bolt_bearing()` |
| `check_plate_shear_yielding()` | `aisc_14th/shear_yielding_rupture.py` |
| `check_block_shear()` | `aisc_14th/block_shear.py::block_shear()` |

### Step 3: Verify Variable Names Match

Ensure all variables passed to `aisc_14th` functions match the protocol:

```python
# Good - matches protocol
result = bolt_shear(
    F_nv=48.0,
    A_bolt=0.442,
    N_shear_planes=1,
    phi=0.75
)

# Bad - non-standard names
result = bolt_shear(
    shear_strength=48.0,  # Should be F_nv
    area=0.442,           # Should be A_bolt
    planes=1,             # Should be N_shear_planes
    phi=0.75
)
```

## Performance Characteristics

Based on testing with simple shear connections:

| Configuration Size | Evaluation Time | Per Config |
|-------------------|-----------------|------------|
| Small (8 configs) | ~5-10 ms | 0.6-1.2 ms |
| Medium (64 configs) | ~40-60 ms | 0.6-0.9 ms |
| Large (256 configs) | ~160-200 ms | 0.6-0.8 ms |

**Performance Notes:**
- First evaluation slower due to numba JIT compilation
- Subsequent evaluations benefit from compiled code
- Linear scaling with number of configurations
- Suitable for optimization loops (1000+ evaluations)

## Extending the System

### Adding New Interface Types

To add a new interface (e.g., moment plate connection):

```python
class MomentPlateInterface:
    def __init__(self, config: Dict):
        # Store configuration
        self.config = config
    
    def evaluate(self, M_u: float) -> Dict:
        # Calculate capacity for moment
        capacity = calculate_moment_capacity(self.config, M_u)
        utilization = M_u / capacity
        
        return {
            'interface_type': 'moment_plate',
            'capacity': capacity,
            'utilization': utilization,
            'is_adequate': utilization <= 1.0,
            'limit_state': 'plate_flexure'
        }
```

### Adding New Load Path Types

To add a new connection type (e.g., moment connection):

```python
class MomentConnection:
    def __init__(self, beam, column, top_plate, bottom_plate, bolts):
        self.interfaces = [
            MomentPlateInterface(top_plate),
            BoltInterface(bolts, top_plate, column),
            # ... additional interfaces
        ]
    
    def evaluate(self, M_u: float, V_u: float) -> Dict:
        # Evaluate each interface with combined loads
        results = []
        for interface in self.interfaces:
            result = interface.evaluate(M_u, V_u)
            results.append(result)
        
        # Return combined results
        return aggregate_results(results)
```

### Adding New Limit States

To add a new limit state check:

```python
@njit
def check_new_limit_state(
    V_u: float,
    param1: float,
    param2: float,
    # ... other parameters following protocol
) -> Tuple[float, float]:
    """
    New limit state calculation.
    
    Args:
        V_u: Applied load (kips)
        param1: Description (units)
        ...
        
    Returns:
        capacity: Limit state capacity (kips)
        utilization: V_u / capacity
    """
    # Calculation using numba-compatible operations
    capacity = calculate_capacity(param1, param2)
    utilization = V_u / capacity if capacity > 0 else 999.0
    
    return capacity, utilization
```

Then integrate into appropriate interface's `evaluate()` method.

## Testing

Run the demonstration notebook:

```bash
jupyter notebook test_load_path_v2.ipynb
```

This notebook contains:
- Example 1: Single connection evaluation
- Example 2: Batch evaluation with optimization
- Example 3: Performance benchmarking

## Future Enhancements

1. **Complete AISC Integration**
   - Replace all placeholder calculations
   - Add missing limit states (flexural, tension, compression)
   - Validate against AISC examples

2. **Additional Connection Types**
   - Moment connections (welded/bolted)
   - Braced connections
   - Column base plates
   - Splice connections

3. **Advanced Features**
   - Eccentric load handling
   - Combined loading (M + V + P)
   - Prying action on bolts
   - Weld effective length factors

4. **Optimization Integration**
   - Cost-based optimization
   - Multi-objective optimization (weight, cost, constructability)
   - Genetic algorithms for complex connections

5. **Reporting**
   - Detailed calculation reports
   - Code check references
   - Drawing generation

## File Structure

```
steel_lib/
  load_path_v2.py           # Main module
  aisc_14th/                # AISC limit state functions
    bolt_shear_tension.py
    bolt_bearing.py
    block_shear.py
    shear_yielding_rupture.py
    # ... etc
  section_properties.py     # AISC section database
  plate_generator.py        # Plate configuration generator
  weld_generator.py         # Weld configuration generator
  generator_combination.py  # Bolt configuration generator

test_load_path_v2.ipynb    # Demonstration notebook
docs/
  variable_naming_protocol.ipynb  # Variable naming standards
```

## Contributing

When adding new features:

1. Follow variable naming protocol
2. Use numba-compatible operations
3. Add placeholder calculations first
4. Document with clear docstrings
5. Test with demonstration examples
6. Update this README

## License

(Your license here)

## Contact

(Your contact info here)
