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
    def check_limit_states(self, connection: Connection, detailed: bool = False, optimize: bool = False):
        """
        Checks all defined limit states for both members in the connection.
        If optimize is True, returns a single objective value for optimization (lower is better, closer to 1).
        Otherwise, returns a dictionary with results and LaTeX solutions for each member,
        plus combined average DCR and highest DCR.
        """
        if not self.limit_states:
            raise ValueError("No limit states defined for this design code.")

        # Define members to check
        members = {"Member A": connection.member_a, "Member B": connection.member_b}
        results = {}

        # Iterate over each member
        for member_name, member in members.items():
            member_results = []
            latex_solutions = []

            # Check each limit state for the current member
            for limit_state in self.limit_states:
                try:
                    # Instantiate calculator and perform DCR check
                    calculator = limit_state(member)
                    result, sol_latex = calculator.check_dcr(detailed=detailed)

                    if result.dcr < 1:
                        # Collect results if DCR passes
                        latex_solutions.append(sol_latex)
                        member_results.append(result)
                    else:
                        # Break if DCR fails (no need to check further limit states)
                        print("Breaking due to DCR > 1")
                        break
                except Exception as e:
                    print(f"Error in limit state {limit_state.__name__}: {e}")

            # Store results for this member
            results[member_name] = (pd.DataFrame(member_results), latex_solutions)
        
        # Combine DCRs from both members
        all_dcrs = pd.concat([
            results["Member A"][0]["dcr"] if not results["Member A"][0].empty else pd.Series(dtype=float),
            results["Member B"][0]["dcr"] if not results["Member B"][0].empty else pd.Series(dtype=float)
        ])
        
        average_dcr = all_dcrs.mean() if not all_dcrs.empty else None
        highest_dcr = all_dcrs.max() if not all_dcrs.empty else None
        
        # Add combined metrics to results
        results["combined_average_dcr"] = average_dcr
        results["combined_highest_dcr"] = highest_dcr
        
        if optimize:
            # Return objective value for optimization: average deviation from 1 (lower is better)
            if average_dcr is not None and highest_dcr is not None:
                objective = (abs(average_dcr - 1) + abs(highest_dcr - 1)) / 2
            else:
                objective = float('inf')  # Penalty for no valid DCRs
            return objective
        
        return results
    def workflow(self, connections: List[Connection], detailed: bool = False):
        all_results = []
        all_latexs = []
        all_combined_metrics = []
        for conn in connections:
            results = self.check_limit_states(conn, detailed=detailed)
            
            # Extract and combine member DataFrames
            member_a_df = results["Member A"][0]
            member_b_df = results["Member B"][0]
            combined_df = pd.concat([member_a_df, member_b_df], ignore_index=True)
            combined_df['connection_id'] = conn.id
            combined_df['connection_name'] = conn.name
            
            # Extract combined metrics
            combined_metrics = {
                'connection_id': conn.id,
                'connection_name': conn.name,
                'average_dcr': results["combined_average_dcr"],
                'highest_dcr': results["combined_highest_dcr"]
            }
            
            # Combine LaTeX solutions
            combined_latexs = results["Member A"][1] + results["Member B"][1]
            
            all_results.append(combined_df)
            all_latexs.append(combined_latexs)
            all_combined_metrics.append(combined_metrics)
        
        return all_results, all_latexs, all_combined_metrics
            
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