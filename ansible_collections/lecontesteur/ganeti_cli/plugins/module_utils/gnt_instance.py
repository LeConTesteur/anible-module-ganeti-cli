"""
Class GntInstance
"""
from typing import Callable, Dict, List, Tuple
import re


from ansible_collections.lecontesteur.ganeti_cli.plugins.module_utils.gnt_command import (
  GntCommand,
)
from ansible_collections.lecontesteur.ganeti_cli.plugins.module_utils.gnt_instance_list import (
  build_gnt_instance_list_arguments,
  parse_ganeti_list_output
)

from ansible_collections.lecontesteur.ganeti_cli.plugins.module_utils.parse_info_response import (
  parse_from_stdout
)

from ansible_collections.lecontesteur.ganeti_cli.plugins.\
    module_utils.builder_command_options.builders import (
        BuilderCommand,
        BuilderCommandOptionsRootSpec,
        BuilderCommandOptionsSpecDict,
        BuilderCommandOptionsSpecElement,
        BuilderCommandOptionsSpecElementOnlyCreate,
        BuilderCommandOptionsSpecList,
        BuilderCommandOptionsSpecListSubElement,
        BuilderCommandOptionsSpecNoStateElement,
        BuilderCommandOptionsSpecStateElement,
        BuilderCommandOptionsSpecSubElement,
        CommandType
)


GNT_INSTALL_CMD_DEFAULT = 'gnt-instance'

def parse_state(state:str) -> Tuple[bool, bool]:
    """Parse the string for extract state and admin_state

    Args:
        state (str): The string return by ganeti

    Returns:
        Tuple[bool, bool]: state and admin_state
    """
    match = re.match(
        r'configured to be (?P<admin_state>\w+), actual state is (?P<state>\w+)',
        state
    )
    return match.group('admin_state'),  match.group('state')

def parse_info_instances(*_, stdout: str, **__) -> List[Dict]:
    """Parse info return of ganeti commands

    Args:
        stdout (str): the information

    Returns:
        List[Dict]: Lsit of information parsed
    """
    info_instances = parse_from_stdout(stdout=stdout)
    l_info = []
    for info_instance in info_instances:
        admin_state, state = parse_state(info_instance['State'])
        info_instance['name'] = info_instance['Instance name'].strip()
        info_instance['state'] = state
        info_instance['admin_state'] = admin_state
        l_info.append(info_instance)
    return l_info

disk_templates = ['sharedfile', 'diskless', 'plain', 'gluster', 'blockdev',
                  'drbd', 'ext', 'file', 'rbd']
file_driver_choices = ["loop", "blktap", "blktap2" ]
hypervisor_choices = ['chroot', 'xen-pvm', 'kvm', 'xen-hvm', 'lxc', 'fake']
nic_types_choices = ['bridged', 'openvswitch']
hypervisor_params_list = [
    "boot_order",
    "blockdev_prefix",
    "floppy_image_path",
    "cdrom_image_path",
    "cdrom2_image_path",
    "nic_type",
    "vif_type",
    "disk_type",
    "cdrom_disk_type",
    "vnc_bind_address",
    "vnc_password_file",
    "vnc_tls",
    "vnc_x509_path",
    "vnc_x509_verify",
    "spice_bind",
    "spice_ip_version",
    "spice_password_file",
    "spice_image_compression",
    "spice_jpeg_wan_compression",
    "spice_zlib_glz_wan_compression",
    "spice_streaming_video",
    "spice_playback_compression",
    "spice_use_tls",
    "spice_tls_ciphers",
    "spice_use_vdagent",
    "cpu_type",
    "acpi",
    "pae",
    "viridian",
    "use_localtime",
    "kernel_path",
    "kernel_args",
    "initrd_path",
    "root_path",
    "serial_console",
    "serial_speed",
    "disk_cache",
    "disk_aio",
    "security_model",
    "security_domain",
    "kvm_flag",
    "mem_path",
    "use_chroot",
    "user_shutdown",
    "migration_downtime",
    "cpu_mask",
    "cpu_cap",
    "cpu_weight",
    "usb_mouse",
    "keymap",
    "reboot_behavior",
    "cpu_cores",
    "cpu_threads",
    "cpu_sockets",
    "soundhw",
    "cpuid",
    "usb_devices",
    "vga",
    "kvm_extra",
    "machine_version",
    "migration_caps",
    "kvm_path",
    "vnet_hdr",
    "virtio_net_queues",
    "startup_timeout",
    "extra_cgroups",
    "drop_capabilities",
    "devices",
    "extra_config",
    "num_ttys",
]

disks_options = [
    BuilderCommandOptionsSpecListSubElement(name='name', type="str", require=True),
    BuilderCommandOptionsSpecListSubElement(
        name='size', type="int", require=True, only=CommandType.CREATE),
    BuilderCommandOptionsSpecListSubElement(name='spindles', type="str", require=True),
    BuilderCommandOptionsSpecListSubElement(name='metavg', type="str", require=True),
    BuilderCommandOptionsSpecListSubElement(name='access', type="str", require=True),
    BuilderCommandOptionsSpecListSubElement(name='access', type="str", require=True),
]

