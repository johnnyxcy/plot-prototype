import typing


class Singleton(type):
    _instances: dict[type, typing.Any] = {}

    def __call__(cls, *args: typing.Any, **kwargs: typing.Any) -> typing.Any:
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]
