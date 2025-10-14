## \file schema.py
# \brief Classes and functions to facilitate parsing csbschema schema for use in metadata and other workflow tools
#
# Copyright 2025 OpenVBI Project.  All Rights Reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
# OR OTHER DEALINGS IN THE SOFTWARE.

from abc import ABC
from typing import Optional, TypeVar
from pathlib import Path
from importlib import resources
import json
import io


class SchemaNode(ABC):
    """
    Parent class for all schema nodes
    """
    def __init__(self, name: str | None, path: str | None, parent: Optional['SchemaNode'],
                 *,
                 required: bool = False):
        self.name: str|None = name
        if path is None:
            self.path = "#/"
        else:
            self.path = path
        self.parent: Optional['SchemaNode'] = parent
        self.is_required = required

    def to_string(self, *, depth: int = 1) -> str:
        ...

    def resolve(self, path: str) -> 'SchemaNode':
        ...

    def get_path(self) -> str:
        if self.parent is None:
            return f"/{self.name}"
        else:
            return f"{self.parent.get_path()}/{self.name}"

    def join_path(self, child: str) -> str:
        if self.path.endswith('/'):
            return f"{self.path}{child}"
        else:
            return f"{self.path}/{child}"

class SchemaRef(SchemaNode):
    """
    Reference to another entity
    """
    def __init__(self, name: str | None, path: str, parent: SchemaNode, *, required: bool = False):
        super().__init__(name, path, parent, required=required)
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
        self.required: set[str] = set()
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

    def resolve_refs(self, *, defs: dict | None = None) -> int:
        n_resolved: int = 0
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
                n_resolved += node.resolve_refs(defs=d)
            elif isinstance(node, SchemaArray):
                n_resolved += node.resolve_refs(defs=d)
            elif isinstance(node, SchemaRef):
                if node.path not in d:
                    print(f"WARNING: Unable to resolve reference for node path {node.path}")
                else:
                    if not node.referent:
                        node.referent = d[node.path]
                        n_resolved += 1

        # Now resolve refs in this object's properties
        for node in self.properties.values():
            if node is None:
                # TODO: Remove after we have implemented all node types, after which no nodes will be None
                continue
            if isinstance(node, SchemaObject):
                n_resolved += node.resolve_refs(defs=d)
            elif isinstance(node, SchemaArray):
                n_resolved += node.resolve_refs(defs=d)
            if isinstance(node, SchemaRef):
                if node.path not in d:
                    print(f"WARNING: Unable to resolve reference for node path {node.path}")
                else:
                    if not node.referent:
                        node.referent = d[node.path]
                        n_resolved += 1

        return n_resolved
    
    def _from_dict(self, d: dict):
        if 'required' in d:
            for r in d['required']:
                self.required.add(r)
        if 'properties' in d:
            for k, v in d['properties'].items():
                if k == 'features':
                    # Features are defined in the schema, but they're constructed, rather than
                    # specified.  Therefore we need to ignore them when parsing the schema to
                    # construct the GUI.
                    continue
                if isinstance(v, dict):
                    if '$ref' in v:
                        # Property is a reference node
                        required: bool = False
                        if k in self.required:
                            required = True
                        parsed: SchemaRef = SchemaRef(k, v['$ref'], self, required=required)
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
                        self.properties[k] = parse_schema(v, self.join_path(k), k, self, required=k in self.required)
        # Attempt to process defs
        for ref in self.defs_keys:
            if ref in d:
                for k, v in d[ref].items():
                    path: str = f"{self.path}{ref}/{k}"
                    parsed: SchemaNode = parse_schema(v, path, k, self)
                    self.defs[path] = parsed

