import json

import unittest
from unittest.mock import patch
from ansible.module_utils import basic
from ansible.module_utils.common.text.converters import to_bytes
from library.ganeti_instance_cli import run_module


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

class TestGanetiInstanceCli(unittest.TestCase):

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
            run_module()

    @patch('library.ganeti_instance_cli.run_gnt_instance_list')
    def test_ensure_command_called(self, run_gnt_list):
        set_module_args({
            'state': 'absent',
            'name': 'vm_test',
        })

        run_gnt_list.return_value = [{'name': 'vm_test', 'admin_state':'up'}]
        with self.assertRaises(AnsibleExitJson) as result:
            run_module()
        self.assertTrue(result.exception.args[0]['changed']) # ensure result is changed
        self.assertEqual(run_gnt_list.call_count, 1)

