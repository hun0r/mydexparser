from io import BufferedReader
from typing import Callable
import inspect


class Obj:
    __cache = {}

    def __init_subclass__(cls):
        cls.__blueprint = vars(cls).copy()
        for k in list(cls.__blueprint.keys()):
            if k.startswith("_"):
                cls.__blueprint.pop(k)

        return super().__init_subclass__()

    def __new__(cls, buff: BufferedReader, *_, **__) -> None:
        if (buff.tell(), cls) in cls.__cache:
            return cls.__cache[(buff.tell(), cls)]
        instance = super().__new__(cls)
        cls.__cache[(buff.tell(), cls)] = instance
        return instance

    def __init__(
        self,
        buff: BufferedReader,
        context: Obj | None = None,
        off: int | None = None,
        ret: int | None = None,
    ):
        if off is not None:
            ret = ret if ret is not None else buff.tell()
            buff.seek(off)
        for k, v in self.__blueprint.items():
            setattr(self, k, v.parse(buff, self))
        if off is not None:
            buff.seek(ret)

    def __str__(self):
        return (
            self.__class__.__name__
            + "[\n\t"
            + "\n\t".join(
                k + ": " + str(getattr(self, k, None)).replace("\n", "\n\t")
                for k in self.__blueprint.keys()
            )
            + "\n]"
        )


class Tuple[T](tuple[T]):
    def __str__(self):
        return "(\n\t" + "\n\t".join(str(v).replace("\n", "\n\t") for v in self) + "\n)"


class Type[T]:
    def __init__(
        self, parser: Callable[[BufferedReader], T] | Callable[[BufferedReader, Obj], T]
    ):
        """only functions with more than 1 positional parameter are assumed to require context"""
        if len(inspect.signature(parser).parameters) == 1:
            self.parse = lambda buff, obj, *args, **kwargs: parser(
                buff, *args, **kwargs
            )
        else:
            self.parse = parser

    def __get__(self, instance, owner) -> T:
        raise NotImplementedError("this is only a type hint and should not be called")

    def parse(self, buff: BufferedReader, obj: Obj | None = None) -> T:
        raise NotImplementedError(
            "this should be set in __init__ something wrong happened"
        )

    def __getitem__(self, key: str | int) -> Type[Tuple[T]]:
        if isinstance(key, int):
            return Type(
                lambda buff, obj: Tuple(self.parse(buff, obj) for _ in range(key))
            )

        def parser(buff: BufferedReader, obj: Obj) -> Tuple[T]:
            return Tuple(self.parse(buff, obj) for _ in range(getattr(obj, key)))

        return Type(parser)
