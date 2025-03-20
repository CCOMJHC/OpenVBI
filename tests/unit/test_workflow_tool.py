from typing import cast
from pathlib import Path
from importlib import resources
import json

from openvbi.core.schema import parse_schema, SchemaNode, SchemaObject


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
