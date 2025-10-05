# Automatic Global Naming System

## Overview

The steel_lib unified API now features an **automatic global naming system** that eliminates the need for manual naming in connection interfaces. All generators (`generate_aisc_members`, `generate_bolt_configurations`, `generate_fillet_welds`, `generate_shear_plates`) now include a `type_id` parameter that enables automatic name extraction.

## Key Benefits

✅ **Zero Manual Configuration**: No need to specify `member_a_name`, `member_b_name`, `connector_name`  
✅ **Self-Documenting Code**: Property keys like `m0_beam`, `c0_bolts`, `m1_plate_shear` are clear  
✅ **Consistent Naming**: Global type code ranges prevent conflicts  
✅ **Backward Compatible**: Old code still works with manual naming

## Type Code Ranges

The naming system uses integer codes organized into ranges:

### 001-099: Members
| type_id | Name | Description |
|---------|------|-------------|
| 1 | `beam` | Beam member (horizontal) |
| 2 | `column` | Column member (vertical) |
| 3 | `brace` | Brace member (diagonal) |
| 4 | `girder` | Girder member (main beam) |
| 5 | `joist` | Joist member (light framing) |
| 6 | `truss_chord` | Truss chord member |
| 7 | `truss_web` | Truss web member |
| 8 | `strut` | Strut member (compression) |
| 9 | `tie` | Tie member (tension) |
| 10 | `gusset_member` | Gusset member |

### 100-199: Bolts
| type_id | Name | Description |
|---------|------|-------------|
| 100 | `bolts` | Generic bolts |
| 101 | `bolts_shear` | Shear bolts |
| 102 | `bolts_tension` | Tension bolts |
| 103 | `bolts_combined` | Combined loading bolts |
| 104 | `anchor_bolts` | Anchor bolts |
| 105 | `hsfg_bolts` | High strength friction grip |

### 200-299: Welds
| type_id | Name | Description |
|---------|------|-------------|
| 200 | `weld` | Generic weld |
| 201 | `weld_fillet` | Fillet weld |
| 202 | `weld_groove` | Groove weld (CJP) |
| 203 | `weld_plug` | Plug weld |
| 204 | `weld_slot` | Slot weld |
| 205 | `weld_partial_penetration` | PJP weld |

### 300-399: Plates
| type_id | Name | Description |
|---------|------|-------------|
| 300 | `plate` | Generic plate |
| 301 | `plate_shear` | Shear plate |
| 302 | `plate_flange` | Flange plate |
| 303 | `plate_stiffener` | Stiffener plate |
| 304 | `plate_gusset` | Gusset plate |
| 305 | `plate_base` | Base plate |
| 306 | `plate_doubler` | Doubler plate |

## Usage Examples

### Basic Usage

```python
from steel_lib.load_transfer_unified import (
    generate_aisc_members,
    create_connection_interface,
    build_connection_chain_from_interfaces
)
from steel_lib.plate_generator import generate_shear_plates
from steel_lib.generator_combination import generate_bolt_configurations
from steel_lib.weld_generator import generate_fillet_welds
import numpy as np

# 1. Generate with type_id
beams = generate_aisc_members(
    designations=['W14X68'],
    type_id=1  # Automatically becomes 'beam'
)

plates = generate_shear_plates(
    plate_grade_id=[1],
    t=[0.375],
    w=[5.0],
    l=[12.0],
    type_id=301  # Automatically becomes 'plate_shear'
)

bolts = generate_bolt_configurations(
    bolt_size=np.array([0.75]),
    bolt_grade_id=np.array([0]),
    member_a_BHT_id=np.array([0]),
    member_b_BHT_id=np.array([0]),
    N_r=np.array([4]),
    S_r=np.array([3.0]),
    N_c=np.array([1]),
    S_c=np.array([3.0]),
    L_ev=np.array([1.5]),
    L_eh=np.array([2.0]),
    Ga=np.array([0.0]),
    type_id=100  # Automatically becomes 'bolts'
)

# 2. Create interface - NO MANUAL NAMING!
interface = create_connection_interface(
    member_a_data=beams,     # Auto-extracts 'beam'
    member_b_data=plates,    # Auto-extracts 'plate_shear'
    connector_data=bolts     # Auto-extracts 'bolts'
    # Names automatically extracted from type_id!
)

# Result properties:
# - m0_beam (not just m0)
# - c0_bolts (not just c0)
# - m1_plate_shear (not just m1)
```

### Complete Workflow

