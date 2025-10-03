# Load Path V2 - Migration Guide: Placeholder to AISC Calculations

## Overview

This guide explains how to replace the placeholder calculations in `load_path_v2.py` with actual AISC 360 limit state calculations from the `aisc_14th` module.

## Current Status

### Placeholder Functions (To Be Replaced)

| Function | Location | AISC Reference | Status |
|----------|----------|----------------|--------|
| `transfer_weld_to_plate()` | load_path_v2.py:52 | J2.4 | ⚠️ Placeholder |
| `transfer_bolts_shear()` | load_path_v2.py:90 | J3.6 | ⚠️ Placeholder |
| `check_bolt_bearing()` | load_path_v2.py:127 | J3.10 | ⚠️ Placeholder |
| `check_plate_shear_yielding()` | load_path_v2.py:178 | J4.2 | ⚠️ Placeholder |
| `check_block_shear()` | load_path_v2.py:216 | J4.3 | ⚠️ Placeholder |

### Existing AISC Functions (Ready to Use)

| Module | Functions | Status |
|--------|-----------|--------|
| `aisc_14th/bolt_shear_tension.py` | `bolt_shear()`, `calculation_area_bolt()` | ✅ Ready |
| `aisc_14th/bolt_bearing.py` | `bolt_bearing()`, `calculation_lc()` | ✅ Ready |
| `aisc_14th/block_shear.py` | `block_shear()` | ✅ Ready |
| `aisc_14th/shear_yielding_rupture.py` | `shear_yielding_rupture()` | ✅ Ready |

### Missing Functions (Need to Create)

| Function | Purpose | AISC Reference |
|----------|---------|----------------|
| Fillet weld shear | Weld capacity calculation | J2.4, Table J2.5 |

## Migration Steps

### Step 1: Update Bolt Shear Calculation

**Current Placeholder:**
```python
@njit
def transfer_bolts_shear(
    V_u: float,
    d_bolt: float,
    F_nv: float,
    N_r: int,
    N_c: int,
    N_shear_planes: int
) -> Tuple[float, float]:
    # PLACEHOLDER
    phi = 0.75
    n_bolts = N_r * N_c
    A_bolt = np.pi * (d_bolt ** 2) / 4.0
    capacity = phi * F_nv * A_bolt * N_shear_planes * n_bolts
    utilization = V_u / capacity if capacity > 0 else 999.0
    return capacity, utilization
```

**Replace With:**
```python
from steel_lib.aisc_14th.bolt_shear_tension import bolt_shear, calculation_area_bolt

@njit
def transfer_bolts_shear(
    V_u: float,
    d_bolt: float,
    F_nv: float,
    N_r: int,
    N_c: int,
    N_shear_planes: int
) -> Tuple[float, float]:
    """
    Calculate bolt group shear capacity.
    
    AISC 360-16 Section J3.6
    """
    phi = 0.75
    n_bolts = N_r * N_c
    
    # Calculate bolt area
    A_bolt = calculation_area_bolt(d_bolt)
    
    # Calculate bolt shear capacity
    capacity = bolt_shear(
        F_nv=F_nv,
        A_bolt=A_bolt,
        N_shear_planes=N_shear_planes,
        phi=phi
    )
    
    # Total capacity for bolt group
    capacity_total = capacity * n_bolts
    
    utilization = V_u / capacity_total if capacity_total > 0 else 999.0
    
    return capacity_total, utilization
```

### Step 2: Update Bolt Bearing Calculation

**Current Placeholder:**
```python
@njit
def check_bolt_bearing(
    V_u: float,
    d_bolt: float,
    t: float,
    F_u: float,
    L_ev: float,
    L_eh: float,
    S_r: float,
    S_c: float,
    N_r: int,
    N_c: int
) -> Tuple[float, float]:
    # PLACEHOLDER
    phi = 0.75
    n_bolts = N_r * N_c
    capacity_per_bolt = phi * 2.4 * d_bolt * t * F_u
    capacity = capacity_per_bolt * n_bolts
    utilization = V_u / capacity if capacity > 0 else 999.0
    return capacity, utilization
```

