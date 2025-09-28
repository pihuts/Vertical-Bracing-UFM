import itertools
import numpy as np
from .materials import BOLT_GRADES

# Efficient integer mappings for categorical data
BOLT_GRADE_MAP = {
    0: 'a325_n',
    1: 'a325_x', 
    2: 'a490_n',
    3: 'a490_x'
}

HOLE_TYPE_MAP = {
    0: 'STD',  # Standard
    1: 'OVS',  # Oversize
    2: 'SSL',  # Short slotted longitudinal
    3: 'SST'   # Short slotted transverse
}

def generate_combinations_dict(**kwargs):
    """
    Generates a single dictionary containing all combinations as columnar arrays.

    This is ideal for unpacking into functions or creating a Pandas DataFrame.

    Args:
        **kwargs: A collection of keyword arguments (e.g., param1=arr1, param2=arr2).
                  The values should be array-like (lists, NumPy arrays, etc.).

    Returns:
        A single dictionary where keys are the original parameter names and
        values are 1D NumPy arrays containing the values for that parameter
        across all combinations.
    """
    # 1. Capture the parameter names (keys) and their corresponding arrays (values)
    keys = list(kwargs.keys())
    value_arrays = list(kwargs.values())

    # Handle the edge case of no input
    if not value_arrays:
        return {}
        
    # 2. Generate all combination rows using itertools.product
    # This creates an efficient iterator
    combinations_iterator = itertools.product(*value_arrays)
    
    # 3. Convert the iterator of rows into a 2D NumPy array
    # This is a key step: it arranges the data like a table.
    # We need to determine the data type to handle mixes of numbers/strings.
    # np.array() is smart about this and will choose a common type (like '<U32' for strings).
    combinations_array = np.array(list(combinations_iterator))

    # 4. Handle the edge case where there are no combinations (e.g., an empty input list)
    if combinations_array.size == 0:
        return {key: np.array([]) for key in keys}

    # 5. Transpose the array. This is the magic step.
    # It pivots the data from rows of combinations to columns of parameters.
    # (Rows, Columns) -> (Columns, Rows)
    transposed_array = combinations_array.T
    
    # 6. Create the final dictionary by zipping the original keys
    # with the new columnar arrays.
    return dict(zip(keys, transposed_array))


def generate_bolt_configurations(bolt_size, bolt_grade_id, member_a_BHT_id, member_b_BHT_id, 
                                N_r, S_r, N_c, S_c, L_ev, L_eh, Ga):
    """
    Generates all combinations of bolt configuration parameters using integer inputs for efficiency.
    Automatically includes F_nv and F_nt strength values based on bolt grades.
    
    Args:
        bolt_size: Array-like of bolt sizes as integers (e.g., [16, 20, 24])
        bolt_grade_id: Array-like of bolt grade IDs as integers (e.g., [0, 1, 2] for a325_n, a325_x, a490_n)
        member_a_BHT_id: Array-like of member A hole type IDs (e.g., [0, 1] for STD, OVS)
        member_b_BHT_id: Array-like of member B hole type IDs (e.g., [0, 2] for STD, SSL)
        N_r: Array-like of number of bolt rows (e.g., [1, 2, 3])
        S_r: Array-like of bolt row spacing values (e.g., [60, 80, 100])
        N_c: Array-like of number of bolt columns (e.g., [1, 2, 3])
        S_c: Array-like of bolt column spacing values (e.g., [60, 80, 100])
        L_ev: Array-like of vertical edge distance values (e.g., [30, 40, 50])
        L_eh: Array-like of horizontal edge distance values (e.g., [30, 40, 50])
        Ga: Array-like of gap/gauge values (e.g., [0, 5, 10])
    
    Returns:
        Dictionary with all bolt configuration combinations as columnar arrays,
        including F_nv and F_nt values automatically derived from bolt grades
    """
    # Generate base combinations using all integers
    combinations = generate_combinations_dict(
        bolt_size=bolt_size,
        bolt_grade_id=bolt_grade_id,  
        member_a_BHT_id=member_a_BHT_id,
        member_b_BHT_id=member_b_BHT_id,
        N_r=N_r,
        S_r=S_r,
        N_c=N_c,
        S_c=S_c,
        L_ev=L_ev,
        L_eh=L_eh,
        Ga=Ga
    )
    
    # Add derived values using efficient vectorized operations
    if combinations and 'bolt_grade_id' in combinations:
        grade_ids = combinations['bolt_grade_id']
        
        # Pre-compute strength arrays for vectorized lookup
        grade_keys = [BOLT_GRADE_MAP[gid] for gid in np.unique(grade_ids)]
        fnv_lookup = {gid: BOLT_GRADES[BOLT_GRADE_MAP[gid]].Fnv.value for gid in np.unique(grade_ids)}
        fnt_lookup = {gid: BOLT_GRADES[BOLT_GRADE_MAP[gid]].Fnt.value for gid in np.unique(grade_ids)}
        
        # Vectorized mapping using numpy indexing
        f_nv_values = np.array([fnv_lookup[gid] for gid in grade_ids])
        f_nt_values = np.array([fnt_lookup[gid] for gid in grade_ids])
        
        # Add strength values and mapped strings
        combinations['F_nv'] = f_nv_values
        combinations['F_nt'] = f_nt_values
        combinations['bolt_grade'] = np.array([BOLT_GRADE_MAP[gid] for gid in grade_ids])
        combinations['member_a_BHT'] = np.array([HOLE_TYPE_MAP[hid] for hid in combinations['member_a_BHT_id']])
        combinations['member_b_BHT'] = np.array([HOLE_TYPE_MAP[hid] for hid in combinations['member_b_BHT_id']])
    
    return combinations