```python
# Generate all components
beams = generate_aisc_members(designations=['W14X68'], type_id=1)
columns = generate_aisc_members(designations=['W14X90'], type_id=2)
plates = generate_shear_plates(plate_grade_id=[1], t=[0.375], w=[5.0], l=[12.0], type_id=301)
welds = generate_fillet_welds(electrode_id=[1], weld_size=[0.25], weld_length=[12.0], type_id=201)
bolts = generate_bolt_configurations(..., type_id=100)

# Create interfaces (automatic naming)
iface1 = create_connection_interface(
    member_a_data=beams,
    member_b_data=plates,
    connector_data=welds
)

iface2 = create_connection_interface(
    member_a_data=plates,
    member_b_data=columns,
    connector_data=bolts
)

# Build chain
chain = build_connection_chain_from_interfaces(iface1, iface2)

# Access properties with clear names
print(chain['topology'])  # "beam → weld_fillet → plate_shear → bolts → column"
print(chain['properties']['m0_beam']['tw'])  # Beam web thickness
print(chain['properties']['m1_plate_shear']['thickness'])  # Plate thickness
print(chain['properties']['c0_weld_fillet']['weld_size'])  # Weld size
print(chain['properties']['m2_column']['d'])  # Column depth
```

### Using String Names

You can also use string names instead of integers:

```python
# These are equivalent:
beams1 = generate_aisc_members(designations=['W14X68'], type_id=1)
beams2 = generate_aisc_members(designations=['W14X68'], type_id='beam')

# The system automatically converts strings to integers
```

### Manual Override (Still Supported)

If you need custom names, you can still override:

```python
interface = create_connection_interface(
    member_a_data=beams,
    member_b_data=plates,
    connector_data=bolts,
    member_a_name='custom_beam',  # Override automatic name
    connector_name='special_bolts'  # Override automatic name
)
# Result: m0_custom_beam, c0_special_bolts, m1_plate_shear (mixed auto/manual)
```

## How It Works

### 1. Generators Add Type Information

All generators now add two fields to their output:

```python
{
    'type_id': np.array([1, 1, 1]),      # Integer code
    'type_name': np.array(['beam', 'beam', 'beam'])  # String name
    # ... other properties ...
}
```

### 2. create_connection_interface Extracts Names

The function uses `extract_type_name()` helper:

```python
def extract_type_name(data: Dict[str, np.ndarray]) -> Optional[str]:
    """Extract type name from data dictionary using type_id."""
    if 'type_id' not in data:
        return None
    type_id = int(data['type_id'][0])
    return GLOBAL_TYPE_MAP.get(type_id, None)
```

### 3. Names Propagate Through System

Once extracted, names propagate through:
- Property keys: `m0_beam`, `c0_bolts`, `m1_plate_shear`
- Relationship tracking: `{'member': 'm0_beam', 'connected_to': ['c0_bolts']}`
- Topology strings: `"beam → bolts → plate_shear"`

## Migration Guide

### Old Code (Still Works)

```python
# Manual naming (backward compatible)
interface = create_connection_interface(
    member_a_data=beams,
    member_b_data=plates,
    connector_data=bolts,
    member_a_name='beam',
    member_b_name='plate_shear',
    connector_name='bolts'
)
```

### New Code (Automatic)

```python
# Just add type_id to generators
beams = generate_aisc_members(..., type_id=1)
plates = generate_shear_plates(..., type_id=301)
bolts = generate_bolt_configurations(..., type_id=100)

# Remove manual naming
interface = create_connection_interface(
    member_a_data=beams,
    member_b_data=plates,
    connector_data=bolts
    # No naming parameters needed!
)
```

## Best Practices

### 1. Use Descriptive type_ids

Choose type_ids that match your use case:

```python
# Good: Clear purpose
beams = generate_aisc_members(..., type_id=1)  # beam
columns = generate_aisc_members(..., type_id=2)  # column
braces = generate_aisc_members(..., type_id=3)  # brace

# Also good: Specific bolt types
shear_bolts = generate_bolt_configurations(..., type_id=101)  # bolts_shear
tension_bolts = generate_bolt_configurations(..., type_id=102)  # bolts_tension
```

### 2. Consistent Ranges

Keep your custom extensions within the defined ranges:

```python
# Custom member types (001-099)
custom_member = generate_aisc_members(..., type_id=11)  # Your custom member

# Custom bolt types (100-199)
custom_bolts = generate_bolt_configurations(..., type_id=110)  # Your custom bolt
```

### 3. Document Custom type_ids

If you create custom type_ids, document them:

```python
# Custom type_ids for project
# 11: 'collector_beam' - Special beam for load collection
# 12: 'transfer_girder' - Transfer girder for offset columns
# 110: 'slip_critical_bolts' - SC bolts for seismic connections

collector = generate_aisc_members(..., type_id=11)
```

