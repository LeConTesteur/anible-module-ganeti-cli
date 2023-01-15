import ast
from typing import Dict, List
from collections import namedtuple, OrderedDict
from functools import partial

try:
    from ansible.module_utils.gnt_command import build_gnt_instance_list, run_ganeti_cmd
except (ModuleNotFoundError, ImportError):
    from module_utils.gnt_command import build_gnt_instance_list, run_ganeti_cmd

GntListOption = namedtuple('gnt_list_option', ['alias', 'type', 'group_by', 'single_name'])


separator_col = ' '*4

filter_headers = {
    'name': GntListOption('name', 'str',None,None),
    'nic_names': GntListOption('nic.names', 'list', 'nics', 'name'),
    'nic_modes': GntListOption('nic.modes', 'list_str', 'nics', 'mode'),
    'nic_vlans': GntListOption('nic.vlans', 'list', 'nics', 'vlans'),
    'nic_ips': GntListOption('nic.ips', 'list', 'nics', 'ip'),
    'nic_links': GntListOption('nic.links', 'list_str', 'nics', 'link'),
    'nic_macs': GntListOption('nic.macs', 'list_str', 'nics','mac'),
    'nic_count': GntListOption('nic.count', 'number',None,None),
    'nic_networks': GntListOption('nic.networks.names', 'list', 'nics', 'network'),
    'disk_count': GntListOption('disk.count', 'number',None,None),
    'disk_names': GntListOption('disk.names', 'list', 'disks', 'name'),
    'disk_sizes': GntListOption('disk.sizes', 'list_str', 'disks', 'size'),
    'disk_template': GntListOption('disk_template', 'list_str', 'disks', 'template'),
    'hvparams': GntListOption('hvparams', 'dict',None,None),
    'os': GntListOption('os', 'str',None,None),
    'osparams': GntListOption('osparams', 'dict',None,None),
    'hypervisor': GntListOption('hypervisor', 'str',None,None),
    'pnode': GntListOption('pnode', 'str',None,None),
    'oper_ram': GntListOption('oper_ram', 'str',None,None),
    'oper_state': GntListOption('oper_state', 'boolean',None,None),
    'oper_vcpus': GntListOption('oper_vcpus', 'number',None,None),
    'network_port': GntListOption('network_port', 'str',None,None),
    'beparams': GntListOption('beparams', 'dict',None,None),
    'admin_state': GntListOption('admin_state', 'str',None,None),
    'admin_up': GntListOption('admin_up', 'boolean',None,None),
    'console': GntListOption('console', 'dict',None,None),
}
filter_headers = OrderedDict(sorted(filter_headers.items(), key=lambda x: x[0]))


def subheaders(*header_names):
    return {k: v for k, v in filter_headers.items() if k in header_names}


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
        headers = filter_headers
    if not stdout.strip():
        return None
    col_strip = map(
        lambda x: x.strip(),
        filter(
            None,
            stdout.split(separator_col)
        )
    )
    out_dict_string = dict(zip(headers.keys(), col_strip))
    return {h_k: parse(h_v.type, out_dict_string[h_k]) for h_k, h_v in headers.items()}


def parse_ganeti_list_output(
        *_: str, 
        code: int,
        stdout: str,
        stderr: str = None,
        headers: Dict[str, GntListOption] = None
    ) -> list:
    if code != 0:
        return []
    if headers is None:
        headers = filter_headers
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
        headers = filter_headers
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
                            filter_headers.items()
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
                            filter_headers.items()
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
