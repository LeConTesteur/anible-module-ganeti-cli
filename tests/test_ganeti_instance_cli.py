import json

import functools
import unittest
from unittest.mock import patch, Mock
from ansible.module_utils import basic
from ansible.module_utils.common.text.converters import to_bytes
from ansible_module_ganeti_cli.library.ganeti_instance_cli import main

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

def run_gnt_instance_list(name, *args, **kwargs):
    return {
        'name': name,
    }

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
            'ansible_module_ganeti_cli.library.ganeti_instance_cli.GntInstance',
            autospec=True
        )
        self.mock_module_helper.start()
        self.mock_gnt_instance = self.mock_gnt_instance_helper.start()
        self.mock_instance = self.mock_gnt_instance.return_value
        self.addCleanup(self.mock_gnt_instance_helper.stop)
        self.addCleanup(self.mock_module_helper.stop)

    # pylint: disable=too-many-arguments
    def _call_test(self, module_args, vm_info, have_change=True, info_call=1, reboot_call=0, add_call=0, stop_call=0, modify_call=0, remove_call=0):
        set_module_args(module_args)

        self.mock_instance.list = Mock(return_value=vm_info)
        with self.assertRaises(AnsibleExitJson) as result:
            main(catch_exception=False)
        self._assertChangedEqual(result, have_change)
        self.assertEqual(self.mock_instance.list.call_count, info_call)
        self.assertEqual(self.mock_instance.reboot.call_count, reboot_call)
        self.assertEqual(self.mock_instance.add.call_count, add_call)
        self.assertEqual(self.mock_instance.stop.call_count, stop_call)
        self.assertEqual(self.mock_instance.remove.call_count, remove_call)
        self.assertEqual(self.mock_instance.modify.call_count, modify_call)

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


        self.mock_instance.list.return_value = [{'name': 'vm_test2', 'admin_state':'down'}]
        with self.assertRaises(AnsibleFailJson):
            main(catch_exception=False)
        self.assertEqual(self.mock_instance.list.call_count, 1)
        self.assertEqual(self.mock_instance.reboot.call_count, 0)
        self.assertEqual(self.mock_instance.add.call_count, 0)
        self.assertEqual(self.mock_instance.modify.call_count, 0)

    def test_stop_and_remove_if_expected_absent_and_exist(self):
        self._call_test({
            'state': 'absent',
            'name': 'vm_test',
        },
        [{'name': 'vm_test', 'admin_state':'up'}],
        stop_call=1,
        remove_call=1
        )

    def test_nothing_if_expected_absent_and_not_exist(self):
        self._call_test({
            'state': 'absent',
            'name': 'vm_test',
        },
        [],
        have_change=False)

    def test_nothing_if_expected_absent_and_not_exist_2(self):
        self._call_test({
            'state': 'absent',
            'name': 'vm_test',
        },
        [{'name': 'vm_test2', 'admin_state':'up'}],
        have_change=False)

    def test_nothing_if_expected_present_and_was_up_and_have_no_change(self):
        self._call_test({
            'state': 'present',
            'name': 'vm_test',
        },
        [{'name': 'vm_test', 'admin_state':'up'}],
        have_change=False,
        reboot_call=0
        )

    def test_reboot_if_expected_present_and_was_down_and_have_no_change(self):
        self._call_test(
        {
            'state': 'present',
            'name': 'vm_test',
        },
        [{'name': 'vm_test', 'admin_state':'down'}],
        reboot_call=1
        )

    def test_reboot_if_expected_present_and_exist_and_restarted(self):
        self._call_test(
            {
                'state': 'present',
                'name': 'vm_test',
                'admin_state': 'restarted',
            },
            [{'name': 'vm_test', 'admin_state':'down'}],
            reboot_call=1,
            modify_call=0
        )



    def test_reboot_and_modify_if_expected_present_and_exist_with_diff_params(self):
        self._call_test(
            {
                'state': 'present',
                'name': 'vm_test',
                'params': {
                    'disk_template': 'file'
                }
            },
            [{'name': 'vm_test', 'disk_template':'plain','admin_state':'down'}],
            reboot_call=1,
            modify_call=1
        )
