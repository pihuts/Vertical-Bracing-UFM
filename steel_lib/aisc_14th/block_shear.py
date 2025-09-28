import numpy as np
from math import sqrt, pi, inf
from .utils import optional_reporting_handcalc, detailed, calculation_area

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_length_l_path_1(N_r, S_r, L_ev, d_hole):
    l = (N_r - 1) * S_r + L_ev
    l_net = l - (N_r - 0.5) * d_hole
    return l, l_net

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_length_l_path_2(N_c, S_c, t, L_eh, d_hole):
    l = (N_c - 1) * S_c + L_eh
    l_net = l - (N_c - 0.5) * d_hole
    return l, l_net

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_length_u_path_1(N_r, S_r, L_ev, d_hole):
    l = (N_r - 1) * S_r 
    l_net = l - (N_r - 1) * d_hole
    return l, l_net

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_length_u_path_2(N_c, S_c, t, L_eh, d_hole):
    l = ((N_c - 1) * S_c + L_eh) * 2
    l_net = (l - (N_c - 0.5) * d_hole * 2) 
    return l, l_net

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_shear_component(A_g, A_net, F_y, F_u):
    V_yield = 0.6 * F_y * A_g 
    V_rupture = 0.6 * F_u * A_net
    V_n = min(V_yield, V_rupture)
    return V_n

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_tensile_component(A_g, A_net, F_y, F_u, U_bs=1.0):    
    P_n = F_u * A_net * U_bs
    return P_n

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_block_shear(V_n, P_n, phi, n_members=1):
    R_u = phi * (V_n + P_n) * n_members
    return R_u

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed) 
def calculate_path1_pu(N_r, S_r, N_c, S_c, L_ev, L_eh, dv_hole, dh_hole, t, F_y, F_u, phi, n_members=1):
    l_path1, l_net_path1 = calculation_length_l_path_1(N_r, S_r, L_ev, dv_hole)
    A_gt_path1, A_nt_path1 = calculation_area(l_path1, l_net_path1, t)
    P_n1 = calculation_tensile_component(A_gt_path1, A_nt_path1, F_y, F_u)
    l_path2, l_net_path2 = calculation_length_l_path_2(N_c, S_c, t, L_eh, dh_hole)
    A_gv_path1, A_nv_path1 = calculation_area(l_path2, l_net_path2, t)
    V_n1 = calculation_shear_component(A_gv_path1, A_nv_path1, F_y, F_u)
    R_n_path1 = calculation_block_shear(V_n1, P_n1, phi, n_members=n_members)
    return R_n_path1

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculate_path2_pu(N_r, S_r, N_c, S_c, L_ev, L_eh, dv_hole, dh_hole, t, F_y, F_u, phi, n_members=1):
    u_path1, u_net_path1 = calculation_length_u_path_1(N_r, S_r, L_ev, dv_hole)
    A_gt_path2, A_nt_path2 = calculation_area(u_path1, u_net_path1, t)
    P_n2 = calculation_tensile_component(A_gt_path2, A_nt_path2, F_y, F_u)
    u_path2, u_net_path2 = calculation_length_u_path_2(N_c, S_c, t, L_eh, dh_hole)
    A_gv_path2, A_nv_path2 = calculation_area(u_path2, u_net_path2, t)
    V_n2 = calculation_shear_component(A_gv_path2, A_nv_path2, F_y, F_u)
    R_n_path2 = calculation_block_shear(V_n2, P_n2, phi, n_members=n_members)
    return R_n_path2

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculate_path1_vu(N_r, S_r, N_c, S_c, L_ev, L_eh, dv_hole, dh_hole, t, F_y, F_u, phi, coped=False, n_members=1):
    l_path1, l_net_path1 = calculation_length_l_path_1(N_r, S_r, L_ev, dv_hole)
    A_gv_path1, A_nv_path1 = calculation_area(l_path1, l_net_path1, t)
    V_n1 = calculation_shear_component(A_gv_path1, A_nv_path1, F_y, F_u)
    l_path2, l_net_path2 = calculation_length_l_path_2(N_c, S_c, t, L_eh, dh_hole)
    A_gt_path1, A_nt_path1 = calculation_area(l_path2, l_net_path2, t)
    U_bs = 0.5 if coped else 1.0
    P_n1 = calculation_tensile_component(A_gt_path1, A_nt_path1, F_y, F_u, U_bs=U_bs)
    R_n_path1 = calculation_block_shear(V_n1, P_n1, phi, n_members=n_members)
    return R_n_path1

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def block_shear(P_u, V_u, F_y, F_u, t, N_r, S_r, N_c, S_c, L_ev, L_eh, d_v, d_h, phi, coped, n_members=1):
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
        R_n_path1 = calculation_block_shear(V_n1, P_n1, phi, n_members=n_members)
        
        u_path1, u_net_path1 = calculation_length_u_path_1(N_r, S_r, L_ev, dv_hole)
        A_gt_path2, A_nt_path2 = calculation_area(u_path1, u_net_path1, t)
        P_n2 = calculation_tensile_component(A_gt_path2, A_nt_path2, F_y, F_u)
        u_path2, u_net_path2 = calculation_length_u_path_2(N_c, S_c, t, L_eh, dh_hole)
        A_gv_path2, A_nv_path2 = calculation_area(u_path2, u_net_path2, t)
        V_n2 = calculation_shear_component(A_gv_path2, A_nv_path2, F_y, F_u)
        R_n_path2 = calculation_block_shear(V_n2, P_n2, phi, n_members=n_members)
            
    if V_u:
        l_path1, l_net_path1 = calculation_length_l_path_1(N_r, S_r, L_ev, dv_hole)
        A_gv_path1, A_nv_path1 = calculation_area(l_path1, l_net_path1, t)
        V_n1 = calculation_shear_component(A_gv_path1, A_nv_path1, F_y, F_u)
        l_path2, l_net_path2 = calculation_length_l_path_2(N_c, S_c, t, L_eh, dh_hole)
        A_gt_path1, A_nt_path1 = calculation_area(l_path2, l_net_path2, t)
        U_bs = 0.5 if coped else 1.0
        P_n1 = calculation_tensile_component(A_gt_path1, A_nt_path1, F_y, F_u, U_bs=U_bs)
        R_n_path1 = calculation_block_shear(V_n1, P_n1, phi, n_members=n_members)
    return min(R_n_path1, R_n_path2)