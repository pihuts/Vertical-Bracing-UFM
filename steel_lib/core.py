from dataclasses import dataclass, field
from .data_models import Connection
from .calculations import aisc_360_14th,LimitState
from typing import List
import pandas as pd
class DesignCode:
    def __init__(self,limit_states:List[LimitState] = [],debug:bool = False):
        self._debug = debug
        self.limit_states = limit_states if limit_states else []
    def check_limit_states(self,connection: Connection): 
            if self.limit_states:
                results = []
                sol_latexs = []
                for limit_state in self.limit_states:
                    calculator = limit_state(connection.member_a,debug= self._debug)
                    result,sol_latex = calculator.check_dcr()
                    sol_latexs.append(sol_latex)
                    results.append(result)
                return pd.DataFrame(results),sol_latexs
            else:
                raise ValueError("No limit states defined for this design code.")