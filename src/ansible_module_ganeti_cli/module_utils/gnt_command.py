"""
Contains all commands of gnt-instance except gnt-instance list
"""
from itertools import zip_longest, chain, repeat
from typing import Callable, Any, List, Dict, Iterator, Union
from enum import Enum
from abc import ABC

def build_ganeti_cmd(*args:List[str], binary:str, cmd:str) -> str:
    """
    Generic builder cmd
    """
    return "{bin} {cmd} {args_merged}".format(
        bin=binary,
        cmd=cmd,
        args_merged=" ".join(args)
    )

class RunCommandException(Exception):
    """Exception after run_command"""

def run_ganeti_cmd(
        *args,
        builder: Callable,
        parser: Callable,
        runner: Callable,
        error_function: Callable,
        **kwargs
    ) -> Any:
    """
    Generic runner function for ganeti command
    """
    cmd = builder(*args, **kwargs)
    #print(cmd)
    code, stdout, stderr = runner(cmd, check_rc=True)
    if code != 0:
        msg='Command "{}" failed'.format(cmd)
        if error_function:
            return error_function(code, stdout, stderr, msg=msg)
        raise RunCommandException(
            "{msg} with (code={code}, stdout={stdout}, stderr={stderr})".format(
                msg=msg,
                code=code,
                stdout=stdout,
                stderr=stderr
            )
        )
    return parser(*args, stdout=stdout, **kwargs)

def build_dict_to_options(values: dict):
    """
    Transform dictionary to cli options
    """
    return ",".join(
        [
            "{}={}".format(k, v) for k, v in values.items() if v is not None
        ]
    )

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
    def __init__(self, prefix:str=None) -> None:
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

    def __getitem__(self,_):
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
        PrefixTypeEnum.MODIFY: "{}:modify:".format(index),
        PrefixTypeEnum.ADD: "add:",
        PrefixTypeEnum.REMOVE: "{}:remove".format(index),
        PrefixTypeEnum.STR: "{}:".format(prefix.prefix)
    }[prefix.type]

def build_dict_options_with_prefix(
        options: List[Dict], option_name:str, prefixes: Union[List[Prefix], Prefix]=None) -> str:
    """
    Builder of options for add list options (like --net, --disk)
    """

    if not options:
        return ""

    if not option_name:
        raise ValueError('Missing option_name')

    if not prefixes:
        prefixes = [PrefixNone()]

    return " ".join(
        [
            "--{option_name} {prefix}{options}".format(
                option_name=option_name,
                prefix=format_prefix(value[1], index),
                options=build_dict_to_options(value[0]) \
                        if value[1].type != PrefixTypeEnum.REMOVE else ''
            )
            for index, value in enumerate(zip_longest(options, prefixes, fillvalue=prefixes[-1]))
        ]
    )

def build_state_option(name:str, value:Any) -> str:
    """Build option string for one value

    Args:
        name (str): name of option
        value (Any): value of option

    Returns:
        str: the option
    """
    return "--no-{}".format(name) if value is not None and not value else ""

def build_single_option(name:str, value:Any) -> str:
    """Build option string for one value

    Args:
        name (str): name of option
        value (Any): value of option

    Returns:
        str: the option
    """
    return "--{}={}".format(name, value) if value is not None else ""

def build_gnt_instance_state_options(params: dict) -> List[str]:
    """Build all options which are state (--no-*)

    Args:
        params (dict): Dict of data

    Returns:
        List[str]: List of option
    """
    return [
        build_state_option("name-check", params['name_check']),
        build_state_option("ip-check", params['ip_check']),
    ]

def build_gnt_instance_add_single_options(params: dict) -> List[str]:
    """Build all options which are not list

    Args:
        params (dict): Dict of data

    Returns:
        List[str]: List of option
    """
    return [
        build_single_option("disk-template", params['disk_template']),
        build_single_option("os-type", params['os_type']),
        build_single_option("pnode", params['pnode']),
        build_single_option("iallocator", params['iallocator']),
    ]

def build_prefixes_from_count_diff(expected_count:int, actual_count: int) -> Iterator:
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
    if expected_count <= 0:
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
    return iter(ret)

# pylint: disable=unused-argument
def parse_ganeti_cmd_output(*_, stdout: str, **__):
    """
    Default parser for ganeti cmd output
    """
    return None

# pylint: disable=too-few-public-methods
class GntCommand(ABC):
    """
    Generic class for ganeti commands
    """
    def __init__(self, run_function: Callable, error_function: Callable, binary: str=None) -> None:
        self.run_function = run_function
        self.error_function = error_function
        self.binary = binary

    def _run_command(self,
                     *args, command: str, parser: Callable = None, return_none_if_error=False,
                     **kwargs) -> Union[None, Any]:
        """
        Generic runner function for ganeti command
        """
        if parser is None:
            parser = parse_ganeti_cmd_output

        cmd = build_ganeti_cmd(*args, cmd=command, binary=self.binary)
        #print(cmd)
        code, stdout, stderr = self.run_function(cmd, check_rc=True)
        if code != 0:
            msg='Command "{}" failed'.format(cmd)
            if self.error_function:
                return self.error_function(code, stdout, stderr, msg=msg)
            raise RunCommandException(
                "{msg} with (code={code}, stdout={stdout}, stderr={stderr})".format(
                    msg=msg,
                    code=code,
                    stdout=stdout,
                    stderr=stderr
                )
            )
        return parser(*args, stdout=stdout, **kwargs)
