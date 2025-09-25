from functools import wraps
from numba import njit, prange
from handcalcs import handcalc
from forallpeople import Physical
from numpy import atan, sin , cos, tan
import numpy as np  
from typing import Literal
from math import sqrt,pi
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

detailed = 'calculation'
particle_dtype = np.dtype([
    ('id', np.int32),        # A 32-bit integer for the particle's unique ID
    ('velocity', np.float64),  # A 64-bit float for the particle's velocity
    ('position', np.float64)   # A 64-bit float for the particle's current position
])
# This is the JIT-compiled function, defined once at the module level.

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


@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
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
    V_n = min(V_yield,V_rupture)
    return V_n
@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_tensile_component(A_g,A_net,F_y,F_u,U_bs=1.0):    
    P_n = F_u * A_net * U_bs
    return P_n
@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_block_shear(V_n,P_n,phi,n_members=1):
    R_u = phi * (V_n + P_n) * n_members
    return R_u
@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed) 
def calculate_path1_pu(N_r, S_r, N_c, S_c, L_ev, L_eh, dv_hole, dh_hole, t, F_y, F_u, phi,n_members=1):
    l_path1, l_net_path1 = calculation_length_l_path_1(N_r, S_r, L_ev, dv_hole)
    A_gt_path1, A_nt_path1 = calculation_area(l_path1, l_net_path1, t)
    P_n1 = calculation_tensile_component(A_gt_path1, A_nt_path1, F_y, F_u)
    l_path2, l_net_path2 = calculation_length_l_path_2(N_c, S_c, t, L_eh, dh_hole)
    A_gv_path1, A_nv_path1 = calculation_area(l_path2, l_net_path2, t)
    V_n1 = calculation_shear_component(A_gv_path1, A_nv_path1, F_y, F_u)
    R_n_path1 = calculation_block_shear(V_n1, P_n1, phi,n_members=n_members)
    return R_n_path1
@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculate_path2_pu(N_r, S_r, N_c, S_c, L_ev, L_eh, dv_hole, dh_hole, t, F_y, F_u, phi,n_members=1):
    u_path1, u_net_path1 = calculation_length_u_path_1(N_r, S_r, L_ev, dv_hole)
    A_gt_path2, A_nt_path2 = calculation_area(u_path1, u_net_path1, t)
    P_n2 = calculation_tensile_component(A_gt_path2, A_nt_path2, F_y, F_u)
    u_path2, u_net_path2 = calculation_length_u_path_2(N_c, S_c, t, L_eh, dh_hole)
    A_gv_path2, A_nv_path2 = calculation_area(u_path2, u_net_path2, t)
    V_n2 = calculation_shear_component(A_gv_path2, A_nv_path2, F_y, F_u)
    R_n_path2 = calculation_block_shear(V_n2, P_n2, phi,n_members=n_members)
    return R_n_path2
@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculate_path1_vu(N_r, S_r, N_c, S_c, L_ev, L_eh, dv_hole, dh_hole, t, F_y, F_u, phi,coped=False,n_members=1):
    l_path1, l_net_path1 = calculation_length_l_path_1(N_r, S_r, L_ev, dv_hole)
    A_gv_path1, A_nv_path1 = calculation_area(l_path1, l_net_path1, t)
    V_n1 = calculation_shear_component(A_gv_path1, A_nv_path1, F_y, F_u)
    l_path2, l_net_path2 = calculation_length_l_path_2(N_c, S_c, t, L_eh, dh_hole)
    A_gt_path1, A_nt_path1 = calculation_area(l_path2, l_net_path2, t)
    U_bs = 0.5 if coped else 1.0
    P_n1 = calculation_tensile_component(A_gt_path1, A_nt_path1, F_y, F_u, U_bs=U_bs)
    R_n_path1 = calculation_block_shear(V_n1, P_n1, phi,n_members=n_members)
    return R_n_path1

