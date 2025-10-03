from functools import lru_cache, wraps
from numba import njit, prange
from handcalcs import handcalc
from forallpeople import Physical
from numpy import atan, sin, cos, tan
import numpy as np
from typing import Literal
from math import sqrt, pi, inf
from math import log as ln
from functools import wraps
from typing import Literal, Callable, Optional, Dict, Any
from handcalcs.decorator import handcalc
from numba import njit
import inspect
def optional_reporting_handcalc(config_object, *, key: str, detailed: Literal["calculation",'latex','test'] = False, **handcalc_kwargs):
    """
    A single, powerful conditional decorator that combines the functionality
    of @handcalc and @auto_add_subtitle.

    When config.HANDCALC_ENABLED is True, it:
    1. Runs the decorated function through @handcalc.
    2. Takes the resulting LaTeX output.
    3. Adds the LaTeX as a subtitle to the provided config_object.
    4. Returns the original (latex, result) tuple from handcalc.

    When config.HANDCALC_ENABLED is False, it:
    1. Simply runs the original, undecorated function.
    2. Returns the direct result of that function (e.g., a float).

    Args:
        config_object: The report/LaTeX configuration object.
        key (str): The key to use when adding the subtitle.
        **handcalc_kwargs: All keyword arguments for the original @handcalc
                           decorator (e.g., precision=3, override='latex').
    """
    def decorator(func):
        if detailed == 'latex':
            # --- SLOW / DETAILED PATH ---
            @wraps(func)
            def wrapper(*args, **kwargs):
                # 1. Programmatically apply the @handcalc decorator
                handcalc_decorated_func = handcalc(**handcalc_kwargs)(func)

                # 2. Execute to get the (latex, result) tuple
                results = handcalc_decorated_func(*args, **kwargs)

                # 3. Add subtitle
                latex_value = results[0]
                config_object.add_subtitle(key=key, value=latex_value)

                # 4. Return the original result
                return results[1]
            return wrapper
        elif detailed == 'calculation':
            # --- FAST PATH ---
            # Directly return the Numba-compiled function with optimizations
            return njit(func, fastmath=True)
        elif detailed == 'test':
            return handcalc(jupyter_display=True,precision=3,override='long')(func)
        elif detailed == 'base':
            # --- BASE PATH ---
            # Return the original function without any decorators or modifications
            return func
    return decorator

# _NUMBA_CACHE: Dict[str, Callable] = {}

# def optional_reporting_handcalc(
#     *, 
#     key: str, 
#     default_detailed: Literal["calculation", 'latex', 'test', 'base'] = 'base',
#     numba_enabled: bool = True,
#     numba_kwargs: Optional[Dict[str, Any]] = None,
#     **handcalc_kwargs
# ):
#     """
#     A powerful, dynamic decorator where the reporting mode and configuration
#     are specified when the function is called.

#     Args:
#         key (str): The key to use when adding the subtitle in latex mode.
#         default_detailed (str): The default mode if 'mode' is not specified.
#         numba_enabled (bool): Whether to enable Numba compilation for 'calculation' mode.
#         numba_kwargs (dict): Additional kwargs to pass to @njit (default: {'fastmath': True}).
#         **handcalc_kwargs: Default keyword arguments for the @handcalc decorator.
#     """
#     if numba_kwargs is None:
#         numba_kwargs = {'fastmath': True, 'cache': True }
    
#     def decorator(func):
#         func_id = id(func)  # Use function id as unique identifier
        
#         def _get_or_compile_numba_func():
#             """Compile and cache the Numba version of the function."""
#             if func_id not in _NUMBA_CACHE:
#                 try:
#                     print(f"--- Compiling '{func.__name__}' with Numba ---")
#                     compiled = njit(**numba_kwargs)(func)
#                     _NUMBA_CACHE[func_id] = compiled
#                 except Exception as e:
#                     print(f"Warning: Failed to compile '{func.__name__}' with Numba: {e}")
#                     print("Falling back to Python implementation")
#                     _NUMBA_CACHE[func_id] = func
#             return _NUMBA_CACHE[func_id]

#         @wraps(func)
#         def wrapper(*args, **kwargs):
#             # Extract control parameters
#             mode = kwargs.pop('mode', default_detailed)
#             config_object = kwargs.pop('config_object', None)

#             # --- Mode-based execution ---
#             if mode == 'latex':
#                 if config_object is None:
#                     raise ValueError(
#                         f"The 'config_object' keyword argument is required when using mode='latex' "
#                         f"in function '{func.__name__}'."
#                     )
                
#                 # Apply handcalc decorator dynamically
#                 handcalc_decorated_func = handcalc(**handcalc_kwargs)(func)
#                 latex_code, result = handcalc_decorated_func(*args, **kwargs)
#                 config_object.add_subtitle(key=key, value=latex_code)
#                 return result

#             elif mode == 'calculation':
#                 if numba_enabled:
#                     compiled_func = _get_or_compile_numba_func()
#                     return compiled_func(*args, **kwargs)
#                 else:
#                     # Fall back to base implementation
#                     return func(*args, **kwargs)

