# Weld Generator System

## Quick Start

The weld generator provides a complete system for generating weld configurations in structural steel connections, following the same efficient pattern as your bolt and plate generators.

### Features

- **Multiple Weld Types**: Fillet, groove (CJP/PJP), plug, and slot welds
- **Integer Mappings**: Efficient electrode and weld type codes
- **Auto Properties**: Automatic calculation of throat, capacities
- **Columnar Output**: NumPy arrays for Numba compatibility
- **AISC Compliant**: Follows AISC 360 design provisions

## Basic Usage

```python
from steel_lib.weld_generator import generate_fillet_welds

# Generate fillet weld configurations
welds = generate_fillet_welds(
    electrode_id=[1],                  # E70XX
    weld_size=[0.25, 0.3125, 0.375],  # 1/4", 5/16", 3/8"
    weld_length=[12.0, 18.0],         # 12", 18"
    both_sides=[False, True]          # Single and double
)

# Output is dict of NumPy arrays
print(f"Generated {len(welds['weld_size'])} configurations")
print(f"Capacities: {welds['phi_R_n']} kips")
```

## Weld Type Mappings

```python
WELD_TYPE_MAP = {
    0: 'FILLET',              # Most common
    1: 'CJP',                 # Complete Joint Penetration
    2: 'PJP',                 # Partial Joint Penetration
    3: 'PLUG',                # Plug weld
    4: 'SLOT',                # Slot weld
    5: 'FILLET_BOTH',         # Fillet both sides
    6: 'FILLET_INTERMITTENT'  # Intermittent fillet
}

ELECTRODE_MAP = {
    0: 'E60XX',   # 60 ksi
    1: 'E70XX',   # 70 ksi (most common)
    2: 'E80XX',   # 80 ksi
    3: 'E90XX',   # 90 ksi
    4: 'E100XX',  # 100 ksi
    5: 'E110XX'   # 110 ksi
}
```

## Specialized Generators

### 1. Fillet Welds (Most Common)

```python
from steel_lib.weld_generator import generate_fillet_welds, STANDARD_FILLET_SIZES

# Use standard sizes
welds = generate_fillet_welds(
    electrode_id=[1],                    # E70XX
    weld_size=STANDARD_FILLET_SIZES,    # All 12 standard sizes
    weld_length=[12.0, 18.0, 24.0],
    both_sides=[False, True]
)

# Output includes:
# - weld_type, electrode, F_EXX, F_w
# - weld_size, weld_length, throat
# - R_n, phi_R_n (total capacity)
# - strength_per_inch, phi_strength_per_inch
```

### 2. Groove Welds (CJP and PJP)

```python
from steel_lib.weld_generator import generate_groove_welds

# Complete Joint Penetration (CJP) - full strength
welds = generate_groove_welds(
    electrode_id=[1],              # E70XX
    weld_type_id=[1],             # CJP
    plate_thickness=[0.5, 0.625], # Plate thickness
    weld_length=[12.0, 18.0]
)

# Partial Joint Penetration (PJP) - limited by throat
welds = generate_groove_welds(
    electrode_id=[1],
    weld_type_id=[2],             # PJP
    plate_thickness=[0.5],
    weld_length=[12.0],
    effective_throat=[0.25, 0.375]  # Effective throat
)
```

### 3. Plug and Slot Welds

```python
from steel_lib.weld_generator import generate_plug_slot_welds

# Plug welds
plugs = generate_plug_slot_welds(
    electrode_id=[1],
    weld_type_id=[3],             # PLUG
    diameter_or_width=[0.75, 1.0], # Hole diameter
    thickness=[0.5],
    n_welds=[4, 6, 8]             # Number of plugs
)

# Slot welds
slots = generate_plug_slot_welds(
    electrode_id=[1],
    weld_type_id=[4],             # SLOT
    diameter_or_width=[0.75],     # Slot width
    length=[3.0, 4.0],           # Slot length
    thickness=[0.5],
    n_welds=[2, 4]
)
```

## Weld Length Calculator

Quick utility for preliminary design:

```python
from steel_lib.weld_generator import calculate_weld_length_required

# How much weld length needed for 50 kip force?
L_required = calculate_weld_length_required(
    force=50.0,                # kips
    electrode_grade='E70XX',
    weld_size=0.3125,         # 5/16"
    both_sides=False
)

print(f"Need {L_required:.1f}\" of weld")
```

## Output Format

All generators return a dictionary of NumPy arrays:

```python
{
    'weld_type_id': array([0, 0, 0, ...]),        # Integer codes
    'electrode_id': array([1, 1, 1, ...]),
    'weld_type': array(['FILLET', 'FILLET', ...]), # String names
    'electrode': array(['E70XX', 'E70XX', ...]),
    'F_EXX': array([70.0, 70.0, ...]),            # ksi
    'F_w': array([42.0, 42.0, ...]),              # 0.6*F_EXX
    'weld_size': array([0.25, 0.25, ...]),        # inches
    'weld_length': array([12.0, 18.0, ...]),      # inches
    'throat': array([0.177, 0.177, ...]),         # effective throat
    'R_n': array([89.2, 133.9, ...]),             # nominal capacity (kips)
    'phi_R_n': array([66.9, 100.4, ...]),         # design capacity (kips)
    'strength_per_inch': array([7.43, 7.43, ...]), # k/in
    'phi_strength_per_inch': array([5.57, 5.57, ...]) # φ k/in
}
```

