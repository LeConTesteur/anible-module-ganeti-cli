#!/usr/bin/python
"""
ansible gnt-instance module
"""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type  # pylint: disable=invalid-name

from ansible.module_utils.basic import AnsibleModule
from ansible_module_ganeti_cli.module_utils.gnt_instance_list import (
    get_keys_to_change_module_params_and_result
)
from ansible_module_ganeti_cli.module_utils.arguments_spec import ganeti_instance_args_spec
from ansible_module_ganeti_cli.module_utils.gnt_instance import GntInstance


DOCUMENTATION = r'''
---
module: ganeti_instance_cli

short_description: Create/Remove/Modify ganeti instance from cli
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


# define available arguments/parameters a user can pass to the module
state_choices = ['present', 'absent']
admin_state_choices = ['restarted', 'started', 'stopped']
module_args = {
    "name": {"type":'str', "required":True, "aliases":['instance_name']},
    "state": {"type":'str', "required":False, "default":'present', "choises":state_choices},
    "params": {"type":'dict', "required":False, "options":ganeti_instance_args_spec},
    "admin_state": {
        "type":'str', "required":False, "default":'started', "choises":admin_state_choices
    },
    "reboot_if_change": {"type":'bool', "required":False, "default":False},
}


def main_with_module(module: AnsibleModule) -> None:
    """Main function with module parameter

    Args:
        module (AnsibleModule): Ansible Module
    """
    # seed the result dict in the object
    # we primarily care about changed and state
    # changed is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = {
        "changed":False,
        "original_message":'',
        "message":''
    }

    def error_function(code, stdout, stderr, msg=None):
        module.fail_json(msg=msg, code=code, stdout=stdout, stderr=stderr)

    gnt_instance = GntInstance(module.run_command, error_function)

    def vm_is_present_on_remote(name: str, vm_info):
        return vm_info is not None and vm_info['name'] == name

    def get_vm_info(name: str):
        try:
            return next(
                filter(
                    lambda x: x.get('name') == name,
                    gnt_instance.list(name)
                )
            )
        except StopIteration:
            return None

    def have_vm_change(options, remote):
        return len(get_keys_to_change_module_params_and_result(options, remote)) > 0

    def create_vm(name: str, vm_params):
        return gnt_instance.add(
            name,
            vm_params
        )

    def modify_vm(name: str, vm_params):
        disk_count = len(vm_params.get('disks', []) or [])
        nic_count = len(vm_params.get('nics', []) or [])
        return gnt_instance.modify(
            name,
            vm_params,
            actual_disk_count=disk_count,
            actual_nic_count=nic_count
        )

    def reboot_vm(name: str):
        return gnt_instance.reboot(
            name
        )

    def stop_vm(name: str = False):
        return gnt_instance.stop(
            name
        )

    def remove_vm(name: str):
        return gnt_instance.remove(
            name
        )

    # if present expected
    #   if vm does not exit => create (change) (only_one_vm)
    #   if conf has change => modify (only_one_vm)
    #   reboot if life_state expected is up and (
    #       admin_state is not up or want reboot if change and have change
    #   ) (change) (multi_vm / no conf)
    #   stop if life_state expected is down and admin_state is not down (multi_vm / no conf)
    # if absent expected:
    #   stop (multi_vm / no conf)
    #   remove (list before form multi_vm)

    vm_name = module.params['name']
    vm_info = get_vm_info(vm_name)
    if module.params['state'] == 'present':
        if not vm_is_present_on_remote(vm_name, vm_info) and not module.params['params']:
            module.fail_json(
                msg='The params of VM must be present if VM does\'t exist')

        if not vm_is_present_on_remote(vm_name, vm_info):
            create_vm(vm_name, module.params['params'])
            result['changed'] = True
        elif have_vm_change(module.params['params'], vm_info):
            modify_vm(vm_name, module.params['params'])
            result['changed'] = True
        if module.params['admin_state'] == 'restarted' or \
                module.params['admin_state'] == 'started' and result['changed'] or \
                module.params['admin_state'] == 'started' and vm_info['admin_state'] != 'up':
            reboot_vm(vm_name)
            result['changed'] = True
        elif module.params['admin_state'] == 'stopped' and vm_info['admin_state'] != 'down':
            stop_vm(vm_name)
            result['changed'] = True
    if module.params['state'] == 'absent':
        if vm_is_present_on_remote(vm_name, vm_info):
            stop_vm(vm_name)
            remove_vm(vm_name)
            result['changed'] = True

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        module.exit_json(**result)

    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)


def main(catch_exception: bool = True):
    """
    Main function
    """

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    try:
        main_with_module(module)
    except Exception as exception:
        if catch_exception:
            module.fail_json(msg=str(exception))
        raise


if __name__ == '__main__':
    main()
