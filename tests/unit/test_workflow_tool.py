from abc import ABC
from dataclasses import dataclass
from pathlib import Path
from importlib import resources
import json


@dataclass
class SchemaNode(ABC):
    """
    Parent class for all schema nodes
    """
    path: str

    def __init__(self, path: str):
        self.path = path

    def join_path(self, child: str) -> str:
        ref_root_idx: int = child.find('#/')
        if ref_root_idx == 0:
            # Child is a reference
            return f"{self.path}{child[1:]}"
        else:
            return f"{self.path}/{child}"


@dataclass
class SchemaRef(SchemaNode):
    """
    Reference to another entity
    """
    def __self__(self, path: str):
        super().__init__(path)

@dataclass
class SchemaObject(SchemaNode):
    """
    Class for representing schema interior nodes
    """
    required: list[str]
    properties: dict[str, SchemaNode]

    def from_dict(self, d: dict, path: str):
        self.path = path
        self.required = []
        self.properties = {}

        if 'properties' in d:
            props = d['properties']
            for p, v in props.items():
                if isinstance(v, dict):
                    if '$ref' in v:
                        # Property is a reference node
                        self.properties[p] = SchemaRef(self.join_path(v['$ref']))
                    else:
                        # TODO: Property is a non-reference node
                        print("TODO: Handle non-reference node")

@dataclass
class SchemaLeaf(SchemaNode, ABC):
    """
    Super-class for schema terminal nodes
    """
    pass

@dataclass
class SchemaLeafString(SchemaLeaf):
    title: str | None
    description: str | None
    pattern: str | None


def parse_schema(schema: dict) -> SchemaObject:
    """
    Parse JSON Schema document. Note: Assumes the root of the schema is an object for our purposes for now.
    :param schema:
    :return:
    """
    if 'type' not in schema:
        raise ValueError("schema dictionary doesn't appear to represent a JSON Schema document.")





def test_playground():
    schema_file_name = 'CSB-schema-3_1_0-2024-04.json'
    # TODO: Eventually add an API to csbschema to get the schema files in a safer way, for now this will do...
    schema_path: Path = Path(str(resources.files('csbschema').joinpath(f"data/{schema_file_name}")))
    assert schema_path.exists()
    assert schema_path.is_file()

    with schema_path.open(mode='r') as f:
        schema: dict = json.load(f)
    assert schema is not None