**Replace With:**
```python
from steel_lib.aisc_14th.bolt_bearing import bolt_bearing

@njit
def check_bolt_bearing(
    V_u: float,
    d_bolt: float,
    t: float,
    F_u: float,
    L_ev: float,
    L_eh: float,
    S_r: float,
    S_c: float,
    N_r: int,
    N_c: int
) -> Tuple[float, float]:
    """
    Check bolt bearing on plate or member.
    
    AISC 360-16 Section J3.10
    """
    phi = 0.75
    
    # Calculate hole diameter (standard holes)
    d_v = d_bolt + 0.0625  # 1/16" clearance
    d_h = d_bolt + 0.0625
    
    # Use bolt_bearing function from aisc_14th
    # Note: bolt_bearing handles the entire bolt group
    capacity = bolt_bearing(
        F_u=F_u,
        d_bolt=d_bolt,
        t=t,
        P_u=0.0,  # Pure shear, no axial
        V_u=V_u,
        S_r=S_r,
        N_r=N_r,
        S_c=S_c,
        N_c=N_c,
        L_ev=L_ev,
        L_eh=L_eh,
        d_v=d_v,
        d_h=d_h,
        phi=phi,
        c=1.0  # Load distribution factor
    )
    
    utilization = V_u / capacity if capacity > 0 else 999.0
    
    return capacity, utilization
```

**Important Note:** Check the exact signature of `bolt_bearing()` in your `aisc_14th` module and adjust parameters accordingly.

### Step 3: Update Plate Shear Yielding/Rupture

**Current Placeholder:**
```python
@njit
def check_plate_shear_yielding(
    V_u: float,
    t: float,
    width: float,
    F_y: float,
    F_u: float
) -> Tuple[float, float, float]:
    # PLACEHOLDER
    phi_y = 1.0
    phi_u = 0.75
    A_g = t * width
    capacity_yielding = phi_y * 0.6 * F_y * A_g
    capacity_rupture = phi_u * 0.6 * F_u * A_g
    capacity = min(capacity_yielding, capacity_rupture)
    utilization = V_u / capacity if capacity > 0 else 999.0
    return capacity_yielding, capacity_rupture, utilization
```

**Replace With:**
```python
from steel_lib.aisc_14th.shear_yielding_rupture import shear_yielding_rupture

@njit
def check_plate_shear_yielding(
    V_u: float,
    t: float,
    width: float,
    F_y: float,
    F_u: float
) -> Tuple[float, float, float]:
    """
    Check plate shear yielding and rupture.
    
    AISC 360-16 Section J4.2
    """
    # For plate without bolt holes (gross area = net area)
    # If checking plate with holes, need to account for hole deductions
    
    capacity = shear_yielding_rupture(
        F_y=F_y,
        F_u=F_u,
        t=t,
        d_bolt=0.0,  # No holes for conservative check, or provide actual
        N_r=0,       # No bolt rows yet, or provide actual
        L_ev=width,  # Use plate width as effective length
        S_r=0.0,     # Not applicable for gross area check
        coped=0,     # Not coped
        n_members=1,
        phi_y=1.0,
        phi_u=0.75
    )
    
    # Function returns combined capacity
    # For detailed yielding vs rupture, need to call separately
    # or extract from function internals
    
    utilization = V_u / capacity if capacity > 0 else 999.0
    
    # Return same capacity for both (conservative)
    return capacity, capacity, utilization
```

**Note:** You may need to review the exact implementation of `shear_yielding_rupture()` to ensure proper usage.

### Step 4: Update Block Shear Calculation

**Current Placeholder:**
```python
@njit
def check_block_shear(
    V_u: float,
    t: float,
    F_y: float,
    F_u: float,
    L_ev: float,
    L_eh: float,
    S_r: float,
    N_r: int,
    d_v: float
) -> Tuple[float, float]:
    # PLACEHOLDER
    phi = 0.75
    L_t = L_eh
    A_nt = (L_t - 0.5 * d_v) * t
    L_v = L_ev + (N_r - 1) * S_r
    A_nv = (L_v - (N_r - 0.5) * d_v) * t
    A_gv = L_v * t
    term1 = 0.6 * F_u * A_nv + 1.0 * F_u * A_nt
    term2 = 0.6 * F_y * A_gv + 1.0 * F_u * A_nt
    capacity = phi * min(term1, term2)
    utilization = V_u / capacity if capacity > 0 else 999.0
    return capacity, utilization
```

