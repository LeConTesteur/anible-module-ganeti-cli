"""
Contains all commands of gnt-instance except gnt-instance list
"""
from typing import Callable, Any, List, Union
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
        print(cmd)
        code, stdout, stderr = self.run_function(cmd, check_rc=False)
        if code != 0:
            if return_none_if_error:
                return None
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
