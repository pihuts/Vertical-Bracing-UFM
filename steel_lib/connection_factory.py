from dataclasses import dataclass
from typing import Any, Optional, Union, Literal

from steel_lib.data_models import (
    ConnectionEndpoint,
    ConnectionComponent,
    BoltConfiguration,
    WeldConfiguration,
    Connection, get_component_from_string,Plate
)
from .si_units import si


class ConnectionFactory:
    """Factory for creating Connection objects."""

    @staticmethod
    def _create_connection(
        member_a: Any,
        member_b: Any,
        global_loads: Any,
        component_a: Literal["total", "web", "flange", "along_length", "along_width"],  # Updated type hint
        component_b: Literal["total", "web", "flange", "along_length", "along_width"],  # Updated type hint
        connection_configuration: Optional[Union[BoltConfiguration, WeldConfiguration]],
        override_ag: Optional[float] = None,
    ) -> Connection:
        """Helper method to create a Connection with common logic."""
        # Set roles from members if not provided
        role_a = member_a.Role if hasattr(member_a, 'Role') else None
        role_b = member_b.Role if hasattr(member_b, 'Role') else None
        if role_a is None:
            role_a = getattr(member_a, 'Role', None)
        if role_b is None:
            role_b = getattr(member_b, 'Role', None)
        
        # Convert components if needed
        component_a = get_component_from_string(component_a) if isinstance(component_a, str) else component_a
        component_b = get_component_from_string(component_b) if isinstance(component_b, str) else component_b
        
        endpoint_a = ConnectionEndpoint(
            member=member_a, 
            component=component_a, 
            role=role_a, 
            connection_configuration=connection_configuration
        )
        endpoint_b = ConnectionEndpoint(
            member=member_b, 
            component=component_b, 
            role=role_b, 
            connection_configuration=connection_configuration
        )

        return Connection(
            member_a=endpoint_a,
            member_b=endpoint_b,
            override_Ag=override_ag,
            global_loads=global_loads
        )

    @staticmethod
    def create_connection(
        member_a: Any,
        member_b: Any,
        global_loads: Any,
        component_a: Literal["total", "web", "flange", "along_length", "along_width"],  # Updated type hint
        component_b: Literal["total", "web", "flange", "along_length", "along_width"],  # Updated type hint
        connection_configuration: Optional[Union[BoltConfiguration, WeldConfiguration]] = None,
        override_ag: Optional[float] = None,
        **kwargs  # For configuration creation if needed
    ) -> Connection:
        """
        Creates a connection (bolted or welded), explicitly defining the two members and their
        connected components.
        """
        if isinstance(connection_configuration, WeldConfiguration):
            if connection_configuration.length:
                connection_configuration.length = connection_configuration.length
            else:
                if isinstance(member_a, Plate):
                    connection_configuration.length = member_a.length
                elif isinstance(member_b, Plate):
                    connection_configuration.length = member_b.length
        return ConnectionFactory._create_connection(
            member_a=member_a,
            member_b=member_b,
            global_loads=global_loads,
            component_a=component_a,
            component_b=component_b,
            connection_configuration=connection_configuration,
            override_ag=override_ag,
        )

    # Backward compatibility aliases
    @staticmethod
    def create_bolted_connection(*args, **kwargs) -> Connection:
        kwargs['connection_type'] = 'bolted'
        return ConnectionFactory.create_connection(*args, **kwargs)

    @staticmethod
    def create_welded_connection(*args, **kwargs) -> Connection:
        kwargs['connection_type'] = 'welded'
        return ConnectionFactory.create_connection(*args, **kwargs)