**Replace With:**
```python
from steel_lib.aisc_14th.block_shear import block_shear

@njit
def check_block_shear(
    V_u: float,
    t: float,
    F_y: float,
    F_u: float,
    L_ev: float,
    L_eh: float,
    S_r: float,
    N_r: int,
    d_v: float
) -> Tuple[float, float]:
    """
    Check block shear rupture along bolt pattern.
    
    AISC 360-16 Section J4.3
    """
    phi = 0.75
    
    # Calculate block shear capacity
    capacity = block_shear(
        F_y=F_y,
        F_u=F_u,
        t=t,
        P_u=0.0,     # Pure shear, no tension
        V_u=V_u,
        d_bolt=d_v - 0.0625,  # Back-calculate bolt diameter from hole
        d_v=d_v,
        d_h=d_v,     # Assume same hole size both directions
        N_r=N_r,
        N_c=1,       # Typical single column for shear tab
        S_r=S_r,
        S_c=0.0,     # Not applicable for single column
        L_ev=L_ev,
        L_eh=L_eh,
        coped=0,     # Not coped
        n_members=1,
        phi=phi
    )
    
    utilization = V_u / capacity if capacity > 0 else 999.0
    
    return capacity, utilization
```

### Step 5: Create Weld Shear Function

**This function doesn't exist yet in `aisc_14th` module, so create it:**

**File:** `steel_lib/aisc_14th/weld_shear.py`

```python
"""
Fillet Weld Shear Capacity
AISC 360-16 Section J2.4, Table J2.5
"""

import numpy as np
from numba import njit
from .utils import optional_reporting_handcalc, detailed


@njit
def fillet_weld_shear_capacity(
    weld_size: float,
    L: float,
    FEXX: float,
    phi: float = 0.75
) -> float:
    """
    Calculate fillet weld shear capacity.
    
    AISC 360-16 Table J2.5
    
    Args:
        weld_size: Fillet weld size (inches)
        L: Effective weld length (inches)
        FEXX: Electrode classification strength (ksi)
        phi: Resistance factor (default 0.75)
        
    Returns:
        Design shear capacity (kips)
        
    Notes:
        - Assumes linear weld loaded in shear
        - Effective throat = 0.707 * weld_size
        - Nominal stress = 0.60 * FEXX
        - Does not include effective length reduction for long welds
    """
    # Effective throat thickness
    t_e = 0.707 * weld_size
    
    # Nominal stress on effective area
    F_w = 0.60 * FEXX
    
    # Nominal shear capacity per inch
    R_nw_per_inch = F_w * t_e
    
    # Total nominal capacity
    R_nw = R_nw_per_inch * L
    
    # Design capacity
    R_design = phi * R_nw
    
    return R_design


@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def fillet_weld_shear(
    weld_size: float,
    L: float,
    FEXX: float,
    n_welds: int = 1,
    phi: float = 0.75
) -> float:
    """
    Calculate total fillet weld shear capacity for multiple welds.
    
    Args:
        weld_size: Fillet weld size (inches)
        L: Effective weld length per weld (inches)
        FEXX: Electrode classification strength (ksi)
        n_welds: Number of parallel welds (default 1)
        phi: Resistance factor (default 0.75)
        
    Returns:
        Total design shear capacity (kips)
    """
    capacity_per_weld = fillet_weld_shear_capacity(
        weld_size=weld_size,
        L=L,
        FEXX=FEXX,
        phi=phi
    )
    
    total_capacity = capacity_per_weld * n_welds
    
    return total_capacity
```

**Then update the placeholder in load_path_v2.py:**

```python
from steel_lib.aisc_14th.weld_shear import fillet_weld_shear_capacity

@njit
def transfer_weld_to_plate(
    V_u: float,
    weld_size: float,
    weld_length: float,
    electrode_strength: float,
    both_sides: bool
) -> Tuple[float, float]:
    """
    Calculate load transfer through fillet weld.
    
    AISC 360-16 Section J2.4
    """
    phi = 0.75
    n_welds = 2.0 if both_sides else 1.0
    
    # Calculate capacity using AISC function
    capacity = fillet_weld_shear_capacity(
        weld_size=weld_size,
        L=weld_length,
        FEXX=electrode_strength,
        phi=phi
    )
    
    # Total capacity for all welds
    capacity_total = capacity * n_welds
    
    utilization = V_u / capacity_total if capacity_total > 0 else 999.0
    
    return capacity_total, utilization
```

