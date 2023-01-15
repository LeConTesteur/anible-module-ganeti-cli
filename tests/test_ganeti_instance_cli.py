import json

import unittest
from unittest.mock import patch, DEFAULT
from ansible.module_utils import basic
from ansible.module_utils.common.text.converters import to_bytes
from library.ganeti_instance_cli import main

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

def run_gnt_instance_add(name, *args, **kwargs):
    pass

def run_gnt_instance_reboot(name, *args, **kwargs):
    pass

def run_gnt_instance_stop(name, *args, **kwargs):
    pass

def run_gnt_instance_remove(name, *args, **kwargs):
    pass

class TestMainGanetiInstanceCli(unittest.TestCase):

    def _assertChanged(self, result):
        self.assertTrue(result.exception.args[0]['changed'])

    def _assertNoChanged(self, result):
        self.assertFalse(result.exception.args[0]['changed'])

    def setUp(self):
        self.mock_module_helper = patch.multiple(basic.AnsibleModule,
                                                 exit_json=exit_json,
                                                 fail_json=fail_json)
        self.mock_ganeti_command_helper = patch.multiple('library.ganeti_instance_cli',
                                                 run_gnt_instance_add=run_gnt_instance_add,
                                                 run_gnt_instance_reboot=run_gnt_instance_reboot,
                                                 run_gnt_instance_stop=run_gnt_instance_stop,
                                                 run_gnt_instance_remove=run_gnt_instance_remove,
        )
        self.mock_module_helper.start()
        self.mock_ganeti_command_helper.start()
        self.addCleanup(self.mock_ganeti_command_helper.stop)
        self.addCleanup(self.mock_module_helper.stop)

    def test_module_fail_when_required_args_missing(self):
        with self.assertRaises(AnsibleFailJson):
            set_module_args({})
            main()

    @patch('library.ganeti_instance_cli.run_gnt_instance_remove')
    @patch('library.ganeti_instance_cli.run_gnt_instance_stop')
    @patch('library.ganeti_instance_cli.run_gnt_instance_list')
    def test_remove_if_expected_absent_and_exist(self, run_gnt_list, run_gnt_stop, run_gnt_remove):
        set_module_args({
            'state': 'absent',
            'name': 'vm_test',
        })
        run_gnt_list.return_value = [{'name': 'vm_test', 'admin_state':'up'}]
        with self.assertRaises(AnsibleExitJson) as result:
            main()
        self._assertChanged(result)
        self.assertEqual(run_gnt_list.call_count, 1)
        self.assertEqual(run_gnt_stop.call_count, 1)
        self.assertEqual(run_gnt_remove.call_count, 1)

    @patch('library.ganeti_instance_cli.run_gnt_instance_remove')
    @patch('library.ganeti_instance_cli.run_gnt_instance_stop')
    @patch('library.ganeti_instance_cli.run_gnt_instance_list')
    def test_nothing_if_expected_absent_and_not_exist(self, run_gnt_list, run_gnt_stop, run_gnt_remove):
        set_module_args({
            'state': 'absent',
            'name': 'vm_test',
        })

        run_gnt_list.return_value = []
        with self.assertRaises(AnsibleExitJson) as result:
            main()
        self._assertNoChanged(result)
        self.assertEqual(run_gnt_list.call_count, 1)
        self.assertEqual(run_gnt_stop.call_count, 0)
        self.assertEqual(run_gnt_remove.call_count, 0)

    @patch('library.ganeti_instance_cli.run_gnt_instance_remove')
    @patch('library.ganeti_instance_cli.run_gnt_instance_stop')
    @patch('library.ganeti_instance_cli.run_gnt_instance_list')
    def test_nothing_if_expected_absent_and_not_exist_2(self, run_gnt_list, run_gnt_stop, run_gnt_remove):
        set_module_args({
            'state': 'absent',
            'name': 'vm_test',
        })

        run_gnt_list.return_value = [{'name': 'vm_test2', 'admin_state':'up'}]
        with self.assertRaises(AnsibleExitJson) as result:
            main()
        self._assertNoChanged(result)
        self.assertEqual(run_gnt_list.call_count, 1)
        self.assertEqual(run_gnt_stop.call_count, 0)
        self.assertEqual(run_gnt_remove.call_count, 0)

    @patch('library.ganeti_instance_cli.run_gnt_instance_add')
    @patch('library.ganeti_instance_cli.run_gnt_instance_reboot')
    @patch('library.ganeti_instance_cli.run_gnt_instance_list')
    def test_nothing_if_expected_present_and_was_up_and_have_no_change(self, run_gnt_list, run_gnt_reboot, run_gnt_add):
        set_module_args({
            'state': 'present',
            'name': 'vm_test',
        })

        run_gnt_list.return_value = [{'name': 'vm_test', 'admin_state':'up'}]
        with self.assertRaises(AnsibleExitJson) as result:
            main()
        self._assertNoChanged(result)
        self.assertEqual(run_gnt_list.call_count, 1)
        self.assertEqual(run_gnt_reboot.call_count, 0)
        self.assertEqual(run_gnt_add.call_count, 0)

    @patch('library.ganeti_instance_cli.run_gnt_instance_add')
    @patch('library.ganeti_instance_cli.run_gnt_instance_reboot')
    @patch('library.ganeti_instance_cli.run_gnt_instance_list')
    def test_reboot_if_expected_present_and_was_down_and_have_no_change(self, run_gnt_list, run_gnt_reboot, run_gnt_add):
        set_module_args({
            'state': 'present',
            'name': 'vm_test',
        })

        run_gnt_list.return_value = [{'name': 'vm_test', 'admin_state':'down'}]
        with self.assertRaises(AnsibleExitJson) as result:
            main()
        self._assertChanged(result)
        self.assertEqual(run_gnt_list.call_count, 1)
        self.assertEqual(run_gnt_reboot.call_count, 1)
        self.assertEqual(run_gnt_add.call_count, 0)

    @patch('library.ganeti_instance_cli.run_gnt_instance_modify')
    @patch('library.ganeti_instance_cli.run_gnt_instance_add')
    @patch('library.ganeti_instance_cli.run_gnt_instance_reboot')
    @patch('library.ganeti_instance_cli.run_gnt_instance_list')
    def test_reboot_if_expected_present_and_exist_and_restarted(self, run_gnt_list, run_gnt_reboot, run_gnt_add, run_gnt_modify):
        set_module_args({
            'state': 'present',
            'name': 'vm_test',
            'admin_state': 'restarted',
        })


        run_gnt_list.return_value = [{'name': 'vm_test', 'admin_state':'down'}]
        with self.assertRaises(AnsibleExitJson) as result:
            main()
        self._assertChanged(result)
        self.assertEqual(run_gnt_list.call_count, 1)
        self.assertEqual(run_gnt_reboot.call_count, 1)
        self.assertEqual(run_gnt_add.call_count, 0)
        self.assertEqual(run_gnt_modify.call_count, 0)

    @patch('library.ganeti_instance_cli.run_gnt_instance_modify')
    @patch('library.ganeti_instance_cli.run_gnt_instance_add')
    @patch('library.ganeti_instance_cli.run_gnt_instance_reboot')
    @patch('library.ganeti_instance_cli.run_gnt_instance_list')
    def test_reboot_if_expected_present_and_not_exist_and_without_params(self, run_gnt_list, run_gnt_reboot, run_gnt_add, run_gnt_modify):
        set_module_args({
            'state': 'present',
            'name': 'vm_test',
            'admin_state': 'restarted',
        })


        run_gnt_list.return_value = [{'name': 'vm_test2', 'admin_state':'down'}]
        with self.assertRaises(AnsibleFailJson):
            main()
        self.assertEqual(run_gnt_list.call_count, 1)
        self.assertEqual(run_gnt_reboot.call_count, 0)
        self.assertEqual(run_gnt_add.call_count, 0)
        self.assertEqual(run_gnt_modify.call_count, 0)



        run_gnt_list.return_value = [{'name': 'vm_test2', 'admin_state':'down'}]
        with self.assertRaises(AnsibleFailJson):
            main()
        self.assertEqual(run_gnt_list.call_count, 1)
        self.assertEqual(run_gnt_reboot.call_count, 0)
        self.assertEqual(run_gnt_add.call_count, 0)
        self.assertEqual(run_gnt_modify.call_count, 0)

    @patch('library.ganeti_instance_cli.run_gnt_instance_modify')
    @patch('library.ganeti_instance_cli.run_gnt_instance_add')
    @patch('library.ganeti_instance_cli.run_gnt_instance_reboot')
    @patch('library.ganeti_instance_cli.run_gnt_instance_list')
    def test_reboot_if_expected_present_and_exist_with_diff_params(self, run_gnt_list, run_gnt_reboot, run_gnt_add, run_gnt_modify):
        set_module_args({
            'state': 'present',
            'name': 'vm_test',
            'params': {
                'disk_template': 'file'
            }
        })

        run_gnt_list.return_value = [{'name': 'vm_test', 'disk_template':'plain','admin_state':'down'}]
        with self.assertRaises(AnsibleExitJson) as result:
            main()
        self._assertChanged(result)
        self.assertEqual(run_gnt_list.call_count, 1)
        self.assertEqual(run_gnt_reboot.call_count, 1)
        self.assertEqual(run_gnt_add.call_count, 0)
        self.assertEqual(run_gnt_modify.call_count, 1)