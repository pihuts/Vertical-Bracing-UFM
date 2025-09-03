from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Any, Literal
from enum import Enum
import random # Used for mocking results

# --- 1. Pydantic Models (Matching the Frontend JSON) ---
# These are the same as before.

class BoltConfigurationModel(BaseModel):
    id: str
    name: str
    row_spacing: float = Field(..., alias='rowSpacing')
    column_spacing: float = Field(..., alias='columnSpacing')
    n_rows: int = Field(..., alias='nRows')
    n_columns: int = Field(..., alias='nColumns')
    edge_distance_vertical: float = Field(..., alias='edgeDistanceVertical')
    edge_distance_horizontal: float = Field(..., alias='edgeDistanceHorizontal')
    bolt_diameter: float = Field(..., alias='boltDiameter')
    bolt_grade: str = Field(..., alias='boltGrade')
    angle: float
    connection_type: str = Field(..., alias='connectionType')

class GlobalLoadsModel(BaseModel):
    id: str
    name: str
    fx: float
    fy: float
    fz: float
    mx: float
    my: float
    mz: float
    direct_load: float = Field(..., alias='directLoad')

class MemberModel(BaseModel):
    id: str
    type: Literal["steelpy", "plate"]
    name: str
    section_class: Optional[str] = Field(None, alias='sectionClass')
    section_name: Optional[str] = Field(None, alias='sectionName')
    shape_type: Optional[str] = Field(None, alias='shapeType')
    role: Optional[str] = None
    thickness: Optional[float] = None
    width: Optional[float] = None
    clipping: Optional[float] = None
    material: str
    loading_condition: str = Field(..., alias='loadingCondition')
    length: float

class ConnectionModel(BaseModel):
    id: str
    name: str
    member_a: MemberModel = Field(..., alias='memberA')
    member_b: MemberModel = Field(..., alias='memberB')
    component_a: str = Field(..., alias='componentA')
    component_b: str = Field(..., alias='componentB')
    connection_type: str = Field(..., alias='connectionType')
    bolt_configuration_id: str = Field(..., alias='boltConfigurationId')
    global_loads_id: str = Field(..., alias='globalLoadsId')
    override_ag: Optional[float] = Field(None, alias='overrideAg')

class ProjectData(BaseModel):
    connections: List[ConnectionModel]
    members: List[MemberModel]
    bolt_configurations: List[BoltConfigurationModel] = Field(..., alias='boltConfigurations')
    global_loads: List[GlobalLoadsModel] = Field(..., alias='globalLoads')


# --- 2. Your Python Business Logic Classes ---

class ConnectionComponent(Enum):
    TOTAL = "TOTAL"
    WEB = "WEB"
    FLANGE = "FLANGE"

# Placeholder for your actual member classes
class BaseMember:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key.upper(), value)

class SteelpyMember(BaseMember): pass
class PlateMember(BaseMember): pass
class BoltConfiguration:
    def __init__(self, **kwargs):
        for key, value in kwargs.items(): setattr(self, key, value)
class GlobalLoads:
    def __init__(self, **kwargs):
        for key, value in kwargs.items(): setattr(self, key, value)

class ConnectionEndpoint:
    def __init__(self, member, component, role, connection_configuration):
        self.member = member
        self.component = component
        self.role = role
        self.connection_configuration = connection_configuration

class Connection:
    def __init__(self, member_a, member_b, override_Ag, global_loads):
        self.member_a = member_a
        self.member_b = member_b
        self.override_Ag = override_Ag
        self.global_loads = global_loads
        print(f"Successfully created Connection between {member_a.member.name} and {member_b.member.name}")

class ConnectionFactory:
    @staticmethod
    def create_bolted_connection(
        member_a: Any, member_b: Any, component_a: ConnectionComponent = ConnectionComponent.TOTAL,
        component_b: ConnectionComponent = ConnectionComponent.TOTAL,
        connection_configuration: Optional[BoltConfiguration] = None, *args, **kwargs
    ) -> Connection:
        override_ag = kwargs.pop('override_Ag', None)
        global_loads = kwargs.pop('global_loads', None)
        role_a = member_a.ROLE
        role_b = member_b.ROLE
        endpoint_a = ConnectionEndpoint(member=member_a, component=component_a, role=role_a, connection_configuration=connection_configuration)
        endpoint_b = ConnectionEndpoint(member=member_b, component=component_b, role=role_b, connection_configuration=connection_configuration)
        return Connection(member_a=endpoint_a, member_b=endpoint_b, override_Ag=override_ag, global_loads=global_loads)