## Testing After Migration

### Unit Tests

After replacing each placeholder, run unit tests:

```python
def test_bolt_shear_after_migration():
    """Verify bolt shear calculation matches AISC examples."""
    V_u = 40.0
    d_bolt = 0.75
    F_nv = 48.0  # A325-N
    N_r = 4
    N_c = 1
    N_shear_planes = 1
    
    capacity, util = transfer_bolts_shear(
        V_u, d_bolt, F_nv, N_r, N_c, N_shear_planes
    )
    
    # Expected capacity from hand calc:
    # A_bolt = π * 0.75² / 4 = 0.442 in²
    # Capacity = 0.75 * 48.0 * 0.442 * 1 * 4 = 63.6 kips
    expected_capacity = 63.6
    
    assert abs(capacity - expected_capacity) < 1.0  # Within 1 kip
```

### Integration Tests

Test complete interfaces after migration:

```python
def test_bolt_interface_after_migration():
    """Test bolt interface with actual AISC calculations."""
    # Setup
    bolt_config = {
        'bolt_size': 0.75,
        'F_nv': 48.0,
        'F_nt': 90.0,
        'N_r': 4,
        'N_c': 1,
        'S_r': 3.0,
        'L_ev': 1.5,
        'L_eh': 2.0,
        'd_v': 0.8125,
        'd_h': 0.8125,
    }
    
    plate_config = {
        'thickness': 0.375,
        'width': 5.0,
        'F_y': 50.0,
        'F_u': 65.0,
    }
    
    column_config = {
        'tw': 0.44,
        'F_u': 65.0,
    }
    
    interface = BoltInterface(bolt_config, plate_config, column_config)
    result = interface.evaluate(V_u=40.0)
    
    # Should pass with reasonable utilization
    assert result['is_adequate'] == True
    assert 0.5 < result['utilization'] < 1.0
```

### Validation Against AISC Examples

Compare with published design examples:

```python
def test_aisc_design_example_10_1():
    """
    Validate against AISC Design Example 10.1
    Simple Shear Connection - Bolted/Welded
    """
    # Setup from AISC example
    beam = aisc['get_section_with_material']('W18X35', material='A992')
    column = aisc['get_section_with_material']('W14X90', material='A992')
    
    plate_config = {
        'thickness': 0.375,
        'width': 5.0,
        'length': 17.5,
        'F_y': 50.0,
        'F_u': 65.0,
    }
    
    weld_config = {
        'weld_size': 0.25,
        'weld_length': 17.5,
        'electrode_id': 1,  # E70XX
        'both_sides': True,
    }
    
    bolt_config = {
        'bolt_size': 0.75,
        'F_nv': 48.0,
        'F_nt': 90.0,
        'N_r': 6,
        'N_c': 1,
        'S_r': 3.0,
        'L_ev': 1.5,
        'L_eh': 2.0,
        'd_v': 0.8125,
        'd_h': 0.8125,
    }
    
    connection = SimpleShearConnection(
        beam_section=beam,
        plate_config=plate_config,
        weld_config=weld_config,
        bolt_config=bolt_config,
        column_section=column
    )
    
    V_u = 52.0  # Applied load from example
    result = connection.evaluate(V_u)
    
    # Compare with AISC example results
    # (values from AISC Steel Construction Manual)
    assert result['is_adequate'] == True
    
    # Check specific limit states match
    bolt_result = result['interface_results'][1]
    
    # Example: Bolt shear should control at ~0.89 utilization
    if bolt_result['controlling_limit_state'] == 'bolt_shear':
        assert abs(bolt_result['utilization'] - 0.89) < 0.05
```

## Migration Checklist

- [ ] **Step 1**: Update `transfer_bolts_shear()` with `bolt_shear()`
  - [ ] Import from `aisc_14th.bolt_shear_tension`
  - [ ] Replace calculation
  - [ ] Run unit tests
  
