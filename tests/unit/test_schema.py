from typing import cast

from openvbi.core.schema import open_schema, parse_schema, SchemaNode, SchemaObject


def test_schema_parsing():
    schema: dict = open_schema()
    assert schema is not None
    schema_node: SchemaNode = parse_schema(schema, None,None, None)
    assert schema_node is not None
    assert isinstance(schema_node, SchemaObject)
    schema_obj: SchemaObject = cast(SchemaObject, schema_node)
    # print(f"Parsed schema before resolving refs was:\n{schema_obj.to_string()}")
    schema_obj.resolve_refs()
    print(f"Parsed schema AFTER resolving refs was:\n{schema_obj.to_string()}")
