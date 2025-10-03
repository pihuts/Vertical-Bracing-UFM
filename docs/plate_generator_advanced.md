# Advanced Plate Generator Integration Examples

## 1. Complete Connection Design Space Generator

Combine sections, plates, and bolts for comprehensive connection design:

```python
import numpy as np
from steel_lib.section_properties import create_aisc_section_selector
from steel_lib.plate_generator import generate_shear_plates
from steel_lib.generator_combination import generate_bolt_configurations

def generate_connection_design_space(
    beam_criteria,
    plate_params,
    bolt_params
):
    """
    Generate complete design space for simple shear connections.
    
    Returns all combinations of beams × plates × bolts for optimization.
    """
    # Load AISC sections
    aisc = create_aisc_section_selector('aisc-shapes-database-v16.0.xlsx')
    beams = aisc['select_by_properties'](beam_criteria)
    
    # Generate plates
    plates = generate_shear_plates(**plate_params)
    
    # Generate bolts
    bolts = generate_bolt_configurations(**bolt_params)
    
    # Calculate total design space
    n_total = beams['count'] * len(plates['thickness']) * len(bolts['bolt_size'])
    
    return {
        'beams': beams,
        'plates': plates,
        'bolts': bolts,
        'total_combinations': n_total
    }

# Usage
design_space = generate_connection_design_space(
    beam_criteria={'W': {'min': 15, 'max': 30}},
    plate_params={
        'plate_grade_id': [1],
        'thickness': [0.25, 0.375, 0.5],
        'width': [5.0, 5.5],
        'length': [15.0, 18.0]
    },
    bolt_params={
        'bolt_size': np.array([0.75, 0.875], dtype=np.float64),
        'bolt_grade_id': np.array([0], dtype=np.int64),
        'member_a_BHT_id': np.array([0], dtype=np.int64),
        'member_b_BHT_id': np.array([0], dtype=np.int64),
        'N_r': np.array([3, 4], dtype=np.int64),
        'S_r': np.array([3.0], dtype=np.float64),
        'N_c': np.array([1], dtype=np.int64),
        'S_c': np.array([3.0], dtype=np.float64),
        'L_ev': np.array([1.25, 1.5], dtype=np.float64),
        'L_eh': np.array([1.5], dtype=np.float64),
        'Ga': np.array([0.0], dtype=np.float64)
    }
)

print(f"Total design space: {design_space['total_combinations']:,} combinations")
```

## 2. Batch Capacity Evaluation with Plates

Extend your existing Numba-accelerated limit state functions:

```python
import numpy as np
from numba import njit, prange
from steel_lib.aisc_14th import bolt_bearing, block_shear, shear_yielding_rupture

@njit(parallel=True)
def evaluate_plate_connection_capacity(
    # Plate properties
    plate_F_y, plate_F_u, plate_t,
    # Bolt properties
    bolt_d, bolt_F_nv, bolt_N_r, bolt_S_r, bolt_L_ev, bolt_L_eh,
    # Loading
    P_u, V_u,
    # Results arrays
    results_bearing, results_block, results_syr,
    num_cases
):
    """
    Vectorized capacity evaluation for plate connections.
    """
    for i in prange(num_cases):
        # Bolt bearing on plate
        results_bearing[i] = bolt_bearing(
            F_u=plate_F_u[i],
            d_bolt=bolt_d[i],
            t=plate_t[i],
            P_u=P_u[i],
            V_u=V_u[i],
            S_r=bolt_S_r[i],
            N_r=bolt_N_r[i],
            S_c=3.0,
            N_c=1,
            L_ev=bolt_L_ev[i],
            L_eh=bolt_L_eh[i],
            d_v=bolt_d[i] + 0.0625,
            d_h=bolt_d[i] + 0.0625,
            phi=0.75,
            c=4.0
        )
        
        # Block shear on plate
        results_block[i] = block_shear(
            P_u=P_u[i],
            V_u=V_u[i],
            F_y=plate_F_y[i],
            F_u=plate_F_u[i],
            t=plate_t[i],
            N_r=bolt_N_r[i],
            S_r=bolt_S_r[i],
            N_c=1,
            S_c=3.0,
            L_ev=bolt_L_ev[i],
            L_eh=bolt_L_eh[i],
            d_v=bolt_d[i] + 0.0625,
            d_h=bolt_d[i] + 0.0625,
            phi=0.75,
            coped=0
        )
        
        # Shear yielding/rupture
        syr = shear_yielding_rupture(
            N_r=bolt_N_r[i],
            S_r=bolt_S_r[i],
            L_ev=bolt_L_ev[i],
            t=plate_t[i],
            d_b=bolt_d[i],
            F_y=plate_F_y[i],
            F_u=plate_F_u[i],
            phi=0.75,
            n_members=1,
            coped=0
        )
        results_syr[i] = syr if syr is not None else np.nan
    
    return results_bearing, results_block, results_syr

# Usage
n = len(plates['F_y'])
results_bearing = np.zeros(n)
results_block = np.zeros(n)
results_syr = np.zeros(n)

P_u = np.full(n, 10.0)  # 10 kip axial
V_u = np.full(n, 50.0)  # 50 kip shear

evaluate_plate_connection_capacity(
    plates['F_y'], plates['F_u'], plates['thickness'],
    bolts['bolt_size'], bolts['F_nv'], bolts['N_r'], 
    bolts['S_r'], bolts['L_ev'], bolts['L_eh'],
    P_u, V_u,
    results_bearing, results_block, results_syr,
    n
)
```