# --- NEW: Your DesignCode and a Mock LimitState ---
class LimitState:
    def __init__(self, endpoint, debug=False):
        self.endpoint = endpoint
        self._debug = debug
    def check_dcr(self):
        raise NotImplementedError

class MockBoltShearLimitState(LimitState):
    def check_dcr(self):
        # Simulate a calculation
        capacity = self.endpoint.connection_configuration.n_rows * self.endpoint.connection_configuration.n_columns * 25.5
        demand = self.endpoint.member.global_loads.direct_load
        dcr = demand / capacity if capacity > 0 else 0
        result = {"name": "Bolt Shear", "capacity": round(capacity, 2), "demand": demand, "dcr": round(dcr, 2)}
        sol_latex = f"V_r = {capacity:.2f} \\text{{ kip}} > V_u = {demand:.2f} \\text{{ kip}}"
        return result, sol_latex

class DesignCode:
    def __init__(self,limit_states:List[LimitState] = [],debug:bool = False):
        self._debug = debug
        self.limit_states = limit_states if limit_states else []
    def check_limit_states(self,connection: Connection):
            if self.limit_states:
                results = []
                # For this example, we'll just return the latex of the first limit state
                sol_latex = ""
                for i, limit_state_class in enumerate(self.limit_states):
                    # Assuming the check is on member_a for simplicity
                    calculator = limit_state_class(connection.member_a, debug=self._debug)
                    result, latex = calculator.check_dcr()
                    if i == 0: sol_latex = latex
                    results.append(result)
                return results, sol_latex
            else:
                raise ValueError("No limit states defined for this design code.")

# --- 3. FastAPI Application Setup ---

app = FastAPI()
origins = ["http://localhost", "http://localhost:3000"]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/")
def read_root():
    return {"message": "Structural Connection Calculator Backend is running!"}

@app.post("/api/calculate")
def calculate_connections(project_data: ProjectData):
    print(f"Received calculation request for {len(project_data.connections)} connection(s)...")

    members_by_id = {m.id: (SteelpyMember(**m.model_dump(by_alias=True)) if m.type == 'steelpy' else PlateMember(**m.model_dump(by_alias=True))) for m in project_data.members}
    bolts_by_id = {b.id: BoltConfiguration(**b.model_dump(by_alias=True)) for b in project_data.bolt_configurations}
    loads_by_id = {l.id: GlobalLoads(**l.model_dump(by_alias=True)) for l in project_data.global_loads}

    # Add global loads to members for the mock limit state check
    for conn_model in project_data.connections:
        members_by_id[conn_model.member_a.id].global_loads = loads_by_id[conn_model.global_loads_id]
        members_by_id[conn_model.member_b.id].global_loads = loads_by_id[conn_model.global_loads_id]

    final_results = {}
    # Instantiate your design code with the limit states to check
    design_code = DesignCode(limit_states=[MockBoltShearLimitState])

    for conn_data in project_data.connections:
        connection_obj = ConnectionFactory.create_bolted_connection(
            member_a=members_by_id[conn_data.member_a.id],
            member_b=members_by_id[conn_data.member_b.id],
            component_a=ConnectionComponent[conn_data.component_a],
            component_b=ConnectionComponent[conn_data.component_b],
            connection_configuration=bolts_by_id[conn_data.bolt_configuration_id],
            global_loads=loads_by_id[conn_data.global_loads_id],
            override_Ag=conn_data.override_ag
        )
        # Run the check
        limit_state_results, latex_solution = design_code.check_limit_states(connection_obj)
        
        # For simplicity, we'll just process the first connection's results if multiple are sent
        # A real app might return a list of results.
        if not final_results:
            governing_state = max(limit_state_results, key=lambda x: x['dcr'])
            final_results = {
                "boltShearCapacity": next((r['capacity'] for r in limit_state_results if r['name'] == 'Bolt Shear'), 0),
                "blockShearCapacity": 189.2, # Mocked
                "bearingCapacity": 240.0, # Mocked
                "utilizationRatio": governing_state['dcr'],
                "latexSolution": latex_solution
            }

    return final_results