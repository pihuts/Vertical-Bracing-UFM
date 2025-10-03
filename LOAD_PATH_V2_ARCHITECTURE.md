# Load Path V2 - System Architecture

## Design Philosophy

**Core Principles:**
1. **Modularity**: Each component is independent and testable
2. **Composability**: Components combine to form complete load paths
3. **Performance**: Numba JIT compilation for speed
4. **Standards**: Follow AISC variable naming protocol
5. **Maintainability**: Clear separation of concerns

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    USER INTERFACE LAYER                      │
│  (SimpleShearConnection, evaluate_simple_shear_batch)        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   INTERFACE LAYER                            │
│  (WeldInterface, BoltInterface, PlateInterface, etc.)        │
│                                                               │
│  Each interface:                                             │
│  • Accepts load (V_u, M_u, P_u)                             │
│  • Calculates capacity                                       │
│  • Returns utilization + adequacy                            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│               CALCULATION LAYER (Numba JIT)                  │
│  (transfer_weld_to_plate, transfer_bolts_shear, etc.)       │
│                                                               │
│  Pure functions:                                             │
│  • @njit decorated                                           │
│  • Numpy operations only                                     │
│  • Return (capacity, utilization)                            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  AISC 14th MODULE                            │
│  (bolt_shear, bolt_bearing, block_shear, etc.)              │
│                                                               │
│  AISC code calculations:                                     │
│  • Follows variable_naming_protocol.ipynb                    │
│  • Numba-compatible                                          │
│  • Code reference comments                                   │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Configuration Input

```python
# User provides configuration dictionaries
beam_section = {
    'd': 18.0,      # AISC variable names
    'tw': 0.3,
    'F_y': 50.0,
    'F_u': 65.0,
    ...
}

plate_config = {
    'thickness': 0.375,
    'width': 5.0,
    'length': 12.0,
    'F_y': 50.0,
    'F_u': 65.0,
}

weld_config = {
    'weld_size': 0.25,
    'weld_length': 12.0,
    'electrode_id': 1,  # E70XX
    'both_sides': True,
}

bolt_config = {
    'bolt_size': 0.75,
    'N_r': 4,
    'N_c': 1,
    'F_nv': 48.0,
    'F_nt': 90.0,
    'S_r': 3.0,
    'L_ev': 1.5,
    'L_eh': 2.0,
    'd_v': 0.8125,
    'd_h': 0.8125,
}
```

### 2. Connection Creation

```python
connection = SimpleShearConnection(
    beam_section=beam_section,
    plate_config=plate_config,
    weld_config=weld_config,
    bolt_config=bolt_config,
    column_section=column_section
)

# Internally creates interface objects:
# - WeldInterface(weld_config)
# - BoltInterface(bolt_config, plate_config, column_section)
```

### 3. Load Application & Evaluation

```python
V_u = 40.0  # Applied shear (kips)

result = connection.evaluate(V_u)
# Returns:
# {
#     'is_adequate': True/False,
#     'max_utilization': 0.85,
#     'controlling_interface': 'bolt',
#     'controlling_limit_state': 'bolt_shear',
#     'interface_results': [...]
# }
```

### 4. Interface Evaluation Flow

```
V_u = 40.0 kips
    │
    ├─► WeldInterface.evaluate(V_u)
    │       │
    │       ├─► transfer_weld_to_plate(V_u, weld_size, weld_length, ...)
    │       │       │
    │       │       └─► capacity = 50.0 kips
    │       │
    │       └─► utilization = 40.0 / 50.0 = 0.80 (80%)
    │
    └─► BoltInterface.evaluate(V_u)
            │
            ├─► transfer_bolts_shear(V_u, d_bolt, F_nv, ...)
            │       └─► cap = 55.0 kips, util = 0.73
            │
            ├─► check_bolt_bearing(V_u, d_bolt, t, ...)
            │       └─► cap = 48.0 kips, util = 0.83
            │
            ├─► check_plate_shear_yielding(V_u, t, width, ...)
            │       └─► cap = 52.0 kips, util = 0.77
            │
            └─► check_block_shear(V_u, t, F_y, ...)
                    └─► cap = 60.0 kips, util = 0.67
            
            Controlling: bearing @ 0.83 utilization
            
Result: max_utilization = 0.83 (bolt bearing controls)
```

## Interface Design Pattern

Each interface follows this pattern:

```python
class Interface:
    def __init__(self, config: Dict):
        """Store configuration parameters."""
        self.param1 = config['param1']
        self.param2 = config['param2']
        # ... etc
    
    def evaluate(self, load: float) -> Dict:
        """
        Evaluate interface capacity for given load.
        
        Returns:
            Dict with:
                - interface_type: str
                - capacity: float
                - utilization: float
                - is_adequate: bool
                - limit_state: str
                - [additional details]
        """
        # Calculate capacity using numba functions
        capacity, utilization = numba_calculation(
            load=load,
            param1=self.param1,
            param2=self.param2
        )
        
        return {
            'interface_type': 'interface_name',
            'capacity': capacity,
            'utilization': utilization,
            'is_adequate': utilization <= 1.0,
            'limit_state': 'specific_limit_state'
        }
```