## 3. Optimized Plate Selection

Find minimum weight plate that meets capacity requirements:

```python
def select_optimal_plate(
    required_capacity,
    plate_type='shear',
    grade_preference=[1, 0],  # Prefer A572_50, then A36
    max_thickness=0.75
):
    """
    Select lightest plate meeting capacity requirements.
    """
    from steel_lib.plate_generator import (
        generate_shear_plates, 
        STANDARD_PLATE_THICKNESSES
    )
    
    # Generate candidate plates
    thicknesses = STANDARD_PLATE_THICKNESSES[
        STANDARD_PLATE_THICKNESSES <= max_thickness
    ]
    
    if plate_type == 'shear':
        plates = generate_shear_plates(
            plate_grade_id=grade_preference,
            thickness=thicknesses.tolist(),
            width=[5.0, 5.5, 6.0],
            length=[15.0, 18.0, 24.0]
        )
        capacity_key = 'phi_V_n_gross'
    
    # Filter by capacity
    sufficient = plates[capacity_key] >= required_capacity
    
    if not sufficient.any():
        return None
    
    # Find minimum weight
    weights = plates['total_weight'][sufficient]
    min_idx = np.argmin(weights)
    
    # Extract optimal configuration
    optimal = {
        key: values[sufficient][min_idx]
        for key, values in plates.items()
    }
    
    return optimal

# Usage
optimal_plate = select_optimal_plate(
    required_capacity=40.0,  # kips
    plate_type='shear',
    max_thickness=0.625
)

print(f"Optimal: {optimal_plate['plate_grade']} "
      f"PL {optimal_plate['width']:.2f}\"x{optimal_plate['thickness']:.3f}\"x{optimal_plate['length']:.1f}\" "
      f"({optimal_plate['total_weight']:.2f} lb)")
```

## 4. Connection Factory Integration

Add plate generation to your connection factory:

