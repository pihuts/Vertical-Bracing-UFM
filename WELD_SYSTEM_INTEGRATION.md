# Weld Generator - Complete Integration Guide

## Overview

The weld generator has been successfully added to your steel connection design system! It follows the exact same pattern as your bolt and plate generators for seamless integration.

## System Architecture

```
steel_lib/
├── weld_generator.py         (NEW - 576 lines)
├── plate_generator.py         (550 lines)
├── generator_combination.py   (bolt generator)
├── load_path.py              (load path tracking)
└── section_properties.py     (AISC section selector)
```

## What Was Created

### 1. Core Module: `weld_generator.py`

**Weld Types Supported:**
- Fillet welds (most common) - 90% of connections
- Groove welds (CJP, PJP) - moment connections
- Plug welds - lap joint repairs
- Slot welds - lap joint repairs

**Features:**
- ✅ Integer mappings for efficiency (weld types, electrode grades)
- ✅ Columnar NumPy arrays for Numba compatibility
- ✅ Auto-calculated properties (throat, capacities)
- ✅ AISC 360 Chapter J compliant
- ✅ Standard size library (12 fillet sizes from 3/16" to 1")
- ✅ Electrode grades E60XX through E110XX

### 2. Specialized Generators

#### `generate_fillet_welds()`
Most commonly used - for shear plates, brackets, etc.
```python
welds = generate_fillet_welds(
    electrode_id=[1],                  # E70XX
    weld_size=[0.25, 0.3125, 0.375],  # 1/4", 5/16", 3/8"
    weld_length=[12.0, 18.0],         # 12", 18"
    both_sides=[False, True]          # Single and double
)
# Returns: throat, R_n, phi_R_n, strength_per_inch
```

#### `generate_groove_welds()`
For moment connections and splice plates:
```python
welds = generate_groove_welds(
    electrode_id=[1],
    weld_type_id=[1],      # CJP or PJP
    plate_thickness=[0.5, 0.625],
    weld_length=[12.0, 18.0],
    effective_throat=[0.25]  # For PJP
)
```

#### `generate_plug_slot_welds()`
For repair connections:
```python
welds = generate_plug_slot_welds(
    electrode_id=[1],
    weld_type_id=[3],      # PLUG or SLOT
    diameter_or_width=[0.75, 1.0],
    thickness=[0.5],
    n_welds=[4, 6, 8]
)
```

### 3. Utility Functions

#### `calculate_weld_length_required()`
Quick preliminary design calculator:
```python
L_required = calculate_weld_length_required(
    force=50.0,                # kips
    electrode_grade='E70XX',
    weld_size=0.3125,         # 5/16"
    both_sides=False
)
# Returns: 7.2 inches needed
```

#### `get_weld_mapping_info()`
Returns all mapping tables and properties.

## Integer Mapping System

### Weld Types
```python
0: FILLET              # Most common
1: CJP                 # Complete Joint Penetration
2: PJP                 # Partial Joint Penetration
3: PLUG                # Plug weld
4: SLOT                # Slot weld
5: FILLET_BOTH         # Both sides flag
6: FILLET_INTERMITTENT # Intermittent pattern
```

### Electrode Grades
```python
0: E60XX   # F_EXX=60 ksi, F_w=36.0 ksi
1: E70XX   # F_EXX=70 ksi, F_w=42.0 ksi (most common)
2: E80XX   # F_EXX=80 ksi, F_w=48.0 ksi
3: E90XX   # F_EXX=90 ksi, F_w=54.0 ksi
4: E100XX  # F_EXX=100 ksi, F_w=60.0 ksi
5: E110XX  # F_EXX=110 ksi, F_w=66.0 ksi
```

## Output Format

All generators return dictionary of NumPy arrays:

```python
{
    'weld_type_id': array([0, 0, ...]),       # Integer code
    'electrode_id': array([1, 1, ...]),       # Integer code
    'weld_type': array(['FILLET', ...]),      # String name
    'electrode': array(['E70XX', ...]),       # String name
    'F_EXX': array([70.0, ...]),              # Electrode tensile strength (ksi)
    'F_w': array([42.0, ...]),                # Weld strength = 0.6*F_EXX (ksi)
    'weld_size': array([0.25, ...]),          # Leg size (inches)
    'weld_length': array([12.0, ...]),        # Length (inches)
    'throat': array([0.177, ...]),            # Effective throat (inches)
    'R_n': array([89.2, ...]),                # Nominal capacity (kips)
    'phi_R_n': array([66.9, ...]),            # Design capacity φ=0.75 (kips)
    'strength_per_inch': array([7.43, ...]),  # R_n per inch (k/in)
    'phi_strength_per_inch': array([5.57, ...]) # φR_n per inch (k/in)
}
```

