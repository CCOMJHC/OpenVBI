from abc import ABC
from typing import Optional, TypeVar
from pathlib import Path
from importlib import resources
import json


class SchemaNode(ABC):
    """
    Parent class for all schema nodes
    """
    def __init__(self, name: str, parent: Optional['SchemaNode']):
        self.name: str = name
        self.parent: Optional['SchemaNode'] = parent

    def __str__(self) -> str:
        return f"name: self.name, parent: {str(self.parent)} }}"

    def resolve(self, path: str) -> 'SchemaNode':
        pass

    # def join_path(self, child: str) -> str:
    #     ref_root_idx: int = child.find('#/')
    #     if ref_root_idx == 0:
    #         # Child is a reference
    #         return f"{self.path}{child[1:]}"
    #     else:
    #         return f"{self.path}/{child}"

    def get_path(self) -> str:
        if self.parent is None:
            return f"/{self.name}"
        else:
            return f"{self.parent.get_path()}/{self.name}"


class SchemaRef(SchemaNode):
    """
    Reference to another entity
    """
    def __self__(self, name: str, parent: SchemaNode):
        super().__init__(name, parent)
        self.referent: SchemaNode | None = None

    def __str__(self) -> str:
        referent = self.referent.name if self.referent is not None else 'nil'
        return f"SchemaRef(name: {self.name}, parent.name: {self.parent.name}, referent: {referent})"

class SchemaObject(SchemaNode):
    """
    Class for representing schema interior nodes
    """

    def __init__(self, name: str, parent: SchemaNode | None, d: dict):
        super().__init__(name, parent)

        self.properties: dict[str, SchemaNode] = {}
        self.required: list[str] = []
        self.defs_keys: set[str] = set()
        self.defs: dict[str, SchemaNode] = {}
        # self.ref_lookup: dict[str, SchemaRef] = {}

        # Initialize object from dict
        self._from_dict(d)

    def resolve(self, path: str) -> SchemaNode:
        # TODO:
        pass

    def _from_dict(self, d: dict):
        if 'properties' in d:
            for k, v in d['properties'].items():
                if isinstance(v, dict):
                    if '$ref' in v:
                        # Property is a reference node
                        parsed: SchemaRef = SchemaRef(k, self)
                        self.properties[k] = parsed
                        # Look at first element of path to record the defs key to later support
                        # resolving references to referents
                        assert v['$ref'][0] == '#'
                        ref_path = v['$ref'].strip('#')
                        assert ref_path[0] == '/'
                        ref_path_components = ref_path.split('/')
                        assert len(ref_path_components) >= 2
                        self.defs_keys.add(ref_path_components[1])
                        # Map referent name to SchemaRef node to facilitate later lookups
                        # self.ref_lookup[ref_path_components[2]] = parsed
                        # If we have a parent, it may hold the definition for this object
                    else:
                        # Property is a non-reference node
                        self.properties[k] = parse_schema(v, k, self)
        # Attempt to process defs
        for ref in self.defs_keys:
            if ref in d:
                for k, v in d[ref].items():
                    parsed: SchemaNode = parse_schema(v, k, self)
                    self.defs[k] = parsed
                    # if k in self.ref_lookup:
                    #     # Associate parsed referent schema with SchemaRef
                    #     self.ref_lookup[k].referent = parsed



class SchemaLeaf(SchemaNode, ABC):
    """
    Super-class for schema terminal nodes
    """
    pass

class SchemaLeafString(SchemaLeaf):
    def __init__(self, name: str, parent: SchemaNode | None, d: dict):
        super().__init__(name, parent)

        self.title: str | None
        self.description: str | None
        self.pattern: str | None

        # Initialize object from dict
        self._from_dict(d)

    def __str__(self) -> str:
        title = self.title if self.title is not None else 'nil'
        desc = self.description if self.description is not None else 'nil'
        patt = self.pattern if self.pattern is not None else 'nil'
        parent = self.parent.name if self.parent is not None else 'nil'
        return f"SchemaLeafString(title: {title}, description: {desc}, pattern: {patt}, parent: {parent})"

    def _from_dict(self, d: dict):
        self.title = d.get('title')
        self.description = d.get('description')
        self.pattern = d.get('pattern')


S = TypeVar('S', bound=SchemaNode)
def parse_schema(schema: dict, name: str | None, parent: SchemaNode | None) -> S:
    """
    Parse JSON Schema document. Note: Assumes the root of the schema is an object for our purposes for now.
    :param schema:
    :param parent:
    :return:
    """
    if 'type' not in schema:
        raise ValueError("schema dictionary doesn't appear to represent a JSON Schema document.")

    match schema['type']:
        case 'object':
            return SchemaObject(name, parent, schema)
        case 'string':
            return SchemaLeafString(name, parent, schema)
        case _:
            print(f"Have not yet implemented parsing of schema of type {schema['type']}")



def test_playground():
    schema_file_name = 'XYZ-CSB-schema-3_1_0-2024-04.json'
    # TODO: Eventually add an API to csbschema to get the schema files in a safer way, for now this will do...
    schema_path: Path = Path(str(resources.files('csbschema').joinpath(f"data/{schema_file_name}")))
    assert schema_path.exists()
    assert schema_path.is_file()

    with schema_path.open(mode='r') as f:
        schema: dict = json.load(f)
    assert schema is not None

    schema_node: SchemaNode = parse_schema(schema, None, None)
    assert schema_node is not None
