import numpy as np
from math import sqrt, pi, inf
from .utils import optional_reporting_handcalc, detailed
from .bolt_shear_tension import calculation_bolt_tension_modified, calculation_area_bolt

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_b_prying(L, L_eh, t=0):
    b = L - L_eh - t/2
    return b

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_b_prime_prying(b, d_bolt):
    b_prime = b - 0.5 * d_bolt
    return b_prime

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_a_prying(L_eh):
    a = L_eh
    return a

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_a_prime_prying(a, b, d_bolt):
    a_prime = min(1.25*b, a) + 0.5 * d_bolt
    return a_prime

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_tributary_length_prying(S_r, ga, b, L_ev):
    p_1 = L_ev + 0.5 * S_r
    p_2 = 2 * b
    p = min(p_1, p_2, ga, S_r)
    return p

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_delta_prying(dv, p):
    delta = 1 - dv/p
    return delta

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_rho_prying(b_prime, a_prime):
    rho = b_prime/a_prime
    return rho

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_beta_prying(rho, N_t, B, P_u, p):
    beta = (1/rho) * (((2*N_t*B)/P_u) - 1)
    return beta

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_alpha_prime_prying(beta, delta):
    if beta >= 1: alpha_prime = 1
    else: alpha_prime = min(1, (1/delta)*(beta/(1-beta)))
    return alpha_prime

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def calculation_prying_action(t, F_u, N_t, p, b_prime, delta, alpha_prime, prying):
    if not prying: P_n = (t**2*(p*F_u)*(2*N_t))/(4*b_prime)
    else: P_n = ((2*N_t*t**2*p*F_u)/(4*b_prime))*(1+delta*alpha_prime)
    return P_n

@optional_reporting_handcalc(config_object=None, key=None, detailed=detailed)
def prying_action(t, F_u, F_nv, F_nt, N_t, n_bolts, L, L_eh, L_ev, d_bolt, dv, S_r, ga, V_u, P_u, prying: bool, bf=None):
    A_bolt = calculation_area_bolt(d_bolt)
    B = calculation_bolt_tension_modified(F_nv=F_nv, F_nt=F_nt, A_bolt=A_bolt, n_bolts=n_bolts, phi=0.9, V_u=V_u)
    if bf:
        L = ga/2
        b = calculation_b_prying(L=L, L_eh=0, t=t)
        p = calculation_tributary_length_prying(S_r=S_r, ga=ga, b=b, L_ev=np.inf)
    else:b = calculation_b_prying(L=L, L_eh=L_eh, t=t);p = calculation_tributary_length_prying(S_r=S_r, ga=ga, b=b, L_ev=L_ev)

    b_prime = calculation_b_prime_prying(b=b, d_bolt=d_bolt)
    a = calculation_a_prying(L_eh=L_eh)
    a_prime = calculation_a_prime_prying(a=a, b=b, d_bolt=d_bolt)
    
    delta = calculation_delta_prying(dv=dv, p=p)
    rho = calculation_rho_prying(b_prime=b_prime, a_prime=a_prime)
    beta = calculation_beta_prying(rho=rho, N_t=N_t, B=B, P_u=P_u, p=p)
    alpha_prime = calculation_alpha_prime_prying(beta=beta, delta=delta)
    P_n = calculation_prying_action(t=t, F_u=F_u, N_t=N_t, p=p, b_prime=b_prime, delta=delta, alpha_prime=alpha_prime, prying=prying)
    return P_n