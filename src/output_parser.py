from typing import Dict, Union, List
import json
import traceback
import re
from global_import import *

from pydantic import BaseModel, Field
from langchain_core.output_parsers import JsonOutputParser
from langchain.output_parsers import PydanticOutputParser
from langchain.output_parsers import OutputFixingParser
from langchain_core.exceptions import OutputParserException


class NodeDictParser(BaseModel):
    node1_type:     str           = Field(description="node1_type")
    node1_property: Dict[str,str] = Field(description="you are required to fill this up by extracting from text")
    relationship:   str           = Field(description="Relationship between the nodes")
    node2_type:     str           = Field(description="node2_type")
    node2_property: Dict[str,str] = Field(description="you are required to fill this up")


class CaseMetadataParser(BaseModel):
    hasCaseID:       str = Field(description = "This is Case number. For Example: Criminal Appeal No. 1392 of 2011/ Criminal Appeal Nos. 1864-1865 of 2010/ SLP(C) No. 000242 - 000284 / 2014 Registered on 24-11-2014/ CIVIL APPEAL NO. 17308 OF 2017")
    hasCourtName:    str = Field(description = "Name of the Court. Example: Supreme Court of India/ High Court of Madhya Pradesh/ Disctrict Coutr of Udaipur")
    hasCaseName:     str = Field(description= """
                          Name of the case. Each Example separated by a /: Chunthuram Versus State of Chhattisgarh / 
                                                    Sajid Khan v. L Rahmathullah & Ors. / 
                                                    State of U.P. Versus Gayatri Prasad Prajapati / 
                                                    M. Ravindran Versus The Intelligence Officer, Directorate of Revenue Intelligence
                                                    """
                          )


class NodeTriple(BaseModel):
    node1_type:      str             = Field(description="Type of node1")
    node1_value:     Union[Dict,str] = Field(description="Properties of node1 extracted from the text")
    relationship:    str             = Field(description="Relationship between node1 and node2")
    node2_type:      str             = Field(description="Type of node2")
    node2_value:     Union[Dict,str] = Field(description="Properties of node2 extracted from the text")


def strip_markdown_json(text):
    # Strip ```json ... ``` or ``` ... ``` blocks
    return re.sub(r"^```(?:json)?\s*(.*?)\s*```$", r"\1", text.strip(), flags=re.DOTALL)



class ListOfTriplesParser():
    def __init__(self, model_cls):
        self.model_cls = model_cls
        self.single_parser = PydanticOutputParser(pydantic_object=model_cls)
        self.fix_parser = OutputFixingParser.from_llm(parser=self.single_parser, llm=output_fixer_model)

    def get_format_instructions(self) -> str:
        # Tell the LLM to return a JSON list of NodeTriple objects
        return (
            "Return a JSON array where each element follows this schema:\n"
            f"{self.single_parser.get_format_instructions()}"
        )

    def parse(self, text: str) -> List[NodeTriple]:
        # Assume output is a JSON array of objects
        try:
            text = strip_markdown_json(text)
            items = json.loads(text)
            if isinstance(items, dict) and "Data" in items:
                items = items["Data"]
            elif isinstance(items, list):
                print("Items is a list LLM did mistake However parsing now as list")
            ls = []
            for item in items:
                try:
                    triple = self.model_cls(**item)
                except OutputParserException as e:
                    for _ in range(RETRY_LIMIT):
                        try:
                            print(f"Fixing output parser {item}")
                            triple = self.fix_parser.parse("{}".format(item))
                            break
                        except:
                            pass
                ls.append(triple)
            return ls
            # return [self.model_cls(**item) for item in items]
        except Exception as e:
            print(f"Could not parse LLM output as list of triples: {traceback.format_exc()} \n LLMresponse {text}")




# parser = JsonOutputParser(pydantic_object=node_dict_format)
# metadata_parser = JsonOutputParser(pydantic_object = case_metadata_parser)
# output_parser = ListOfTriplesParser(NodeTriple)