from functools import wraps
from numba import njit, prange
from handcalcs import handcalc
from forallpeople import Physical
from numpy import atan, sin , cos, tan
import numpy as np  
from typing import Literal
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
    return decorator

detailed = 'test'
particle_dtype = np.dtype([
    ('id', np.int32),        # A 32-bit integer for the particle's unique ID
    ('velocity', np.float64),  # A 64-bit float for the particle's velocity
    ('position', np.float64)   # A 64-bit float for the particle's current position
])
# This is the JIT-compiled function, defined once at the module level.
@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def bolt_shear(F_nv, A_bolt, N_shear_planes: int, phi: float):
    V_n = F_nv * A_bolt * N_shear_planes
    V_u = phi * V_n
    return V_u
@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_bolt_bearing(l_c_inner,l_c_edge,t,F_u,N_bolts,d_bolt,phi,c):
    V_u_bearing = 2.4 * d_bolt * t * F_u
    V_u_inner_1 = 1.2 * l_c_inner * t * F_u
    V_u_inner = min(V_u_inner_1, V_u_bearing) * (N_bolts - 1)
    V_u_edge_1 = 1.2 * l_c_edge * t * F_u * 1
    V_u_edge = min(V_u_edge_1, V_u_bearing)
    V_u = (V_u_inner + V_u_edge)*(c/N_bolts) * phi
    return V_u
# @optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
# def calculation_bolt_bear_multi_column(V_u_shear,V_u_axial):
#     V_u = min(V_u_shear,V_u_axial)
#     return V_u
@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_lc(theta,L_edge_1,L_edge_2,S,d_hole):

    if theta != 0:L_c_1 = L_edge_1/sin(theta) - 0.5*d_hole;L_c_2 = S/cos(theta) - d_hole;L_c_3 = L_edge_2/cos(theta) - 0.5*d_hole;lc_inner = min(L_c_1,L_c_2);lc_edge = min(L_c_1,L_c_3)
    elif theta == 0: lc_inner = S/cos(theta) - d_hole;lc_edge = L_edge_2/cos(theta) - 0.5*d_hole

    return lc_inner, lc_edge
@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_theta(P_u,V_u):
    if P_u == 0: theta = 0
    else: theta = atan(P_u/V_u)
    return theta
# dtype_bearing = np.dtype([('spacing', np.float64), ("edge_distance_horizontal", np.float64),("edge_distance_vertical", np.float64),("number_of_bolts",np.int32)])



def bolt_bearing(F_u, d_bolt, t, P_u, V_u, S_r, N_r, S_c, N_c, L_ev, L_eh, dv, dh, phi, c):
    """
    Calculates the bolt bearing strength for single or multiple columns of bolts.
    """

    def _calculate_bearing_for_direction(theta, L_edge_1, L_edge_2, S, d_hole, N_bolts):
        """Helper function to calculate bearing strength for a given direction."""
        lc_inner, lc_edge = calculation_lc(theta, L_edge_1=L_edge_1, L_edge_2=L_edge_2, S=S, d_hole=d_hole)
        return calculation_bolt_bearing(
            l_c_inner=lc_inner,
            l_c_edge=lc_edge,
            t=t,
            F_u=F_u,
            N_bolts=N_bolts,
            d_bolt=d_bolt,
            c=c,
            phi=phi
        )

    if N_c == 1:
        # Case for a single column of bolts
        theta = calculation_theta(P_u, V_u)
        bearing_strength = _calculate_bearing_for_direction(theta, L_eh, L_ev, S_r, dv, N_r)
    else:
        # Case for multiple columns of bolts, check shear and axial directions separately
        
        # Strength in the direction of shear (theta = 0)
        bearing_strength_shear = _calculate_bearing_for_direction(0, L_eh, L_ev, S_r, dv, N_r)
        
        # Strength in the direction of axial load (theta = 90, but handled as 0 with swapped inputs)
        bearing_strength_axial = _calculate_bearing_for_direction(0, L_ev, L_eh, S_c, dh, N_c)

        # The final strength is the minimum of the two directions
        bearing_strength = min(bearing_strength_shear, bearing_strength_axial)
        
    return bearing_strength
@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_length_l_path_1(N_r,S_r,L_ev,d_hole):
    l = (N_r - 1) * S_r + L_ev
    l_net = l - (N_r - 0.5) * d_hole
    return l,l_net
