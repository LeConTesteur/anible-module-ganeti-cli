"""Function for extract data in dictionnary
"""
import re
from functools import reduce
from typing import List, Any, Callable, Dict
import yaml

DefaultValidator = Callable[[str], bool]


def dict_get(data: dict, key: str) -> Any:
    """Get element in dict

    Args:
        data (dict): dictionnary
        key (str): the key

    Returns:
        Any: The value
    """
    if data is None:
        return None
    return dict.get(data, key)


def recursive_get(data: dict, keys: List[str]) -> Any:
    """Get element in dict

    Args:
        data (dict): _description_
        keys (List[str]): _description_

    Returns:
        Any: _description_
    """
    keys = list(keys)
    if len(keys) == 0:
        return None
    return reduce(dict_get, keys, data)


def info_default_validator(value: str) -> bool:
    """Validator for check if is a default value

    Args:
        value (str): Value to check

    Returns:
        bool: Is a default value
    """
    if not value:
        return False
    return bool(re.match(r'default\s+[(][^)]*[)]', value))


def nic_default_validator(value: str) -> bool:
    """Validator for check if is a default value if nic dictionnary

    Args:
        value (str): Value to check

    Returns:
        bool: Is a default value
    """
    if value is None:
        return False
    if not value.strip():
        return True
    return bool(re.match(r'\s*None\s*', value))


def value_info_extractor(data: dict, keys: List[str], default_validator: DefaultValidator = None) -> Any:
    """Extract value from vm information

    Args:
        data (dict): Data
        keys (List[str]): Key of value to extract
        default_validator (DefaultValidator, optional): Default validator. Defaults to None.

    Returns:
        Any: Value. None if is a default value
    """
    value = recursive_get(data, keys)
    if not isinstance(value, str):
        return value
    if default_validator and default_validator(value):
        return None
    return yaml.safe_load(value)


def size_param_info_extractor(data: dict, keys: List[str]) -> Any:
    """Extract size value

    Args:
        data (dict): Data
        keys (List[str]): Key of value to extract

    Returns:
        Any: The size. None if not match
    """
    value = recursive_get(data, keys)
    if not value or not isinstance(value, str):
        return None
    match = re.search(r'(?P<value>[.0-9]+)(?P<unit>[a-zA-Z])', value)
    if not match:
        return None
    return '{}{}'.format(float(match.group('value')), match.group('unit'))


ValueParamExtractor = Callable[[Dict, List[str]], Any]
ValueInfoExtractor = Callable[[Dict, List[str]], Any]
