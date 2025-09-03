from dataclasses import dataclass
from typing import Any, Optional, Union

from steel_lib.data_models import (
    ConnectionEndpoint,
    ConnectionComponent,
    BoltConfiguration,
    WeldConfiguration,
    Connection,get_component_from_string
)
from .si_units import si


@dataclass
class ConnectionFactory:
    """Factory for creating Connection objects."""
    connection:Connection = None

    @staticmethod
    def create_bolted_connection(
        member_a: Any,
        member_b: Any,
        component_a: ConnectionComponent = ConnectionComponent.TOTAL,
        component_b: ConnectionComponent = ConnectionComponent.TOTAL,
        connection_configuration: Optional[BoltConfiguration] = None,
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
        component_a = get_component_from_string(component_a)
        component_b = get_component_from_string(component_b)
        endpoint_a = ConnectionEndpoint(member=member_a, component=component_a, role=role_a,connection_configuration=connection_configuration)
        endpoint_b = ConnectionEndpoint(member=member_b, component=component_b, role=role_b, connection_configuration=connection_configuration)

        return Connection(
            member_a=endpoint_a,
            member_b=endpoint_b,
            override_Ag=override_ag,
            global_loads=global_loads
        )

    @staticmethod
    def create_welded_connection(
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
        endpoint_a = ConnectionEndpoint(member=member_a, component=component_a, role=role_a, configuration=WeldConfiguration(*args, **kwargs))
        endpoint_b = ConnectionEndpoint(member=member_b, component=component_b, role=role_b, configuration=WeldConfiguration(*args, **kwargs))

        return Connection(
            member_a=endpoint_a,
            member_b=endpoint_b,
            override_Ag=override_ag,
            global_loads=global_loads
        )
