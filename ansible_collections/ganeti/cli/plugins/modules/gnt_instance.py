#!/usr/bin/python
"""
ansible gnt-instance module
"""

from __future__ import (absolute_import, division, print_function)
from functools import wraps
from typing import Any, Dict
__metaclass__ = type  # pylint: disable=invalid-name

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ganeti.cli.plugins.module_utils.builder_command_options.builders \
    import BuilderCommand
from ansible_collections.ganeti.cli.plugins.module_utils.gnt_instance import (
    GntInstance,
    builder_gnt_instance_spec
)


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
    "state": {"type":'str', "required":False, "default":'present', "choices":state_choices},
    "params": BuilderCommand(builder_gnt_instance_spec).generate_args_spec(),
    "admin_state": {
        "type":'str', "required":False, "default":'started', "choices":admin_state_choices
    },
    "restart_if_have_any_change": {"type":'bool', "required":False, "default":False},
}

class VM:
    def __init__(self, params: Dict[str, Any]) -> None:
        self.params = params

    def must_be(self, attribute: str, value: Any) -> bool:
        return self.params[attribute] == value

    @property
    def have_options(self) -> bool:
        return bool(self.params['params'])

    @property
    def name(self) -> str:
        return self.params['name']

    @property
    def must_be_absent(self) -> bool:
        return self.must_be('state', 'absent')

    @property
    def must_be_present(self) -> bool:
        return self.must_be('state', 'present')

    @property
    def must_be_reboot_if_have_difference(self) -> bool:
        return self.params['restart_if_have_any_change']

    @property
    def must_be_up(self) -> bool:
        return self.must_be('admin_state', 'started')

    @property
    def must_be_down(self) -> bool:
        return self.must_be('admin_state', 'stopped')

    @property
    def must_be_restarted(self) -> bool:
        return self.must_be('admin_state', 'restarted')


def need_status(method):
    @wraps(method)
    def _impl(self, *args, **kwargs):
        if self.status is None:
            raise Exception('No VM status')
        return method(self, *args, **kwargs)
    return _impl

class VmStatus:
    #pylint: disable=invalid-name
    def __init__(self, vm: VM, status: Dict[str, Any]) -> None:
        self.vm = vm #pylint: disable=invalid-name
        self.status = status

    @property
    def name(self) -> str:
        return self.vm.name

    @property
    def is_present(self) -> bool:
        return self.status is not None and self.status['name'] == self.name

    @property
    def is_absent(self) -> bool:
        return not self.is_present

    @property
    @need_status
    def is_up(self) -> bool:
        return self.status['admin_state'] == 'up'

    @property
    @need_status
    def is_down(self) -> bool:
        return self.status['admin_state'] == 'down'

class ModuleActions:
    def __init__(self, module) -> None:
        self.module = module
        self.gnt_instance = GntInstance(module.run_command, self.error)
        self.vm = VM(self.module.params) #pylint: disable=invalid-name
        self.last_status = VmStatus(self.vm, None)

    def error(self, code, stdout, stderr, msg=None):
        self.module.fail_json(msg=msg, code=code, stdout=stdout, stderr=stderr)

    def have_difference(self) -> bool:
        if not self.vm.have_options:
            return False
        return self.gnt_instance.config_and_remote_have_difference(
            self.vm.params,
            self.last_status.status
        )

    def refresh_vm_status(self) -> VmStatus:
        def filter_by_name(vm_info: Dict) -> bool:
            return vm_info.get('name') == self.vm.name
        try:
            self.last_status = VmStatus(
                self.vm,
                next(
                    filter(
                        filter_by_name,
                        self.gnt_instance.info(self.vm.name) or []
                    )
                )
            )
        except StopIteration:
            self.last_status = VmStatus(self.vm, None)
        return self.last_status



    def create_vm(self):
        return self.gnt_instance.add(
            self.vm.name,
            self.vm.params
        )

    def modify_vm(self):
        return self.gnt_instance.modify(
            self.vm.name,
            self.vm.params,
            self.last_status.status
        )

    def reboot_vm(self):
        return self.gnt_instance.reboot(
            self.vm.name
        )

    def stop_vm(self):
        return self.gnt_instance.stop(
            self.vm.name
        )

    def remove_vm(self):
        return self.gnt_instance.remove(
            self.vm.name
        )


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
        "changed": False,
        "original_message": '',
        "message": ''
    }

    actions = ModuleActions(module)
    vm = actions.vm #pylint: disable=invalid-name
    status = actions.refresh_vm_status()



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


    if vm.must_be_present:
        if not status.is_present and not vm.have_options:
            module.fail_json(
                msg='The params of VM must be present if VM does\'t exist')

        if status.is_absent:
            actions.create_vm()
            result['changed'] = True
        elif actions.have_difference():
            if vm.must_be_reboot_if_have_difference:
                actions.stop_vm()
            actions.modify_vm()
            result['changed'] = True

        if result['changed']:
            status = actions.refresh_vm_status()

        if vm.must_be_restarted or vm.must_be_up and not status.is_up:
            actions.reboot_vm()
            result['changed'] = True
        elif vm.must_be_down and not status.is_down:
            actions.stop_vm()
            result['changed'] = True

    if vm.must_be_absent and not status.is_absent:
        actions.stop_vm()
        actions.remove_vm()
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
