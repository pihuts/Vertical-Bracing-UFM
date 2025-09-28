from numpy import atan, sin, cos, tan
import numpy as np
from math import sqrt, pi, inf
from .utils import optional_reporting_handcalc, detailed

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_bolt_bearing(l_c_inner, l_c_edge, t, F_u, N_bolts, d_bolt, phi, c):
    V_u_bearing = 2.4 * d_bolt * t * F_u
    V_u_inner_1 = 1.2 * l_c_inner * t * F_u
    V_u_inner = min(V_u_inner_1, V_u_bearing) * (N_bolts - 1)
    V_u_edge_1 = 1.2 * l_c_edge * t * F_u * 1
    V_u_edge = min(V_u_edge_1, V_u_bearing)
    V_u = (V_u_inner + V_u_edge)*(c/N_bolts) * phi
    return V_u

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_lc(theta, L_edge_1, L_edge_2, S, d_hole):
    if theta != 0:L_c_1 = L_edge_1/sin(theta) - 0.5*d_hole;L_c_2 = S/cos(theta) - d_hole;L_c_3 = L_edge_2/cos(theta) - 0.5*d_hole;lc_inner = min(L_c_1,L_c_2);lc_edge = min(L_c_1,L_c_3)
    elif theta == 0: lc_inner = S/cos(theta) - d_hole;lc_edge = L_edge_2/cos(theta) - 0.5*d_hole
    return lc_inner, lc_edge

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_theta(P_u, V_u):
    if P_u == 0: theta = 0
    else: theta = atan(P_u/V_u)
    return theta

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