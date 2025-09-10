from .data_models import BoltConfiguration,WeldConfiguration

import itertools
import time

def create_valid_bolt_configs(
    bolt_grid,
    lower_length_bound=None,
    upper_length_bound=None,
    lower_width_bound=None,
    upper_width_bound=None,
):
    """
    Generates valid BoltConfiguration objects by pre-filtering combinations
    based on dimensional constraints in an optimized manner.

    Args:
        bolt_grid (dict): A dictionary containing lists of possible values for each
                          bolt grid parameter.
        lower_length_bound (float, optional): The minimum allowed length.
        upper_length_bound (float, optional): The maximum allowed length.
        lower_width_bound (float, optional): The minimum allowed width.
        upper_width_bound (float, optional): The maximum allowed width.

    Yields:
        BoltConfiguration: A valid bolt configuration object.
    """
    # --- 1. Input Validation ---
    if lower_length_bound is not None and upper_length_bound is not None and lower_length_bound > upper_length_bound:
        # Silently exit if bounds are invalid, as a generator shouldn't print errors.
        return
    if lower_width_bound is not None and upper_width_bound is not None and lower_width_bound > upper_width_bound:
        return

    # --- 2. Pre-filter combinations for LENGTH ---
    length_params = [
        bolt_grid.get('n_columns', [None]),
        bolt_grid.get('column_spacing', [None]),
        bolt_grid.get('edge_distance_horizontal', [None])
    ]
    valid_lengths = []
    for n_cols, col_s, edge_h in itertools.product(*length_params):
        length = (n_cols - 1) * col_s + 2 * edge_h
        if (lower_length_bound is None or length >= lower_length_bound) and \
           (upper_length_bound is None or length <= upper_length_bound):
            valid_lengths.append({
                'n_columns': n_cols,
                'column_spacing': col_s,
                'edge_distance_horizontal': edge_h
            })
    
    if not valid_lengths:
        return

    # --- 3. Pre-filter combinations for WIDTH ---
    width_params = [
        bolt_grid.get('n_rows', [None]),
        bolt_grid.get('row_spacing', [None]),
        bolt_grid.get('edge_distance_vertical', [None])
    ]
    valid_widths = []
    for n_rows, row_s, edge_v in itertools.product(*width_params):
        width = (n_rows - 1) * row_s + 2 * edge_v
        if (lower_width_bound is None or width >= lower_width_bound) and \
           (upper_width_bound is None or width <= upper_width_bound):
            valid_widths.append({
                'n_rows': n_rows,
                'row_spacing': row_s,
                'edge_distance_vertical': edge_v
            })

    if not valid_widths:
        return
        
    # --- 4. Get remaining independent parameters ---
    other_params_grid = {
        'bolt_diameter': bolt_grid.get('bolt_diameter', [None]),
        'bolt_grade': bolt_grid.get('bolt_grade', [None])
    }
    # Create a generator for the remaining parameter combinations
    other_combinations = (
        dict(zip(other_params_grid.keys(), combo))
        for combo in itertools.product(*other_params_grid.values())
    )

    # --- 5. Combine and yield BoltConfiguration objects ---
    # This product is now on much smaller lists, making it efficient.
    for length_data, width_data, other_data in itertools.product(valid_lengths, valid_widths, other_combinations):
        # Merge all parameter dictionaries
        config_params = {**length_data, **width_data, **other_data}
        # Yield a complete BoltConfiguration object
        yield BoltConfiguration(**config_params)
def create_valid_weld_configs(
    weld_grid,
    lower_length_bound=None,
    upper_length_bound=None,
):
    """
    Generates valid WeldConfiguration objects by pre-filtering combinations
    based on length constraints in an optimized manner.

    Args:
        weld_grid (dict): A dictionary containing lists of possible values for each
                          weld parameter.
        lower_length_bound (float, optional): The minimum allowed weld length.
        upper_length_bound (float, optional): The maximum allowed weld length.

    Yields:
        WeldConfiguration: A valid weld configuration object.
    """
    # --- 1. Input Validation ---
    if lower_length_bound is not None and upper_length_bound is not None and lower_length_bound > upper_length_bound:
        # A generator should not print errors, so we just stop iteration.
        return

    # --- 2. Pre-filter the `length` parameter directly ---
    # This is the core optimization for this specific class.
    valid_lengths = [
        l for l in weld_grid.get('length', [])
        if (lower_length_bound is None or l >= lower_length_bound) and \
           (upper_length_bound is None or l <= upper_length_bound)
    ]

    # If no lengths are valid, no combinations can be valid.
    if not valid_lengths:
        return

    # --- 3. Get remaining independent parameters ---
    # These are all parameters that are NOT used for filtering.
    other_params = [
        weld_grid.get('weld_size', [None]),
        weld_grid.get('electrode', [None]),
        weld_grid.get('weld_type', [None])
    ]

    # --- 4. Combine filtered lengths with other parameters and yield ---
    # The product is created with the already-filtered list of lengths.
    for length, size, electrode, w_type in itertools.product(valid_lengths, *other_params):
        yield WeldConfiguration(
            length=length,
            weld_size=size,
            electrode=electrode,
            weld_type=w_type
        )