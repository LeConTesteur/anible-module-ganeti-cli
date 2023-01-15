#!/usr/bin/python

# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
try:
    from ansible.module_utils.ganeti_instance_list_cli import run_gnt_instance_list, convert_gnt_list_out_to_ansible_options_list
except ModuleNotFoundError:
    from module_utils.ganeti_instance_list_cli import run_gnt_instance_list, convert_gnt_list_out_to_ansible_options_list

DOCUMENTATION = r'''
---
module: my_test

short_description: This is my test module

# If this is part of a collection, you need to use semantic versioning,
# i.e. the version is of the form "2.5.0" and not "2.4".
version_added: "1.0.0"

description: This is my longer description explaining my test module.

options:
    name:
        description: This is the message to send to the test module.
        required: true
        type: str
    new:
        description:
            - Control to demo if the result of this module is changed or not.
            - Parameter description can be a list as well.
        required: false
        type: bool
# Specify this value according to your collection
# in format of namespace.collection.doc_fragment_name
extends_documentation_fragment:
    - my_namespace.my_collection.my_doc_fragment_name

author:
    - Your Name (@yourGitHubHandle)
'''

EXAMPLES = r'''
# Pass in a message
- name: Test with a message
  my_namespace.my_collection.my_test:
    name: hello world

# pass in a message and have changed true
- name: Test with a message and changed output
  my_namespace.my_collection.my_test:
    name: hello world
    new: true

# fail the module
- name: Test failure of the module
  my_namespace.my_collection.my_test:
    name: fail me
'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.
original_message:
    description: The original name param that was passed in.
    type: str
    returned: always
    sample: 'hello world'
message:
    description: The output message that the test module generates.
    type: str
    returned: always
    sample: 'goodbye'
'''

from ansible.module_utils.basic import AnsibleModule
import json
import flatdict

def copy_options_nth(options, number=8):
  return [options for _ in range(number)]

def vm_is_present_on_remote(name:str, run_command):
    return any(filter(lambda x: x['name'] == name, run_gnt_instance_list(name, runner=run_command)))

def vm_info(name:str, run_command):
    return next(filter(lambda x: x['name'] == name, run_gnt_instance_list(name, runner=run_command)))

def get_keys_to_change(options, remote):
    options_flat = flatdict.FlatterDict(options, delimiter='.')
    remote_flat = flatdict.FlatterDict(remote, delimiter='.')
    return [
        o_keys
        for o_keys, o_value in options_flat.items()
        if o_value is not None and o_keys in remote_flat and o_value != remote_flat[o_keys]
    ]

def have_vm_change(options, remote):
    return len(get_keys_to_change(options, remote)) > 0

def run_module():
    # define available arguments/parameters a user can pass to the module
    disk_templates = ['sharedfile', 'diskless', 'plain', 'gluster', 'blockdev',
                      'drbd', 'ext', 'file', 'rbd']
    hypervisor_choices = ['chroot', 'xen-pvm', 'kvm', 'xen-hvm', 'lxc', 'fake']
    state_choices = ['present', 'absent', 'restarted', 'started', 'stopped']
    nic_types_choices = ['bridged', 'openvswitch']
    nics_options = dict(
      name=dict(type="str", require=True),
      mode=dict(type="str", require=False, default=nic_types_choices[0], choices=nic_types_choices),
      vlan=dict(type="int", require=False),
      network=dict(type="str", require=False),
      mac=dict(type="str", require=False),
      link=dict(type="str", require=False),
      ip=dict(type="str", require=False),
    )
    create_params = dict(
        disk_template=dict(type='str', default='plain', choices=disk_templates),
        disks=dict(type='list', required=False),
        hypervisor=dict(type='str', default='kvm', choices=hypervisor_choices),
        iallocator=dict(type='str', required=False, default='hail'),
        nics=dict(type='list', required=False, options=copy_options_nth(nics_options)),
        os_type=dict(type='str', required=False),
        osparams=dict(type='dict', required=False),
        pnode=dict(type='str', required=False, default=None),
        # beparams
        memory=dict(type='int', required=False),
        vcpus=dict(type='int', required=False),
    )
    module_args = dict(
        name=dict(type='str', required=True,aliases=['instance_name']),
        state=dict(type='str', required=False, default='present', choises=state_choices),
        params=dict(type='dict', required=False, options=create_params)
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # changed is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        original_message='',
        message=''
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        module.exit_json(**result)

    # manipulate or modify the state as needed (this is going to be the
    # part where your module will do what it needs to do)
    result['original_message'] = module.params['name']
    result['message'] = json.dumps(module.params)

    # use whatever logic you need to determine whether or not this module
    # made any modifications to your target
    if module.params['state'] == 'present':
        result['changed'] = True

    # during the execution of the module, if there is an exception or a
    # conditional state that effectively causes a failure, run
    # AnsibleModule.fail_json() to pass in the message and the result
    if module.params['name'] == 'fail me':
        module.fail_json(msg='You requested this to fail', **result)
    vm_is_present_on_remote(module.params['name'], module.run_command)
    result['is_present'] = json.dumps(vm_is_present_on_remote(module.params['name'], module.run_command))
    info = vm_info(module.params['name'], module.run_command)
    result['vm_info'] = json.dumps(info)
    result['keys'] = json.dumps(get_keys_to_change(module.params['params'], info))
    result['have_change'] = json.dumps(have_vm_change(module.params['params'], info))
    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()

