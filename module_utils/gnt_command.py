from functools import partial
from typing import Callable, Any, List, Dict
from enum import Enum

def build_ganeti_cmd(*args:List[str], binary:str, cmd:str) -> str:
    return "{bin} {cmd} {args_merged}".format(
        bin=binary,
        cmd=cmd,
        args_merged=" ".join(args)
    )

build_gnt_instance = partial(build_ganeti_cmd, binary='gnt-instance')
build_gnt_instance_list = partial(build_gnt_instance, cmd='list')
build_gnt_instance_add = partial(build_gnt_instance, cmd='add')
build_gnt_instance_remove = partial(build_gnt_instance, cmd='remove')
build_gnt_instance_stop = partial(build_gnt_instance, cmd='stop')
build_gnt_instance_start = partial(build_gnt_instance, cmd='start')
build_gnt_instance_reboot = partial(build_gnt_instance, cmd='reboot')

def run_ganeti_cmd(*args, builder: Callable, parser: Callable, runner: Callable, error_function: Callable, **kwargs) -> Any:
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

def builder_dict_to_options(value: dict):
    return ",".join(
        [
            "{}={}".format(k, v) for k, v in value if value is not None
        ]
    )

class PrefixEnum(Enum):
    NONE = 0
    INDEX = 1
    ADD = 2
    STR = 3

def builder_gnt_instance_add_list_options(nics: List[Dict], option_name:str, prefix_enum=PrefixEnum.NONE, prefix:str=None) -> str:
    def get_prefix(index) -> str:
        return {
            PrefixEnum.NONE:None,
            PrefixEnum.INDEX: "{}:".format(index),
            PrefixEnum.ADD: "add:",
            PrefixEnum.STR: prefix
        }[prefix_enum]

    return " ".join(
        [
            "--{option_name} {prefix}{options}".format(
                option_name=option_name,
                prefix=get_prefix(index),
                options=builder_dict_to_options(value)
            )
            for index, value in enumerate(nics)
        ]
    )

def builder_gnt_instance_add(name, params, is_create=True):
    prefix_enum=PrefixEnum.ADD if is_create else PrefixEnum.INDEX
    return build_gnt_instance_add(
        *builder_gnt_instance_add_list_options(params['backend_param'], 'backend-parameters'),
        *builder_gnt_instance_add_list_options(params['hypervisor_param'], 'hypervisor-parameters', prefix_enum=PrefixEnum.STR, prefix=params['hypervisor']),
        *builder_gnt_instance_add_list_options(params['os_params'], 'os-parameters'),
        *builder_gnt_instance_add_list_options(params['nics'], 'net', prefix_enum=prefix_enum),
        *builder_gnt_instance_add_list_options(params['disks'], 'disk', prefix_enum=prefix_enum),
        name
    )

def builder_gnt_instance_reboot(name, timeout=0):
    return build_gnt_instance_reboot(
        "--shutdown-timeout={}".format(timeout),
        name
    )

def builder_gnt_instance_stop(name, timeout=0, force=False):
    return build_gnt_instance_stop(
        "--timeout={}".format(timeout),
        "--force" if force else "",
        name
    )

def builder_gnt_instance_start(name):
    return build_gnt_instance_start(
        name
    )

def builder_gnt_instance_remove(name):
    return build_gnt_instance_remove(
        "--dry-run",
        "--force",
        name
    )

# pylint: disable=unused-argument
def parse_ganeti_cmd_output(*_, stdout: str, **__):
    return None

run_gnt_instance_add = partial(
    run_ganeti_cmd,
    builder=builder_gnt_instance_add,
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
