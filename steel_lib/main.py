from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Any, Literal
from enum import Enum
import random # Used for mocking results
from .member_factory import MemberFactory
from .data_models import BoltConfiguration,GlobalLoads,get_component_from_string,Plate
from .calculations import aisc_360_14th
from .core import DesignCode
from .connection_factory import ConnectionFactory
from .member_factory import MemberFactory


from forallpeople import Physical # Make sure to import the Physical class

# Define a simple function that tells FastAPI how to convert a Physical object
# The str() function on a Physical object usually gives a nice representation like "50.0 kip"
custom_encoder = {
    Physical: lambda v: str(v)
}
# --- 1. Pydantic Models (Matching the Frontend JSON) ---
# These are the same as before.
from steel_lib.connection_factory import ConnectionFactory
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
    loading_condition: int = Field(..., alias='loadingCondition')
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


def create_member(member):
    member_type = member_type["type"]
    if member_type == "steelpy":
        return MemberFactory.create_steelpy_member(**member)
    elif member_type == "plate":
        return Plate(**member)

app = FastAPI(json_encoders=custom_encoder)
origins = ["*"] 
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/")
def read_root():
    return {"message": "Structural Connection Calculator Backend is running!"}

@app.post("/api/calculate")
def calculate_connections(project_data: ProjectData):
    design_code = DesignCode(aisc_360_14th, debug=False)
    connection_data = project_data.connections[0]
    global_loads = GlobalLoads(**project_data.global_loads[0].model_dump())
    member_a_data = connection_data.member_a.model_dump()
    member_b_data = connection_data.member_b.model_dump()
    
    connection_configuration = project_data.bolt_configurations[0]

    member_a = MemberFactory.create_member(**member_a_data)
    member_b = MemberFactory.create_member(**member_b_data)
    component_a = get_component_from_string(connection_data.component_a)
    component_b = get_component_from_string(connection_data.component_b)
    bolt_1 = BoltConfiguration(**connection_configuration.model_dump())
    connection = ConnectionFactory.create_bolted_connection(
        member_a=member_a,
        member_b=member_b,
        component_a=component_a,
        component_b=component_b,
        connection_configuration=bolt_1,
        global_loads=global_loads
    )
    # print(global_loads)
    # print(bolt_1)
    # print(connection)
    results_df, sol_latexs = design_code.check_limit_states(connection)

    # --- The Performance-Optimized Solution ---

    # 2. Use applymap() to convert every object in the DataFrame to a string.
    #    This operation is vectorized and significantly faster than a Python for-loop.
    serializable_df = results_df.applymap(str)

    # 3. Convert the now-safe, string-only DataFrame to a list of dictionaries.
    results_json = serializable_df.to_dict(orient='records')
    
    # --- End of Optimization ---

    # 4. Return the fully serializable data.
    return {"results": results_json, "sol_latexs": sol_latexs}