class SchemaArray(SchemaNode):
    def __init__(self, name: str, path: str | None, parent: SchemaNode | None, d: dict,
                 *,
                 required: bool = False):
        super().__init__(name, path, parent, required=required)

        self.unique_items: bool | None = None
        self.min_items: int | None = None
        self.max_items: int | None = None

        self.items: list[SchemaNode] = []
        self.items_all_of: list[SchemaNode] = []
        self.items_any_of: list[SchemaNode] = []
        self.items_one_of: list[SchemaNode] = []

        # Initialize object from dict
        self._from_dict(d)

    def to_string(self, *, depth: int = 1) -> str:
        indent_root: str = '\t\t\t\t' * (depth-1)
        indent: str = '\t\t\t' * depth
        # cont: str = '\t\t\t' * (depth+1)
        # cont_sub = '\t\t' * (depth+2)
        parent = self.parent.name if self.parent is not None else 'nil'
        o = io.StringIO()
        o.write(f"{indent_root}SchemaArray(name: {self.name}, path: {self.path}, parent: {parent},\n")
        o.write(f"{indent}required: {self.is_required},\n")
        o.write(f"{indent}uniqueItems: {self.unique_items}\n")
        o.write(f"{indent}minItems: {self.min_items},\n")
        o.write(f"{indent}maxItems: {self.max_items},\n")
        o.write(f"{indent}items:\n")
        for i in self.items:
            if i is None:
                # TODO: Remove after we have implemented all node types, after which no nodes will be None
                continue
            o.write(f"{i.to_string(depth=depth+1)}\n")
        o.write(f"{indent}items::allOf:\n")
        for i in self.items_all_of:
            if i is None:
                # TODO: Remove after we have implemented all node types, after which no nodes will be None
                continue
            o.write(f"{i.to_string(depth=depth+1)}\n")
        o.write(f"{indent}items::anyOf:\n")
        for i in self.items_any_of:
            if i is None:
                # TODO: Remove after we have implemented all node types, after which no nodes will be None
                continue
            o.write(f"{i.to_string(depth=depth+1)}\n")
        o.write(f"{indent}items::oneOf:\n")
        for i in self.items_one_of:
            if i is None:
                # TODO: Remove after we have implemented all node types, after which no nodes will be None
                continue
            o.write(f"{i.to_string(depth=depth+1)}\n")
        o.write(f"\n{indent_root})")
        return o.getvalue()

    def resolve_refs(self, *, defs: dict) -> int:
        n_resolved: int = 0
        for node in self.items:
            if isinstance(node, SchemaRef):
                if node.path not in defs:
                    print(f"WARNING: Unable to resolve reference for node path {node.path}")
                else:
                    if not node.referent:
                        node.referent = defs[node.path]
                        n_resolved += 1
        for node in self.items_all_of:
            if isinstance(node, SchemaRef):
                if node.path not in defs:
                    print(f"WARNING: Unable to resolve reference for node path {node.path}")
                else:
                    if not node.referent:
                        node.referent = defs[node.path]
                        n_resolved += 1
        for node in self.items_any_of:
            if isinstance(node, SchemaRef):
                if node.path not in defs:
                    print(f"WARNING: Unable to resolve reference for node path {node.path}")
                else:
                    if not node.referent:
                        node.referent = defs[node.path]
                        n_resolved += 1
        for node in self.items_one_of:
            if isinstance(node, SchemaRef):
                if node.path not in defs:
                    print(f"WARNING: Unable to resolve reference for node path {node.path}")
                else:
                    if not node.referent:
                        node.referent = defs[node.path]
                        n_resolved += 1
        return n_resolved

    def _from_dict(self, d: dict):
        self.unique_items = d.get('uniqueItems', False)
        if 'minItems' in d:
            self.min_items = d['minItems']
        if 'maxItems' in d:
            self.max_items = d['maxItems']
        if 'items' in d:
            items: dict = d['items']
            if 'allOf' in items:
                all_of_items: list[dict] = items['allOf']
                for i in all_of_items:
                    for k, v in i.items():
                        path: str = self.join_path(f"items/allOf/{k}")
                        if '$ref' in v:
                            self.items_all_of.append(parse_reference(i, self))
                        else:
                            self.items_all_of.append(parse_schema(v, path, k, self, required=True))
            elif 'anyOf' in items:
                any_of_items: list[dict] = items['anyOf']
                for i in any_of_items:
                    for k, v in i.items():
                        if '$ref' in k:
                            self.items_any_of.append(parse_reference(i, self))
                        else:
                            path: str = self.join_path(f"items/anyOf/{k}")
                            self.items_any_of.append(parse_schema(v, path, k, self, required=False))
            elif 'oneOf' in items:
                one_of_items: list[dict] = items['oneOf']
                for i in one_of_items:
                    for k, v in i.items():
                        if '$ref' in k:
                            self.items_one_of.append(parse_reference(i, self))
                        else:
                            path: str = self.join_path(f"items/oneOf/{k}")
                            self.items_one_of.append(parse_schema(v, path, k, self, required=True))
            else:
                for k in items.keys():
                    match k:
                        case '$ref':
                            self.items_all_of.append(parse_reference(items, self))
                        case 'type':
                            path: str = self.join_path('items')
                            self.items_one_of.append(parse_schema(items, path, k, self, required=True))