# def calculate_path2_vu(N_r, S_r, N_c, S_c, L_ev, L_eh, dv_hole, dh_hole, t, F_y, F_u, phi):
#     u_path1, u_net_path1 = calculation_length_u_path_1(N_r, S_r, L_ev, dv_hole)
#     A_gv_path2, A_nv_path2 = calculation_area(u_path1, u_net_path1, t)
#     V_n2 = calculation_shear_component(A_gv_path2, A_nv_path2, F_y, F_u)
#     u_path2, u_net_path2 = calculation_length_u_path_2(N_c, S_c, t, L_eh, dh_hole)
#     A_gt_path2, A_nt_path2 = calculation_area(u_path2, u_net_path2, t)
#     P_n2 = calculation_tensile_component(A_gt_path2, A_nt_path2, F_y, F_u, U_bs=0.5)
#     R_n_path2 = calculation_block_shear(V_n2, P_n2, phi)
#     return R_n_path2
@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def block_shear(P_u, V_u, F_y, F_u, t, N_r, S_r, N_c, S_c, L_ev, L_eh, d_v, d_h, phi,coped,n_members=1):
    """ 
    Calculates the block shear strength for a given set of parameters by evaluating two paths.
    The original engineering logic and helper functions are preserved.
    """
    dv_hole = d_v + 0.0625
    dh_hole = d_h + 0.0625
    R_n_path1 = np.inf
    R_n_path2 = np.inf
    if P_u:

        l_path1, l_net_path1 = calculation_length_l_path_1(N_r, S_r, L_ev, dv_hole)
        A_gt_path1, A_nt_path1 = calculation_area(l_path1, l_net_path1, t)
        P_n1 = calculation_tensile_component(A_gt_path1, A_nt_path1, F_y, F_u)
        l_path2, l_net_path2 = calculation_length_l_path_2(N_c, S_c, t, L_eh, dh_hole)
        A_gv_path1, A_nv_path1 = calculation_area(l_path2, l_net_path2, t)
        V_n1 = calculation_shear_component(A_gv_path1, A_nv_path1, F_y, F_u)
        R_n_path1 = calculation_block_shear(V_n1, P_n1, phi,n_members=n_members)
        
        u_path1, u_net_path1 = calculation_length_u_path_1(N_r, S_r, L_ev, dv_hole)
        A_gt_path2, A_nt_path2 = calculation_area(u_path1, u_net_path1, t)
        P_n2 = calculation_tensile_component(A_gt_path2, A_nt_path2, F_y, F_u)
        u_path2, u_net_path2 = calculation_length_u_path_2(N_c, S_c, t, L_eh, dh_hole)
        A_gv_path2, A_nv_path2 = calculation_area(u_path2, u_net_path2, t)
        V_n2 = calculation_shear_component(A_gv_path2, A_nv_path2, F_y, F_u)
        R_n_path2 = calculation_block_shear(V_n2, P_n2, phi,n_members=n_members)
            
    if V_u:

        l_path1, l_net_path1 = calculation_length_l_path_1(N_r, S_r, L_ev, dv_hole)
        A_gv_path1, A_nv_path1 = calculation_area(l_path1, l_net_path1, t)
        V_n1 = calculation_shear_component(A_gv_path1, A_nv_path1, F_y, F_u)
        l_path2, l_net_path2 = calculation_length_l_path_2(N_c, S_c, t, L_eh, dh_hole)
        A_gt_path1, A_nt_path1 = calculation_area(l_path2, l_net_path2, t)
        U_bs = 0.5 if coped else 1.0
        P_n1 = calculation_tensile_component(A_gt_path1, A_nt_path1, F_y, F_u, U_bs=U_bs)
        R_n_path1 = calculation_block_shear(V_n1, P_n1, phi,n_members=n_members)
    return min(R_n_path1,R_n_path2)


@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_connection_length_bolted(N_r,S_r,L_ev):
    l = (N_r-1) * S_r + L_ev * 2
    return l
@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_area_gross(l,t):
    A_g = l*t
    return A_g
@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_area_holes(N_r,d_b,t):
    d_holes = d_b + 0.0625 * 2
    A_holes = N_r * d_holes * t
    return A_holes
@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_area_net_plates(A_g,A_holes):
    A_net = A_g - A_holes
    return A_net
@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_shear_yielding(A_g,F_y,phi):
    V_n_yielding = 0.6 * A_g * F_y
    V_u_yielding = phi * V_n_yielding
    return V_u_yielding
@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_shear_rupture(A_net,F_u,phi):
    V_n_rupture = 0.6 * A_net * F_u
    V_u_rupture = V_n_rupture * phi
    return V_u_rupture
@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_shear_strength(V_u_yielding,V_u_rupture,n_members=1,coped=0):
    if coped == 2: V_u = min(V_u_yielding,V_u_rupture) * n_members
    else: V_u = V_u_yielding * n_members
    return V_u
