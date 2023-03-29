"""
  Parse generic info response
"""
import re
from typing import Dict
from enum import Enum
import yaml

INFO = """
Cluster name: smc-manual-resources
Cluster UUID: 690b0a04-35ba-4ca0-8e3f-fd866566736e
Creation time: 2017-09-27 14:02:47
Modification time: 2022-12-20 12:22:53
Master node: sakharine.arkoon.test
Architecture (this node): 64bits (x86_64)
Tags: (none)
Default hypervisor: kvm
Enabled hypervisors: kvm
Hypervisor parameters: 
  kvm: 
    acpi: True
    boot_order: disk
    cdrom2_image_path: 
    cdrom_disk_type: 
    cdrom_image_path: 
    cpu_cores: 0
    cpu_mask: all
    cpu_sockets: 0
    cpu_threads: 0
    cpu_type: 
    disk_aio: threads
    disk_cache: default
    disk_type: paravirtual
    floppy_image_path: 
    initrd_path: 
    kernel_args: ro
    kernel_path: 
    keymap: fr
    kvm_extra: 
    kvm_flag: 
    kvm_path: /usr/bin/kvm
    machine_version: 
    mem_path: 
    migration_bandwidth: 32
    migration_caps: 
    migration_downtime: 30
    migration_mode: live
    migration_port: 8102
    nic_type: paravirtual
    reboot_behavior: reboot
    root_path: /dev/vda1
    security_domain: 
    security_model: none
    serial_console: True
    serial_speed: 38400
    soundhw: 
    spice_bind: 
    spice_image_compression: 
    spice_ip_version: 0
    spice_jpeg_wan_compression: 
    spice_password_file: 
    spice_playback_compression: True
    spice_streaming_video: 
    spice_tls_ciphers: HIGH:-DES:-3DES:-EXPORT:-DH
    spice_use_tls: False
    spice_use_vdagent: True
    spice_zlib_glz_wan_compression: 
    usb_devices: 
    usb_mouse: 
    use_chroot: False
    use_localtime: False
    user_shutdown: False
    vga: 
    vhost_net: False
    virtio_net_queues: 1
    vnc_bind_address: 0.0.0.0
    vnc_password_file: 
    vnc_tls: False
    vnc_x509_path: 
    vnc_x509_verify: False
    vnet_hdr: True
OS-specific hypervisor parameters: 
OS parameters: 
Hidden OSes: 
Blacklisted OSes: 
Cluster parameters: 
  candidate pool size: 10
  maximal number of jobs running simultaneously: 20
  maximal number of jobs simultaneously tracked by the scheduler: 25
  mac prefix: aa:00:00
  master netdev: eno1
  master netmask: 32
  use external master IP address setup script: False
  lvm volume group: Ganeti
  lvm reserved volumes: (none)
  drbd usermode helper: None
  file storage path: /srv/ganeti/file-storage
  shared file storage path: /srv/ganeti/shared-file-storage
  gluster storage path: /var/run/ganeti/gluster
  maintenance of node health: False
  uid pool: 
  default instance allocator: hail
  default instance allocator parameters: 
  primary ip version: 4
  preallocation wipe disks: False
  OS search path: /srv/ganeti/os, /usr/local/lib/ganeti/os, /usr/lib/ganeti/os, /usr/share/ganeti/os
  ExtStorage Providers search path: /srv/ganeti/extstorage, /usr/local/lib/ganeti/extstorage, /usr/lib/ganeti/extstorage, /usr/share/ganeti/extstorage
  enabled disk templates: plain, diskless
  install image: 
  instance communication network: 
  zeroing image: 
  compression tools: 
    - gzip
    - gzip-fast
    - gzip-slow
  enabled user shutdown: True
  modify ssh setup: True
  ssh_key_type: rsa
  ssh_key_bits: 2048
Default node parameters: 
  cpu_speed: 1
  exclusive_storage: False
  oob_program: 
  ovs: False
  ovs_link: 
  ovs_name: switch1
  spindle_count: 1
  ssh_port: 22
Default instance parameters: 
  default: 
    always_failover: False
    auto_balance: True
    maxmem: 128
    minmem: 128
    spindle_use: 1
    vcpus: 1
Default nic parameters: 
  default: 
    link: br-main
    mode: bridged
    vlan: 
Default disk parameters: 
  blockdev: 
  diskless: 
  drbd: 
    c-delay-target: 1
    c-fill-target: 0
    c-max-rate: 61440
    c-min-rate: 4096
    c-plan-ahead: 20
    data-stripes: 1
    disk-barriers: n
    disk-custom: 
    dynamic-resync: False
    meta-barriers: False
    meta-stripes: 1
    metavg: Ganeti
    net-custom: 
    protocol: C
    resync-rate: 61440
  ext: 
    access: kernelspace
  file: 
  gluster: 
    access: kernelspace
    host: 127.0.0.1
    port: 24007
    volume: gv0
  plain: 
    stripes: 1
  rbd: 
    access: kernelspace
    pool: rbd
  sharedfile: 
Instance policy - limits for instances: 
  bounds specs: 
    - max/0: 
        cpu-count: 8
        disk-count: 16
        disk-size: 1048576
        memory-size: 32768
        nic-count: 32
        spindle-use: 12
      min/0: 
        cpu-count: 1
        disk-count: 1
        disk-size: 1024
        memory-size: 128
        nic-count: 0
        spindle-use: 1
  std: 
    cpu-count: 1
    disk-count: 1
    disk-size: 1024
    memory-size: 128
    nic-count: 1
    spindle-use: 1
  allowed disk templates: diskless, plain
  vcpu-ratio: 4
  spindle-ratio: 128
Data collectors: 
  cpu-avg-load: 
    active: True
    interval: 5.000s
  diskstats: 
    active: True
    interval: 5.000s
  drbd: 
    active: True
    interval: 5.000s
  inst-status-xen: 
    active: True
    interval: 5.000s
  lv: 
    active: True
    interval: 5.000s
  xen-cpu-avg-load: 
    active: True
    interval: 5.000s
  """