```python
# In connection_factory.py

from steel_lib.plate_generator import (
    generate_shear_plates,
    generate_flange_plates,
    generate_stiffener_plates,
    generate_gusset_plates
)

class ConnectionFactory:
    """Factory for generating and evaluating steel connections."""
    
    def __init__(self, aisc_database_path):
        self.aisc = create_aisc_section_selector(aisc_database_path)
        self.plate_cache = {}
        self.bolt_cache = {}
    
    def generate_simple_shear_connection(
        self,
        beam_designation,
        reaction,  # kips
        eccentricity=0.0
    ):
        """Generate all viable simple shear connections for given beam."""
        
        # Get beam properties
        beam = self.aisc['get_properties'](beam_designation)
        
        # Determine plate parameters from beam
        min_width = beam['tw'] * 12  # Rule of thumb
        max_length = beam['d'] - 2 * beam['tf']
        
        # Generate candidate plates
        plates = generate_shear_plates(
            plate_grade_id=[0, 1],  # A36 and A572_50
            thickness=[0.25, 0.375, 0.5],
            width=np.arange(min_width, min_width + 2, 0.5).tolist(),
            length=np.arange(12, max_length, 3).tolist()
        )
        
        # Generate candidate bolt patterns
        # (bolt generation code here)
        
        # Evaluate all combinations
        # (capacity evaluation here)
        
        return {
            'beam': beam,
            'plates': plates,
            'bolts': bolts,
            'capacities': capacities
        }
    
    def generate_moment_connection(
        self,
        beam_designation,
        column_designation,
        moment,  # kip-in
        shear   # kips
    ):
        """Generate FR moment connection configurations."""
        
        beam = self.aisc['get_properties'](beam_designation)
        column = self.aisc['get_properties'](column_designation)
        
        # Flange plates
        flange_plates = generate_flange_plates(
            plate_grade_id=[1, 2],  # A572_50 and A992
            thickness=[0.75, 1.0, 1.25, 1.5],
            width=np.arange(beam['bf'], beam['bf'] + 4, 1).tolist(),
            length=[15.0, 18.0, 24.0]
        )
        
        # Shear plate/tab
        shear_plates = generate_shear_plates(
            plate_grade_id=[1],
            thickness=[0.375, 0.5],
            width=[5.0, 5.5],
            length=np.arange(12, beam['d'] - 2*beam['tf'], 3).tolist()
        )
        
        return {
            'beam': beam,
            'column': column,
            'flange_plates': flange_plates,
            'shear_plates': shear_plates
        }
```

## 5. Parametric Study Generator

Create parametric studies efficiently:

```python
def parametric_plate_thickness_study(
    base_params,
    thickness_range
):
    """
    Study effect of plate thickness on connection capacity.
    """
    from steel_lib.plate_generator import generate_shear_plates
    
    results = []
    
    for t in thickness_range:
        # Generate plates with current thickness
        plates = generate_shear_plates(
            **{**base_params, 'thickness': [t]}
        )
        
        # Evaluate capacity
        # (capacity calculation here)
        
        results.append({
            'thickness': t,
            'capacity': plates['phi_V_n_gross'][0],
            'weight': plates['total_weight'][0],
            'cost_index': plates['total_weight'][0] * 1.2  # $/lb factor
        })
    
    return results

# Usage
study = parametric_plate_thickness_study(
    base_params={
        'plate_grade_id': [1],
        'width': [5.5],
        'length': [18.0]
    },
    thickness_range=np.arange(0.25, 1.0, 0.0625)
)

# Plot results
import matplotlib.pyplot as plt
t = [r['thickness'] for r in study]
cap = [r['capacity'] for r in study]
cost = [r['cost_index'] for r in study]

fig, ax1 = plt.subplots()
ax1.plot(t, cap, 'b-', label='Capacity')
ax1.set_xlabel('Thickness (in)')
ax1.set_ylabel('Capacity (kips)', color='b')

ax2 = ax1.twinx()
ax2.plot(t, cost, 'r-', label='Cost Index')
ax2.set_ylabel('Cost Index', color='r')

plt.title('Plate Thickness Parametric Study')
plt.show()
```

## 6. Database Export

Convert configurations to structured database format:

```python
import pandas as pd
import sqlite3

def export_plates_to_database(
    plates,
    db_path='connection_database.db',
    table_name='shear_plates'
):
    """
    Export plate configurations to SQLite database.
    """
    # Convert to DataFrame
    df = pd.DataFrame(plates)
    
    # Add unique ID
    df.insert(0, 'plate_id', range(1, len(df) + 1))
    
    # Add timestamp
    df['created_at'] = pd.Timestamp.now()
    
    # Write to database
    conn = sqlite3.connect(db_path)
    df.to_sql(table_name, conn, if_exists='append', index=False)
    conn.close()
    
    print(f"Exported {len(df)} plates to {db_path}")

def query_plates_from_database(
    db_path,
    table_name,
    min_capacity=None,
    max_weight=None,
    grade=None
):
    """
    Query plates from database with filters.
    """
    conn = sqlite3.connect(db_path)
    
    query = f"SELECT * FROM {table_name} WHERE 1=1"
    params = []
    
    if min_capacity:
        query += " AND phi_V_n_gross >= ?"
        params.append(min_capacity)
    
    if max_weight:
        query += " AND total_weight <= ?"
        params.append(max_weight)
    
    if grade:
        query += " AND plate_grade = ?"
        params.append(grade)
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    
    return df
```

## 7. Connection Reporting

Generate formatted reports with plate specifications:

