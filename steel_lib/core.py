from dataclasses import dataclass, field
from .data_models import Connection,BoltConfiguration,WeldConfiguration,GlobalLoads
from .calculations import aisc_360_14th,LimitState
from .connection_factory import ConnectionFactory
from typing import List
import pandas as pd
class DesignCode:
    def __init__(self,limit_states:List[LimitState] = [],debug:bool = False):
        self._debug = debug
        self.limit_states = limit_states if limit_states else []
    def check_limit_states(self,connection: Connection,detailed:bool = False): 
            if self.limit_states:
                results = []
                sol_latexs = []
                for limit_state in self.limit_states:
                    calculator = limit_state(connection.member_a,debug= self._debug)
                    result,sol_latex = calculator.check_dcr(detailed=detailed)
                    sol_latexs.append(sol_latex)
                    results.append(result)
                return pd.DataFrame(results),sol_latexs
            else:
                raise ValueError("No limit states defined for this design code.")
    def workflow(self,connections:List[Connection],detailed:bool = False):
        all_results = []
        all_latexs = []
        for conn in connections:
            results_df, sol_latexs = self.check_limit_states(conn,detailed=detailed)
            results_df['connection_id'] = conn.id
            results_df['connection_name'] = conn.name
            all_results.append(results_df)
            all_latexs.append(sol_latexs)
        return all_results,all_latexs
            
import itertools
from dataclasses import dataclass, field
from typing import Literal, Dict, Any, Optional, Union, List
from functools import lru_cache
import math
import time



# ============================================================================
# GENERATOR FACTORIES (Improvement #1 - Fix Generator Exhaustion)
# ============================================================================

def create_bolt_configs(param_grid):
    """Factory function to create fresh bolt configuration generator"""
    return (BoltConfiguration(**dict(zip(param_grid.keys(), combo))) 
            for combo in itertools.product(*param_grid.values()))

def create_all_connections_generator(bolt_grid, member_a, member_b,loads):
    """
    Master generator that creates all valid connection combinations.
    Uses factory functions to avoid generator exhaustion.
    """
    for bolt_config in create_bolt_configs(bolt_grid):
                    # Apply pruning if available
                    yield ConnectionFactory.create_connection(
                        member_a=member_a,
                        member_b=member_b,
                        global_loads=loads,
                        component_a="total",
                        component_b="total",
                        connection_configuration=bolt_config
                    )

def create_all_connections_list_comprehension(bolt_grid, member_a, member_b, loads):
    """
    Creates and returns a list of all connections using a concise list comprehension.
    """
    return [
        ConnectionFactory.create_connection(
                        member_a=member_a,
                        member_b=member_b,
                        global_loads=loads,
                        component_a="total",
                        component_b="total",
                        connection_configuration=bolt_config
        )
        for bolt_config in create_bolt_configs(bolt_grid)
    ]