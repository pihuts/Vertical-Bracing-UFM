import numpy as np
from math import sqrt, pi, inf
from .utils import optional_reporting_handcalc, detailed

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def bolt_shear(F_nv, A_bolt, N_shear_planes: int, phi: float):
    V_n = F_nv * A_bolt * N_shear_planes
    V_u = phi * V_n
    return V_u

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def bolt_shear_modified(F_nv, F_nt, A_bolt, N_shear_planes: int, n_bolts: int, phi: float, P_u):
    F_rt = P_u / (phi * A_bolt * N_shear_planes)
    F_nv_prime = 1.3 * F_nv - F_nv * (F_rt / F_nt)
    F_nv_prime = min(F_nv, max(F_nv_prime, 0))  # Ensure F_nv_prime is not negative
    V_n = F_nv_prime * A_bolt * N_shear_planes
    V_u = phi * V_n
    return V_u

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_bolt_tension_modified(F_nv, F_nt, A_bolt, n_bolts: int, phi: float, V_u):
    F_rv = V_u / (phi * A_bolt * n_bolts)
    F_nt_prime_ = max(1.3 * F_nt - F_nt * (F_rv / F_nv), 0)
    F_nt_prime = min(F_nt, F_nt_prime_)  
    P_u = F_nt_prime * A_bolt * 0.9
    return P_u

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_area_bolt(d):
    A_bolt = ((d**2)/4) * pi
    return A_bolt