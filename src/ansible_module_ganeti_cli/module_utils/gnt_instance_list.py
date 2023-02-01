"""
Module contains ganeti command list function.
"""
import ast
from itertools import chain
from typing import Dict, List
from collections import OrderedDict
import flatdict

from ansible_module_ganeti_cli.module_utils.arguments_spec import ganeti_instance_args_spec


class GntListOption:
    """
    Class relation between gnt-instance list field and parser type
    alias => the field name
    type => type of perser. @PARSERS
    """
    # pylint: disable=redefined-builtin
    def __init__(self, alias, type) -> None:
        self._alias = alias
        self._type = type

    @property
    def alias(self):
        """
        Get alias
        """
        return self._alias

    @property
    def type(self):
        """
        Get type
        """
        return self._type

    def __eq__(self, other) -> bool:
        return self._alias == other.alias \
            and self._type == other.type

    def __repr__(self):
        return 'GntListOption(alias={}, type={})'.format(self.alias, self.type)


SEPARATOR_COL = '--##'

# print(ganeti_instance_args_spec)


def args_spec_to_field_headers(args_spec: dict, index:int=None) -> dict:
    """
    Convert ganeti instance arguments spec to field headers
    """
    headers = {}
    for name, spec in args_spec.items():
        if spec.gnt_list_ignore:
            continue
        if spec['type'] == 'dict':
            headers[name] = args_spec_to_field_headers(spec['options'])
        elif spec['type'] == 'list':
            headers[name] = [
                args_spec_to_field_headers(spec['options'], index)
                for index in range(spec['options'].count)
            ]
        else:
            headers[name] = GntListOption(spec.format(index) or name, spec['type'])
    return headers


def ganeti_instance_args_spec_flat_items():
    """
    Flat ganeti instance arguments spec
    """
    return flatdict.FlatterDict(
        args_spec_to_field_headers(ganeti_instance_args_spec),
        delimiter='.'
    ).items()


fix_field_headers = {
    'name': GntListOption('name', 'str'),
    'nic_names': GntListOption('nic.names', 'list'),
    'nic_modes': GntListOption('nic.modes', 'list_str'),
    'nic_vlans': GntListOption('nic.vlans', 'list'),
    'disk_sizes': GntListOption('disk.sizes', 'list_str'),
    'hvparams': GntListOption('hvparams', 'dict'),
    'admin_state': GntListOption('admin_state', 'str'),
    'disk_count': GntListOption('disk.count', 'int'),
    'nic_count': GntListOption('nic.count', 'int'),
}

field_headers = OrderedDict(
    sorted(chain(fix_field_headers.items(),
           ganeti_instance_args_spec_flat_items()), key=lambda x: x[0])
)

def subheaders(*header_names):
    """
    Get sub field headers
    *header_names > list of headers to use. If empty, return empty dict
    """
    headers = []
    for name in header_names:
        if name not in field_headers:
            raise KeyError(
                "The header {} is not present in 'field_headers'".format(name))
        headers.append((name, field_headers[name]))
    return OrderedDict(headers)


def get_keys_to_change_module_params_and_result(options, remote):
    """
    Get missing keys or changed value between options and remote instance
    information
    """
    options_flat = flatdict.FlatterDict(options, delimiter='.')
    remote_flat = flatdict.FlatterDict(remote, delimiter='.')
    return [
        o_keys
        for o_keys, o_value in options_flat.items()
        if o_value is not None and o_keys in remote_flat and o_value != remote_flat[o_keys]
    ]


def get_disk_count(remote:dict) -> int:
    """Get number of disk in server

    Args:
        remote (dict):  The remote information

    Returns:
        int: Number of disk
    """
    return remote['disk_count']

def get_nic_count(remote:dict) -> int:
    """Get number of interface in server

    Args:
        remote (dict): The remote information

    Returns:
        int: Number of interface
    """
    return remote['nic_count']

def parse_str(value):
    """
    Parse string value from gnt-instance list column
    """
    return value


def parse_list_str(value):
    """
    Parse list string value separated by coma  from gnt-instance list column
    """
    return value.split(',')


def parse_list(value):
    """
    Parse python list value from gnt-instance list column
    """
    return ast.literal_eval(value)


def parse_dict(value):
    """
    Parse python dict value from gnt-instance list column
    """
    return ast.literal_eval(value)


def parse_boolean(value: str):
    """
    Parse yes/no boolean value from gnt-instance list column
    """
    if value.lower() == 'y':
        return True
    if value.lower() == 'n':
        return False
    raise ValueError(
        'Boolean value must be "y" or "Y" or "N" or "n", not : {}'.format(value))

def parse_int(value: str):
    """
    Parse number value from gnt-instance list column
    """
    return int(value)

PARSERS = {
    'str': parse_str,
    'list_str': parse_list_str,
    'list': parse_list,
    'dict': parse_dict,
    'boolean': parse_boolean,
    'int': parse_int,
}


def parse(key, value):
    """
    Generic parse function. This function call other function selected by keys
    """
    if value == '-':
        return None
    return PARSERS[key](value)


def parse_ganeti_list_output_line(stdout: str, headers: Dict[str, GntListOption] = None) -> dict:
    """
    Parse one line of gnt-instance list result
    """
    # print(stdout)
    if headers is None:
        headers = field_headers
    if not stdout.strip():
        return None

    col_strip = map(
        lambda x: x.strip(),
        stdout.split(SEPARATOR_COL)
    )
    out_dict_string = OrderedDict(zip(headers.keys(), col_strip))
    # print(out_dict_string)
    return OrderedDict(
        [
            (h_k, parse(h_v.type, out_dict_string[h_k]))
            for h_k, h_v in headers.items()
        ]
    )


def parse_ganeti_list_output(
        *_: str,
        stdout: str,
        headers: Dict[str, GntListOption] = None
    ) -> list:
    """
    Parse gnt-instance list result
    """
    if headers is None:
        headers = field_headers
    gen_list = map(lambda o: parse_ganeti_list_output_line(
        headers=headers, stdout=o), stdout.strip().split('\n'))
    return list(gen_list)


def get_alias(gnt_list_option):
    """
    Get alias for gnt list options
    """
    return gnt_list_option.alias

def merge_alias_headers(headers:Dict[str, GntListOption]):
    """
    Merge all alias from headers
    """
    return ','.join(
        map(get_alias, headers.values())
    )

def build_gnt_instance_list_arguments(*names:List[str], header_names:List[str]):
    """Run gnt-instance list. Get all information on instances.

    Args:
        names (list[str]): name of instances to view
        header_names (List[str]): Column to view for instances.
            Defaults to None.

    Returns:
        str: The return of command
    """
    headers = field_headers if not header_names else subheaders(*header_names)
    if len(headers) == 0:
        raise ValueError("Must be have headers")
    filter_options = merge_alias_headers(headers)

    return [
        '--no-headers',
        "--separator='{}'".format(SEPARATOR_COL),
        "--output",
        filter_options,
        *names,
    ]
