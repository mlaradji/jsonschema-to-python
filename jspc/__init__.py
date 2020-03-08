# -*- coding: utf-8 -*-
import typing as t
import string

from frozendict import frozendict
import networkx as nx

# Python indentation.
INDENT: str = "    "

JSON_TYPE_MAP: t.Final[t.Dict[str, type]] = frozendict(
    {"string": str, "number": float, "boolean": bool, "null": None}
)
PYTHON_TYPE_MAP: t.Final[t.Dict[type, str]] = frozendict(
    {str: "str", float: "Union[float, int]", bool: "bool", None: "None"}
)

print("from typing import Union\nfrom typing import TypedDict\n")


class JSONSchema:
    graph: nx.DiGraph

    class Ref(tuple):
        @property
        def path(self):
            path = ()
            for i in range(len(self) - 1, -1, -1):
                path = (self[: i + 1],) + path
            return path

        @property
        def name(self) -> str:
            return "".join(
                subref.lower().capitalize()
                for subref in self
                if set(subref).issubset(tuple(string.ascii_letters + string.digits))
            )

        @property
        def unique_name(self) -> str:
            return self.name + str(self.positive_hash()) if self.name else "Root"

        def positive_hash(self) -> int:
            """Return a positive hash by prepending 1 if normal hash is negative and 2 if normal hash is positive."""
            _hash = hash(self)
            if _hash < 0:
                return int(f"1{abs(_hash)}")
            return int(f"2{abs(_hash)}")

        def __add__(
            self, other: "t.Union[JSONSchema.Ref, t.Tuple[str, ...]]"
        ) -> "JSONSchema.Ref":
            return JSONSchema.Ref(super().__add__(other))

    Dict = t.TypedDict(
        "Dict",
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

    class Class(t.NamedTuple):
        ref: "JSONSchema.Ref"
        supers: t.Sequence[str]
        description: str = ""

        def __str__(self) -> str:
            return self.ref.unique_name

        def definition(self) -> str:
            if self.supers:
                return f'class {self.ref.unique_name}({", ".join(self.supers)}):\n{INDENT}"""{self.description}"""\n'

            return "" # No need to define this class.

    def __init__(self, schema: "JSONSchema.Dict"):
        self.graph = nx.DiGraph()
        self.schema = schema
        self._class = self._add_type(JSONSchema.Ref(("#",)), schema)

    def _add_type(self, ref: "JSONSchema.Ref", schema: "JSONSchema.Dict", is_definition: bool = False) -> str:
        
        # Add the node to the graph.
        nx.add_path(self.graph, ref.path)

        if subref := schema.get("$ref"):
            # This schema has a reference. Let's not resolve the references just yet.
            nx.add_path(JSONSchema.Ref(subref.split("/")).path+(ref,))

        # 20200307: @mlaradji: master - Currently, we only have output for when type is defined.
        schema_type = schema["type"]
        if schema_type in JSON_TYPE_MAP:
            type_str = PYTHON_TYPE_MAP[JSON_TYPE_MAP[schema_type]]

            if is_definition:
                print(f"{ref.unique_name} = {type_str}\n")
                return ref.unique_name
            return type_str

        properties = schema["properties"]
        required_properties = schema.get("required", [])
        class_supers: t.List[str] = []

        # Create class for optional properties.
        if optional_class_name := self._add_class(
            ref=ref + ("properties",),
            property_names=filter(lambda p: p not in required_properties, properties),
            schema_properties=properties,
            total=False,
        ):
            class_supers.append(optional_class_name)

        # Create class for required properties.
        if required_class_name := self._add_class(
            ref=ref + ("properties",),
            property_names=required_properties,
            schema_properties=properties,
            total=True,
        ):
            class_supers.append(required_class_name)

        # Create definitions but don't add them as a super (yet).
        definitions = schema.get("definitions", {})
        self._add_class(
            ref=ref + ("definitions",),
            property_names=definitions.keys(),
            schema_properties=definitions,
            is_definition=True
        )

        # Combine the classes through inheritance to get a dict with both required and optional keys.
        _class = JSONSchema.Class(ref, class_supers)
        print(_class.definition())
        return _class

    def _add_class(
        self,
        ref: "JSONSchema.Ref",
        property_names: t.Iterable[str],
        schema_properties: t.Dict[str, "JSONSchema.Dict"],
        total: bool = False,
        is_definition: bool = False,
    ) -> t.Optional["JSONSchema.Ref"]:
        """
        Print out a new class with properties in `properties`.

        :param total: True if all is required and False otherwise.
        :param is_definition: Empty suffix if True, instead of 'Required' or 'Optional'.
        :returns: Name of the new class, or `None` if no class was created (if properties is empty).
        """

        class_name_suffix = "" if is_definition else "Required" if total else "Optional"
        class_name = f"{ref.name}{class_name_suffix}{ref.positive_hash()}"
        class_text = f'class {class_name}(TypedDict, total={total}):\n{INDENT}""""""\n'


        # Only create a class if we have some defined properties.
        props = list(property_names)

        if not props:
            return None

        # Construct the attributes of the new class.
        for prop in props:
            property_type = self._add_type(
                ref + (prop,), schema_properties[prop], is_definition=is_definition
            )
            class_text += f"{INDENT}{prop}: {property_type}\n"

        # Now output what we made.
        print(class_text)
        return class_name

    def visualize(self):
        """
        Plot the JSON Schema.
        
        Note: requires `matplotlib` and `EoN`.
        """

        from matplotlib import pyplot as plt
        import EoN

        nx.draw(a.graph, with_labels=True,pos=EoN.auxiliary.hierarchy_pos(a.graph))
        plt.show()

example_schema = {
    "type": "object",
    "properties": {
        "hi": {
            "type": "object",
            "properties": {
                "hello": {"$ref": "#/definitions/status"},
                "test": {"type": "object", "properties": {"test1": {"type": "number"}}},
            },
        },
        "hello": {"type": "number"},
    },
    "required": ["hi"],
    "definitions": {"status": {"type": "string"}},
}

a = JSONSchema(example_schema)
#print(a.graph.nodes)
#print(a.graph[('#','properties')])
a.visualize()


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
