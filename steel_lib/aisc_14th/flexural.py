import numpy as np
from math import sqrt, pi, inf, log as ln
from .utils import (optional_reporting_handcalc, detailed, calculation_elastic_modulus,
                   calculation_plastic_modulus, calculation_plastic_modulus_holes,
                   calculation_plastic_modulus_net, calculation_plate_length_bolted)

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_lambda_flexural(d, F_y, t, e):
    lamb = (d*sqrt(F_y/(1)))/(10*t*sqrt(475+280*(d/e)**2))
    return lamb

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_Critical_buckling_factor(lamb):
    if lamb <= 0.7: Q = 1
    elif 0.7 < lamb <= 1.41:Q = (1.34 - 0.486*lamb)
    elif lamb > 1.41: Q = 1.30 / (lamb**2)
    return Q

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_FCR(Q, F_y):
    F_cr = Q*F_y
    return F_cr

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_flexural_yielding(F_y, Z_g, e):
    V__yielding = (F_y * Z_g)/e
    return V__yielding

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_flexural_rupture(F_u, Z_net, e):
    V_rupture = (F_u * Z_net)/e
    return V_rupture

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_flexural_buckling(F_cr, S_g, e):
    V_buckling = (F_cr * S_g)/e
    return V_buckling

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_eccentricity(l, k_a, L_eh, N_c, _S_c):
    e = l - k_a - L_eh - (N_c - 1) * _S_c
    return e

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_unbraced_length(a=None, s_b=None, W=None, g_a=None, k_a=None, t=None):
    if a is not None: L_u = a
    elif s_b is not None and W is not None:L_u = s_b + min(W, 0.3125)
    elif g_a is not None and k_a is not None and t is not None: L_u = (g_a + t) / 2 - k_a
    else:L_u = 0.0  # Default value for Numba compatibility
    return L_u

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_C_b(L_b, d, d_ct):
    C_b = max((3 + ln(L_b/d))*(1-d_ct/d), 1.84)
    return C_b

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_moment_plastic_plates(F_y, S_x, Z_x):
    M_p = min(F_y * Z_x, 1.6* F_y * S_x)
    return M_p

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_moment_elastic_plates(F_y, S_x):
    M_y = F_y * S_x
    return M_y

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_flexural_yielding_plates(M_y, M_p, e):
    M_n_yield = min(M_p, 1.6*M_y)
    V_n_yield = M_n_yield / e
    return V_n_yield

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_lateral_torsional_buckling(C_b, M_p, M_y, L_u, d, t, F_y, E, S_x, e):
    lamb_p = (L_u*d)/t**2
    lamb_l = (0.08*E)/F_y
    lamb_u = (1.9 * E)/F_y
    if lamb_p <= lamb_l:M_n_LTB = inf
    elif lamb_l < lamb_p <=lamb_u: M_n_LTB = min(C_b*(1.52 - 0.274*(lamb_p)*(F_y/E)) * M_y, M_p)
    elif lamb_p > lamb_u :F_cr = (1.9*E*C_b)/lamb_p; M_n_LTB = min(F_cr *S_x,M_p)
    V_n_LTB = M_n_LTB / e
    return V_n_LTB

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_flexural_rupture_plates(F_u, Z_x, e):
    M_n_rupture = F_u * Z_x
    V_n_rupture = M_n_rupture / e
    return V_n_rupture

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_dr(d_b, d_plate, L_ev):
    d_r = (d_b - d_plate)/2 + L_ev
    return d_r

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_flexural_strength(V_n_yielding, V_n_buckling, V_n_rupture, member_type):
    if member_type == "PL": V_n = min(V_n_yielding, V_n_buckling, V_n_rupture)#PL 0
    elif member_type == "L": V_n = min(V_n_yielding, V_n_buckling)#L 1
    return V_n

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def flexural_14th(l, k_a, L_eh, N_c, _S_c, t, N_r, S_r, d_b, d, F_y, F_u, e_override=None):
    d = calculation_plate_length_bolted(N_r, S_r, L_eh) if d is None else d
    e = calculation_eccentricity(l, k_a, L_eh, N_c, _S_c) if e_override is None else e_override
    S_g = calculation_elastic_modulus(t, d)
    Z_g = calculation_plastic_modulus(t, d)
    Z_hole = calculation_plastic_modulus_holes(N_r, S_r, d_b, t)
    Z_net = calculation_plastic_modulus_net(Z_g, Z_hole)
    lamb = calculation_lambda_flexural(d, F_y, t, e)
    critical_buckling_factor = calculation_Critical_buckling_factor(lamb)
    F_cr = calculation_FCR(critical_buckling_factor, F_y)
    V_yielding = calculation_flexural_yielding(F_y, Z_g, e)
    V_rupture = calculation_flexural_rupture(F_u, Z_net, e)
    V_buckling = calculation_flexural_buckling(F_cr, S_g, e)
    V_u = min(V_yielding, V_rupture, V_buckling)
    return V_u

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def flexural_15th(member_type, a=None, s_b=None, W=None, g_a=None, k_a=None, t=None, F_y=None, E=None, d_b=None, L_ev=0, F_u=None, N_r=None, S_r=None, d_bolt=None):
    if member_type == "PL" or member_type == "L":
        d_plate = calculation_plate_length_bolted(N_r, S_r, L_ev)
        d_r = calculation_dr(d_b=d_b, d_plate=d_plate, L_ev=L_ev)# this variable will be computed as it needs the properties of 2 members connected
        L_u = calculation_unbraced_length(a=a, s_b=s_b, W=W, g_a=g_a, k_a=k_a, t=t) 
        S_x = calculation_elastic_modulus(t, d_plate)
        Z_x = calculation_plastic_modulus(t, d_plate)
        Z_g_holes = calculation_plastic_modulus_holes(N_r, S_r, d_bolt, t)
        Z_g_net = calculation_plastic_modulus_net(Z_x, Z_g_holes)
        M_p = calculation_moment_plastic_plates(F_y, S_x, Z_x)
        M_y = calculation_moment_elastic_plates(F_y, S_x)
        V_n_yielding = calculation_flexural_yielding_plates(M_y, M_p, e=L_u)
        C_b = calculation_C_b(L_u, d_plate, d_r)
        V_n_buckling = calculation_lateral_torsional_buckling(C_b, M_p, M_y, L_u, d_plate, t, F_y, E, S_x, e=L_u)
        V_n_rupture = calculation_flexural_rupture_plates(F_u, Z_g_net, e=L_u)
        V_n = calculation_flexural_strength(V_n_yielding, V_n_buckling, V_n_rupture, member_type)
        return V_n