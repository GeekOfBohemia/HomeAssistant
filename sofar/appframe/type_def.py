from dataclasses import dataclass
from typing import Any, Callable, Union, Dict, Final


DictType = Union[dict, None]
StrType = Union[None, str]
CallableType = Union[Callable, None]
IntType = Union[None, int]
DictList = Dict[str, dict]
DictListDef = Final[DictList]
StateType = Union[None, str, int, float]
DictKeys = Dict[str, Any]


@dataclass
class BasicEntity:
    entity_id: str = ""
    ha_instance: Any = None

    def debug(self, msg) -> None:
        if self.ha_instance is not None:
            self.ha_instance.debug(msg)