## Integration with Connection System

### Complete Shear Connection

```python
from steel_lib.generator_combination import generate_bolt_combinations
from steel_lib.plate_generator import generate_shear_plates
from steel_lib.weld_generator import generate_fillet_welds

# Bolts (beam side)
bolts = generate_bolt_combinations(
    bolt_diameter=[0.75],
    bolt_grade=[0],  # A325
    n_cols=[2],
    n_rows=[4, 5, 6],
    s_row=[3.0],
    s_col=[3.0]
)

# Shear plate
plates = generate_shear_plates(
    plate_grade_id=[1],  # A572-50
    thickness=[0.375, 0.5],
    width=[5.0, 6.0],
    length=[15.0, 18.0]
)

# Welds (column side)
welds = generate_fillet_welds(
    electrode_id=[1],  # E70XX
    weld_size=[0.3125, 0.375],
    weld_length=[15.0, 18.0],
    both_sides=[True]
)

# Find critical capacity for each combination
for i in range(len(bolts['n_bolts'])):
    for j in range(len(plates['thickness'])):
        for k in range(len(welds['weld_size'])):
            capacity = min(
                bolts['phi_R_n'][i],
                plates['phi_V_n_gross'][j],
                welds['phi_R_n'][k]
            )
            # Store viable combinations
```

### With Load Path System

```python
from steel_lib.load_path import LoadPathGenerator, LoadVector

# Create load path with weld element
generator = LoadPathGenerator()

# Applied load
applied_load = LoadVector(V_y=40.0)

# Create connection (automatically includes welds)
path = generator.create_simple_shear_connection(
    beam_section='W18X35',
    column_section='W14X90',
    bolt_config=bolts,
    plate_config=plates,
    weld_config=welds,
    applied_load=applied_load
)

# Evaluate
results = generator.evaluate_load_path(path)
print(f"Weld capacity: {results['WELDS_B']['capacity']:.1f} kips")
```

## AISC Design Provisions

### Fillet Welds (AISC J2.2)

- **Minimum size**: Table J2.4 based on material thickness
- **Maximum size**: 
  - For t < 1/4": max = t
  - For t ≥ 1/4": max = t - 1/16"
- **Effective throat**: 
  - Equal leg: throat = 0.707 × leg size
  - Unequal leg: throat = 0.707 × smaller leg
- **Design strength**: φR_n = 0.75 × F_w × A_we
- **F_w = 0.60 × F_EXX**

### Groove Welds (AISC J2.1)

- **CJP**: Full base metal strength
- **PJP**: Limited by effective throat
- **Effective throat**: Depends on groove angle and root opening
- **Design strength**: φR_n = 0.75 × F_BM × A_eff

### Standard Sizes

12 standard fillet weld sizes from 3/16" to 1":
```
3/16", 1/4", 5/16", 3/8", 7/16", 1/2", 9/16", 5/8", 11/16", 3/4", 7/8", 1"
```

## Advanced Features

### Intermittent Welds

```python
welds = generate_fillet_welds(
    electrode_id=[1],
    weld_size=[0.25],
    weld_length=[4.0],           # Length of each weld segment
    intermittent=[True],
    intermittent_pitch=[12.0]    # Center-to-center spacing
)
# Capacity automatically adjusted for effective length ratio
```

### Custom Electrode Matching

```python
# Match weld electrode to base metal
base_F_y = 50  # A572-50

if base_F_y <= 50:
    electrode_id = [1]  # E70XX
elif base_F_y <= 65:
    electrode_id = [2]  # E80XX
else:
    electrode_id = [3]  # E90XX
```

## See Also

- `docs/weld_generator_guide.md` - Comprehensive guide with all details
- `test_speed.ipynb` - Working examples and demonstrations
- `steel_lib/load_path.py` - Integration with load path system
- AISC 360 Chapter J - Connections specification

## Quick Reference

```python
# Get all mappings
from steel_lib.weld_generator import get_weld_mapping_info
mappings = get_weld_mapping_info()

# Common configurations
E70XX = 1                    # Most common electrode
FILLET = 0                   # Most common weld type
QUARTER_INCH = 0.25         # Common size
FIVE_SIXTEENTHS = 0.3125    # Common size

# Quick generation
welds = generate_fillet_welds(
    electrode_id=[E70XX],
    weld_size=[QUARTER_INCH, FIVE_SIXTEENTHS],
    weld_length=[12.0, 18.0, 24.0],
    both_sides=[False, True]
)
```