INFO_INSTANCE ="""
- Instance name: test
  UUID: 550fc540-dda2-4c11-95a0-6c1de852c11d
  Serial number: 3
  Creation time: 2023-02-06 21:44:56
  Modification time: 2023-02-06 21:44:59
  State: configured to be up, actual state is up
  Nodes: 
    - primary: node1
      group: default (UUID 936412ad-f058-4d8b-83f3-617e75894c2c)
    - secondaries: 
  Operating system: noop
  Operating system parameters: 
  Allocated network port: None
  Hypervisor: fake
  Hypervisor parameters: 
  Back-end parameters: 
    always_failover: default (False)
    auto_balance: default (True)
    maxmem: default (128)
    memory: default (128)
    minmem: default (128)
    spindle_use: default (1)
    vcpus: default (1)
  NICs: 
    - nic/0: 
      MAC: aa:00:00:6b:2b:d0
      IP: None
      mode: bridged
      link: br_gnt
      vlan: 
      network: None
      UUID: 1290a6d7-b6ee-4324-ba2c-57c9c3bb61c5
      name: None
  Disk template: file
  Disks: 
    - disk/0: file, size 10.0G
      access mode: rw
      logical_id: ['loop', '/srv/ganeti/file-storage/test/8287dcbb-b8fe-4e0e-acdd-6ac909db01f6.file.disk0']
      on primary: /srv/ganeti/file-storage/test/8287dcbb-b8fe-4e0e-acdd-6ac909db01f6.file.disk0 (N/A:N/A)
      name: None
      UUID: 031b68c5-30b9-4ca4-bfc1-3259384335f1
"""

DELIMITER='.'

