"""Preconfigured converters for tomlkit."""
from base64 import b85decode, b85encode
from datetime import datetime
from typing import Any, Type, TypeVar

from tomlkit import dumps, loads

from cattrs._compat import Set, is_mapping

from ..converters import GenConverter
from . import validate_datetime

T = TypeVar("T")


class TomlkitConverter(GenConverter):
    def dumps(self, obj: Any, unstructure_as=None, **kwargs) -> str:
        return dumps(self.unstructure(obj, unstructure_as=unstructure_as), **kwargs)

    def loads(self, data: str, cl: Type[T]) -> T:
        return self.structure(loads(data), cl)


def configure_converter(converter: GenConverter):
    """
    Configure the converter for use with the tomlkit library.

    * bytes are serialized as base85 strings
    * sets are serialized as lists
    * tuples are serializas as lists
    * mapping keys are coerced into strings when unstructuring
    """
    converter.register_structure_hook(bytes, lambda v, _: b85decode(v))
    converter.register_unstructure_hook(
        bytes, lambda v: (b85encode(v) if v else b"").decode("utf8")
    )

    def gen_unstructure_mapping(cl: Any, unstructure_to=None):
        key_handler = str
        args = getattr(cl, "__args__", None)
        if args and issubclass(args[0], str):
            key_handler = None
        return converter.gen_unstructure_mapping(
            cl, unstructure_to=unstructure_to, key_handler=key_handler
        )

    converter._unstructure_func.register_func_list(
        [(is_mapping, gen_unstructure_mapping, True)]
    )
    converter.register_structure_hook(datetime, validate_datetime)


def make_converter(*args, **kwargs) -> TomlkitConverter:
    kwargs["unstruct_collection_overrides"] = {
        **kwargs.get("unstruct_collection_overrides", {}),
        Set: list,
        tuple: list,
    }
    res = TomlkitConverter(*args, **kwargs)
    configure_converter(res)

    return res
