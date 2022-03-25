"""Preconfigured converters for orjson."""
from base64 import b85decode, b85encode
from datetime import datetime
from enum import Enum
from typing import Any, Type, TypeVar

from orjson import dumps, loads

from cattrs._compat import Set, is_mapping

from ..converters import GenConverter

T = TypeVar("T")


class OrjsonConverter(GenConverter):
    def dumps(self, obj: Any, unstructure_as=None, **kwargs) -> bytes:
        return dumps(self.unstructure(obj, unstructure_as=unstructure_as), **kwargs)

    def loads(self, data: bytes, cl: Type[T]) -> T:
        return self.structure(loads(data), cl)


def configure_converter(converter: GenConverter):
    """
    Configure the converter for use with the orjson library.

    * bytes are serialized as base85 strings
    * datetimes are serialized as ISO 8601
    * sets are serialized as lists
    * string enum mapping keys have special handling
    * mapping keys are coerced into strings when unstructuring
    """
    converter.register_unstructure_hook(
        bytes, lambda v: (b85encode(v) if v else b"").decode("utf8")
    )
    converter.register_structure_hook(bytes, lambda v, _: b85decode(v))

    converter.register_unstructure_hook(datetime, lambda v: v.isoformat())
    converter.register_structure_hook(datetime, lambda v, _: datetime.fromisoformat(v))

    def gen_unstructure_mapping(cl: Any, unstructure_to=None):
        key_handler = str
        args = getattr(cl, "__args__", None)
        if args and issubclass(args[0], str) and issubclass(args[0], Enum):

            def key_handler(v):
                return v.value

        return converter.gen_unstructure_mapping(
            cl, unstructure_to=unstructure_to, key_handler=key_handler
        )

    converter._unstructure_func.register_func_list(
        [(is_mapping, gen_unstructure_mapping, True)]
    )


def make_converter(*args, **kwargs) -> OrjsonConverter:
    kwargs["unstruct_collection_overrides"] = {
        **kwargs.get("unstruct_collection_overrides", {}),
        Set: list,
    }
    res = OrjsonConverter(*args, **kwargs)
    configure_converter(res)

    return res
