from typing import List, Type, TypeVar, Union

T = TypeVar("T")


class RawConnection:
    @staticmethod
    def __make_request(
            sql: str,
            params: Union[tuple, List[tuple]] = None,
            fetch: bool = False,
            mult: bool = False
    ):
        raise NotImplementedError

    @staticmethod
    def _make_request(
            sql: str,
            params: Union[tuple, List[tuple]] = None,
            fetch: bool = False,
            mult: bool = False,
            model_type: Type[T] = None
    ):
        raise NotImplementedError
