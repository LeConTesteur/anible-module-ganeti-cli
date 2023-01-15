import ast
from itertools import chain
from typing import Dict, List
from collections import OrderedDict
from functools import partial
import flatdict


try:
    from ansible.module_utils.gnt_command import build_gnt_instance_list, run_ganeti_cmd
    from ansible.module_utils.argurments_spec import ganeti_instance_args_spec
except ImportError:
    from module_utils.gnt_command import build_gnt_instance_list, run_ganeti_cmd
    from module_utils.argurments_spec import ganeti_instance_args_spec

#GntListOption = namedtuple('gnt_list_option', ['alias', 'type'])
class GntListOption:
    # pylint: disable=redefined-builtin
    def __init__(self, alias, type) -> None:
        self._alias = alias
        self._type = type

    @property
    def alias(self):
        return self._alias

    @property
    def type(self):
        return self._type

    def __eq__(self, other) -> bool:
        return self._alias == other.alias \
            and self._type == other.type

    def __repr__(self):
        return 'GntListOption(alias={}, type={})'.format(self.alias, self.type)

separator_col = '--##'

#print(ganeti_instance_args_spec)

def args_spec_to_field_headers(args_spec: dict) -> dict:
    headers = {}
    for name, spec in args_spec.items():
        if spec.get('gnt_list_ignore', False):
            continue
        if spec['type'] == 'dict':
            headers[name] = args_spec_to_field_headers(spec['options'])
        elif spec['type'] == 'list':
            headers[name] = [args_spec_to_field_headers(s) for s in spec['options']]
        else:
            headers[name] = GntListOption(spec.get('gnt_list_field', name), spec['type'])
    return headers

def ganeti_instance_args_spec_flat_items():
    return flatdict.FlatterDict(args_spec_to_field_headers(ganeti_instance_args_spec), delimiter='.').items()

fix_headers = {
    'name': GntListOption('name', 'str'),
    'nic_names': GntListOption('nic.names', 'list'),
    'nic_modes': GntListOption('nic.modes', 'list_str'),
    'nic_vlans': GntListOption('nic.vlans', 'list'),
    'disk_sizes': GntListOption('disk.sizes', 'list_str'),
    'hvparams': GntListOption('hvparams', 'dict'),
    'admin_state': GntListOption('admin_state', 'str'),
}

field_headers = OrderedDict(
    sorted(chain(fix_headers.items(), ganeti_instance_args_spec_flat_items()), key=lambda x: x[0])
)

#print(field_headers)


def subheaders(*header_names):
    headers = []
    for name in header_names:
        if name not in field_headers:
            raise KeyError("The header {} is not present in 'field_headers'".format(name))
        headers.append((name, field_headers[name]))
    return OrderedDict(headers)


def get_keys_to_change_module_params_and_result(options, remote):
    options_flat = flatdict.FlatterDict(options, delimiter='.')
    remote_flat = flatdict.FlatterDict(remote, delimiter='.')
    return [
        o_keys
        for o_keys, o_value in options_flat.items()
        if o_value is not None and o_keys in remote_flat and o_value != remote_flat[o_keys]
    ]

def parse_str(value):
    return value


def parse_list_str(value):
    return value.split(',')


def parse_list(value):
    return ast.literal_eval(value)


def parse_dict(value):
    return ast.literal_eval(value)

def parse_boolean(value:str):
    if value.lower() == 'y':
        return True
    if value.lower() == 'n':
        return False
    raise Exception('Boolean value must be "y" or "Y" or "N" or "n", not : {}'.format(value))

parsers = {
    'str': parse_str,
    'list_str': parse_list_str,
    'list': parse_list,
    'dict': parse_dict,
    'boolean': parse_boolean,
    'int': parse_str,
}


def parse(key, value):
    if value == '-':
        return None
    return parsers[key](value)


def parse_ganeti_list_output_line(stdout: str, headers: Dict[str, GntListOption] = None) -> dict:
    #print(stdout)
    if headers is None:
        headers = field_headers
    if not stdout.strip():
        return None

    col_strip = map(
        lambda x: x.strip(),
        stdout.split(separator_col)
    )
    out_dict_string = OrderedDict(zip(headers.keys(), col_strip))
    #print(out_dict_string)
    return OrderedDict([(h_k, parse(h_v.type, out_dict_string[h_k])) for h_k, h_v in headers.items()])


def parse_ganeti_list_output(
        *_: str, 
        stdout: str,
        headers: Dict[str, GntListOption] = None
    ) -> list:
    if headers is None:
        headers = field_headers
    gen_list = map(lambda o: parse_ganeti_list_output_line(
        headers=headers, stdout=o), stdout.strip().split('\n'))
    return list(gen_list)

def get_alias(gnt_list_option):
    return gnt_list_option.alias

def build_command_gnt_instance_list(
        *names: List[str],
        headers: Dict[str, GntListOption] = None
    ) -> str:
    """Run gnt-instance list. Get all information on instances.

    Args:
        names (list[str]): name of instances to view
        headers (Dict[str, GntListOption], optional): Column to view for instances. Defaults to None.

    Raises:
        Exception: if no headers

    Returns:
        str: The return of command
    """
    if headers is None:
        headers = field_headers
    if len(headers) == 0:
        raise Exception("Must be have headers")
    filter_options = ','.join(
        map(get_alias, headers.values())
    )

    return build_gnt_instance_list(*[
        '--no-headers',
        "--separator='{}'".format(separator_col),
        "--output",
        filter_options,
        *names
    ])

run_gnt_instance_list = partial(
    run_ganeti_cmd,
    builder=build_command_gnt_instance_list,
    parser=parse_ganeti_list_output
)