@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def shear_yielding_rupture(N_r, S_r, L_ev, t, d_b, F_y, F_u, phi,n_members=1,coped = 0):
    def _calculate_shear_yielding_rupture_bolted(N_r, S_r, L_ev, t, d_b, F_y, F_u, phi):
        l = calculation_connection_length_bolted(N_r, S_r, L_ev)
        A_g = calculation_area_gross(l, t)
        A_holes = calculation_area_holes(N_r, d_b,t)
        A_net = calculation_area_net_plates(A_g, A_holes)
        V_u_yielding = calculation_shear_yielding(A_g, F_y, 1)
        V_u_rupture = calculation_shear_rupture(A_net, F_u, phi)
        V_u = calculation_shear_strength(V_u_yielding, V_u_rupture,n_members=n_members,coped=coped)
        return V_u
    return _calculate_shear_yielding_rupture_bolted(N_r, S_r, L_ev, t, d_b, F_y, F_u, phi)




@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_ubs_w_section_uncoped(b_f,t_f,d,t_w,l):
    A_flange = (b_f/2 * t_f)
    M_arm_flange =  (b_f/4)
    A_web = (d - 2*t_f)* t_w/2
    M_arm_web = t_w/4
    x_g = ((A_flange * M_arm_flange * 2 )+ (A_web * M_arm_web)) / (A_flange * 2 + A_web)
    U_bs_1 = 1 - x_g/l
    return U_bs_1
@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_ubs_w_section_coped(A_g,A_conn,t_f,d,t_w,n_flange,d_top,d_bot,U_bs_1 = None):
    U_bs_limit = A_conn /A_g
    if U_bs_1: U_bs = max(U_bs_limit,U_bs_1)
    else: U_bs = U_bs_limit
    return U_bs
@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_connection_length_bolted(N_r,S_r,L_ev):
    l = (N_r-1) * S_r + L_ev * 2
    return l
@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_connection_width_bolted(N_c,S_c,L_eh,a = None):
    l = (N_c-1) * S_c + L_eh * 2
    return l
@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_area_gross(l,t):
    A_g = l*t
    return A_g
@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_area_tension_beams(A_flange,A_web,coped):
    if coped == 0: A_tension = A_flange + A_web
    elif coped > 0: A_tension = A_web
    return A_tension
@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_area_holes(N_r,d_b,t):
    d_holes = d_b + 0.0625 * 2
    A_holes = N_r * d_holes * t
    return A_holes

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_area_net_beam(A_g,A_holes,d,d_top,d_bot,t_f,t_w,n_flange,U_bs = 1,coped = 0):
    A_net = (A_g - A_holes) * U_bs
    if coped ==  1:l_w = d - d_top - d_bot - t_f * n_flange;A_w = l_w * t_w;A_w_net = A_w - A_holes;A_e = min(A_net,A_w_net)
    elif coped == 0: A_e = A_net
    return A_e

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_area_net_plates(A_g,A_holes,U_bs = 1):
    A_e = (A_g - A_holes) * U_bs
    return A_e
@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_tensile_yielding(A_g,F_y,phi):
    P_n_yielding = A_g * F_y
    P_u_yielding = phi * P_n_yielding
    return P_u_yielding
@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_tensile_rupture(A_net,F_u,phi):
    P_n_rupture = A_net * F_u
    P_u_rupture = phi * P_n_rupture
    return P_u_rupture
@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_area_flange(b_f,t_f,n_flange):
    A_flange = b_f * t_f * n_flange
    return A_flange
@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_area_web(d,t_w,t_f,d_top,d_bot):
    d_top_cut = max(d_top,t_f)
    d_bot_cut = max(d_bot,t_f)
    A_web = (d - d_top_cut * d_bot_cut) * t_w
    return A_web
@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_tensile_strength(P_u_yielding,P_u_rupture,n_members=1):
    P_u = min(P_u_yielding,P_u_rupture) * n_members
    return P_u
@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def tension_yielding_rupture(b_f,t_f,t_w,d,N_r, S_r, L_ev, t, d_b, F_y, F_u, phi,n_members,A_g = 0):
    def _calculate_tension_yielding_rupture_bolted(N_r, S_r, L_ev, t, d_b, F_y, F_u, phi,coped = 2):
        if coped == 2:
            l = calculation_connection_length_bolted(N_r, S_r, L_ev)
            A_g = calculation_area_gross(l, t)
            A_holes = calculation_area_holes(N_r, d_b,t)
            A_net = calculation_area_net_plates(A_g, A_holes)
            P_n_yielding = calculation_tensile_yielding(A_g, F_y, 0.9)
            P_n_rupture = calculation_tensile_rupture(A_net, F_u, phi)
            P_u = calculation_tensile_strength(P_n_yielding, P_n_rupture,n_members=n_members)
        elif coped == 0:
            U_bs = calculation_ubs_w_section_uncoped(b_f=b_f,t_f = t_f ,d = d , t_w = t_w , l = l)
    return _calculate_tension_yielding_rupture_bolted(N_r, S_r, L_ev, t, d_b, F_y, F_u, phi)