class SchemaLeaf(SchemaNode, ABC):
    """
    Super-class for schema terminal nodes
    """
    def __init__(self, name: str, path: str | None, parent: SchemaNode | None,
                 *,
                 required: bool = False):
        super().__init__(name, path, parent, required=required)

class SchemaString(SchemaLeaf):
    def __init__(self, name: str, path: str | None, parent: SchemaNode | None, d: dict,
                 *,
                 required: bool = False):
        super().__init__(name, path, parent, required=required)

        self.title: str | None = None
        self.description: str | None = None
        self.pattern: str | None = None
        self.enum_values: set | None = None

        # Initialize object from dict
        self._from_dict(d)

    def to_string(self, *, depth: int = 1) -> str:
        indent_root: str = '\t\t\t\t\t' * (depth - 1)
        indent: str = '\t\t\t\t' * depth
        title = self.title if self.title is not None else 'nil'
        desc = self.description if self.description is not None else 'nil'
        patt = self.pattern if self.pattern is not None else 'nil'
        parent = self.parent.name if self.parent is not None else 'nil'
        return (f"{indent_root}SchemaString(path: {self.path},\n{indent}title: {title},\n{indent}"
                f"description: {desc},\n{indent}pattern: {patt},\n{indent}parent: {parent},\n{indent}"
                f"required: {self.is_required}.\n{indent}enum_values: {self.enum_values})")

    def _from_dict(self, d: dict):
        self.title = d.get('title')
        self.description = d.get('description')
        self.pattern = d.get('pattern')
        if 'enum' in d and isinstance(d['enum'], list):
            self.enum_values: set | None = set(d['enum'])

class SchemaInteger(SchemaLeaf):
    def __init__(self, name: str, path: str | None, parent: SchemaNode | None, d: dict,
                 *,
                 required: bool = False):
        super().__init__(name, path, parent, required=required)

        self.title: str | None
        self.description: str | None
        self.minimum: int | None
        self.maximum: int | None

        # Initialize object from dict
        self._from_dict(d)

    def to_string(self, *, depth: int = 1) -> str:
        indent_root: str = '\t\t\t\t\t' * (depth - 1)
        indent: str = '\t\t\t\t' * depth
        title = self.title if self.title is not None else 'nil'
        desc = self.description if self.description is not None else 'nil'
        minimum = self.minimum if self.minimum is not None else 'nil'
        maximum = self.maximum if self.maximum is not None else 'nil'
        parent = self.parent.name if self.parent is not None else 'nil'
        return (f"{indent_root}SchemaInteger(path: {self.path},\n{indent}title: {title},\n{indent}"
                f"description: {desc},\n{indent}minimum: {minimum},\n{indent}maximum: {maximum},\n{indent}parent: {parent},\n{indent}"
                f"required: {self.is_required})")

    def _from_dict(self, d: dict):
        self.title = d.get('title')
        self.description = d.get('description')
        self.minimum = d.get('minimum')
        self.maximum = d.get('maximum')

