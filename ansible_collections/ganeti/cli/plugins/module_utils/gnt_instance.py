"""
Class GntInstance
"""
from typing import Callable, List

from ansible_collections.ganeti.cli.plugins.module_utils.gnt_command import (
  GntCommand,
  build_gnt_instance_add_single_options,
  build_dict_options_with_prefix,
  build_prefixes_from_count_diff,
  build_gnt_instance_state_options,
  PrefixStr,
  PrefixIndex
)
from ansible_collections.ganeti.cli.plugins.module_utils.gnt_instance_list import (
  build_gnt_instance_list_arguments,
  parse_ganeti_list_output
)

GNT_INSTALL_CMD_DEFAULT = 'gnt-instance'

class GntInstance(GntCommand):
    """
    Class GntInstance
    """
    def __init__(self, run_function: Callable, error_function: Callable, binary: str=None) -> None:
        super().__init__(run_function, error_function, binary or GNT_INSTALL_CMD_DEFAULT)


    def reboot(self, name:str, timeout:bool=0):
        """
        Builder of options of reboot
        """
        return self._run_command(
            "--shutdown-timeout={}".format(timeout),
            name,
            command='reboot',

        )

    def stop(self, name:str, timeout:int=0, force:bool=False):
        """
        Builder of options of stop
        """
        return self._run_command(
            "--timeout={}".format(timeout),
            "--force" if force else "",
            name,
            command='stop'
        )

    def start(self, name:str, start:bool=False):
        """
        Builder of options of start
        """
        return self._run_command(
            "--no-start" if not start else "",
            name,
            command='start'
        )

    def remove(self, name:str):
        """
        Builder of options of remove
        """
        return self._run_command(
            "--dry-run",
            "--force",
            name,
            command='remove'
        )

    def list(self, *names:List[str], header_names: List[str] = None) -> List:
        """Run gnt-instance list. Get all information on instances.

        Args:
            names (list[str]): name of instances to view
            headers (List[str]): Column to view for instances.
                Defaults to None.

        Returns:
            str: The return of command
        """
        return self._run_command(
            *build_gnt_instance_list_arguments(*names, header_names=header_names),
            command='list',
            parser=parse_ganeti_list_output
        )

    def add(self, name:str, params: dict):
        """
        Run command: gnt-instance add
        """
        return self._run_command(
            *build_gnt_instance_state_options(params),
            *build_gnt_instance_add_single_options(params),
            build_dict_options_with_prefix(params.get('backend_param'), 'backend-parameters'),
            build_dict_options_with_prefix(
                params.get('hypervisor_param'),
                'hypervisor-parameters',
                prefixes=PrefixStr(params['hypervisor'])
            ),
            build_dict_options_with_prefix(params.get('os_params'), 'os-parameters'),
            build_dict_options_with_prefix(
                    params.get('nics'),
                    'net',
                    prefixes=PrefixIndex()
            ),
            build_dict_options_with_prefix(
                    params.get('disks'),
                    'disk',
                    prefixes=PrefixIndex()
            ),
            name,
            command='add'
        )

    def modify(self, name:str, params: dict, actual_disk_count:int, actual_nic_count:int):
        """
        Run command: gnt-instance modify
        """
        return self.run_function(
            *build_gnt_instance_add_single_options(params),
            *build_dict_options_with_prefix(params['backend_param'], 'backend-parameters'),
            *build_dict_options_with_prefix(
                params['hypervisor_param'],
                'hypervisor-parameters',
                prefixes=PrefixStr(params['hypervisor'])
            ),
            *build_dict_options_with_prefix(params['os_params'], 'os-parameters'),
            *build_dict_options_with_prefix(
                params['nics'],
                'net',
                prefixes=build_prefixes_from_count_diff(len(params['nics']), actual_nic_count)
            ),
            *build_dict_options_with_prefix(
                params['disks'],
                'disk',
                prefixes=build_prefixes_from_count_diff(len(params['disks']), actual_disk_count)
            ),
            name,
            command='modify'
        )