@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_elastic_modulus(t,l):
    S_g = (t*l**2)/6
    return S_g
@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_plastic_modulus(t,l):
    Z_g = (t*l**2)/4
    return Z_g
@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_plastic_modulus_holes(N_r,S_r,d_b,t):
    d_holes = d_b + 0.0625*2
    Z_holes_1 = (N_r%2) * ((d_b/2) * t) * d_b/4 
    Z_holes_2 = (S_r*N_r**2* d_holes) * t/4
    return Z_holes_1 + Z_holes_2

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_plastic_modulus_net(Z_g,Z_holes):
    Z_net = Z_g - Z_holes
    return Z_net
@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_lambda_flexural(d,F_y,t,e):
    lamb = (d*sqrt(F_y/(1)))/(10*t*sqrt(475+280*(d/e)**2))
    return lamb
@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_Critical_buckling_factor(lamb):
    if lamb <= 0.7: Q = 1
    elif 0.7 < lamb <= 1.41:Q = (1.34 - 0.486*lamb)
    elif lamb > 1.41: Q = 1.30 / (lamb**2)
    return Q
@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_FCR(Q,F_y):
    F_cr = Q*F_y
    return F_cr
@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_flexural_yielding(F_y,Z_g,e):
    V__yielding = (F_y * Z_g)/e
    return V__yielding
@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_flexural_rupture(F_u,Z_net,e):
    V_rupture = (F_u * Z_net)/e
    return V_rupture
@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_flexural_buckling(F_cr,S_g,e):
    V_buckling = (F_cr * S_g)/e
    return V_buckling
@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_eccentricity(l,k_a,L_eh,N_c,_S_c):
    e = l - k_a - L_eh - (N_c - 1) * _S_c
    return e

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def flexural_14th(l , k_a, L_eh, N_c, _S_c, t, N_r, S_r, d_b, d, F_y, F_u, e_override=None):
    d = calculation_connection_length_bolted(N_r, S_r, L_eh) if d is None else d
    e = calculation_eccentricity(l, k_a, L_eh, N_c, _S_c) if e_override is None else e_override
    S_g = calculation_elastic_modulus(t, d)
    Z_g = calculation_plastic_modulus(t, d)
    Z_hole = calculation_plastic_modulus_holes(N_r, S_r, d_b,t)
    Z_net = calculation_plastic_modulus_net(Z_g, Z_hole)
    lamb = calculation_lambda_flexural(d, F_y, t, e)
    critical_buckling_factor = calculation_Critical_buckling_factor(lamb)
    F_cr = calculation_FCR(critical_buckling_factor, F_y)
    V_yielding = calculation_flexural_yielding(F_y, Z_g, e)
    V_rupture = calculation_flexural_rupture(F_u, Z_net, e)
    V_buckling = calculation_flexural_buckling(F_cr, S_g, e)
    V_u = min(V_yielding, V_rupture, V_buckling)
    return V_u

def _calculations(self,Vu,no_bolts,F_nv,F_nt_,A_bolt,phi,detailed:bool):
    @optional_reporting_handcalc(config_object=self.latex_config, detailed=detailed, key = "Parameters",jupyter_display=jupyter_display, precision=3, override="params")
    def parameters(Vu,no_bolts,F_nv,F_nt_,A_bolt,phi):
        Vu = Vu
        no_bolts = no_bolts
        F_nv = F_nv
        F_nt_ = F_nt_
        A_bolt = A_bolt
        phi = phi

    @optional_reporting_handcalc(config_object=self.latex_config, key = "Bolt Tensile Modified Strength Calculations", detailed=detailed,jupyter_display=jupyter_display, precision=3, override=jupyter_format)
    def calculations(Vu,no_bolts,F_nv,F_nt_,A_bolt,phi):
        shear_bolt = Vu / no_bolts
        F_rv = shear_bolt/A_bolt
        interaction_coefficient = F_rv / (phi * F_nv) # Ratio of required shear stress to available shear stress
        F_prime_nt = 1.3 * F_nt_ - F_nt_ * interaction_coefficient 
        F_nt = min(F_prime_nt, F_nt_) * A_bolt * phi
        return F_nt
    
    result = calculations(Vu=Vu,no_bolts=no_bolts,F_nv=F_nv,F_nt_=F_nt_,A_bolt=A_bolt,phi=phi)
    return result