@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_length_l_path_2(N_c,S_c,t,L_eh,d_hole):
    l = (N_c - 1) * S_c + L_eh
    l_net = l - (N_c - 0.5) * d_hole
    return l,l_net

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_length_u_path_1(N_r,S_r,L_ev,d_hole):
    l = (N_r - 1) * S_r 
    l_net = l - (N_r - 1) * d_hole
    return l,l_net

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_length_u_path_2(N_c,S_c,t,L_eh,d_hole):
    l = ((N_c - 1) * S_c + L_eh )*2
    l_net = (l - (N_c - 0.5) * d_hole * 2) 
    return l,l_net

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_area(l,l_net,t):
    A_g = l * t
    A_n = l_net * t
    return A_g,A_n
@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_shear_component(A_g,A_net,F_y,F_u):
    V_yield = 0.6 * F_y * A_g 
    V_rupture = 0.6 * F_u * A_net
    V_u = min(V_yield,V_rupture)
    return V_u
@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_tensile_component(A_g,A_net,F_y,F_u,U_bs=1.0):    
    P_u = F_u * A_net * U_bs
    return P_u
@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_block_shear(V_n,P_n,phi):
    R_u = phi * (V_n + P_n)
    return R_u  
def block_shear(P_u, V_u, F_y, F_u, t, N_r, S_r, N_c, S_c, L_ev, L_eh, d_v, d_h, phi):
    """ 
    Calculates the block shear strength for a given set of parameters by evaluating two paths.
    The original engineering logic and helper functions are preserved.
    """
    dv_hole = d_v + 0.0625
    dh_hole = d_h + 0.0625
    if P_u:
        # --- Path 1: Shear on longitudinal plane, tension on transverse plane ---

        # l_path1, l_net_path1 = calculation_length_l_path_1(N_r, S_r, L_ev, dv_hole)
        # A_gt_path1, A_nt_path1 = calculation_area(l_path1, l_net_path1, t)
        # P_n1 = calculation_tensile_component(A_gt_path1, A_nt_path1, F_y, F_u)

        # l_path2, l_net_path2 = calculation_length_l_path_2(N_c, S_c, t, L_eh, dh_hole)
        # A_gv_path1, A_nv_path1 = calculation_area(l_path2, l_net_path2, t)
        # V_n1 = calculation_shear_component(A_gv_path1, A_nv_path1, F_y, F_u)
        # # Note: calculation_area expects two length values, but calculation_length_l_path_1 only returns one.
        # # Assuming the gross length is not needed or can be derived if necessary. Using l_net_path1 for both.
  
        # R_n_path1 = calculation_block_shear(V_n1, P_n1, phi)

        # --- Path 2: Shear on transverse planes, tension on longitudinal plane ---
        # u_path1, u_net_path1 = calculation_length_u_path_1(N_r, S_r, L_ev, dv_hole)
        # A_gt_path2, A_nt_path2 = calculation_area(u_path1, u_net_path1, t)
        # P_n2 = calculation_tensile_component(A_gt_path2, A_nt_path2, F_y, F_u)
        
        # u_path2, u_net_path2 = calculation_length_u_path_2(N_c, S_c, t, L_eh, dh_hole)
        # A_gv_path2, A_nv_path2 = calculation_area(u_path2, u_net_path2, t)
        # V_n2 = calculation_shear_component(A_gv_path2, A_nv_path2, F_y, F_u)

        # R_n_path2 = calculation_block_shear(V_n2, P_n2, phi)
        pihuts = 1

        # # The final block shear strength is the minimum of the two paths.
        # R_n = min(R_n_path1, R_n_path2)
    if V_u:
        # --- Path 1: Shear on longitudinal plane, tension on transverse plane ---
        l_path1,l_net_path1 = calculation_length_l_path_1(N_r, S_r, L_ev, dv_hole)
        l_path2, l_net_path2 = calculation_length_l_path_2(N_c, S_c, t, L_eh, dh_hole)

        # Note: calculation_area expects two length values, but calculation_length_l_path_1 only returns one.
        # Assuming the gross length is not needed or can be derived if necessary. Using l_net_path1 for both.
        A_gv_path1, A_nv_path1 = calculation_area(l_path1, l_net_path1, t)
        A_gt_path1, A_nt_path1 = calculation_area(l_path2, l_net_path2, t)

        V_n1 = calculation_shear_component(A_gv_path1, A_nv_path1, F_y, F_u)
        P_n1 = calculation_tensile_component(A_gt_path1, A_nt_path1, F_y, F_u,U_bs = 0.5)
        R_n_path1 = calculation_block_shear(V_n1, P_n1, phi)


    return 123
