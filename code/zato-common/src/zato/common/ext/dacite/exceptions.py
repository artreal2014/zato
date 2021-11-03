"""
This module is a modified vendor copy of the dacite package from https://pypi.org/project/dacite/

MIT License

Copyright (c) 2018 Konrad Hałas

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

# flake8: noqa

from typing import Any, Type, Optional, Set, Dict


def _name(type_: Type) -> str:
    return type_.__name__ if hasattr(type_, "__name__") else str(type_)


class DaciteError(Exception):
    pass


class DaciteFieldError(DaciteError):
    def __init__(self, field_path: Optional[str] = None):
        self.field_path = field_path

    def update_path(self, parent_field_path: str) -> None:
        if self.field_path:
            self.field_path = f"{parent_field_path}.{self.field_path}"
        else:
            self.field_path = parent_field_path


class WrongTypeError(DaciteFieldError):
    def __init__(self, field_type: Type, value: Any, field_path: Optional[str] = None) -> None:
        super().__init__(field_path=field_path)
        self.field_type = field_type
        self.value = value

    def __str__(self) -> str:
        return (
            f'wrong value type for field "{self.field_path}" - should be "{_name(self.field_type)}" '
            f'instead of value "{self.value}" of type "{_name(type(self.value))}"'
        )


class MissingValueError(DaciteFieldError):
    def __init__(self, field_path: Optional[str] = None):
        super().__init__(field_path=field_path)

    def __str__(self) -> str:
        return f'missing value for field "{self.field_path}"'


class UnionMatchError(WrongTypeError):
    def __str__(self) -> str:
        return (
            f'can not match type "{_name(type(self.value))}" to any type '
            f'of "{self.field_path}" union: {_name(self.field_type)}'
        )


class StrictUnionMatchError(DaciteFieldError):
    def __init__(self, union_matches: Dict[Type, Any], field_path: Optional[str] = None) -> None:
        super().__init__(field_path=field_path)
        self.union_matches = union_matches

    def __str__(self) -> str:
        conflicting_types = ", ".join(_name(type_) for type_ in self.union_matches)
        return f'can not choose between possible Union matches for field "{self.field_path}": {conflicting_types}'


class ForwardReferenceError(DaciteError):
    def __init__(self, message: str) -> None:
        super().__init__()
        self.message = message

    def __str__(self) -> str:
        return f"can not resolve forward reference: {self.message}"


class UnexpectedDataError(DaciteError):
    def __init__(self, keys: Set[str]) -> None:
        super().__init__()
        self.keys = keys

    def __str__(self) -> str:
        formatted_keys = ", ".join(f'"{key}"' for key in self.keys)
        return f"can not match {formatted_keys} to any data class field"