```python
def generate_connection_report(
    connection_id,
    beam,
    plate,
    bolts,
    capacities
):
    """
    Generate formatted connection design report.
    """
    from datetime import datetime
    
    report = f"""
SIMPLE SHEAR CONNECTION DESIGN REPORT
Connection ID: {connection_id}
Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}

{'='*70}
BEAM SPECIFICATION
{'='*70}
Designation: {beam['designation']}
Depth: {beam['d']:.2f} in
Web Thickness: {beam['tw']:.3f} in

{'='*70}
CONNECTION PLATE
{'='*70}
Material: {plate['plate_grade']}
Size: PL {plate['width']:.2f}" × {plate['thickness']:.3f}" × {plate['length']:.1f}"
Weight: {plate['total_weight']:.2f} lb

Material Properties:
  F_y = {plate['F_y']:.0f} ksi
  F_u = {plate['F_u']:.0f} ksi
  E = {plate['E']:.0f} ksi

{'='*70}
BOLT PATTERN
{'='*70}
Size: {bolts['bolt_size']:.3f}" φ {bolts['bolt_grade']}
Pattern: {bolts['N_r']}×{bolts['N_c']} @ {bolts['S_r']:.1f}" o.c.
Edge Distance: L_ev = {bolts['L_ev']:.2f}", L_eh = {bolts['L_eh']:.2f}"

Bolt Strength:
  F_nv = {bolts['F_nv']:.1f} ksi
  F_nt = {bolts['F_nt']:.1f} ksi

{'='*70}
DESIGN CAPACITIES
{'='*70}
Bolt Bearing:     φR_n = {capacities['bearing']:.1f} kips
Block Shear:      φR_n = {capacities['block_shear']:.1f} kips
Shear Yield/Rupt: φR_n = {capacities['shear_yr']:.1f} kips

GOVERNING CAPACITY: {min(capacities.values()):.1f} kips

{'='*70}
"""
    return report

# Usage
report = generate_connection_report(
    connection_id='SC-001',
    beam={'designation': 'W18X35', 'd': 17.7, 'tw': 0.300},
    plate=optimal_plate,
    bolts={...},
    capacities={'bearing': 45.2, 'block_shear': 52.1, 'shear_yr': 48.3}
)

print(report)

# Save to file
with open(f'connection_report_{connection_id}.txt', 'w') as f:
    f.write(report)
```

## 8. Multi-Plate Assembly Generator

Generate complex multi-plate assemblies:

```python
def generate_gusset_assembly(
    brace_force,
    brace_angle,
    beam_depth,
    column_width
):
    """
    Generate complete gusset plate assembly with stiffeners.
    """
    from steel_lib.plate_generator import (
        generate_gusset_plates,
        generate_stiffener_plates
    )
    
    # Main gusset plate
    gusset = generate_gusset_plates(
        plate_grade_id=[1],  # A572_50
        thickness=[0.5, 0.625, 0.75],
        width=[18.0, 24.0, 30.0],
        length=[18.0, 24.0, 30.0],
        angle=[brace_angle]
    )
    
    # Beam web stiffeners (if needed)
    beam_stiffeners = generate_stiffener_plates(
        plate_grade_id=[1],
        thickness=[0.375, 0.5],
        width=np.arange(3, 7, 0.5).tolist(),
        height=[beam_depth - 1.0]  # Account for fillets
    )
    
    # Column stiffeners (if needed)
    column_stiffeners = generate_stiffener_plates(
        plate_grade_id=[1],
        thickness=[0.375, 0.5],
        width=np.arange(3, column_width/2, 0.5).tolist(),
        height=[8.0, 10.0, 12.0]
    )
    
    return {
        'gusset': gusset,
        'beam_stiffeners': beam_stiffeners,
        'column_stiffeners': column_stiffeners,
        'total_weight': (
            gusset['total_weight'] + 
            2 * beam_stiffeners['total_weight'] +  # Both sides
            2 * column_stiffeners['total_weight']   # Both sides
        )
    }
```

## Summary

The plate generator system provides:

1. **Consistent API** - Same pattern as bolts and sections
2. **High Performance** - NumPy arrays ready for Numba
3. **Comprehensive** - All plate types for structural connections
4. **Composable** - Easy integration with existing systems
5. **Extensible** - Add custom plate types as needed

Use these patterns to build sophisticated connection design and optimization tools!
