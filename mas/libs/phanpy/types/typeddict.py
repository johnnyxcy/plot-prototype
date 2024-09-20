from typing import Any, Mapping, TypeVar, cast

T = TypeVar("T")


def keysafe_typeddict(
    d: Mapping[str, Any],
    typ: type[T],
    **defaults: Any,
) -> T:
    cleaned: dict[str, Any] = {}
    for k in typ.__annotations__.keys():
        if k in d:
            cleaned[k] = d[k]
        elif k in defaults:
            cleaned[k] = defaults[k]

    return cast(T, cleaned)


def pop_key_in_typeddict(
    d: dict[str, Any],
    typ: type[T],
    **defaults: Any,
) -> T:
    removed: dict[str, Any] = {}
    for k in typ.__annotations__.keys():
        if k in d:
            removed[k] = d.pop(k)
        elif k in defaults:
            removed[k] = defaults[k]

    return cast(T, removed)