class SchemaNumber(SchemaLeaf):
    def __init__(self, name: str, path: str | None, parent: SchemaNode | None, d: dict,
                 *,
                 required: bool = False):
        super().__init__(name, path, parent, required=required)
        self.title: str | None
        self.description: str | None
        self.minimum: float | None
        self.maximum: float | None

        self._from_dict(d)
    
    def to_string(self, *, depth: int = 1) -> str:
        indent_root: str = '\t\t\t\t\t' * (depth - 1)
        indent: str = '\t\t\t\t' * depth
        title = self.title if self.title is not None else 'nil'
        desc = self.description if self.description is not None else 'nil'
        minimum = self.minimum if self.minimum is not None else 'nil'
        maximum = self.maximum if self.maximum is not None else 'nil'
        parent = self.parent.name if self.parent is not None else 'nil'
        return (f"{indent_root}SchemaNumber(path: {self.path},\n{indent}title: {title},\n{indent}"
                f"description: {desc},\n{indent}minimum: {minimum},\n{indent}maximum: {maximum},\n{indent}parent: {parent},\n{indent}"
                f"required: {self.is_required})")

    def _from_dict(self, d: dict):
        self.title = d.get('title')
        self.description = d.get('description')
        self.minimum = d.get('minimum')
        self.maximum = d.get('maximum')

class SchemaBoolean(SchemaLeaf):
    def __init__(self, name: str, path: str | None, parent: SchemaNode | None, d: dict,
                 *,
                 required: bool = False):
        super().__init__(name, path, parent, required=required)
        self.title: str | None = None
        self.description: str | None = None
        self._from_dict(d)

    def to_string(self, *, depth: int = 1) -> str:
        indent_root: str = '\t\t\t\t\t' * (depth - 1)
        indent: str = '\t\t\t\t' * depth
        title = self.title if self.title is not None else 'nil'
        desc = self.description if self.description is not None else 'nil'
        parent = self.parent.name if self.parent is not None else 'nil'
        return (f"{indent_root}SchemaBoolean(path: {self.path},\n{indent}title: {title},\n{indent}"
                f"description: {desc},\n{indent}parent: {parent},\n{indent}"
                f"required: {self.is_required})")

    def _from_dict(self, d: dict):
        self.title = d.get('title')
        self.description = d.get('description')

def parse_reference(schema: dict, parent: SchemaNode) -> SchemaRef:
    if '$ref' not in schema:
        raise ValueError(f"schema must contain '$ref' key but did not")
    return SchemaRef(None, schema['$ref'], parent)


S = TypeVar('S', bound=SchemaNode | None)
def parse_schema(schema: dict, path: str | None, name: str | None, parent: SchemaNode | None,
                 *,
                 required: bool | None = None) -> S:
    """
    Parse JSON Schema document. Note: Assumes the root of the schema is an object for our purposes for now.
    :param name:
    :param path:
    :param schema:
    :param parent:
    :param required: Should only be set for SchemaLeafString, will be ignored for other types
    :return:
    """
    if 'type' not in schema:
        raise ValueError(f"schema dictionary doesn't appear to represent a JSON Schema document (no 'type' specified) for: {name} | {path}.")

    match schema['type']:
        case 'object':
            if name == 'GeoJSONFeature':
                # Special case: GeoJSONFeature is defined in the schema, but it's constructed, rather than
                # specified.  Therefore we need to ignore it when parsing the schema to construct the GUI.
                return None
            return SchemaObject(name, path, parent, schema)
        case 'array':
            return SchemaArray(name, path, parent, schema)
        case 'string':
            if required is None:
                is_required = False
            else:
                is_required = required
            return SchemaString(name, path, parent, schema, required=is_required)
        case 'integer':
            if required is None:
                is_required = False
            else:
                is_required = required
            return SchemaInteger(name, path, parent, schema, required=is_required)
        case 'number':
            if required is None:
                is_required = False
            else:
                is_required = required
            return SchemaNumber(name, path, parent, schema, required=required)
        case 'boolean':
            if required is None:
                is_required = False
            else:
                is_required = required
            return SchemaBoolean(name, path, parent, schema, required=is_required)
        case _:
            print(f"warning: have not yet implemented parsing of schema of type {schema['type']} | {name} | {path}")

def open_schema(*, schema_filename: str = 'CSB-schema-3_1_0-2024-04.json') -> dict:
    # TODO: Eventually add an API to csbschema to get the schema files in a safer way, for now this will do...
    schema_path: Path = Path(str(resources.files('csbschema').joinpath(f"data/{schema_filename}")))
    assert schema_path.exists()
    assert schema_path.is_file()

    with schema_path.open(mode='r') as f:
        schema: dict = json.load(f)
    assert schema is not None

    return schema