# @optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
# def flexural_15th():
@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def bolt_shear(F_nv, A_bolt, N_shear_planes: int, phi: float,):
    V_n = F_nv * A_bolt * N_shear_planes
    V_u = phi * V_n
    return V_u
@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def bolt_shear_modified(F_nv,F_nt, A_bolt, N_shear_planes: int,n_bolts: int, phi: float,P_u):
    F_rt = P_u / (phi * A_bolt * N_shear_planes)
    F_nv_prime = 1.3 * F_nv - F_nv * (F_rt / F_nt)
    F_nv_prime = min(F_nv,max(F_nv_prime, 0))  # Ensure F_nv_prime is not negative
    V_n = F_nv_prime * A_bolt * N_shear_planes
    V_u = phi * V_n
    return V_u
@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_bolt_tension_modified(F_nv,F_nt, A_bolt, n_bolts: int, phi: float,V_u):
    F_rv = V_u / (phi * A_bolt * n_bolts)
    F_nt_prime_ = max(1.3 * F_nt - F_nt * (F_rv / F_nv),0)
    F_nt_prime = min(F_nt,F_nt_prime_)  
    P_u = F_nt_prime * A_bolt * 0.9
    return P_u

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_b_prying(L_osl, L_eh, t):
    b = L_osl - L_eh - t/2
    return b
@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_b_prime_prying(b,d_bolt):
    b_prime = b - 0.5 * d_bolt
    return b_prime
@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_a_prying(L_eh):
    a = L_eh
    return a

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_a_prime_prying(a,b,d_bolt):
    a_prime = min(1.25*b,a ) + 0.5 * d_bolt

    return a_prime
@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_tributary_length_prying(S_r,ga,b,L_ev):
    p_1 = L_ev + 0.5 *S_r
    p_2 = 2 * b
    p = min(p_1, p_2,ga,S_r)
    return p
@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_delta_prying(dv,p):
    delta = 1 - dv/p
    return delta

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_rho_prying(b_prime,a_prime):
    rho = b_prime/a_prime
    return rho
@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_beta_prying(rho,N_t,B,P_u,p):
    beta = (1/rho) * (((2*N_t*B)/P_u )- 1)
    return beta
@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_alpha_prime_prying(beta,delta   ):
    if beta >= 1: alpha_prime = 1
    else: alpha_prime = min(1,(1/delta)*(beta/(1-beta)))
    return alpha_prime

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_area_bolt(d):
    A_bolt = ((d**2)/4) * pi
    return A_bolt
@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_prying_action(t, F_u, N_t, p, b_prime, delta, alpha_prime, prying):
    if not prying: P_n = (t**2*(p*F_u)*(2*N_t))/(4*b_prime)
    else: P_n = ((2*N_t*t**2*p*F_u)/(4*b_prime))*(1+delta*alpha_prime)
    return P_n
@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def prying_action(t, F_u,F_nv,F_nt, N_t,n_bolts, L_osl, L_eh, L_ev, d_bolt, dv, S_r, ga,V_u, P_u, prying: bool):
    A_bolt = calculation_area_bolt(d_bolt)
    B = calculation_bolt_tension_modified(F_nv = F_nv,F_nt = F_nt, A_bolt = A_bolt, n_bolts= n_bolts, phi = 0.9,V_u = V_u)
    b = calculation_b_prying(L_osl=L_osl, L_eh=L_eh, t=t)
    b_prime = calculation_b_prime_prying(b=b, d_bolt=d_bolt)
    a = calculation_a_prying(L_eh=L_eh)
    a_prime = calculation_a_prime_prying(a=a, b=b, d_bolt=d_bolt)
    p = calculation_tributary_length_prying(S_r=S_r, ga=ga, b=b, L_ev=L_ev)
    delta = calculation_delta_prying(dv=dv, p=p)
    rho = calculation_rho_prying(b_prime=b_prime, a_prime=a_prime)
    beta = calculation_beta_prying(rho=rho, N_t=N_t, B=B, P_u=P_u, p=p)
    alpha_prime = calculation_alpha_prime_prying(beta=beta, delta=delta)
    
    P_n = calculation_prying_action(t=t, F_u=F_u, N_t=N_t, p=p, b_prime=b_prime, delta=delta, alpha_prime=alpha_prime, prying=prying)
    return P_n
