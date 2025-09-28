import numpy as np
from math import sqrt, pi, inf
from .utils import optional_reporting_handcalc, detailed, calculation_area_gross, calculation_area_holes, calculation_plate_length_bolted

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_ubs_w_section_uncoped(b_f, t_f, d, t_w, l):
    A_flange = (b_f/2 * t_f)
    M_arm_flange = (b_f/4)
    A_web = (d - 2*t_f)* t_w/2
    M_arm_web = t_w/4
    x_g = ((A_flange * M_arm_flange * 2) + (A_web * M_arm_web)) / (A_flange * 2 + A_web)
    U_bs_1 = 1 - x_g/l
    return U_bs_1

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_ubs_w_section_coped(A_g, A_conn, t_f, d, t_w, n_flange, d_top, d_bot, U_bs_1=None):
    U_bs_limit = A_conn / A_g
    if U_bs_1: U_bs = max(U_bs_limit, U_bs_1)
    else: U_bs = U_bs_limit
    return U_bs

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_area_tension_beams(A_flange, A_web, coped):
    if coped == 0: A_tension = A_flange + A_web
    elif coped > 0: A_tension = A_web
    return A_tension

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_area_net_beam(A_g, A_holes, d, d_top, d_bot, t_f, t_w, n_flange, U_bs=1, coped=0):
    A_net = (A_g - A_holes) * U_bs
    if coped == 1:l_w = d - d_top - d_bot - t_f * n_flange;A_w = l_w * t_w;A_w_net = A_w - A_holes;A_e = min(A_net,A_w_net)
    elif coped == 0: A_e = A_net
    return A_e

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_area_net_plates(A_g, A_holes, U_bs=1):
    A_e = (A_g - A_holes) * U_bs
    return A_e

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_tensile_yielding(A_g, F_y, phi):
    P_n_yielding = A_g * F_y
    P_u_yielding = phi * P_n_yielding
    return P_u_yielding

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_tensile_rupture(A_net, F_u, phi):
    P_n_rupture = A_net * F_u
    P_u_rupture = phi * P_n_rupture
    return P_u_rupture

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_area_flange(b_f, t_f, n_flange):
    A_flange = b_f * t_f * n_flange
    return A_flange

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_area_web(d, t_w, t_f, d_top, d_bot):
    d_top_cut = max(d_top, t_f)
    d_bot_cut = max(d_bot, t_f)
    A_web = (d - d_top_cut * d_bot_cut) * t_w
    return A_web

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_tensile_strength(P_u_yielding, P_u_rupture, n_members=1):
    P_u = min(P_u_yielding, P_u_rupture) * n_members
    return P_u

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def tension_yielding_rupture(b_f, t_f, t_w, d, N_r, S_r, L_ev, t, d_b, F_y, F_u, phi, n_members, A_g=0):
    def _calculate_tension_yielding_rupture_bolted(N_r, S_r, L_ev, t, d_b, F_y, F_u, phi, coped=2):
        if coped == 2:
            l = calculation_plate_length_bolted(N_r, S_r, L_ev)
            A_g = calculation_area_gross(l, t)
            A_holes = calculation_area_holes(N_r, d_b, t)
            A_net = calculation_area_net_plates(A_g, A_holes)
            P_n_yielding = calculation_tensile_yielding(A_g, F_y, 0.9)
            P_n_rupture = calculation_tensile_rupture(A_net, F_u, phi)
            P_u = calculation_tensile_strength(P_n_yielding, P_n_rupture, n_members=n_members)
        elif coped == 0:
            U_bs = calculation_ubs_w_section_uncoped(b_f=b_f, t_f=t_f, d=d, t_w=t_w, l=l)
    return _calculate_tension_yielding_rupture_bolted(N_r, S_r, L_ev, t, d_b, F_y, F_u, phi)