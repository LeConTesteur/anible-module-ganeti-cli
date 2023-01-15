"""
Contains all commands of gnt-instance except gnt-instance list
"""
from functools import partial
from itertools import zip_longest, chain, repeat
from collections import namedtuple
from typing import Callable, Any, List, Dict, Iterator
from enum import Enum

def build_ganeti_cmd(*args:List[str], binary:str, cmd:str) -> str:
    """
    Generic builder cmd
    """
    return "{bin} {cmd} {args_merged}".format(
        bin=binary,
        cmd=cmd,
        args_merged=" ".join(args)
    )

build_gnt_instance = partial(build_ganeti_cmd, binary='gnt-instance')
build_gnt_instance_list = partial(build_gnt_instance, cmd='list')
build_gnt_instance_add = partial(build_gnt_instance, cmd='add')
build_gnt_instance_modify = partial(build_gnt_instance, cmd='modify')
build_gnt_instance_remove = partial(build_gnt_instance, cmd='remove')
build_gnt_instance_stop = partial(build_gnt_instance, cmd='stop')
build_gnt_instance_start = partial(build_gnt_instance, cmd='start')
build_gnt_instance_reboot = partial(build_gnt_instance, cmd='reboot')

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
        raise Exception("{msg} with (code={code}, stdout={stdout}, stderr={stderr})".format(
            msg=msg,
            code=code,
            stdout=stdout,
            stderr=stderr
        ))
    return parser(*args, stdout=stdout, **kwargs)

def builder_dict_to_options(values: dict):
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

Prefix = namedtuple('Prefix', ['type', 'prefix'])

def build_prefix(prefix_type: PrefixTypeEnum, index: int, prefix: str = None) -> str:
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
        PrefixTypeEnum.MODIFY: "{}:modify:".format(index),
        PrefixTypeEnum.ADD: "add:",
        PrefixTypeEnum.REMOVE: "{}:remove".format(index),
        PrefixTypeEnum.STR: "{}:".format(prefix)
    }[prefix_type]


def builder_gnt_instance_add_list_options(
        options: List[Dict], option_name:str, prefixes: List[Prefix]=None) -> str:
    """
    Builder of options for add list options (like --net, --disk)
    """

    if not options:
        return ""

    if not option_name:
        raise Exception('Missing option_name')

    if not prefixes:
        prefixes = [Prefix(PrefixTypeEnum.NONE, '')]

    return " ".join(
        [
            "--{option_name} {prefix}{options}".format(
                option_name=option_name,
                prefix=build_prefix(value[1].type, index, value[1].prefix),
                options=builder_dict_to_options(value[0]) \
                        if value[1].type != PrefixTypeEnum.REMOVE else ''
            )
            for index, value in enumerate(zip_longest(options, prefixes, fillvalue=prefixes[-1]))
        ]
    )

def build_single_option(name:str, value:Any) -> str:
    """Build option string for one value

    Args:
        name (str): name of option
        value (Any): value of option

    Returns:
        str: the option
    """
    return "--{}={}".format(name, value) if value is not None else ""

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

