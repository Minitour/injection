from typing import Generic, TypeVar

from injection.providers.base import BaseProvider

T = TypeVar("T")


class ClassGetItemMeta(Generic[T], type):
    def __getitem__(cls, item: BaseProvider[T]) -> T:
        return cls(item)


class Provide(metaclass=ClassGetItemMeta):
    def __init__(self, provider: BaseProvider[T]) -> None:
        self.provider = provider

    def __call__(self) -> T:
        return self