## Calculation Function Pattern

All calculation functions follow this pattern:

```python
@njit
def calculation_function(
    load: float,
    param1: float,
    param2: float,
    # ... additional parameters following AISC naming
) -> Tuple[float, float]:
    """
    Calculate capacity for specific limit state.
    
    Args:
        load: Applied load (kips, kip-in, etc.)
        param1: Description (units)
        param2: Description (units)
        
    Returns:
        capacity: Limit state capacity (same units as load)
        utilization: load / capacity ratio
        
    AISC Reference: [Section number, equation]
    """
    # Numba-compatible calculations only
    # - Numpy operations: OK
    # - Math operations: OK
    # - Dictionary lookups: NO
    # - String operations: NO
    # - Object methods: NO
    
    phi = 0.75  # Resistance factor
    
    # Calculate nominal capacity
    nominal_capacity = formula(param1, param2)
    
    # Apply resistance factor
    design_capacity = phi * nominal_capacity
    
    # Calculate utilization
    utilization = load / design_capacity if design_capacity > 0 else 999.0
    
    return design_capacity, utilization
```

## Batch Processing Architecture

```
Input: Multiple configurations
┌────────────────────────────────────────────┐
│  Plates[n_p] × Welds[n_w] × Bolts[n_b]   │
│  Total: n_p × n_w × n_b configurations    │
└────────────────┬───────────────────────────┘
                 │
                 ▼
         Triple nested loop
         (can be parallelized)
                 │
    ┌────────────┼────────────┐
    │            │            │
    ▼            ▼            ▼
Config 1    Config 2    Config n
    │            │            │
    └────────────┼────────────┘
                 │
                 ▼
        Evaluate each with
      SimpleShearConnection
                 │
                 ▼
┌────────────────────────────────────────────┐
│           Result Arrays                    │
│  • results_adequate[n]                     │
│  • results_utilization[n]                  │
│  • results_controlling_state[n]            │
└────────────────────────────────────────────┘
                 │
                 ▼
         find_optimal_design()
                 │
                 ▼
┌────────────────────────────────────────────┐
│  Optimal Configuration                     │
│  • Minimum utilization                     │
│  • Among adequate designs                  │
└────────────────────────────────────────────┘
```

## Example: Simple Shear Connection

### Physical System

```
Beam                    Column
┌───┐                   ┌───┐
│   │                   │   │
│   │    ╱╲╱╲╱╲        │   │
│   ├───┤WELD├────┬────┤   │
│   │    ╲╱╲╱╲╱   │    │   │
│   │             │    │   │
│Web│             │Plate   │Web│
│   │    ╱╲╱╲╱╲   │    │   │
│   ├───┤WELD├────┤    │   │
│   │    ╲╱╲╱╲╱   │    │   │
│   │             ○────┼───┤
│   │             ○ BOLTS  │
│   │             ○────┼───┤
│   │             │    │   │
└───┘             └────└───┘
                  Shear Tab
```

### Load Path Sequence

1. **Beam Web** (starting point)
   - Load originates here
   - No calculations needed (load source)

2. **Weld Interface** (beam web → plate)
   - Limit State: Weld shear capacity
   - Check: AISC J2.4
   - Input: V_u, weld_size, weld_length, electrode
   - Output: capacity, utilization

3. **Plate** (load transfer element)
   - Multiple limit states checked in bolt interface:
     - Shear yielding/rupture (AISC J4.2)
     - Block shear (AISC J4.3)
     - Bolt bearing on plate (AISC J3.10)

4. **Bolt Interface** (plate → column web)
   - Limit States:
     - Bolt shear (AISC J3.6)
     - Bearing on plate (AISC J3.10)
     - Bearing on column (AISC J3.10)
     - Plate shear (AISC J4.2)
     - Block shear (AISC J4.3)
   - Input: V_u, bolt properties, plate properties, column properties
   - Output: capacity (min of all), utilization (max of all)

5. **Column Web** (ending point)
   - Included in bolt interface bearing checks
   - Additional checks (web yielding, crippling) could be separate interface

### Code Representation

```python
class SimpleShearConnection:
    def __init__(self, beam, plate, weld, bolt, column):
        self.interfaces = [
            WeldInterface(weld),                      # Interface 1
            BoltInterface(bolt, plate, column)        # Interface 2
        ]
    
    def evaluate(self, V_u):
        results = []
        for interface in self.interfaces:
            result = interface.evaluate(V_u)
            results.append(result)
        
        # Find controlling interface
        max_util = max(r['utilization'] for r in results)
        
        return {
            'is_adequate': all(r['is_adequate'] for r in results),
            'max_utilization': max_util,
            'interface_results': results
        }
```