def builder_gnt_instance_add(name, params):
    """
    Builder of options for add
    """
    return build_gnt_instance_add(
        *build_gnt_instance_add_single_options(params),
        *builder_gnt_instance_add_list_options(params['backend_param'], 'backend-parameters'),
        *builder_gnt_instance_add_list_options(
            params['hypervisor_param'],
            'hypervisor-parameters',
            prefixes=[Prefix(PrefixTypeEnum.STR, params['hypervisor'])]
        ),
        *builder_gnt_instance_add_list_options(params['os_params'], 'os-parameters'),
        *builder_gnt_instance_add_list_options(
                params['nics'],
                'net',
                prefixes=[Prefix(PrefixTypeEnum.ADD, '')
            ]
        ),
        *builder_gnt_instance_add_list_options(
                params['disks'],
                'disk',
                prefixes=[Prefix(PrefixTypeEnum.ADD, '')
            ]
        ),
        name
    )

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
        raise Exception('Error in remote count')
    count_diff = expected_count - actual_count

    ret = []

    if count_diff == 0: # same number
        ret = repeat(Prefix(PrefixTypeEnum.MODIFY, ''), expected_count)

    elif count_diff < 0: #Much element, need remove surplus
        ret = chain(
                repeat(Prefix(PrefixTypeEnum.MODIFY, ''), expected_count),
                repeat(Prefix(PrefixTypeEnum.REMOVE, ''), abs(count_diff))
            )
    elif count_diff > 0: #Missing element, need add missing
        ret = chain(
                repeat(Prefix(PrefixTypeEnum.MODIFY, ''), actual_count),
                repeat(Prefix(PrefixTypeEnum.ADD, ''), abs(count_diff))
            )
    return iter(ret)

def builder_gnt_instance_modify(name, params, actual_disk_count:int, actual_nic_count:int):
    """
    Build the options for modify command
    """

    return build_gnt_instance_modify(
        *build_gnt_instance_add_single_options(params),
        *builder_gnt_instance_add_list_options(params['backend_param'], 'backend-parameters'),
        *builder_gnt_instance_add_list_options(
            params['hypervisor_param'],
            'hypervisor-parameters',
            prefixes=[Prefix(PrefixTypeEnum.STR, params['hypervisor'])]
        ),
        *builder_gnt_instance_add_list_options(params['os_params'], 'os-parameters'),
        *builder_gnt_instance_add_list_options(
            params['nics'],
            'net',
            prefixes=build_prefixes_from_count_diff(len(params['nics']), actual_nic_count)
        ),
        *builder_gnt_instance_add_list_options(
            params['disks'],
            'disk',
            prefixes=build_prefixes_from_count_diff(len(params['disks']), actual_disk_count)
        ),
        name
    )

def builder_gnt_instance_reboot(name, timeout=0):
    """
    Builder of options of reboot
    """
    return build_gnt_instance_reboot(
        "--shutdown-timeout={}".format(timeout),
        name
    )

def builder_gnt_instance_stop(name, timeout=0, force=False):
    """
    Builder of options of stop
    """
    return build_gnt_instance_stop(
        "--timeout={}".format(timeout),
        "--force" if force else "",
        name
    )

def builder_gnt_instance_start(name, start=False):
    """
    Builder of options of start
    """
    return build_gnt_instance_start(
        "--no-start" if not start else "",
        name
    )

def builder_gnt_instance_remove(name):
    """
    Builder of options of remove
    """
    return build_gnt_instance_remove(
        "--dry-run",
        "--force",
        name
    )

# pylint: disable=unused-argument
def parse_ganeti_cmd_output(*_, stdout: str, **__):
    """
    Default parser for ganeti cmd output
    """
    return None

run_gnt_instance_add = partial(
    run_ganeti_cmd,
    builder=builder_gnt_instance_add,
    parser=parse_ganeti_cmd_output
)

run_gnt_instance_modify = partial(
    run_ganeti_cmd,
    builder=builder_gnt_instance_modify,
    parser=parse_ganeti_cmd_output
)


run_gnt_instance_reboot = partial(
    run_ganeti_cmd,
    builder=builder_gnt_instance_reboot,
    parser=parse_ganeti_cmd_output
)

run_gnt_instance_stop = partial(
    run_ganeti_cmd,
    builder=builder_gnt_instance_stop,
    parser=parse_ganeti_cmd_output
)

run_gnt_instance_start = partial(
    run_ganeti_cmd,
    builder=builder_gnt_instance_start,
    parser=parse_ganeti_cmd_output
)

run_gnt_instance_remove = partial(
    run_ganeti_cmd,
    builder=builder_gnt_instance_remove,
    parser=parse_ganeti_cmd_output
)
