from functools import partial
from typing import Callable, Any, List


def build_ganeti_cmd(*args:List[str], binary:str, cmd:str) -> str:
    return "{bin} {cmd} {args_merged}".format(
        bin=binary,
        cmd=cmd,
        args_merged=" ".join(args)
    )

build_gnt_instance = partial(build_ganeti_cmd, binary='gnt-instance')
build_gnt_instance_list = partial(build_gnt_instance, cmd='list')


def run_ganeti_cmd(*args, builder: Callable, parser: Callable, runner: Callable, **kwargs) -> Any:
    run_ganeti_cmd.__doc__ = builder.__doc__
    code, stdout, stderr = runner(builder(*args, **kwargs), check_rc=True)
    return parser(*args, **kwargs, code=code, stdout=stdout, stderr=stderr)