def example_bolt_configurations_with_strengths():
    """
    Example usage of the optimized bolt configuration generator using integer inputs.
    
    Returns:
        Dictionary containing all combinations of bolt configurations with F_nv and F_nt values
    """
    # Example parameter ranges using integers for maximum efficiency
    bolt_configurations = generate_bolt_configurations(
        bolt_size=[16, 20, 24],                   # Bolt sizes as integers (mm)
        bolt_grade_id=[0, 1, 2],                  # 0=a325_n, 1=a325_x, 2=a490_n
        member_a_BHT_id=[0, 1],                   # 0=STD, 1=OVS
        member_b_BHT_id=[0, 2],                   # 0=STD, 2=SSL
        N_r=[1, 2],                               # 1 or 2 rows of bolts
        S_r=[60, 80],                             # Row spacing in mm
        N_c=[2, 3],                               # 2 or 3 columns of bolts
        S_c=[60, 80],                             # Column spacing in mm
        L_ev=[30, 40],                            # Vertical edge distance
        L_eh=[30, 40],                            # Horizontal edge distance
        Ga=[0, 5]                                 # gage values
    )
    
    return bolt_configurations


def get_mapping_info():
    """
    Returns mapping information for integer-based inputs.
    
    Returns:
        Dictionary with mapping information for bolt grades and hole types
    """
    return {
        'bolt_grades': {id: grade for id, grade in BOLT_GRADE_MAP.items()},
        'hole_types': {id: hole_type for id, hole_type in HOLE_TYPE_MAP.items()}
    }


if __name__ == "__main__":
    # Show mapping information
    mappings = get_mapping_info()
    print("Integer Mappings:")
    print(f"Bolt Grades: {mappings['bolt_grades']}")
    print(f"Hole Types: {mappings['hole_types']}")
    print()
    
    # Example usage with optimized integer inputs
    configs = example_bolt_configurations_with_strengths()
    print(f"Generated {len(configs['bolt_size'])} bolt configurations")
    print(f"Parameters: {list(configs.keys())}")
    
    # Show first 3 configurations with strength values
    print("\nFirst 3 configurations with strength values:")
    for i in range(min(3, len(configs['bolt_size']))):
        config = {key: values[i] for key, values in configs.items()}
        print(f"Config {i+1}:")
        print(f"  Bolt: M{config['bolt_size']} grade {config['bolt_grade']}")
        print(f"  F_nv: {config['F_nv']:.1f} ksi, F_nt: {config['F_nt']:.1f} ksi")
        print(f"  Holes: {config['member_a_BHT']} / {config['member_b_BHT']}")
        print(f"  Geometry: {config['N_r']}x{config['N_c']} @ {config['S_r']}x{config['S_c']}mm")
        print()


