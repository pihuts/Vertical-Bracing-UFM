# Unified Functional API Reference

## Overview

The unified functional API provides high-level convenience functions that simplify the connection chaining workflow. All functions are pure (no classes, no state) and work with simple dictionary containers.

## Core Functions

### 1. `create_connection_interface()`

**Purpose:** Bundle connection matrix with member and connector data in a single dict.

**Signature:**
```python
def create_connection_interface(
    member_a_data: Dict[str, np.ndarray],
    member_b_data: Dict[str, np.ndarray],
    connector_data: Dict[str, np.ndarray]
) -> Dict[str, Any]
```

**Returns:** Dictionary with keys:
- `'connection_matrix'`: Connection combinations matrix
- `'member_a_data'`: First member data
- `'member_b_data'`: Second member data
- `'connector_data'`: Connector data
- `'n_connections'`: Total number of combinations

**Example:**
```python
interface = create_connection_interface(
    member_a_data=beam_configs,
    member_b_data=plate_configs,
    connector_data=bolt_configs
)
# Interface now contains everything bundled together
```

---

### 2. `extract_all_properties()`

**Purpose:** Automatically extract ALL numpy array properties from data dictionaries.

**Signature:**
```python
def extract_all_properties(
    matrix: Dict[str, Any],
    *data: Dict[str, np.ndarray]
) -> Dict[str, np.ndarray]
```

**Features:**
- No need to specify `properties_to_extract`
- Automatically filters out scalar values
- Only extracts numpy.ndarray properties
- Properties named as `m0_property`, `c0_property`, `m1_property`, etc.

**Example:**
```python
chain = chain_connections(conn1, conn2)
props = extract_all_properties(
    chain,
    beam_configs,
    bolt_configs,
    plate_configs,
    weld_configs,
    column_configs
)
# All array properties automatically extracted!
```

---

### 3. `build_connection_chain_from_interfaces()`

**Purpose:** Chain multiple interfaces and extract properties in ONE call.

**Signature:**
```python
def build_connection_chain_from_interfaces(
    *interfaces: Dict[str, Any],
    extract_properties: bool = True
) -> Dict[str, Any]
```

**Returns:** Dictionary with keys:
- `'chain'`: Complete connection chain
- `'properties'`: All extracted properties organized by member/connector:
  ```python
  {
      'm0': {'tw': array, 'F_y': array, ...},  # Member 0 properties
      'c0': {'bolt_size': array, ...},         # Connector 0 properties
      'm1': {'t': array, 'F_y': array, ...},   # Member 1 properties
      'c1': {'weld_size': array, ...},         # Connector 1 properties
      'm2': {...},                              # Member 2 properties
      ...
  }
  ```

**Key Feature:** Properties use the **same keys as your input data** - no prefixes needed!

**Example:**
```python
result = build_connection_chain_from_interfaces(
    interface_beam_plate,
    interface_plate_column
)

# Access with clean nested structure
chain = result['chain']
beam_props = result['properties']['m0']  # All beam properties
beam_tw = beam_props['tw']                # Same key as input!
bolt_size = result['properties']['c0']['bolt_size']  # Direct access
```

---

### 4. `quick_chain()`

**Purpose:** Ultimate convenience - chain + extract + apply loads in ONE call.

**Signature:**
```python
def quick_chain(
    *interfaces: Dict[str, Any],
    loads: Optional[Dict[str, float]] = None,
    eccentricity: Optional[Dict[str, float]] = None
) -> Dict[str, Any]
```

**Returns:** Dictionary with keys:
- `'chain'`: Complete connection chain
- `'properties'`: All extracted properties (nested dict structure)
- `'loads'`: Applied loads (if provided)
- `'n_chains'`: Total number of configurations

**Example:**
```python
result = quick_chain(
    interface_beam_plate,
    interface_plate_column,
    loads={'P': 20.0, 'V_y': 50.0},
    eccentricity={'e_x': 3.0}
)

# Everything done in one line!
# Access with clean structure
beam_tw = result['properties']['m0']['tw']
bolt_size = result['properties']['c0']['bolt_size']
loads = result['loads']
```

---

## Typical Workflow

### Old Way (5+ steps):
```python
# Step 1: Generate combinations
conn1 = generate_connection_combinations(len(beams), len(plates), len(bolts))
conn2 = generate_connection_combinations(len(plates), len(columns), len(welds))

# Step 2: Chain connections
chain = chain_connections(conn1, conn2)

# Step 3: Extract properties (must specify!)
props = extract_connection_properties(
    chain,
    beams, bolts, plates, welds, columns,
    properties_to_extract={
        'member_0': ['tw', 'F_y'],
        'connector_0': ['bolt_size'],
        # ... must list all properties!
    }
)

# Step 4: Create loads
loads = {'P': 20.0, 'V_y': 50.0, ...}

# Step 5: Apply eccentricity
loads = apply_eccentricity_moments(loads, {'e_x': 3.0})
```