def remove_after_dash(key:str, delimiter=DELIMITER) -> str:
    """_summary_

    Args:
        key (str): _description_
        delimiter (_type_, optional): _description_. Defaults to DELIMITER.

    Returns:
        str: _description_
    """
    return re.sub(r'\s+[-](\s|\w)+[^{delimiter}]'.format(delimiter=delimiter), '', key).strip()

def remove_parenthesis(key:str) -> str:
    """_summary_

    Args:
        key (str): _description_
        delimiter (_type_, optional): _description_. Defaults to DELIMITER.

    Returns:
        str: _description_
    """
    return re.sub(r'\s+[(](\s|\w)+[)]', '', key).strip()

def remove_list_index(key:str) -> str:
    """_summary_

    Args:
        key (str): _description_
        delimiter (_type_, optional): _description_. Defaults to DELIMITER.

    Returns:
        str: _description_
    """
    return re.sub(r'[/]\w+', '', key).strip()

def remove_duplicate_underscore(key: str) -> str:
    """_summary_

    Args:
        key (str): _description_
        delimiter (_type_, optional): _description_. Defaults to DELIMITER.

    Returns:
        str: _description_
    """
    return re.sub(r'[_]+', '_', key).strip()

def replace_space_and_lower_all(key:str) -> str:
    """_summary_

    Args:
        key (str): _description_
        delimiter (_type_, optional): _description_. Defaults to DELIMITER.

    Returns:
        str: _description_
    """
    return key.replace(' ', '_').lower()

def transform_key(key: str) -> str:
    """_summary_

    Args:
        key (str): _description_

    Returns:
        str: _description_
    """

    for f_format in [
      remove_after_dash,
      remove_parenthesis,
      remove_list_index,
      replace_space_and_lower_all,
      remove_duplicate_underscore]:
        key = f_format(key)
    return  key

def transform_none_to_none(info:str):
    """_summary_

    Args:
        info (str): _description_

    Returns:
        _type_: _description_
    """
    return re.sub(r'None', 'null', info)

def default_to_none(info:str):
    """_summary_

    Args:
        info (str): _description_

    Returns:
        _type_: _description_
    """
    return re.sub(r'default [(]([^)])+[)]', 'null', transform_none_to_none(info))

def true_value(info:str):
    """_summary_

    Args:
        info (str): _description_

    Returns:
        _type_: _description_
    """
    return re.sub(r'default [(]([^)]+)[)]', r'\1', transform_none_to_none(info))

class ParseType(Enum):
    """_summary_

    Args:
        Enum (_type_): _description_
    """
    RAW = 0
    DEFAULT_TO_NONE = 1
    TRUE_VALUE = 2

#def parse(info: str, parse_type:ParseType = ParseType.RAW) -> FlatterDict:
#    """Parse info output.
#    - Using yaml parser.
#    - Flat parsed data
#    - Transform key for directly use it
#
#    Args:
#        info (str): Data to parse
#
#    Returns:
#        FlatterDict: Dict of data
#    """
#    if parse_type == ParseType.DEFAULT_TO_NONE:
#        info = default_to_none(info)
#    if parse_type == ParseType.TRUE_VALUE:
#        info = true_value(info)
#    info_parsed = yaml.safe_load(info)
#    print(info_parsed)
#    info_flatted = FlatDict(info_parsed, delimiter=DELIMITER)
#    for k in info_flatted.keys():
#        info_flatted[transform_key(k)] = info_flatted.pop(k)
#    return info_flatted

def parse(info: str) -> Dict:
    """Parse info output.
    - Using yaml parser.
    - Flat parsed data
    - Transform key for directly use it

    Args:
        info (str): Data to parse

    Returns:
        Dict: Dict of data
    """
    return yaml.safe_load(info)

def parse_from_stdout(*_, stdout: str, **__) -> Dict:
    """_summary_

    Args:
        stdout (str): _description_

    Returns:
        FlatterDict: _description_
    """
    return parse(stdout)
