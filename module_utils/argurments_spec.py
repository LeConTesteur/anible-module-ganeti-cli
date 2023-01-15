import flatdict

def copy_options_nth(options, parent_gnt_list_prefix, number=8):
    return [
        {
            o_k:dict(
                **o_v,
                gnt_list_field="{prefix}.{name}/{index}".format(
                    prefix=parent_gnt_list_prefix,
                    name=o_v.get('gnt_list_field_name', o_k),
                    index=index
                )
            )
            for o_k, o_v in options.items()
        }
        for index in range(number)
    ]

disk_templates = ['sharedfile', 'diskless', 'plain', 'gluster', 'blockdev',
                    'drbd', 'ext', 'file', 'rbd']
hypervisor_choices = ['chroot', 'xen-pvm', 'kvm', 'xen-hvm', 'lxc', 'fake']
nic_types_choices = ['bridged', 'openvswitch']
nics_options = dict(
    name=dict(type="str", require=True,),
    mode=dict(type="str", require=False, default=nic_types_choices[0], choices=nic_types_choices),
    vlan=dict(type="int", require=False),
    network=dict(type="str", require=False),
    mac=dict(type="str", require=False),
    link=dict(type="str", require=False),
    ip=dict(type="str", require=False),
)
disks_options = dict(
    name=dict(type="str", require=True),
    size=dict(type="int", require=True),
    spindles=dict(type="str", require=False),
    vg=dict(type="str", require=False),
    metavg=dict(type="str", require=False),
    access=dict(type="str", require=False),
)
backend_param = dict(
    memory=dict(type='int', required=False, gnt_list_field='be/memory'),
    vcpus=dict(type='int', required=False, gnt_list_field='be/vcpus'),
)

hypervisor_params = dict(
    kernel_args=dict(type='str', required=False, gnt_list_field='hv/kernel_args'),
    kernel_path=dict(type='str', required=False, gnt_list_field='hv/kernel_path'),
)

osparams = dict()

ganeti_instance_args_spec = dict(
    disk_template=dict(type='str', default='plain', choices=disk_templates),
    disks=dict(type='list', required=False, options=copy_options_nth(disks_options, 'disk')),
    hypervisor=dict(type='str', default='kvm', choices=hypervisor_choices),
    iallocator=dict(type='str', required=False, default='hail'),
    nics=dict(type='list', required=False, options=copy_options_nth(nics_options, 'nic')),
    os_type=dict(type='str', required=False),
    osparams=dict(type='dict', required=False, options=osparams),
    pnode=dict(type='str', required=False, default=None),
    hypervisor_params=dict(type='dict', required=False, options=hypervisor_params),
    backend_param=dict(type='dict', required=False, options=backend_param),
)