## Integration Examples

### With Plate Generator

```python
from steel_lib.plate_generator import generate_shear_plates
from steel_lib.weld_generator import generate_fillet_welds

# Generate plates
plates = generate_shear_plates(
    plate_grade_id=[1],  # A572-50
    thickness=[0.375, 0.5],
    width=[5.0, 6.0],
    length=[15.0, 18.0]
)

# Generate matching welds
welds = generate_fillet_welds(
    electrode_id=[1],  # E70XX
    weld_size=[0.3125, 0.375],
    weld_length=[15.0, 18.0],  # Match plate lengths
    both_sides=[True]
)

# Find combinations that work for 40 kip force
for plate_idx in range(len(plates['thickness'])):
    for weld_idx in range(len(welds['weld_size'])):
        # Match lengths
        if abs(welds['weld_length'][weld_idx] - plates['length'][plate_idx]) < 0.1:
            capacity = min(
                plates['phi_V_n_gross'][plate_idx],
                welds['phi_R_n'][weld_idx]
            )
            if capacity >= 40.0:
                print(f"Viable: {capacity:.1f} kips")
```

### With Load Path System

```python
from steel_lib.load_path import LoadPathGenerator, LoadVector

generator = LoadPathGenerator()

# Create connection element for welds
weld_element = ConnectionElement(
    element_id='WELDS_B',
    element_type='WELD',
    geometry={
        'weld_type': 'FILLET',
        'electrode': 'E70XX',
        'weld_size': 0.3125,
        'weld_length': 18.0,
        'both_sides': True,
        'throat': 0.221
    },
    material={
        'F_EXX': 70.0,
        'F_w': 42.0
    },
    load=LoadVector(V_y=40.0),
    capacities={'phi_R_n': 250.5}
)
```

### With AISC Section Selector

```python
# Select beam section
results = aisc['select_by_properties']({
    "designation": ["W18X35"],
})

# Get web thickness for weld sizing
t_w = results['t_w'][0]

# Select appropriate weld size
# Per AISC J2.2b, minimum weld for t_w
if t_w <= 0.25:
    min_weld_size = 0.1875  # 3/16"
elif t_w <= 0.5:
    min_weld_size = 0.25    # 1/4"
elif t_w <= 0.75:
    min_weld_size = 0.3125  # 5/16"
else:
    min_weld_size = 0.375   # 3/8"

welds = generate_fillet_welds(
    electrode_id=[1],
    weld_size=[min_weld_size, min_weld_size + 0.0625],  # Min and next size up
    weld_length=[beam_depth - 2*k_des],
    both_sides=[True]
)
```

## AISC Design Provisions

### Fillet Weld Design (J2.2)

**Effective Throat:**
- Equal leg: `throat = 0.707 × leg_size`
- Unequal leg: `throat = 0.707 × smaller_leg`

**Design Strength:**
- φ = 0.75 (weld material)
- φR_n = 0.75 × F_w × A_we
- A_we = throat × length
- F_w = 0.60 × F_EXX

**Minimum Size (Table J2.4):**
- Material ≤ 1/4": 3/16" minimum
- 1/4" < t ≤ 1/2": 1/4" minimum
- 1/2" < t ≤ 3/4": 5/16" minimum
- t > 3/4": 3/8" minimum

**Maximum Size:**
- For t < 1/4": max = t
- For t ≥ 1/4": max = t - 1/16"

### Groove Weld Design (J2.1)

**CJP (Complete Joint Penetration):**
- Full base metal strength
- throat = plate thickness

**PJP (Partial Joint Penetration):**
- Limited by effective throat
- throat = depth of groove preparation

### Standard Sizes

**Fillet Weld Leg Sizes (12 standard):**
3/16", 1/4", 5/16", 3/8", 7/16", 1/2", 9/16", 5/8", 11/16", 3/4", 7/8", 1"

