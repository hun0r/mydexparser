from typing import Any, Callable, Self, overload, Protocol
import inspect

class File(Protocol):
    def read(self, size: int = -1, /) -> bytes:
        """
        Read and return up to n bytes.

        If the size argument is omitted, None, or negative, read and return all data until EOF.

        If the size argument is positive, and the underlying raw stream is not 'interactive', 
        multiple raw reads may be issued to satisfy the byte count (unless EOF is reached first). 
        However, for interactive raw streams (as well as sockets and pipes), at most one raw 
        read will be issued, and a short result does not imply that EOF is imminent.
        """
        raise NotImplementedError()
    def tell(self, /) -> int:
        """Return current stream position."""
        raise NotImplementedError()
    def seek(self,target: int,
        whence: int = 0,
        /
    ) -> int:
        """
        Change the stream position to the given byte offset.

        offset
            The stream position, relative to 'whence'.
        whence
            The relative position to seek from.

        The offset is interpreted relative to the position indicated by
        whence. Values for whence are:

        os.SEEK_SET or 0 -- start of stream (the default); offset should
        be zero or positive
        os.SEEK_CUR or 1 -- current stream position; offset may be
        negative
        os.SEEK_END or 2 -- end of stream; offset is usually negative

        Return the new absolute position.
        """
        raise NotImplementedError()

class Tuple[T](tuple[T]):
    def __str__(self) -> str:
        return "(\n\t" + "\n\t".join(str(v).replace("\n", "\n\t") for v in self) + "\n)"


class Type[T](type):
    @overload
    def __new__(
        cls: type[Type[T]], parser: Callable[..., T], /
    ) -> Type[T]: ...

    @overload
    def __new__(
        cls: type[Type[T]],
        parser: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        /,
        **kwargs: Any,
    ) -> Type[T]: ...

    def __new__(
        cls: type[Type[T]],
        parser: str | Callable[..., T],
        *args: Any,
        **kwargs: Any,
    ):
        if isinstance(parser, str):
            return type.__new__(cls, parser, *args, **kwargs)
        return type.__new__(cls, parser.__name__, (), {})

    @overload
    def __init__(self, parser: Callable[[File, Obj], T], /) -> None: ...

    @overload
    def __init__(self, parser: Callable[[File], T], /) -> None: ...

    @overload
    def __init__(self, parser: Callable[..., T], /) -> None: ...

    @overload
    def __init__(self, parser: str, /) -> None: ...

    @overload
    def __init__(
        self,
        parser: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        /,
        **kwargs: Any,
    ) -> None: ...

    def __init__(
        self,
        parser: str | Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> None:
        if isinstance(parser, str):
            if args or kwargs:
                type.__init__(self, parser, *args, **kwargs)
            else:
                type.__init__(self, parser, (), {})
            return
        """only functions with more than 1 positional parameter are assumed to require context"""
        if len(inspect.signature(parser).parameters) == 1:
            self.parse = lambda buff, obj, *args, **kwargs: parser(  # type: ignore
                buff, *args, **kwargs  # type: ignore
            )
        else:
            self.parse = parser  # pyright: ignore[reportAttributeAccessIssue]

    @overload
    def __get__(self, instance: None, owner: type[T] | None = None) -> Type[T]: ...

    @overload
    def __get__(self, instance: T, owner: type[T] | None = None) -> T: ...

    def __get__(self, instance: T | None, owner: type[T] | None = None) -> Type[T] | T:
        if instance is None:
            return self
        raise NotImplementedError("this is only a type hint and should not be called")

    def parse(
        self,
        buff: File,
        obj: Obj | None = None,
        **kwargs: Any,
    ) -> T:
        return self(buff, obj, **kwargs)

    def __getitem__(self, key: str | int) -> Type[Tuple[T]]:
        def parser(
            buff: File,
            obj: Obj | None = None,
            off: int | None = None,
            ret: int | None = None,
            **kwargs: Any,
        ) -> Tuple[T]:
            if off is not None:
                ret = ret if ret is not None else buff.tell()
                buff.seek(off)
            res = Tuple(
                self.parse(buff, obj, **kwargs)
                for _ in range(key if isinstance(key, int) else getattr(obj, key))
            )
            if off is not None:
                buff.seek(ret)  # pyright: ignore[reportArgumentType]
            return res

        return Type(parser)


class Obj(metaclass=Type['Obj']):
    __cache: dict[tuple[int, type[Self]], Self] = {}
    __cached: bool = False  # only instances are cached
    parser: Type[Self]

    def __init_subclass__(cls: type[Self]) -> None:
        cls.__blueprint = vars(cls).copy()
        for k in list(cls.__blueprint.keys()):
            if k.startswith("_"):
                cls.__blueprint.pop(k)
        cls.parser = Type(cls)
        return super().__init_subclass__()

    def __new__(
        cls,
        buff: File,
        *args: Any,
        **kwargs: Any,
    ) -> Self:
        key = (buff.tell(), cls)
        if key in cls.__cache:
            return cls.__cache[key]
        instance = super().__new__(cls)
        cls.__cache[key] = instance
        return instance

    def __init__(
        self,
        buff: File,
        context: Obj | None = None,
        off: int | None = None,
        ret: int | None = None,
    ) -> None:
        if self.__cached:
            return
        if off is not None:
            ret = ret if ret is not None else buff.tell()
            buff.seek(off)
        for k, v in self.__blueprint.items():
            setattr(self, k, v.parse(buff, self))
        if off is not None:
            buff.seek(ret)  # pyright: ignore[reportArgumentType]
        self.__cached = True

    def __str__(self) -> str:
        return (
            self.__class__.__name__
            + "[\n\t"
            + "\n\t".join(
                k + ": " + str(getattr(self, k, None)).replace("\n", "\n\t")
                for k in self.__blueprint.keys()
            )
            + "\n]"
        )