- [ ] **Step 2**: Update `check_bolt_bearing()` with `bolt_bearing()`
  - [ ] Import from `aisc_14th.bolt_bearing`
  - [ ] Verify parameter mapping
  - [ ] Replace calculation
  - [ ] Run unit tests
  
- [ ] **Step 3**: Update `check_plate_shear_yielding()` with `shear_yielding_rupture()`
  - [ ] Import from `aisc_14th.shear_yielding_rupture`
  - [ ] Handle net area vs gross area
  - [ ] Replace calculation
  - [ ] Run unit tests
  
- [ ] **Step 4**: Update `check_block_shear()` with `block_shear()`
  - [ ] Import from `aisc_14th.block_shear`
  - [ ] Verify tension/shear plane calculations
  - [ ] Replace calculation
  - [ ] Run unit tests
  
- [ ] **Step 5**: Create and integrate weld shear function
  - [ ] Create `aisc_14th/weld_shear.py`
  - [ ] Implement `fillet_weld_shear_capacity()`
  - [ ] Add to `aisc_14th/__init__.py`
  - [ ] Update `transfer_weld_to_plate()`
  - [ ] Run unit tests
  
- [ ] **Step 6**: Run integration tests
  - [ ] Test `WeldInterface`
  - [ ] Test `BoltInterface`
  - [ ] Test `SimpleShearConnection`
  
- [ ] **Step 7**: Run validation tests
  - [ ] Compare with AISC Design Examples
  - [ ] Verify utilization ratios
  - [ ] Check controlling limit states
  
- [ ] **Step 8**: Performance benchmarking
  - [ ] Compare speed before/after
  - [ ] Verify numba compilation works
  - [ ] Check batch evaluation performance
  
- [ ] **Step 9**: Update documentation
  - [ ] Update README with actual AISC references
  - [ ] Remove "placeholder" notes
  - [ ] Add validation examples
  
- [ ] **Step 10**: Final validation
  - [ ] Run all tests
  - [ ] Verify against multiple AISC examples
  - [ ] Benchmark performance

## Common Issues and Solutions

### Issue 1: Import Errors with Numba

**Problem:** `aisc_14th` functions use decorators that aren't compatible with `@njit`

**Solution:** 
- Remove decorators when importing for numba functions
- Or create numba-specific versions without decorators
- Example:
  ```python
  # In aisc_14th module, provide both versions:
  
  @optional_reporting_handcalc(...)
  def bolt_shear(F_nv, A_bolt, N_shear_planes, phi):
      return _bolt_shear_core(F_nv, A_bolt, N_shear_planes, phi)
  
  @njit  # Numba-compatible version
  def _bolt_shear_core(F_nv, A_bolt, N_shear_planes, phi):
      V_n = F_nv * A_bolt * N_shear_planes
      V_u = phi * V_n
      return V_u
  ```

### Issue 2: Parameter Mismatch

**Problem:** `aisc_14th` function expects parameters in different order/names

**Solution:**
- Create adapter function that maps parameters
- Example:
  ```python
  @njit
  def check_bolt_bearing(V_u, d_bolt, t, F_u, ...):
      # Map to aisc_14th parameter names
      capacity = _bolt_bearing_core(
          F_u=F_u,
          d=d_bolt,  # Different parameter name
          thickness=t,  # Different parameter name
          ...
      )
      return capacity, V_u / capacity
  ```

### Issue 3: Return Type Mismatch

**Problem:** `aisc_14th` function returns single value, need (capacity, utilization)

**Solution:**
- Wrap function to return tuple
- Example:
  ```python
  @njit
  def check_limit_state(V_u, param1, param2):
      capacity = aisc_function(param1, param2)
      utilization = V_u / capacity if capacity > 0 else 999.0
      return capacity, utilization
  ```

## Summary

After completing this migration:

✅ All calculations will use actual AISC 360 formulas  
✅ Results will match AISC Design Examples  
✅ Code will reference specific AISC sections  
✅ System maintains numba compatibility  
✅ Performance remains optimized  

The placeholder functions provided a working system architecture while allowing development to proceed. Now they can be systematically replaced with production-ready AISC calculations.
