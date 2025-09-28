from functools import wraps
from numba import njit, prange
from handcalcs import handcalc
from forallpeople import Physical
from numpy import atan, sin, cos, tan
import numpy as np
from typing import Literal
from math import sqrt, pi, inf
from math import log as ln

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