**Common Electrodes:**
- E70XX: Most common for A36, A572-50, A992
- E80XX: For high-strength steels
- E90XX, E100XX: For very high-strength applications

## Demonstration Results

From `test_speed.ipynb`:

### Example 1: Fillet Weld Configurations
- Generated 18 configurations (3 sizes × 3 lengths × 2 sides)
- Capacity range: 66.9 to 250.5 kips
- Output includes throat, F_w, φR_n, strength per inch

### Example 2: Weld Length Calculator
For 50 kip force with E70XX electrode:
```
Weld Size     Single Side    Both Sides
3/16"         12.0"          6.0"
1/4"          9.0"           4.5"
5/16"         7.2"           3.6"
3/8"          6.0"           3.0"
1/2"          4.5"           2.2"
```

### Example 3: Integrated Plate + Weld System
Found 5+ viable configurations for 40 kip force:
- A572-50 PL 5.0" × 0.375" × 15.0"
- E70XX 1/4" fillet, 15.0" both sides
- Capacity: 56.2 kips (Limited by PLATE)
- Utilization: 71.1%

## Files Created

1. **steel_lib/weld_generator.py** (576 lines)
   - Main weld generation module
   - All specialized generators
   - Utility functions

2. **WELD_GENERATOR_README.md**
   - Quick start guide
   - Usage examples
   - Integration patterns

3. **WELD_SYSTEM_INTEGRATION.md** (this file)
   - Complete integration documentation
   - System architecture
   - Design provisions

4. **test_speed.ipynb** (updated)
   - Added 4 new cells demonstrating weld system
   - All examples tested and working

## Next Steps

### Immediate Use
You can now use the weld generator in your connection designs:
```python
from steel_lib import (
    generate_fillet_welds,
    generate_groove_welds,
    calculate_weld_length_required
)
```

### Integration with Load Path System
The weld generator output is ready to integrate with your load path system:
- Add weld evaluation to `LoadPathGenerator._evaluate_welds()`
- Use weld capacities in connection evaluation
- Track force transfer through welded connections

### Add to Optimization Workflows
```python
# Generate all combinations
plates = generate_shear_plates(...)
welds = generate_fillet_welds(...)

# Optimize for minimum weight while meeting capacity
for plate_config in plates:
    for weld_config in welds:
        capacity = evaluate_connection(plate_config, weld_config)
        weight = plate_config['weight'] + weld_config['weight']
        if capacity >= required and weight < min_weight:
            best_config = (plate_config, weld_config)
```

### Enhanced Features to Add

1. **Intermittent Welds**
   - Already supported with `intermittent=True` parameter
   - Automatically adjusts capacity for effective length

2. **Weld Group Analysis**
   - Combine multiple welds
   - Calculate center of gravity
   - Check for torsion effects

3. **End Returns**
   - Add wrap-around welds
   - Improve edge conditions

4. **Weld Symbols**
   - Generate AWS weld symbols for drawings

## Performance

The weld generator maintains the same high performance as other generators:
- Generates 1000+ configurations in milliseconds
- Columnar NumPy arrays for Numba JIT compilation
- Integer mappings minimize memory usage
- Ready for optimization loops with 10,000+ combinations

## Compatibility

✅ Works with existing system:
- Bolt generator (generator_combination.py)
- Plate generator (plate_generator.py)
- Section selector (section_properties.py)
- Load path system (load_path.py)
- AISC limit states (aisc_14th.py)

✅ Consistent API:
- Same dict-of-arrays output format
- Same integer mapping pattern
- Same parameter naming conventions
- Same documentation style

## Summary

The weld generator completes your connection design toolkit:

**Before:** Section + Bolts + Plates
**Now:** Section + Bolts + Plates + **Welds**

You now have a complete system for designing structural steel connections with:
- AISC section selection
- Bolt configuration generation
- Plate member generation
- **Weld specification generation**
- Load path tracking
- Limit state evaluation

All components work together seamlessly with consistent APIs and efficient NumPy-based implementations!

---

**Questions or Issues?**
- See `WELD_GENERATOR_README.md` for quick start
- Check `test_speed.ipynb` for working examples
- Review `docs/weld_generator_guide.md` (to be created) for detailed documentation