## API Reference

### Updated Generator Signatures

```python
def generate_aisc_members(
    designations: Optional[List[str]] = None,
    filters: Optional[Dict[str, Any]] = None,
    type_id: Union[int, str] = 1,  # NEW: Automatic naming
    material: str = 'A992',
    database_path: str = 'aisc-shapes-database-v16.0.xlsx'
) -> Dict[str, np.ndarray]

def generate_bolt_configurations(
    bolt_size, bolt_grade_id, member_a_BHT_id, member_b_BHT_id,
    N_r, S_r, N_c, S_c, L_ev, L_eh, Ga,
    type_id=100  # NEW: Automatic naming
)

def generate_fillet_welds(
    electrode_id, weld_size, weld_length,
    both_sides=None, intermittent=None, intermittent_pitch=None,
    type_id=201  # NEW: Automatic naming
)

def generate_shear_plates(
    plate_grade_id, t, w=None, l=None, a=None,
    type_id=301  # NEW: Automatic naming
)
```

### extract_type_name()

```python
def extract_type_name(data: Dict[str, np.ndarray]) -> Optional[str]:
    """
    Extract the type name from a data dictionary using the global naming system.
    
    Args:
        data: Dictionary with properties (must contain 'type_id' array)
    
    Returns:
        String name (e.g., 'beam', 'bolts', 'weld_fillet') or None
    """
```

## Technical Details

### Global Type Mappings

The system uses several dictionaries for mapping:

```python
# Member types (001-099)
MEMBER_TYPE_MAP = {
    1: 'beam', 2: 'column', 3: 'brace', ...
}

# Bolt types (100-199)
BOLT_TYPE_MAP = {
    100: 'bolts', 101: 'bolts_shear', ...
}

# Weld types (200-299)
WELD_TYPE_MAP = {
    200: 'weld', 201: 'weld_fillet', ...
}

# Plate types (300-399)
PLATE_TYPE_MAP = {
    300: 'plate', 301: 'plate_shear', ...
}

# Combined for lookup
GLOBAL_TYPE_MAP = {**MEMBER_TYPE_MAP, **BOLT_TYPE_MAP, 
                   **WELD_TYPE_MAP, **PLATE_TYPE_MAP}
```

### Reverse Mappings

For string to integer conversion:

```python
MEMBER_TYPE_TO_INT = {v: k for k, v in MEMBER_TYPE_MAP.items()}
# {'beam': 1, 'column': 2, 'brace': 3, ...}
```

## Troubleshooting

### Issue: Names not appearing in properties

**Cause**: Generator missing `type_id` parameter  
**Solution**: Add `type_id` parameter to generator call

```python
# Before (no automatic naming)
beams = generate_aisc_members(designations=['W14X68'])

# After (automatic naming)
beams = generate_aisc_members(designations=['W14X68'], type_id=1)
```

### Issue: Wrong name extracted

**Cause**: Incorrect `type_id` value  
**Solution**: Check type_id reference table and use correct code

```python
# Wrong range (bolt type for member)
beams = generate_aisc_members(..., type_id=100)  # Returns 'bolts' name!

# Correct range
beams = generate_aisc_members(..., type_id=1)  # Returns 'beam'
```

### Issue: Manual names not working

**Cause**: Both automatic and manual naming attempted  
**Solution**: Choose one approach

```python
# Automatic (preferred)
interface = create_connection_interface(
    member_a_data=beams,  # Has type_id
    member_b_data=plates,
    connector_data=bolts
)

# Manual override
interface = create_connection_interface(
    member_a_data=beams,
    member_b_data=plates,
    connector_data=bolts,
    member_a_name='custom_name'  # Overrides automatic
)
```

## Performance

The automatic naming system has **zero performance impact**:

- Type extraction: O(1) dictionary lookup
- Names stored as views: No data copying
- Generators: Single assignment operation

## Future Extensions

Planned additions to the naming system:

- **400-499**: Other connectors (pins, clevises, etc.)
- **500-599**: Connection components (stiffeners, doubler plates specific to connections)
- **600-699**: Foundation components (footing plates, anchor rods, etc.)

## Summary

The automatic global naming system provides:

1. **Simplicity**: No manual naming needed
2. **Clarity**: Self-documenting property keys
3. **Consistency**: Global type code ranges
4. **Flexibility**: Manual override still available
5. **Performance**: Zero overhead

**Recommended Usage**: Always include `type_id` in generators for automatic, self-documenting code.
