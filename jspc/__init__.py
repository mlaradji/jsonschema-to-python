# -*- coding: utf-8 -*-
import typing as t

from frozendict import frozendict

# Python indentation.
INDENT: str = "    "

JSONSchema = t.TypedDict(
    "JSONSchema",
    {
        "$schema": str,
        "$ref": str,
        "$id": str,
        "id": str,
        "title": str,
        "description": str,
        "definitions": t.Dict[str, "JSONSchema"],
        "type": t.Literal["object", "string", "number", "boolean", "null"],
        "properties": t.Dict[str, "JSONSchema"],
        "oneOf": t.List["JSONSchema"],
        "anyOf": t.List["JSONSchema"],
        "allOf": t.List["JSONSchema"],
        "required": t.List[str],
    },
    total=False,
)

map_types: t.Final[t.Dict[str, str]] = frozendict(
    {"string": "str", "number": "Union[float, int]", "boolean": "bool", "null": "None"}
)

print("from typing import Union\nfrom typing import TypedDict\n")


def standardize_name(name: str, parents: t.List[str] = None) -> str:
    # Abuse the fact that '"' is not allowed as part of a property name in JSON to create unique names for objects.
    return (
        name.capitalize()
        if parents is None
        else "".join(map(lambda n: n.capitalize(), [*parents, name]))
        + '"'.join([name, *parents]).encode().hex()
    )


def return_type(
    schema: JSONSchema, name: str = None, parents: t.List[str] = None
) -> str:
    name = name or schema.get("title", "root")
    if schema["type"] in map_types:
        return map_types[schema["type"]]

    # Create required class.
    required_class = (
        f"class {standardize_name(name, parents)}Required(TypedDict, total=True):\n"
    )
    for required_property in schema.get("required", []):
        property_type = return_type(
            schema["properties"][required_property],
            name=required_property,
            parents=(parents if parents else []) + [name],
        )
        required_class += f"{INDENT}{required_property}: {property_type}\n"
    required_class += f"{INDENT}pass\n\n"

    # Create optional class.
    optional_class = (
        f"class {standardize_name(name, parents)}Optional(TypedDict, total=False):\n"
    )
    for optional_property in filter(
        lambda p: p not in schema.get("required", []), schema.get("properties", {})
    ):
        property_type = return_type(
            schema["properties"][optional_property],
            name=optional_property,
            parents=(parents if parents else []) + [name],
        )
        optional_class += f"{INDENT}{optional_property}: {property_type}\n"
    optional_class += f"{INDENT}pass\n\n"

    # Combine the classes through inheritance to get a dict with both required and optional keys.
    combined_class = f"class {standardize_name(name, parents)}({standardize_name(name, parents)}Required, {standardize_name(name, parents)}Optional):\n{INDENT}pass\n"

    # Output the new classes defined.
    print(required_class + optional_class + combined_class)

    return standardize_name(name, parents)


schema = {
    "type": "object",
    "properties": {
        "hi": {"type": "object", "properties": {"hello": {"type": "number"}}},
        "hello": {"type": "number"},
    },
    "required": ["hi"],
}

return_type(schema)
# schema = {
#     "$schema": "http://json-schema.org/draft-07/schema#",
#     "definitions": {
#         "address": {
#             "type": "object",
#             "properties": {
#                 "street_address": {"type": "string"},
#                 "city": {"type": "string"},
#                 "state": {"type": "string"},
#             },
#             "required": ["street_address", "city", "state"],
#         }
#     },
#     "type": "object",
#     "properties": {
#         "billing_address": {"$ref": "#/definitions/address"},
#         "shipping_address": {"$ref": "#/definitions/address"},
#     },
# }