## Extending to Other Connection Types

### Moment Connection

```python
class MomentConnection:
    def __init__(self, beam, column, top_flange_plate, 
                 bottom_flange_plate, web_plate, bolts):
        self.interfaces = [
            FlangeWeldInterface(top_flange_plate),
            FlangeBoltInterface(bolts, top_flange_plate, column),
            FlangeWeldInterface(bottom_flange_plate),
            FlangeBoltInterface(bolts, bottom_flange_plate, column),
            WebShearInterface(web_plate)
        ]
    
    def evaluate(self, M_u, V_u):
        # Decompose moment to flange forces
        d_beam = self.beam['d']
        P_flange = M_u / d_beam
        
        # Evaluate each interface
        results = []
        results.append(self.interfaces[0].evaluate(P_flange))
        results.append(self.interfaces[1].evaluate(P_flange))
        # ... etc
        
        return aggregate_results(results)
```

### Braced Connection

```python
class BracedConnection:
    def __init__(self, brace, gusset_plate, welds, bolts, beam, column):
        self.interfaces = [
            BraceInterface(brace),
            GussetWeldInterface(welds, gusset_plate, brace),
            GussetBoltInterface(bolts, gusset_plate, beam),
            GussetBoltInterface(bolts, gusset_plate, column),
            WhitmoreSectionInterface(gusset_plate)
        ]
    
    def evaluate(self, P_u):
        # Axial load in brace
        results = []
        for interface in self.interfaces:
            result = interface.evaluate(P_u)
            results.append(result)
        
        return aggregate_results(results)
```

## Performance Considerations

### Numba JIT Compilation

**First call:**
```
connection.evaluate(V_u)
→ Compile all @njit functions
→ Slower (100-500ms typical)
→ Compiled code cached
```

**Subsequent calls:**
```
connection.evaluate(V_u)
→ Use compiled code
→ Fast (0.1-1ms typical)
→ Suitable for optimization loops
```

### Vectorization Strategy

Current implementation uses **loop-based batch processing**:
- Simple to understand and maintain
- Adequate performance for most cases
- Can be parallelized with numba.prange

**Future enhancement** - True vectorization:
- Pass arrays directly to calculation functions
- Process all configs in single function call
- Requires refactoring of calculation functions
- Potential 10-100x speedup for large batches

### Memory Efficiency

- Result arrays pre-allocated
- No dynamic resizing during evaluation
- Minimal object creation in hot path
- NumPy arrays for efficient storage

## Testing Strategy

### Unit Tests

Test each calculation function independently:

```python
def test_transfer_weld_to_plate():
    V_u = 40.0
    weld_size = 0.25
    weld_length = 12.0
    electrode_strength = 70.0
    both_sides = True
    
    capacity, util = transfer_weld_to_plate(
        V_u, weld_size, weld_length, 
        electrode_strength, both_sides
    )
    
    assert capacity > 0
    assert 0 < util < 2.0
    assert capacity > V_u  # Should be adequate
```

### Integration Tests

Test complete interfaces:

```python
def test_bolt_interface():
    bolt_config = {...}
    plate_config = {...}
    column_config = {...}
    
    interface = BoltInterface(bolt_config, plate_config, column_config)
    result = interface.evaluate(V_u=40.0)
    
    assert 'capacity' in result
    assert 'utilization' in result
    assert result['is_adequate'] in [True, False]
```

### System Tests

Test complete load paths:

```python
def test_simple_shear_connection():
    connection = SimpleShearConnection(...)
    result = connection.evaluate(V_u=40.0)
    
    assert result['is_adequate'] == True
    assert result['max_utilization'] < 1.0
    assert len(result['interface_results']) == 2
```

### Validation Tests

Compare with hand calculations and AISC examples:

```python
def test_aisc_example_10_1():
    """Validate against AISC Design Example 10.1"""
    # Setup from example
    beam = {...}
    column = {...}
    # ... etc
    
    connection = SimpleShearConnection(...)
    result = connection.evaluate(V_u=52.0)
    
    # Compare with expected from AISC manual
    assert abs(result['max_utilization'] - 0.89) < 0.02
```

## Summary

This architecture provides:

✅ **Modularity**: Independent, testable components  
✅ **Composability**: Build complex connections from simple interfaces  
✅ **Performance**: Numba JIT for speed, vectorized batch processing  
✅ **Standards**: AISC variable naming throughout  
✅ **Extensibility**: Easy to add new connection types  
✅ **Maintainability**: Clear separation of concerns  
✅ **Debuggability**: Each layer can be tested independently  

The system is ready for integration with the `aisc_14th` module to replace placeholder calculations with actual AISC code checks.
