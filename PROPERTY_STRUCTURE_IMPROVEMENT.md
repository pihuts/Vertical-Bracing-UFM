# Property Structure Improvement

## Summary

The `build_connection_chain_from_interfaces()` function now returns properties in a **clean nested dict structure** that uses the **same keys as your input data**.

---

## What Changed?

### Old Structure (Flat with Prefixes)

```python
result = build_connection_chain_from_interfaces(iface1, iface2)

props = result['properties']
# Properties had prefixed names:
beam_tw = props['m0_tw']           # ❌ Key changed from input
bolt_size = props['c0_bolt_size']  # ❌ Key changed from input
plate_t = props['m1_t']            # ❌ Key changed from input
weld_size = props['c1_weld_size']  # ❌ Key changed from input
```

**Problems:**
- ❌ Property names have prefixes (`m0_`, `c0_`, etc.)
- ❌ Different from input data keys
- ❌ Hard to get all properties for a member
- ❌ Requires mental mapping

---

### New Structure (Nested, Same Keys)

```python
result = build_connection_chain_from_interfaces(iface1, iface2)

props = result['properties']
# Properties organized by member/connector:
beam_tw = props['m0']['tw']           # ✅ Same key as input!
bolt_size = props['c0']['bolt_size']  # ✅ Same key as input!
plate_t = props['m1']['t']            # ✅ Same key as input!
weld_size = props['c1']['weld_size']  # ✅ Same key as input!

# Bonus: Get all properties for a member
all_beam_props = props['m0']
# {'tw': array, 'F_y': array, 'designations': array, ...}
```

**Benefits:**
- ✅ Same keys as input data - no mental mapping
- ✅ Logical grouping by member/connector
- ✅ Easy to get all properties for a member
- ✅ More intuitive and Pythonic
- ✅ Easier to iterate

---

## Full Structure

```python
result = {
    'chain': {
        'n_chains': 6144,
        'n_members': 3,
        'n_connectors': 2,
        'member_0_idx': array([...]),
        'connector_0_idx': array([...]),
        'member_1_idx': array([...]),
        'connector_1_idx': array([...]),
        'member_2_idx': array([...])
    },
    'properties': {
        'm0': {  # Member 0 (e.g., Beam)
            'tw': array([...]),
            'F_y': array([...]),
            'designations': array([...]),
            # ... all other beam properties with SAME KEYS as input
        },
        'c0': {  # Connector 0 (e.g., Bolts)
            'bolt_size': array([...]),
            'N_r': array([...]),
            'F_nv': array([...]),
            # ... all other bolt properties with SAME KEYS as input
        },
        'm1': {  # Member 1 (e.g., Plate)
            't': array([...]),
            'F_y': array([...]),
            'a': array([...]),
            # ... all other plate properties with SAME KEYS as input
        },
        'c1': {  # Connector 1 (e.g., Welds)
            'weld_size': array([...]),
            'weld_length': array([...]),
            'F_w': array([...]),
            # ... all other weld properties with SAME KEYS as input
        },
        'm2': {  # Member 2 (e.g., Column)
            'tw': array([...]),
            'F_y': array([...]),
            'designations': array([...]),
            # ... all other column properties with SAME KEYS as input
        }
    }
}
```

---

## Usage Examples

### Example 1: Direct Access

```python
result = build_connection_chain_from_interfaces(
    beam_plate_interface,
    plate_column_interface
)

# Get specific properties
beam_web_thickness = result['properties']['m0']['tw']
bolt_rows = result['properties']['c0']['N_r']
plate_thickness = result['properties']['m1']['t']
weld_size = result['properties']['c1']['weld_size']
column_designation = result['properties']['m2']['designations']
```

### Example 2: Get All Properties for a Member

```python
# Get all beam properties as a dict
beam_props = result['properties']['m0']

# Use in calculations
for key, value in beam_props.items():
    print(f"Beam {key}: {value[:3]}")

# {'tw': array([...]), 'F_y': array([...]), 'designations': array([...]), ...}
```

### Example 3: With quick_chain

```python
result = quick_chain(
    beam_plate_interface,
    plate_column_interface,
    loads={'P': 20.0, 'V_y': 50.0},
    eccentricity={'e_x': 3.0}
)

# Access everything cleanly
chain = result['chain']
props = result['properties']
loads = result['loads']

# Use in AISC checks
bolt_capacity = bolt_shear(
    F_nv=props['c0']['F_nv'],
    A_bolt=props['c0']['A_bolt'],
    N_shear_planes=1,
    phi=0.75
)

bolt_utilization = loads['V_y'] / (props['c0']['N_r'] * bolt_capacity)
```

### Example 4: Iteration Over Members

```python
props = result['properties']

# Iterate over all members
for member_key in ['m0', 'm1', 'm2']:
    if member_key in props:
        member_props = props[member_key]
        if 'F_y' in member_props:
            print(f"{member_key} yield strength: {member_props['F_y'][:3]}")

# Iterate over all connectors
for connector_key in ['c0', 'c1']:
    if connector_key in props:
        connector_props = props[connector_key]
        print(f"{connector_key} properties: {list(connector_props.keys())}")
```

---

## Comparison Table

| Aspect | Old (Flat) | New (Nested) |
|--------|-----------|--------------|
| **Key names** | `m0_tw`, `c0_bolt_size` | `['m0']['tw']`, `['c0']['bolt_size']` |
| **Same as input?** | ❌ No (prefixed) | ✅ Yes (exact match) |
| **Grouping** | ❌ All flat | ✅ By member/connector |
| **Get all props** | ❌ Must filter | ✅ Just `props['m0']` |
| **Iteration** | ❌ Complex | ✅ Simple |
| **Readability** | ❌ Prefixes everywhere | ✅ Clean nested access |
| **Maintainability** | ❌ Manual mapping | ✅ Automatic |

---

## Migration

If you have existing code using the old flat structure, update it like this:

```python
# Old code
beam_tw = props['m0_tw']
bolt_size = props['c0_bolt_size']
plate_t = props['m1_t']

# New code
beam_tw = props['m0']['tw']
bolt_size = props['c0']['bolt_size']
plate_t = props['m1']['t']
```

---

## Why This Matters

1. **Consistency**: Keys match your input data exactly
2. **Simplicity**: No mental mapping from input keys to output keys
3. **Organization**: Properties logically grouped by member/connector
4. **Pythonic**: Follows Python conventions for nested data structures
5. **Flexibility**: Easy to add helper functions that work with member dicts
6. **Maintainability**: Code is easier to read and understand

---

## Summary

The new nested dict structure makes the API:
- ✅ More intuitive
- ✅ Easier to use
- ✅ More consistent with input data
- ✅ More Pythonic
- ✅ Better organized

All while maintaining the same performance and functionality!
