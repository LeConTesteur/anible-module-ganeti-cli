import ast
import flatdict
from itertools import chain
from typing import Dict, List
from collections import namedtuple, OrderedDict
from functools import partial

try:
    from ansible.module_utils.gnt_command import build_gnt_instance_list, run_ganeti_cmd
except (ModuleNotFoundError, ImportError):
    from module_utils.gnt_command import build_gnt_instance_list, run_ganeti_cmd

try:
    from ansible.module_utils.argurments_spec import ganeti_instance_args_spec
except (ModuleNotFoundError, ImportError):
    from module_utils.argurments_spec import ganeti_instance_args_spec

#GntListOption = namedtuple('gnt_list_option', ['alias', 'type'])
class GntListOption:
    def __init__(self, alias, type) -> None:
        self.alias = alias
        self.type = type

    def __eq__(self, other) -> bool:
        return self.alias == other.alias \
            and self.type == other.type

    def __repr__(self):
        return '(alias={}, type={})'.format(self.alias, self.type)

separator_col = ' '*4

#print(ganeti_instance_args_spec)

def args_spec_to_field_headers(args_spec: dict) -> dict:
    headers = {}
    for name, spec in args_spec.items():
        if spec['type'] == 'dict':
            headers[name] = args_spec_to_field_headers(spec['options'])
        elif spec['type'] == 'list':
            headers[name] = [args_spec_to_field_headers(s) for s in spec['options']]
        else:
            headers[name] = GntListOption(spec.get('gnt_list_field', name), spec['type'])
    return headers

def ganeti_instance_args_spec_flat_items():
    return {
        param_name: GntListOption(option, option.replace('gnt_list_field', 'type'))
        for param_name, option in flatdict.FlatterDict(args_spec_to_field_headers(ganeti_instance_args_spec), delimiter='.').items()
        if 'gnt_list_field' in param_name
    }.items()

fix_headers = {
    'name': GntListOption('name', 'str'),
    'nic_names': GntListOption('nic.names', 'list'),
    'nic_modes': GntListOption('nic.modes', 'list_str'),
    'nic_vlans': GntListOption('nic.vlans', 'list'),
    'disk_sizes': GntListOption('disk.sizes', 'list_str'),
    'hvparams': GntListOption('hvparams', 'dict'),
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
    'number': parse_str,
}


def parse(key, value):
    return parsers[key](value)


def parse_ganeti_list_output_line(stdout: str, headers: Dict[str, GntListOption] = None) -> dict:
    if headers is None:
        headers = field_headers
    if not stdout.strip():
        return None
    col_strip = map(
        lambda x: x.strip(),
        filter(
            None,
            stdout.split(separator_col)
        )
    )
    out_dict_string = OrderedDict(zip(headers.keys(), col_strip))
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
    return convert_gnt_list_out_to_ansible_options_list(list(gen_list))


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
        map(lambda x: x.alias, headers.values())
    )

    return build_gnt_instance_list(*[
        '--no-headers',
        "--separator='{}'".format(separator_col),
        "--output",
        filter_options,
        *names
    ])


def convert_gnt_list_out_to_ansible_options_list(outputs: list) -> list:
    return [convert_gnt_list_out_to_ansible_options(o) for o in outputs]

def merge_group_field(output, group):
    group_options = list(
                        filter(
                            lambda x: x[1].group_by == group,
                            field_headers.items()
                        )
                    )
    group_keys_short = [g[1].single_name for g in group_options]
    group_keys = [g[0] for g in group_options]
    return [
        dict(zip(group_keys_short, group_info))
        for group_info in zip(
            *[output.get(v) for v in group_keys]
        )
    ]

def get_ungroup_filed(output):
    ungroup_keys = list(
                    map(
                        lambda x: x[0],
                        filter(
                            lambda x: not x[1].group_by,
                            field_headers.items()
                        )
                    )
                )

    return {
        k: output.get(k) for k in ungroup_keys
    }

def convert_gnt_list_out_to_ansible_options(output:dict) -> dict:
    options = get_ungroup_filed(output)
    options['nics'] = merge_group_field(output, 'nics')
    options['disks'] = merge_group_field(output, 'disks')
    return options

run_gnt_instance_list = partial(
    run_ganeti_cmd,
    builder=build_command_gnt_instance_list,
    parser=parse_ganeti_list_output
)
