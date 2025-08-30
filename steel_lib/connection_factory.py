from dataclasses import dataclass
from typing import Any, Optional, Union

from steel_lib.data_models import (
    ConnectionEndpoint,
    ConnectionComponent,
    BoltConfiguration,
    WeldConfiguration,DesignLoads,GlobalLoads,result
)
from steel_lib.calculations import (
    ConnectionCapacityCalculator,
    BlockShearCalculator,
    PryingActionCalculator,
    ShearYieldingCalculator,
    WebLocalYieldingCalculator,
    CompressionBucklingCalculator,
    TensileRuptureCalculator,
    TensileYieldingCalculator,LimitState

)
from steel_lib import si
@dataclass
class Connection:
    """
    A unified connection class that explicitly defines the two members and their
    respective components being joined.
    """
    member_a: ConnectionEndpoint
    member_b: ConnectionEndpoint
    configuration: Union["BoltConfiguration", "WeldConfiguration"]
    global_loads: Optional[GlobalLoads] = None
    override_Ag: Optional[float] = None  # Allow manual override of gross area
    design_method: str = "LRFD"  # Default design method
    shear_condition = max(member_a.member.loading_condition, member_b.member.loading_condition)
    def __post_init__(self):
        """
        Automatically transforms and assigns global loads to the respective
        connection endpoints after the connection is initialized.
        """
        if self.global_loads:
            self._transform_and_assign_loads()

    def _transform_and_assign_loads(self):
        """
        Determines member roles and assigns the appropriate DesignLoads.
        It prioritizes explicit roles and falls back to a heuristic based
        on connection topology if roles are not provided.
        """
        # Step 1: Define transformation rules for each role
        transformation_rules = {
            'BEAM':       {'Pu': self.global_loads.fx, 'Vu': self.global_loads.fy},
            'COLUMN':     {'Pu': self.global_loads.fy, 'Vu': self.global_loads.fx},
            'GIRDER':     {'Pu': self.global_loads.fx, 'Vu': self.global_loads.fy},
            'END_PLATE':  {'Pu': self.global_loads.fy, 'Vu': self.global_loads.fx},
            'SHEAR_PLATE':{'Pu': self.global_loads.fx, 'Vu': self.global_loads.fy},
            'BRACE':   {'Pu': self.global_loads.direct_load, 'Vu': 0 * si.kip},
        }

        # Step 2: Assign loads based on explicit roles if they exist
        # Check member_a
        if self.member_a.role in transformation_rules:
            self.member_a.loads = DesignLoads(**transformation_rules[self.member_a.role])
        # Check member_b
        if self.member_b.role in transformation_rules:
            self.member_b.loads = DesignLoads(**transformation_rules[self.member_b.role])

        # If both roles were provided and handled, the job is done.
        if self.member_a.role and self.member_b.role:
            return

        # Step 3: Fallback to heuristic if one or both explicit roles are not provided
        if not (self.member_a.role and self.member_b.role):
            if self.member_a.component in [ConnectionComponent.WEB, ConnectionComponent.FLANGE]:
                primary_member_endpoint = self.member_a
                secondary_member_endpoint = self.member_b
            elif self.member_b.component in [ConnectionComponent.WEB, ConnectionComponent.FLANGE]:
                primary_member_endpoint = self.member_b
                secondary_member_endpoint = self.member_a
            else:
                primary_member_endpoint = self.member_a
                secondary_member_endpoint = self.member_b

            # Apply transformations based on inferred roles, only if not explicitly set
            if not primary_member_endpoint.role:
                primary_member_endpoint.loads = DesignLoads(Pu=self.global_loads.fy, Vu=self.global_loads.fx)
            if not secondary_member_endpoint.role:
                secondary_member_endpoint.loads = DesignLoads(Pu=self.global_loads.fx, Vu=self.global_loads.fy)
        
    @classmethod
    def check_limit_states(cls,limit_states : LimitState):
        """
        Checks if the connection meets the required limit states based on the
        assigned loads and configuration.
        """
        # Placeholder for actual limit state checks
        results = []
        for limit_state in limit_states:
            calculator = limit_state(cls)
            result = calculator.check_dcr()
            results.append(result)


@dataclass
class ConnectionFactory:
    """Factory for creating Connection objects."""
    connection:Connection = None

    @staticmethod
    def create_bolted_connection(self,
        member_a: Any,
        member_b: Any,
        component_a: ConnectionComponent = ConnectionComponent.TOTAL,
        component_b: ConnectionComponent = ConnectionComponent.TOTAL,
        *args, **kwargs
    ) -> Connection:
        """
        Creates a bolted connection, explicitly defining the two members and their
        connected components.
        """
        override_ag = kwargs.pop('override_Ag', None)
        global_loads = kwargs.pop('global_loads', None)
        role_a = member_a.Role 
        role_b = member_b.Role 
        endpoint_a = ConnectionEndpoint(member=member_a, component=component_a, role=role_a)
        endpoint_b = ConnectionEndpoint(member=member_b, component=component_b, role=role_b)

        return Connection(
            member_a=endpoint_a,
            member_b=endpoint_b,
            configuration=BoltConfiguration(*args, **kwargs),
            override_Ag=override_ag,
            global_loads=global_loads
        )

    @staticmethod
    def create_welded_connection(self,
        member_a: Any,
        member_b: Any,
        component_a: ConnectionComponent = ConnectionComponent.TOTAL,
        component_b: ConnectionComponent = ConnectionComponent.TOTAL,
        role_a: Optional[str] = None,
        role_b: Optional[str] = None,
        *args, **kwargs
    ) -> Connection:
        """
        Creates a welded connection, explicitly defining the two members and their
        connected components.
        """
        override_ag = kwargs.pop('override_Ag', None)
        global_loads = kwargs.pop('global_loads', None)
        endpoint_a = ConnectionEndpoint(member=member_a, component=component_a, role=role_a)
        endpoint_b = ConnectionEndpoint(member=member_b, component=component_b, role=role_b)

        return Connection(
            member_a=endpoint_a,
            member_b=endpoint_b,
            configuration=WeldConfiguration(*args, **kwargs),
            override_Ag=override_ag,
            global_loads=global_loads
        )
