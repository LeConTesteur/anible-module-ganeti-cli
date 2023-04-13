import json

import functools
import unittest
from unittest.mock import patch, Mock
from ansible.module_utils import basic
from ansible.module_utils.common.text.converters import to_bytes
from ansible_collections.lecontesteur.ganeti_cli.plugins.modules.gnt_instance import main

def set_module_args(args):
    """prepare arguments so that they will be picked up during module creation"""
    args = json.dumps({'ANSIBLE_MODULE_ARGS': args})
    basic._ANSIBLE_ARGS = to_bytes(args)


class AnsibleExitJson(Exception):
    """Exception class to be raised by module.exit_json and caught by the test case"""
    pass


class AnsibleFailJson(Exception):
    """Exception class to be raised by module.fail_json and caught by the test case"""
    pass


def exit_json(*args, **kwargs):
    """function to patch over exit_json; package return data into an exception"""
    if 'changed' not in kwargs:
        kwargs['changed'] = False
    raise AnsibleExitJson(kwargs)


def fail_json(*args, **kwargs):
    """function to patch over fail_json; package return data into an exception"""
    kwargs['failed'] = True
    raise AnsibleFailJson(kwargs)

class MockGntInstance:
    vms = {}
    def __init__(self, *args) -> None:
        pass

    def reboot(self, name:str, timeout:bool=0):
        self.vms[name]['admin_state'] = 'up'

    def stop(self, name:str, timeout:int=0, force:bool=False):
        self.vms[name]['admin_state'] = 'down'

    def start(self, name:str, start:bool=False):
        self.vms[name]['admin_state'] = 'up'

    def remove(self, name:str):
        self.vms.pop(name)

    def list(self, *names, header_names = None):
        pass

    def add(self, name:str, params: dict):
        self.vms[name] = {'name': name, 'admin_state':'down'}

    def modify(self, name:str, params: dict, vm_info: dict):
        pass

    def config_and_remote_have_difference(self, params: dict, vm_info) -> bool:
        pass

    def info(self, name:str):
        return list(self.vms.values())

    @classmethod
    def _set_vm_info(cls, vm_info):
        cls.vms = {}
        for info in vm_info:
            if 'name' in info:
                cls.vms[info['name']] = info

class TestMainGanetiInstanceCli(unittest.TestCase):

    def _assertChanged(self, result):
        self._assertChangedEqual(result, True)

    def _assertNoChanged(self, result):
        self._assertChangedEqual(result, False)

    def _assertChangedEqual(self, result, state:bool):
        self.assertEqual(result.exception.args[0]['changed'], state)

    def setUp(self):
        self.mock_module_helper = patch.multiple(basic.AnsibleModule,
                                                 exit_json=exit_json,
                                                 fail_json=fail_json)
        self.mock_gnt_instance_helper = patch(
            'ansible_collections.lecontesteur.ganeti_cli.plugins.modules.gnt_instance.GntInstance',
            MockGntInstance
        )
        self.mock_module_helper.start()
        self.mock_gnt_instance = self.mock_gnt_instance_helper.start()
        self.mock_gnt_instance.config_and_remote_have_difference = Mock()
        self.mock_gnt_instance.modify = Mock()
        self.mock_instance = self.mock_gnt_instance()
        self.addCleanup(self.mock_gnt_instance_helper.stop)
        self.addCleanup(self.mock_module_helper.stop)

    # pylint: disable=too-many-arguments
    def _call_test(self, module_args, vm_info, expected_vm_info, expected_change=True, have_change=False, modify_call_count=0):
        set_module_args(module_args)

        self.mock_instance._set_vm_info(vm_info)
        self.mock_gnt_instance.config_and_remote_have_difference.return_value = have_change
        with self.assertRaises(AnsibleExitJson) as result:
            main(catch_exception=False)
        self._assertChangedEqual(result, expected_change)
        self.assertEqual(self.mock_gnt_instance.modify.call_count, modify_call_count)
        self.assertEqual(self.mock_instance.info(''), expected_vm_info)

    def test_module_fail_when_required_args_missing(self):
        with self.assertRaises(AnsibleFailJson):
            set_module_args({})
            main(catch_exception=False)

    def test_restarted_if_expected_present_and_not_exist_and_without_params(self):
        set_module_args({
            'state': 'present',
            'name': 'vm_test',
            'admin_state': 'restarted',
        })

        self.mock_instance._set_vm_info([{'name': 'vm_test2', 'admin_state':'down'}])
        with self.assertRaises(AnsibleFailJson):
            main(catch_exception=False)

    def test_stop_and_remove_if_expected_absent_and_exist(self):
        self._call_test({
            'state': 'absent',
            'name': 'vm_test',
        },
        [{'name': 'vm_test', 'admin_state':'up'}],
        [],
        )

    def test_nothing_if_expected_absent_and_not_exist(self):
        self._call_test({
            'state': 'absent',
            'name': 'vm_test',
        },
        [],
        [],
        expected_change=False)

    def test_nothing_if_expected_absent_and_not_exist_with_other_vm(self):
        self._call_test({
            'state': 'absent',
            'name': 'vm_test',
        },
        [{'name': 'vm_test2', 'admin_state':'up'}],
        [{'name': 'vm_test2', 'admin_state':'up'}],
        expected_change=False)

    def test_nothing_if_expected_present_and_was_up_and_have_no_change(self):
        self._call_test({
            'state': 'present',
            'name': 'vm_test',
        },
        [{'name': 'vm_test', 'admin_state':'up'}],
        [{'name': 'vm_test', 'admin_state':'up'}],
        expected_change=False,
        )

    def test_reboot_if_expected_present_and_was_down_and_have_no_change(self):
        self._call_test(
        {
            'state': 'present',
            'name': 'vm_test',
        },
        [{'name': 'vm_test', 'admin_state':'down'}],
        [{'name': 'vm_test', 'admin_state':'up'}],
        )

    def test_reboot_if_expected_present_and_exist_and_restarted(self):
        self._call_test(
            {
                'state': 'present',
                'name': 'vm_test',
                'admin_state': 'restarted',
            },
            [{'name': 'vm_test', 'admin_state':'down'}],
            [{'name': 'vm_test', 'admin_state':'up'}],
        )

    def test_reboot_and_modify_if_expected_present_and_exist_with_diff_params(self):
        self._call_test(
            {
                'state': 'present',
                'name': 'vm_test',
                'options': {
                    'disk-template': 'file',
                    'os-type': 'noop',
                }
            },
            [{'name': 'vm_test', 'admin_state':'down'}],
            [{'name': 'vm_test', 'admin_state':'up'}],
            have_change=True,
            modify_call_count=1
        )

if __name__ == '__main__':
    unittest.main()