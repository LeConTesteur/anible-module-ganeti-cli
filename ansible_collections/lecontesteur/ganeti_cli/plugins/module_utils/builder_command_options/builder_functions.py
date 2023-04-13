"""Builder function use by arg spec and options builders
"""
from itertools import chain, repeat, zip_longest
from typing import Any, Iterator, List, Union
from ansible_collections.lecontesteur.ganeti_cli.plugins.\
    module_utils.builder_command_options.prefixes import (
        Prefix,
        PrefixAdd,
        PrefixModify,
        PrefixNone,
        PrefixRemove,
        PrefixTypeEnum,
        format_prefix
)


def build_prefixes_from_count_diff(expected_count:int, actual_count: int) -> Iterator[str]:
    """Create list of Prefix depends of difference between expected and actual count

    Args:
        expected_count (int): The count expected in playbook
        actual_count (int): The acount actual in server

    Raises:
        Exception: If actual count is negative

    Returns:
        _type_: An iterator of Prefix

    Yields:
        Iterator: An iterator of Prefix
    """
    if expected_count < 0:
        return iter([])

    if actual_count < 0:
        raise ValueError('Error in remote count')
    count_diff = expected_count - actual_count

    ret = []

    if count_diff == 0: # same number
        ret = repeat(PrefixModify(), expected_count)

    elif count_diff < 0: #Much element, need remove surplus
        ret = chain(
                repeat(PrefixModify(), expected_count),
                repeat(PrefixRemove(), abs(count_diff))
            )
    elif count_diff > 0: #Missing element, need add missing
        ret = chain(
                repeat(PrefixModify(), actual_count),
                repeat(PrefixAdd(), abs(count_diff))
            )
    return ret

def build_options_with_prefixes(
        options: List[str], option_name:str, prefixes: Union[List[Prefix], Prefix]=None) -> str:
    """
    Builder of options for add list options (like --net, --disk)
    """
    last_prefix = None
    def remove_none(option_prefix):
        nonlocal last_prefix
        option = option_prefix[0] or ''
        prefix = option_prefix[1] or last_prefix or PrefixNone()
        last_prefix = prefix
        return (option, prefix)

    if not options:
        return ""

    if not option_name:
        raise ValueError('Missing option_name')

    if not prefixes:
        prefixes = []

    # pylint: disable=invalid-name
    it = map(remove_none, zip_longest(options, prefixes, fillvalue=None))

    return " ".join(
        [
            "--{option_name} {prefix}{options}".format(
                option_name=option_name,
                prefix=format_prefix(value[1], index),
                options=value[0] \
                        if value[1].type != PrefixTypeEnum.REMOVE else ''
            )
            for index, value in enumerate(it)
            if value[0]
        ]
    )

def build_sub_dict_options(key:str, value:str):
    """Build sub option for dict object

    Args:
        key (str): name of sub option
        value (Any): value of option

    Returns:
        str: the option
    """
    return "{}={}".format(key, value) if None not in (key, value) else ''


def build_state_option(name:str, value:Any) -> str:
    """Build option string for one value

    Args:
        name (str): name of option
        value (Any): value of option

    Returns:
        str: the option
    """
    return "--{}".format(name) if None not in (name, value) and value else ""

def build_no_state_option(name:str, value:Any) -> str:
    """Build option string for one value

    Args:
        name (str): name of option
        value (Any): value of option

    Returns:
        str: the option
    """
    return "--no-{}".format(name) if None not in (name, value) and not value else ""

def build_single_option(name:str, value:Any) -> str:
    """Build option string for one value

    Args:
        name (str): name of option
        value (Any): value of option

    Returns:
        str: the option
    """
    return "--{}={}".format(name, value) if None not in (name, value) else ""
