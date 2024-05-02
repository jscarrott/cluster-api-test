from dataclasses import dataclass
from typing import Annotated, Any, Callable, List, TypeVar, TYPE_CHECKING, get_args

from pydantic_core import ValidationError
from pydantic_core import core_schema as cs


@dataclass
class _Error:
    error: Exception
    original_index: int = -1


@dataclass
class _ErrorItemsMarker:
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: Callable[[Any], cs.CoreSchema]
    ) -> cs.CoreSchema:
        schema = handler(source_type)

        def val(v: Any, handler: cs.ValidatorFunctionWrapHandler) -> Any:
            try:
                return handler(v)
            except ValidationError as exc:
                return _Error(exc)

        return cs.no_info_wrap_validator_function(
            val, schema, serialization=schema.get("serialization")
        )


@dataclass
class _LenientListFilter:
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: Callable[[Any], cs.CoreSchema]
    ) -> cs.CoreSchema:
        schema = handler(source_type)

        def val(v: List[Any]) -> LenientList[Any]:
            successes = []
            errors = []
            original_error_indices = []
            for i, item in enumerate(v):
                if isinstance(item, _Error):
                    errors.append(item.error)
                    original_error_indices.append(i)
                else:
                    successes.append(item)
            result = LenientList(successes)
            result.errors = errors
            result.original_error_indices = original_error_indices
            return result

        return cs.no_info_after_validator_function(
            val, schema, serialization=schema.get("serialization")
        )


T = TypeVar("T")


class LenientList(List[T]):
    def __init__(self, seq=()):
        super().__init__(seq)
        self.original_length = len(seq)
        self.errors: List[ValidationError] = []
        self.original_error_indices = []

    def with_errors(self) -> List[T | ValidationError]:
        if not self.errors:
            return list(self)
        original_error_index: int | None = self.original_error_indices[0]

        item_index = 0
        error_index = 0
        result = []
        n_items = len(self)
        n_errors = len(self.errors)
        while item_index < n_items or error_index < n_errors:
            while original_error_index == len(result):
                result.append(self.errors[error_index])
                error_index += 1
                try:
                    original_error_index = self.original_error_indices[error_index]
                except IndexError:
                    original_error_index = None
            if item_index < len(self):
                result.append(self[item_index])
                item_index += 1
        return result

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: Callable[[Any], cs.CoreSchema]
    ) -> cs.CoreSchema:
        args = get_args(source_type)
        if args:
            return handler(
                Annotated[
                    List[Annotated[args[0], _ErrorItemsMarker()]], _LenientListFilter()
                ]
            )
        else:
            return cs.no_info_after_validator_function(LenientList, handler(List))


# from pydantic import BaseModel


# class Model(BaseModel):
#     x: LenientList[int]
#     y: LenientList[str]


# m = Model(x=[1, "2", "c"], y=["a", "b", 3])

# print(m.x)
# # > [1, 2]
# print(m.x.errors)
# """
# [1 validation error for ValidatorCallable
#   Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='c', input_type=str]]
# """
# print(m.x.with_errors())
# """
# [1, 2, 1 validation error for ValidatorCallable
#   Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='c', input_type=str]]
# """
