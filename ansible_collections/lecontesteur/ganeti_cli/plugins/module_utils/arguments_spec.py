"""
Module contains the arguments spec of gnt-instance module
"""
from collections import UserDict
from ansible_collections.lecontesteur.ganeti_cli.plugins.\
    module_utils.builder_command_options.builders import DEFAULT_VALUE


MAX_NICS = 8
MAX_DISKS = 8


def copy_options_nth(options, parent_gnt_list_prefix, number=8):
    """
    Copy nth the spec for list options
    """
    return [
        {
            o_k: {
                **o_v,
                'gnt_list_field': "{prefix}.{name}/{index}".format(
                    prefix=parent_gnt_list_prefix,
                    name=o_v.get('gnt_list_field_name', o_k),
                    index=index
                )
            }
            for o_k, o_v in options.items()
            if not o_v.get('gnt_list_ignore', False)
        }
        for index in range(number)
    ]


class ArgumentSpec(UserDict):
    """Class ArgumentSpec like Dict for generate easily gnt_instance list or
       gnt command's options

    Args:
        UserDict ([str, Any]): ArgSpec dictionnary
    """

    def __init__(self, name=None, gnt_list_ignore=False, gnt_list_field=None, **kwargs):
        super().__init__(**kwargs)
        self._gnt_list_field = gnt_list_field
        self._parent = None
        self._name = name
        self.gnt_list_ignore = gnt_list_ignore
        for key, value in self.data.items():
            if hasattr(value, 'parent'):
                value.parent = self
            if hasattr(value, 'name') and not value.name:
                value.name = key

    @property
    def gnt_list_field(self) -> str:
        """Get the name of gnt-instance list field

        Returns:
            str: the name
        """
        return self._gnt_list_field or self.name

    def format(self, _: int = None):
        """Get the complexe name of gnt-instance list field

        Returns:
            str: the name
        """
        return self.gnt_list_field

    @property
    def name(self) -> str:
        """The name of argspec

        Returns:
            str: The name
        """
        return self._name

    @name.setter
    def name(self, value: str):
        """Set the name of argspec

        Args:
            value (str): The name
        """
        self._name = value

    @property
    def parent(self):
        """Get tthe parent of instance

        Returns:
            Self: the parent
        """
        return self._parent

    @parent.setter
    def parent(self, value):
        """Set the parent

        Args:
            value (Self): The parent
        """
        self._parent = value


class ArgumentSubSpec(ArgumentSpec):
    """Argspec for suboptions

    Args:
        ArgumentSpec (_type_):
    """

    def format(self, _: int = None):
        return "{parent}/{name}".format(
            parent=self.parent.gnt_list_field,
            name=self.gnt_list_field
        )


class ArgumentListSpec(ArgumentSpec):
    """Argument List int arg spec

    Args:
        ArgumentSpec (_type_):
    """

    def __init__(self, gnt_list_count=0, **kwargs):
        super().__init__(**kwargs)
        self.count = gnt_list_count


class ArgumentListElementSpec(ArgumentSpec):
    """Element of arguement List

    Args:
        ArgumentSpec (_type_):
    """

    def format(self, index: int = None):
        if not index >= 0:
            raise ValueError('Index must be positive')
        return "{parent}.{name}/{index}".format(
            parent=self.parent.gnt_list_field,
            name=self.gnt_list_field,
            index=index
        )


disk_templates = ['sharedfile', 'diskless', 'plain', 'gluster', 'blockdev',
                  'drbd', 'ext', 'file', 'rbd']
hypervisor_choices = ['chroot', 'xen-pvm', 'kvm', 'xen-hvm', 'lxc', 'fake']
nic_types_choices = ['bridged', 'openvswitch']
nics_options = ArgumentListSpec(
    name=ArgumentListElementSpec(type="str", require=True,),
    mode=ArgumentListElementSpec(
        type="str",
        require=False,
        default=nic_types_choices[0],
        choices=nic_types_choices
    ),
    vlan=ArgumentListElementSpec(type="int", require=False),
    network=ArgumentListElementSpec(type="str", require=False),
    mac=ArgumentListElementSpec(type="str", require=False),
    link=ArgumentListElementSpec(type="str", require=False),
    ip=ArgumentListElementSpec(type="str", require=False),
    gnt_list_field='nic',
    gnt_list_count=MAX_NICS
)
disks_options = ArgumentListSpec(
    name=ArgumentListElementSpec(type="str", require=True),
    size=ArgumentListElementSpec(type="int", require=True),
    spindles=ArgumentListElementSpec(type="str", require=False),
    vg=ArgumentListElementSpec(
        type="str", require=False, gnt_list_ignore=True),
    metavg=ArgumentListElementSpec(
        type="str", require=False, gnt_list_ignore=True),
    access=ArgumentListElementSpec(
        type="str", require=False, gnt_list_ignore=True),
    gnt_list_field='disk',
    gnt_list_count=MAX_DISKS
)
backend_param = ArgumentSpec(
    memory=ArgumentSubSpec(type='int', required=False),
    vcpus=ArgumentSubSpec(type='int', required=False),
    gnt_list_field='be'
)

hypervisor_params = ArgumentSpec(
    kernel_args=ArgumentSubSpec(type='str', required=False),
    kernel_path=ArgumentSubSpec(type='str', required=False),
    gnt_list_field='hv'
)


osparams = []

ganeti_instance_args_spec = {
    "disk_template": ArgumentSpec(
        type='str', default=DEFAULT_VALUE, choices=disk_templates),
    "disks": ArgumentSpec(type='list', required=False, options=disks_options),
    "hypervisor": ArgumentSpec(type='str', default='kvm',
                               choices=hypervisor_choices),
    "iallocator": ArgumentSpec(type='str', required=False,
                               default=None, gnt_list_ignore=True),
    "nics": ArgumentSpec(type='list', required=False, options=nics_options),
    "os_type": ArgumentSpec(type='str', required=True, gnt_list_field='os'),
    "pnode": ArgumentSpec(type='str', required=False, default=None),
    "hypervisor_params": ArgumentSpec(
        type='dict', required=False, options=hypervisor_params),
    "backend_param": ArgumentSpec(
        type='dict', required=False, options=backend_param),
    "name_check": ArgumentSpec(type='bool', default=False, gnt_list_ignore=True),
    "ip_check": ArgumentSpec(type='bool', default=False, gnt_list_ignore=True),
}