### New Way (3 lines):
```python
# Step 1: Create interfaces (bundles data + matrix)
iface1 = create_connection_interface(beams, plates, bolts)
iface2 = create_connection_interface(plates, columns, welds)

# Step 2: Done!
result = quick_chain(
    iface1, iface2,
    loads={'P': 20.0, 'V_y': 50.0},
    eccentricity={'e_x': 3.0}
)
# result contains: chain, properties (ALL of them!), loads
```

---

## Benefits

✅ **Pure Functional Style**
- No classes, no state
- Just data in, data out
- Easy to reason about

✅ **Dict-Based Containers**
- Simple, inspectable structures
- Easy to serialize (JSON, pickle)
- Works with standard Python tools

✅ **Auto-Property Extraction**
- No need to specify `properties_to_extract`
- Smart detection of numpy arrays
- Extracts everything automatically

✅ **Data Travels Together**
- Interface bundles matrix + data
- No need to pass data separately
- Reduces function call complexity

✅ **Composable**
- Chain any number of interfaces (2, 3, 4+)
- Flexible for complex load paths
- Scales easily

---

## Property Naming Convention

Properties are organized in a **nested dict structure** by member/connector:
- `m0`: Member 0 (first member)
- `c0`: Connector 0 (first connector)
- `m1`: Member 1 (second member)
- `c1`: Connector 1 (second connector)
- `m2`: Member 2 (third member)
- etc.

**Each nested dict uses the SAME KEYS as your input data!**

**Example:**
```python
props = result['properties']

# Access by member/connector, then property name
beam_tw = props['m0']['tw']          # Member 0 web thickness
bolt_size = props['c0']['bolt_size']  # Connector 0 bolt size
plate_t = props['m1']['t']            # Member 1 plate thickness
weld_size = props['c1']['weld_size']  # Connector 1 weld size
column_tw = props['m2']['tw']         # Member 2 web thickness

# Or get all properties for a member/connector
all_beam_props = props['m0']  # Dict with all beam properties
all_bolt_props = props['c0']  # Dict with all bolt properties
```

**Why nested structure is better:**
- ✅ Same keys as input data - no mental mapping
- ✅ Logical grouping by member/connector
- ✅ Easy to iterate over all properties of a member
- ✅ More Pythonic and intuitive

---

## Advanced Usage

### Multiple Connections (3+ interfaces)
```python
# 4 interfaces = 5 members, 4 connectors
result = quick_chain(
    interface1,  # m0 → c0 → m1
    interface2,  # m1 → c1 → m2
    interface3,  # m2 → c2 → m3
    interface4,  # m3 → c3 → m4
    loads={'P': 100.0}
)
# Creates: m0 → c0 → m1 → c1 → m2 → c2 → m3 → c3 → m4
```

### Extract Only (No Loads)
```python
result = build_connection_chain_from_interfaces(
    interface1,
    interface2,
    extract_properties=True  # Default
)
# Just chain + properties, no loads
```

### Custom Load Application
```python
# Use quick_chain without loads first
result = quick_chain(interface1, interface2)

# Apply custom loads later
custom_loads = your_load_function(result['properties'])
result['loads'] = custom_loads
```

---

## Migration Guide

### From Class-Based to Functional

**Old (Class-Based):**
```python
interface = ConnectionInterface.create(member_a, member_b, connector)
result = build_connection_chain(interface1, interface2)
```

**New (Functional):**
```python
interface = create_connection_interface(member_a, member_b, connector)
result = build_connection_chain_from_interfaces(interface1, interface2)
```

**Key Changes:**
1. `ConnectionInterface.create()` → `create_connection_interface()`
2. `build_connection_chain()` → `build_connection_chain_from_interfaces()`
3. Interface is now a dict, not a class instance
4. Access properties with `interface['key']` not `interface.key`
5. **Properties now use nested dict structure with same keys as input!**

---

## New vs Old Property Access

### Old Flat Structure (with prefixes):
```python
props = result['properties']
beam_tw = props['m0_tw']           # Prefix in key
bolt_size = props['c0_bolt_size']  # Prefix in key
plate_t = props['m1_t']            # Prefix in key
```

### New Nested Structure (same keys as input):
```python
props = result['properties']
beam_tw = props['m0']['tw']           # ✅ Same key as input!
bolt_size = props['c0']['bolt_size']  # ✅ Same key as input!
plate_t = props['m1']['t']            # ✅ Same key as input!

# Bonus: Get all properties for a member
all_beam_props = props['m0']  # {'tw': array, 'F_y': array, ...}
```

---

## Performance Notes

- ✅ Zero-copy indexing maintained throughout
- ✅ Vectorized operations using numpy
- ✅ No data duplication - only index mapping
- ✅ Scales to thousands of configurations efficiently
- ✅ Example: 6,144 chains with 184 properties extracted in < 1 second

---

## See Also

- `test_speed.ipynb`: Complete examples and demonstrations
- `steel_lib/load_transfer.py`: Core low-level functions
- `steel_lib/load_transfer_unified.py`: This unified API module
- `LOAD_PATH_V2_README.md`: Overall load path system documentation
