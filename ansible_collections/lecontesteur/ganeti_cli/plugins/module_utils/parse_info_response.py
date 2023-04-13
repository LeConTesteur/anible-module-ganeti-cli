"""
  Parse generic info response
"""
import re
from typing import Dict
from enum import Enum
import yaml


DELIMITER = '.'


def remove_after_dash(key: str, delimiter=DELIMITER) -> str:
    """_summary_

    Args:
        key (str): _description_
        delimiter (_type_, optional): _description_. Defaults to DELIMITER.

    Returns:
        str: _description_
    """
    return re.sub(r'\s+[-](\s|\w)+[^{delimiter}]'.format(delimiter=delimiter), '', key).strip()


def remove_parenthesis(key: str) -> str:
    """_summary_

    Args:
        key (str): _description_
        delimiter (_type_, optional): _description_. Defaults to DELIMITER.

    Returns:
        str: _description_
    """
    return re.sub(r'\s+[(](\s|\w)+[)]', '', key).strip()


def remove_list_index(key: str) -> str:
    """_summary_

    Args:
        key (str): _description_
        delimiter (_type_, optional): _description_. Defaults to DELIMITER.

    Returns:
        str: _description_
    """
    return re.sub(r'[/]\w+', '', key).strip()


def remove_duplicate_underscore(key: str) -> str:
    """_summary_

    Args:
        key (str): _description_
        delimiter (_type_, optional): _description_. Defaults to DELIMITER.

    Returns:
        str: _description_
    """
    return re.sub(r'[_]+', '_', key).strip()


def replace_space_and_lower_all(key: str) -> str:
    """_summary_

    Args:
        key (str): _description_
        delimiter (_type_, optional): _description_. Defaults to DELIMITER.

    Returns:
        str: _description_
    """
    return key.replace(' ', '_').lower()


def transform_key(key: str) -> str:
    """_summary_

    Args:
        key (str): _description_

    Returns:
        str: _description_
    """

    for f_format in [
            remove_after_dash,
            remove_parenthesis,
            remove_list_index,
            replace_space_and_lower_all,
            remove_duplicate_underscore]:
        key = f_format(key)
    return key


def transform_none_to_none(info: str):
    """_summary_

    Args:
        info (str): _description_

    Returns:
        _type_: _description_
    """
    return re.sub(r'None', 'null', info)


def default_to_none(info: str):
    """_summary_

    Args:
        info (str): _description_

    Returns:
        _type_: _description_
    """
    return re.sub(r'default [(]([^)])+[)]', 'null', transform_none_to_none(info))


def true_value(info: str):
    """_summary_

    Args:
        info (str): _description_

    Returns:
        _type_: _description_
    """
    return re.sub(r'default [(]([^)]+)[)]', r'\1', transform_none_to_none(info))


class ParseType(Enum):
    """_summary_

    Args:
        Enum (_type_): _description_
    """
    RAW = 0
    DEFAULT_TO_NONE = 1
    TRUE_VALUE = 2

# def parse(info: str, parse_type:ParseType = ParseType.RAW) -> FlatterDict:
#    """Parse info output.
#    - Using yaml parser.
#    - Flat parsed data
#    - Transform key for directly use it
#
#    Args:
#        info (str): Data to parse
#
#    Returns:
#        FlatterDict: Dict of data
#    """
#    if parse_type == ParseType.DEFAULT_TO_NONE:
#        info = default_to_none(info)
#    if parse_type == ParseType.TRUE_VALUE:
#        info = true_value(info)
#    info_parsed = yaml.safe_load(info)
#    print(info_parsed)
#    info_flatted = FlatDict(info_parsed, delimiter=DELIMITER)
#    for k in info_flatted.keys():
#        info_flatted[transform_key(k)] = info_flatted.pop(k)
#    return info_flatted


def parse(info: str) -> Dict:
    """Parse info output.
    - Using yaml parser.
    - Flat parsed data
    - Transform key for directly use it

    Args:
        info (str): Data to parse

    Returns:
        Dict: Dict of data
    """
    return yaml.safe_load(info)


def parse_from_stdout(*_, stdout: str, **__) -> Dict:
    """_summary_

    Args:
        stdout (str): _description_

    Returns:
        FlatterDict: _description_
    """
    return parse(stdout)
