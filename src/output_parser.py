from pydantic import BaseModel, Field
from langchain_core.output_parsers import JsonOutputParser

class node_dict_format(BaseModel):
    node1_type: str = Field(description="node1_type")
    node1_property: dict = Field(description="you are required to fill this up by extracting from text")
    relationship: str = Field(description="Relationship between the nodes")
    node2_type: str = Field(description="node2_type")
    node2_property: dict = Field(description="you are required to fill this up")

parser = JsonOutputParser(pydantic_object=node_dict_format)