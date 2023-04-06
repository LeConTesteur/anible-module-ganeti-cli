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
        description: The name of instance
        required: true
        type: str
    state:
        description: Instance must be present of absent
        required: false
        type: str
    admin_state:
        description: Health cycle of instance
        required: false
        type: str
    reboot_if_have_any_change:
        description: Reboot the instance if have modification onto instance
        required: false
        type: bool
    options:
        description: Ganeti instance options
        required: false
        type: dict
# Specify this value according to your collection
# in format of namespace.collection.doc_fragment_name
extends_documentation_fragment:
    - my_namespace.my_collection.my_doc_fragment_name

author:
    - LeContesteur (@LeConTesteur)
'''

EXAMPLES = r'''
# Create a instance
- name: Create Instance
  ganeti.cli.gnt_instance:
    name: Instance Name
    state: present
    options:
      disk-template: file
      disk:
        - size: 10G
        - name: disk2
          size: 2G
      os-type: noop
      name-check: False
      ip-check: False
      hypervisor: fake
      net:
        - name: test
          link: br_gnt
          mode: bridged
        - name: test2
          link: br_gnt
          vlan: 100

# Modify a instance. When you want modify a instance, you need set all information
- name: Modify Instance - Modify
  ganeti.cli.gnt_instance:
    name: modify_instance
    state: present
    admin_state: started
    reboot_if_have_any_change: True
    options:
      disk-template: file
      disk:
        - size: 10G
        - name: disk2
          size: 2G
      os-type: noop
      name-check: False
      ip-check: False
      hypervisor: fake
      net:
        - name: eth0.0
          link: br_gnt

# Restart a instance
- name: Restart Instance
  ganeti.cli.gnt_instance:
    name: Instance Name
    state: present
    admin_state: restarted

# Remove a instance
- name: Remove Instance
  ganeti.cli.gnt_instance:
    name: Instance Name
    state: absent
'''

RETURN = r'''
'''


# define available arguments/parameters a user can pass to the module
state_choices = ['present', 'absent']
admin_state_choices = ['restarted', 'started', 'stopped']
module_args = {
    "name": {"type":'str', "required":True, "aliases":['instance_name']},
    "state": {"type":'str', "required":False, "default":'present', "choices":state_choices},
    "options": BuilderCommand(builder_gnt_instance_spec).generate_args_spec(),
    "admin_state": {
        "type":'str', "required":False, "default":'started', "choices":admin_state_choices
    },
    "reboot_if_have_any_change": {"type":'bool', "required":False, "default":False},
}

class Instance:
    """This class implement method for get information of instance options
    """
    def __init__(self, params: Dict[str, Any]) -> None:
        self.params = params

    def must_be(self, attribute: str, value: Any) -> bool:
        return self.params[attribute] == value

    @property
    def have_options(self) -> bool:
        return bool(self.params['options'])

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
        return self.params['reboot_if_have_any_change']

    @property
    def must_be_up(self) -> bool:
        return self.must_be('admin_state', 'started')

    @property
    def must_be_down(self) -> bool:
        return self.must_be('admin_state', 'stopped')

    @property
    def must_be_restarted(self) -> bool:
        return self.must_be('admin_state', 'restarted')

class InstanceStatusMissing(Exception):
    """Exception raise when status is missing

    Args:
        Exception (str): The message
    """

def need_status(method):
    @wraps(method)
    def _impl(self, *args, **kwargs):
        if self.status is None:
            raise InstanceStatusMissing('No Instance status')
        return method(self, *args, **kwargs)
    return _impl

class InstanceStatus:
    """This class implement method for get status of remote instance
    """
    def __init__(self, instance: Instance, status: Dict[str, Any]) -> None:
        self.instance = instance
        self.status = status

    @property
    def name(self) -> str:
        return self.instance.name

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
    """This class implement actions of module
    """
    def __init__(self, module) -> None:
        self.module = module
        self.gnt_instance = GntInstance(module.run_command, self.error)
        self.instance = Instance(self.module.params)
        self.last_status = InstanceStatus(self.instance, None)

    def error(self, code, stdout, stderr, msg=None):
        self.module.fail_json(msg=msg, code=code, stdout=stdout, stderr=stderr)

    def have_difference(self) -> bool:
        if not self.instance.have_options:
            return False
        return self.gnt_instance.config_and_remote_have_difference(
            self.instance.params,
            self.last_status.status
        )

    def refresh_instance_status(self) -> InstanceStatus:
        def filter_by_name(instance_info: Dict) -> bool:
            return instance_info.get('name') == self.instance.name
        try:
            self.last_status = InstanceStatus(
                self.instance,
                next(
                    filter(
                        filter_by_name,
                        self.gnt_instance.info(self.instance.name) or []
                    )
                )
            )
        except StopIteration:
            self.last_status = InstanceStatus(self.instance, None)
        return self.last_status



    def create_instance(self):
        return self.gnt_instance.add(
            self.instance.name,
            self.instance.params
        )

    def modify_instance(self):
        return self.gnt_instance.modify(
            self.instance.name,
            self.instance.params,
            self.last_status.status
        )

    def reboot_instance(self):
        return self.gnt_instance.reboot(
            self.instance.name
        )

    def stop_instance(self):
        return self.gnt_instance.stop(
            self.instance.name
        )

    def remove_instance(self):
        return self.gnt_instance.remove(
            self.instance.name
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
    }

    actions = ModuleActions(module)
    instance = actions.instance
    status = actions.refresh_instance_status()

    if instance.must_be_present:
        if not status.is_present and not instance.have_options:
            module.fail_json(
                msg='The params of Instance must be present if instance does\'t exist')

        if status.is_absent:
            actions.create_instance()
            result['changed'] = True
        elif actions.have_difference():
            if instance.must_be_reboot_if_have_difference:
                actions.stop_instance()
            actions.modify_instance()
            result['changed'] = True

        if result['changed']:
            status = actions.refresh_instance_status()

        if instance.must_be_restarted or instance.must_be_up and not status.is_up:
            actions.reboot_instance()
            result['changed'] = True
        elif instance.must_be_down and not status.is_down:
            actions.stop_instance()
            result['changed'] = True

    if instance.must_be_absent and not status.is_absent:
        actions.stop_instance()
        actions.remove_instance()
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
