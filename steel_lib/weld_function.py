import math
from math import sin, sqrt
import steel_lib.si_units as si
from steel_lib.latext import optional_reporting_handcalc, LatexConfig, jupyter_format
from steel_lib.data_models import ConnectionComponent
from steel_lib.debugging import check_dcr


def calculate_weld_capacity_and_dcr(
    # Load parameters
    Vu,  # Shear force on the weld
    Peq,  # Equivalent axial force
    Pu,  # Axial force on the weld
    Rw,  # Resultant weld force
    
    # Material properties
    Fy,  # Yield strength of the member
    Fu,  # Ultimate strength of the member
    t,   # Thickness of the member
    
    # Weld properties
    f_exx,       # Effective weld strength (electrode)
    weld_size,   # Size of the weld
    weld_length, # Length of the weld
    
    # Configuration
    connection_component=ConnectionComponent.GUSSET_LENGTH,
    member_role=None,
    detailed=False,
    latex_config=None
):
    """
    Calculates weld capacity and demand-to-capacity ratio.
    
    This function performs the same calculations as the WeldCalculator class
    but as a standalone function.
    
    Parameters:
    -----------
    Vu : float with units
        Shear force on the weld
    Peq : float with units
        Equivalent axial force
    Pu : float with units
        Axial force on the weld
    Rw : float with units
        Resultant weld force
    Fy : float with units
        Yield strength of the member
    Fu : float with units
        Ultimate strength of the member
    t : float with units
        Thickness of the member
    f_exx : float with units
        Effective weld strength (electrode)
    weld_size : float with units
        Size of the weld
    weld_length : float with units
        Length of the weld
    connection_component : ConnectionComponent, optional
        Connection component type (default: GUSSET_LENGTH)
    member_role : str, optional
        Role of the member (e.g., "Column", "endplate")
    detailed : bool, optional
        Whether to show detailed calculations (default: False)
    latex_config : LatexConfig, optional
        LaTeX configuration for reporting
    
    Returns:
    --------
    tuple
        (dcr_result, latex_config) where dcr_result is the demand-to-capacity ratio
        and latex_config contains the calculation documentation
    
    Raises:
    -------
    ValueError
        If weld_length is None or <= 0
    """
    
    # Input validation
    if weld_length is None or weld_length <= 0:
        raise ValueError("Weld length must be a positive value.")
    
    # Set up LaTeX configuration if not provided
    if latex_config is None:
        latex_config = LatexConfig(main_title="Weld Strength")
    
    def _calculate_capacity():
        """
        Performs intermediate calculations for weld design.
        """
        @optional_reporting_handcalc(
            config_object=latex_config,
            key="Controlling Angle",
            jupyter_display=False,
            override=jupyter_format,
            precision=3,
            detailed=detailed
        )
        def _controlling_angle(V_u, P_eq, P_u):
            theta_w = math.atan((V_u + P_eq) / P_u) 
            k_ds = (1 + 0.5 * sin(theta_w)**1.5)
            return k_ds
        
        @optional_reporting_handcalc(
            config_object=latex_config,
            key="Weld Limit",
            jupyter_display=False,
            override=jupyter_format,
            precision=3,
            detailed=detailed
        )
        def _calculation_weld_limit(F_ygp, F_ugp, t_gp, F_uw, W_size):
            k_factor_ty = 0.9
            k_factor_tr = 0.75
            k_factor_weld = 0.75
            W_limit = min(
                max(F_ygp, 50*si.ksi) * t_gp * k_factor_ty, 
                max(F_ugp, 65*si.ksi) * t_gp * k_factor_tr
            ) / (k_factor_weld * 2 * 0.60 * F_uw * 1.5 * (0.5 * sqrt(2)))
            W_weld = min(W_size, W_limit)
            return W_limit, W_weld
        
        @optional_reporting_handcalc(
            config_object=latex_config,
            key="Weld Strength",
            jupyter_display=False,
            override=jupyter_format,
            precision=3,
            detailed=detailed
        )
        def _calculation_weld_strength(L_b, W_size, W_limit, k_ds, F_exx, phi):
            L_weld = L_b - 2 * min(W_size, 0.3125*si.inch) 
            W_weld = min(W_size, W_limit)
            R_n = 0.6 * F_exx * sqrt(2)/2 * W_weld * 2 * L_weld * k_ds
            R_u = phi * R_n
            return R_u
        
        # Determine weld orientation based on connection component and member role
        print(connection_component, member_role)
        if connection_component == ConnectionComponent.GUSSET_LENGTH:
            weld_orientation = "horizontal"
        elif connection_component == ConnectionComponent.GUSSET_WIDTH:
            weld_orientation = "vertical"
        elif member_role == "Column":
            weld_orientation = "vertical"
        elif member_role == "endplate":
            weld_orientation = "vertical"
        
        # Perform calculations
        k_ds = _controlling_angle(V_u=Vu, P_eq=Peq, P_u=Pu)
        W_limit, W_weld = _calculation_weld_limit(
            F_ygp=Fy, F_ugp=Fu, t_gp=t, F_uw=f_exx, W_size=weld_size
        )
        R_u = _calculation_weld_strength(
            L_b=weld_length, W_size=W_weld, W_limit=W_limit, 
            k_ds=k_ds, F_exx=f_exx, phi=0.75
        )
        
        print(f"theta:{k_ds}, w_limit:{W_limit}, W_weld:{W_weld}, R_u:{R_u}")
        return R_u
    
    # Calculate capacity
    capacity = _calculate_capacity()
    
    # Calculate demand-to-capacity ratio
    demand = abs(max(Rw, Vu))
    dcr_result = check_dcr(
        capacity=capacity, 
        demand=demand, 
        limit_state_name="Weld"
    )
    
    return dcr_result, latex_config