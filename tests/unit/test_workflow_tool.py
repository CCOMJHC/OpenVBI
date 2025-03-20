from abc import ABC
from typing import Optional, TypeVar, cast
from pathlib import Path
from importlib import resources
import json
import io


class SchemaNode(ABC):
    """
    Parent class for all schema nodes
    """
    def __init__(self, name: str, path: str | None, parent: Optional['SchemaNode']):
        self.name: str = name
        if path is None:
            self.path = "#/"
        else:
            self.path = path
        self.parent: Optional['SchemaNode'] = parent

    def to_string(self, *, depth: int = 1) -> str:
        pass

    def resolve(self, path: str) -> 'SchemaNode':
        pass

    def get_path(self) -> str:
        if self.parent is None:
            return f"/{self.name}"
        else:
            return f"{self.parent.get_path()}/{self.name}"


class SchemaRef(SchemaNode):
    """
    Reference to another entity
    """
    def __init__(self, name: str, path: str, parent: SchemaNode):
        super().__init__(name, path, parent)
        self.referent: SchemaNode | None = None

    def to_string(self, *, depth: int = 1) -> str:
        indent_root: str = '\t\t\t\t' * (depth - 1)
        indent: str = '\t\t\t' * depth
        referent = self.referent.name if self.referent is not None else 'nil'
        return f"{indent_root}SchemaRef(name: {self.name},\n{indent}path: {self.path}\n{indent}parent.name: {self.parent.name},\n{indent}referent: {referent})"

class SchemaObject(SchemaNode):
    """
    Class for representing schema interior nodes
    """

    def __init__(self, name: str, path: str | None, parent: Optional['SchemaObject'], d: dict):
        super().__init__(name, path, parent)

        self.properties: dict[str, SchemaNode] = {}
        self.required: list[str] = []
        self.defs_keys: set[str] = set()
        self.defs: dict[str, SchemaNode] = {}

        # Initialize object from dict
        self._from_dict(d)

    def to_string(self, *, depth: int = 1) -> str:
        indent_root: str = '\t\t\t\t' * (depth-1)
        indent: str = '\t\t\t' * depth
        cont: str = '\t\t\t' * (depth+1)
        cont_sub = '\t\t' * (depth+2)
        parent = self.parent.name if self.parent is not None else 'nil'
        o = io.StringIO()
        o.write(f"{indent_root}SchemaObject(name: {self.name}, path: {self.path}, parent: {parent},\n")
        o.write(f"{indent}properties:\n")
        for p in self.properties.values():
            if p is None:
                # TODO: Remove after we have implemented all node types, after which no nodes will be None
                continue
            o.write(f"{p.to_string(depth=depth+1)}\n")
        o.write(f"{indent}required:\n")
        for r in self.required:
            o.write(f"{cont_sub}{r}\n")
        o.write(f"{indent}defs:\n")
        for path, obj in self.defs.items():
            if obj is None:
                # TODO: Remove after we have implemented all node types, after which no nodes will be None
                continue
            o.write(f"{cont}path: {path}\n{cont}obj:\n{obj.to_string(depth=depth+1)}\n")
        o.write(f"\n{indent_root})")
        return o.getvalue()

    def resolve_refs(self, *, defs: dict | None = None):
        print(f"resolving refs for path: {self.path}")
        if defs is None:
            d: dict = self.defs
        else:
            d: dict = defs

        assert d is not None

        # First resolve refs in any defs this object may have
        for node in self.defs.values():
            if node is None:
                # TODO: Remove after we have implemented all node types, after which no nodes will be None
                continue
            if isinstance(node, SchemaObject):
                node.resolve_refs(defs=d)
            if isinstance(node, SchemaRef):
                if node.path not in d:
                    print("WARNING: Unable to resolve reference for node path {node.path}")
                else:
                    node.referent = d[node.path]

        # Now resolve refs in this object's properties
        for node in self.properties.values():
            if node is None:
                # TODO: Remove after we have implemented all node types, after which no nodes will be None
                continue
            if isinstance(node, SchemaObject):
                node.resolve_refs(defs=d)
            if isinstance(node, SchemaRef):
                if node.path not in d:
                    print("WARNING: Unable to resolve reference for node path {node.path}")
                else:
                    node.referent = d[node.path]


    def _from_dict(self, d: dict):
        if 'required' in d:
            for r in d['required']:
                self.required.append(r)
        if 'properties' in d:
            for k, v in d['properties'].items():
                if isinstance(v, dict):
                    if '$ref' in v:
                        # Property is a reference node
                        parsed: SchemaRef = SchemaRef(k, v['$ref'], self)
                        self.properties[k] = parsed
                        # Look at first element of path to record the defs key to later support
                        # resolving references to referents
                        assert v['$ref'][0] == '#'
                        ref_path = v['$ref'].strip('#')
                        assert ref_path[0] == '/'
                        ref_path_components = ref_path.split('/')
                        assert len(ref_path_components) >= 2
                        self.defs_keys.add(ref_path_components[1])
                    else:
                        # Property is a non-reference node
                        path: str = f"{self.path}{k}"
                        self.properties[k] = parse_schema(v, path, k, self)
        # Attempt to process defs
        for ref in self.defs_keys:
            if ref in d:
                for k, v in d[ref].items():
                    path: str = f"{self.path}{ref}/{k}"
                    parsed: SchemaNode = parse_schema(v, path, k, self)
                    self.defs[path] = parsed

class SchemaLeaf(SchemaNode, ABC):
    """
    Super-class for schema terminal nodes
    """
    pass

class SchemaLeafString(SchemaLeaf):
    def __init__(self, name: str, path: str | None, parent: SchemaNode | None, d: dict):
        super().__init__(name, path, parent)

        self.title: str | None
        self.description: str | None
        self.pattern: str | None

        # Initialize object from dict
        self._from_dict(d)

    def to_string(self, *, depth: int = 1) -> str:
        indent_root: str = '\t\t\t\t\t' * (depth - 1)
        indent: str = '\t\t\t\t' * depth
        title = self.title if self.title is not None else 'nil'
        desc = self.description if self.description is not None else 'nil'
        patt = self.pattern if self.pattern is not None else 'nil'
        parent = self.parent.name if self.parent is not None else 'nil'
        return f"{indent_root}SchemaLeafString(path: {self.path},\n{indent}title: {title},\n{indent}description: {desc},\n{indent}pattern: {patt},\n{indent}parent: {parent})"

    def _from_dict(self, d: dict):
        self.title = d.get('title')
        self.description = d.get('description')
        self.pattern = d.get('pattern')


S = TypeVar('S', bound=SchemaNode)
def parse_schema(schema: dict, path: str | None, name: str | None, parent: SchemaNode | None) -> S:
    """
    Parse JSON Schema document. Note: Assumes the root of the schema is an object for our purposes for now.
    :param name:
    :param path:
    :param schema:
    :param parent:
    :return:
    """
    if 'type' not in schema:
        raise ValueError("schema dictionary doesn't appear to represent a JSON Schema document.")

    match schema['type']:
        case 'object':
            return SchemaObject(name, path, parent, schema)
        case 'string':
            return SchemaLeafString(name, path, parent, schema)
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

    schema_node: SchemaNode = parse_schema(schema, None,None, None)
    assert schema_node is not None
    assert isinstance(schema_node, SchemaObject)
    schema_obj: SchemaObject = cast(SchemaObject, schema_node)
    # print(f"Parsed schema before resolving refs was:\n{schema_obj.to_string()}")
    schema_obj.resolve_refs()
    print(f"Parsed schema AFTER resolving refs was:\n{schema_obj.to_string()}")
