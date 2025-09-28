import numpy as np
from math import sqrt, pi, inf
from .utils import optional_reporting_handcalc, detailed, calculation_area_gross, calculation_area_holes, calculation_plate_length_bolted

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_area_net_plates(A_g, A_holes):
    A_net = A_g - A_holes
    return A_net

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_shear_yielding(A_g, F_y, phi):
    V_n_yielding = 0.6 * A_g * F_y
    V_u_yielding = phi * V_n_yielding
    return V_u_yielding

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_shear_rupture(A_net, F_u, phi):
    V_n_rupture = 0.6 * A_net * F_u
    V_u_rupture = V_n_rupture * phi
    return V_u_rupture

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_shear_strength(V_u_yielding, V_u_rupture, n_members=1, coped=0):
    if coped == 2: V_u = min(V_u_yielding, V_u_rupture) * n_members
    else: V_u = V_u_yielding * n_members
    return V_u

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def shear_yielding_rupture(N_r, S_r, L_ev, t, d_b, F_y, F_u, phi, n_members=1, coped=0):
    def _calculate_shear_yielding_rupture_bolted(N_r, S_r, L_ev, t, d_b, F_y, F_u, phi):
        l = calculation_plate_length_bolted(N_r, S_r, L_ev)
        A_g = calculation_area_gross(l, t)
        A_holes = calculation_area_holes(N_r, d_b, t)
        A_net = calculation_area_net_plates(A_g, A_holes)
        V_u_yielding = calculation_shear_yielding(A_g, F_y, 1)
        V_u_rupture = calculation_shear_rupture(A_net, F_u, phi)
        V_u = calculation_shear_strength(V_u_yielding, V_u_rupture, n_members=n_members, coped=coped)
        return V_u
    return _calculate_shear_yielding_rupture_bolted(N_r, S_r, L_ev, t, d_b, F_y, F_u, phi)