nics_options = [
    BuilderCommandOptionsSpecListSubElement(name='name', type="str", require=True),
    BuilderCommandOptionsSpecListSubElement(name='link', type="str", require=True),
    BuilderCommandOptionsSpecListSubElement(name='vlan', type="str", require=False),
    BuilderCommandOptionsSpecListSubElement(name='network', type="str", require=False),
    BuilderCommandOptionsSpecListSubElement(
        name='mode', type="str", default='bridged',require=True),
]

hypervisor_params = [
    BuilderCommandOptionsSpecSubElement(name=param, type='str')
    for param in hypervisor_params_list
]

backend_param = [
    BuilderCommandOptionsSpecSubElement(name='maxmem', type='int'),
    BuilderCommandOptionsSpecSubElement(name='minmem', type='int'),
    BuilderCommandOptionsSpecSubElement(name='memory', type='int'),
    BuilderCommandOptionsSpecSubElement(name='vcpus', type='int'),
    BuilderCommandOptionsSpecSubElement(name='always_failover', type='bool'),
]

builder_gnt_instance_spec = BuilderCommandOptionsRootSpec(
    BuilderCommandOptionsSpecElement(
        name='disk-template', type='str', choices=disk_templates,
        info_key='Disk template'
    ),
    BuilderCommandOptionsSpecElement(
        name='file-driver', type='str',
        info_key='File driver'
    ),
    BuilderCommandOptionsSpecElement(
        name='file-storage-dir', type='str',
        info_key='File driver'
    ),
    BuilderCommandOptionsSpecList(
        *disks_options,
        name='disk',
        info_key='Disks'
    ),
    BuilderCommandOptionsSpecElement(
        name='hypervisor', type='str', choices=hypervisor_choices,
        info_key='Hypervisor'
    ),
    BuilderCommandOptionsSpecElementOnlyCreate(name='iallocator', type='str'),
    BuilderCommandOptionsSpecList(
        *nics_options,
        name='net',
        info_key='NICs',
        no_option='--no-nics'
    ),
    BuilderCommandOptionsSpecElement(
        name='os-type', type='str', info_key='Operating system'),
    BuilderCommandOptionsSpecDict(
        *hypervisor_params,
        name='hypervisor-parameters',
        info_key='Hypervisor parameters'
    ),
    BuilderCommandOptionsSpecDict(
        *backend_param,
        name='backend-parameters',
        info_key='Back-end parameters'
    ),
    BuilderCommandOptionsSpecStateElement(name='submit'),
    BuilderCommandOptionsSpecStateElement(name='ignore-ipolicy'),
    BuilderCommandOptionsSpecStateElement(name='offline', only=CommandType.MODIFY),
    BuilderCommandOptionsSpecStateElement(name='online', only=CommandType.MODIFY),
    BuilderCommandOptionsSpecStateElement(name='hotplug', only=CommandType.MODIFY),
    BuilderCommandOptionsSpecStateElement(name='hotplug-if-possible', only=CommandType.MODIFY),
    BuilderCommandOptionsSpecStateElement(name='force', only=CommandType.MODIFY),
    BuilderCommandOptionsSpecNoStateElement(name='name-check', only=CommandType.CREATE),
    BuilderCommandOptionsSpecNoStateElement(name='ip-check', only=CommandType.CREATE),
    BuilderCommandOptionsSpecNoStateElement(name='conflicts-check', only=CommandType.CREATE),
    BuilderCommandOptionsSpecNoStateElement(name='install', only=CommandType.CREATE),
    BuilderCommandOptionsSpecNoStateElement(name='start', default=False, only=CommandType.CREATE),
    BuilderCommandOptionsSpecNoStateElement(name='wait-for-sync'),
)

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
            parser=parse_ganeti_list_output,
            return_none_if_error=True
        )

    def add(self, name:str, params: dict):
        """
        Run command: gnt-instance add
        """
        return self._run_command(
            BuilderCommand(builder_gnt_instance_spec).generate(
                module_params=params, info_data={}, to_command=CommandType.CREATE
            ),
            name,
            command='add'
        )

    def modify(self, name:str, params: dict, vm_info: dict):
        """
        Run command: gnt-instance modify
        """
        return self._run_command(
            BuilderCommand(builder_gnt_instance_spec).generate(
                module_params=params, info_data=vm_info, to_command=CommandType.MODIFY
            ),
            name,
            command='modify'
        )

    def config_and_remote_have_difference(self, params: dict, vm_info) -> bool:
        """Compute different between config and remote information

        Args:
            params (dict): Param of ansible module
            vm_info (_type_): Remote vm information

        Returns:
            bool: Have difference
        """
        options = BuilderCommand(builder_gnt_instance_spec).generate(
            module_params=params, info_data=vm_info, to_command=CommandType.MODIFY
        )
        return bool(options.strip())


    def info(self, name:str) -> List[Dict]:
        """Return Information of instances

        Args:
            name (str): name of instance

        Returns:
            List[Dict]: Instances information
        """
        return self._run_command(
            name,
            command='info',
            parser=parse_info_instances,
            return_none_if_error=True
        )