#             elif mode == 'test':
#                 # Use handcalc with jupyter display for testing
#                 test_kwargs = {
#                     'jupyter_display': True,
#                     'precision': handcalc_kwargs.get('precision', 3),
#                     'override': handcalc_kwargs.get('override', 'long')
#                 }
#                 test_func = handcalc(**test_kwargs)(func)
#                 return test_func(*args, **kwargs)

#             elif mode == 'base':
#                 return func(*args, **kwargs)

#             else:
#                 raise ValueError(
#                     f"Invalid mode '{mode}' for function '{func.__name__}'. "
#                     f"Use 'latex', 'calculation', 'test', or 'base'."
#                 )

#         # Add utility methods to the wrapper
#         wrapper._original_func = func
#         wrapper._decorator_key = key
        
#         # Pre-compile if in calculation mode and numba is enabled
#         if default_detailed == 'calculation' and numba_enabled:
#             # Trigger compilation on decorator application (optional)
#             pass  # Can call _get_or_compile_numba_func() here if you want eager compilation
            
#         return wrapper
    
#     return decorator


# from functools import wraps, lru_cache
# from typing import Literal
# from numba import njit
# # Assuming 'handcalc' and a 'config_object' structure are defined elsewhere
# # from handcalc import handcalc 

# def optional_reporting_handcalc(config_object, *, key: str, detailed: Literal["calculation", 'latex', 'test', 'base'] = 'base', **handcalc_kwargs):
#     """
#     A single, powerful conditional decorator that combines the functionality
#     of @handcalc and @auto_add_subtitle.

#     When config.HANDCALC_ENABLED is True, it:
#     1. Runs the decorated function through @handcalc.
#     2. Takes the resulting LaTeX output.
#     3. Adds the LaTeX as a subtitle to the provided config_object.
#     4. Returns the original (latex, result) tuple from handcalc.

#     When config.HANDCALC_ENABLED is False, it:
#     1. Simply runs the original, undecorated function.
#     2. Returns the direct result of that function (e.g., a float).

#     Args:
#         config_object: The report/LaTeX configuration object.
#         key (str): The key to use when adding the subtitle.
#         detailed (Literal): Controls the decorator's behavior.
#                            'calculation' -> Optimized for speed with Numba and LRU cache.
#                            'latex' -> Generates and reports LaTeX.
#                            'test' -> Runs handcalc for Jupyter display.
#                            'base' -> Returns the original function.
#         **handcalc_kwargs: All keyword arguments for the original @handcalc
#                            decorator (e.g., precision=3, override='latex').
#     """
#     def decorator(func):
#         if detailed == 'latex':
#             # --- SLOW / DETAILED PATH ---
#             @wraps(func)
#             def wrapper(*args, **kwargs):
#                 # 1. Programmatically apply the @handcalc decorator
#                 handcalc_decorated_func = handcalc(**handcalc_kwargs)(func)

#                 # 2. Execute to get the (latex, result) tuple
#                 results = handcalc_decorated_func(*args, **kwargs)

#                 # 3. Add subtitle
#                 latex_value = results[0]
#                 config_object.add_subtitle(key=key, value=latex_value)

#                 # 4. Return the original result
#                 return results[1]
#             return wrapper
#         elif detailed == 'calculation':
#             # --- FASTEST PATH (with Result Caching) ---
#             # 1. First, compile the function with Numba for raw speed.
#             numba_func = njit(func, fastmath=True)
            
#             # 2. Then, wrap the compiled function with an LRU cache to store results.
#             #    maxsize=128 means it will store the 128 most recent unique calls.
#             cached_numba_func = lru_cache(maxsize=128)(numba_func)
            
#             return cached_numba_func
#         elif detailed == 'test':
#             return handcalc(jupyter_display=True, precision=3, override='long')(func)
#         elif detailed == 'base':
#             # --- BASE PATH ---
#             # Return the original function without any decorators or modifications
#             return func
#     return decorator
detailed = 'calculation'

# Common geometric calculations
@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_area(l, l_net, t):
    A_g = l * t
    A_n = l_net * t
    return A_g, A_n

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_area_gross(l, t):
    A_g = l * t
    return A_g

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_area_holes(N_r, d_b, t):
    d_holes = d_b + 0.0625 * 2
    A_holes = N_r * d_holes * t
    return A_holes

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_plate_length_bolted(N_r, S_r, L_ev):
    l = (N_r-1) * S_r + L_ev * 2
    return l

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_connection_width_bolted(N_c, S_c, L_eh, a=None):
    l = (N_c-1) * S_c + L_eh * 2
    return l

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_elastic_modulus(t, l):
    S_g = (t*l**2)/6
    return S_g

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_plastic_modulus(t, l):
    Z_g = (t*l**2)/4
    return Z_g

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_plastic_modulus_holes(N_r, S_r, d_b, t):
    d_holes = d_b + 0.0625
    if N_r%2 == 0: Z_holes = (t/4) * (S_r*N_r**2* d_holes)
    elif N_r%2 != 0: Z_holes =(t/4) * (d_holes**2+(N_r**2-1)*S_r*d_holes )
    return Z_holes

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_plastic_modulus_net(Z_g, Z_holes):
    Z_net = Z_g - Z_holes
    return Z_net