"""Prefixes for arguments list.
"""
from enum import Enum


class PrefixTypeEnum(Enum):
    """
    Enum if set index, add, str or nothing in cli options (like --net)
    """
    NONE = 0
    MODIFY = 1
    ADD = 2
    REMOVE = 3
    STR = 4
    INDEX = 5


class Prefix:
    """
    Prefix class
    """
    _type = None

    def __init__(self, prefix: str = None) -> None:
        self._prefix = prefix
        if self._type == PrefixTypeEnum.STR and not self.prefix:
            raise ValueError('Prefix can\'t be None when Type is STR')

    @property
    def type(self) -> PrefixTypeEnum:
        """
        Type of prefix
        """
        return self._type

    @property
    def prefix(self) -> str:
        "Prefix value"
        return self._prefix

    def __eq__(self, __o: object) -> bool:
        return self.type == __o.type and self.prefix == __o.prefix

    def __iter__(self):
        return iter([self])

    def __getitem__(self, _):
        return self


class PrefixNone(Prefix):
    """
    Prefix None
    """
    _type = PrefixTypeEnum.NONE


class PrefixModify(Prefix):
    """
    Prefix Modify
    """
    _type = PrefixTypeEnum.MODIFY


class PrefixAdd(Prefix):
    """
    Prefix Add
    """
    _type = PrefixTypeEnum.ADD


class PrefixRemove(Prefix):
    """
    Prefix Remove
    """
    _type = PrefixTypeEnum.REMOVE


class PrefixStr(Prefix):
    """
    Prefix Str
    """
    _type = PrefixTypeEnum.STR


class PrefixIndex(Prefix):
    """
    Prefix Index
    """
    _type = PrefixTypeEnum.INDEX


def format_prefix(prefix: Prefix, index: int) -> str:
    """Build prefix string

    Args:
        prefix_type (PrefixTypeEnum): Type of prefix
        index (int): index in list
        prefix (str): prefix in type is string

    Returns:
        str: _description_
    """
    return {
        PrefixTypeEnum.NONE: "",
        PrefixTypeEnum.INDEX: "{}:".format(index),
        PrefixTypeEnum.MODIFY: "{}:modify,".format(index),
        PrefixTypeEnum.ADD: "{}:add,".format(index),
        PrefixTypeEnum.REMOVE: "{}:remove".format(index),
        PrefixTypeEnum.STR: "{}:".format(prefix.prefix)
    }[prefix.type]
