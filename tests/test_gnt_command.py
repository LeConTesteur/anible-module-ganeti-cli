import unittest

from ansible_collections.ganeti.cli.plugins.module_utils.gnt_command import (
    build_prefixes_from_count_diff,
    build_dict_options_with_prefix,
    PrefixStr,
    PrefixModify, PrefixAdd, PrefixRemove,
    build_dict_to_options
)


class TestBuildPrefixesFromCountDiff(unittest.TestCase):

    def test_count_equal_0_return_empty(self):
        self.assertEqual(list(build_prefixes_from_count_diff(0,0)), [])
        self.assertEqual(list(build_prefixes_from_count_diff(0,1)), [])
        self.assertEqual(list(build_prefixes_from_count_diff(0,-1)), [])

    def test_count_lower_0_return_empty(self):
        self.assertEqual(list(build_prefixes_from_count_diff(-1,0)), [])
        self.assertEqual(list(build_prefixes_from_count_diff(-1,1)), [])
        self.assertEqual(list(build_prefixes_from_count_diff(-1,-1)), [])

    def test_remote_count_equal_lower_0_raise_exception(self):
        with self.assertRaises(Exception):
            build_prefixes_from_count_diff(2,-3)

    def test_remote_count_equal_exptected_count_return_nth_prefix(self):
        self.assertEqual(list(build_prefixes_from_count_diff(1,1)), [PrefixModify()])
        self.assertEqual(list(build_prefixes_from_count_diff(3,3)), [
               PrefixModify(),
               PrefixModify(),
               PrefixModify()
            ]
        )
        self.assertEqual(list(build_prefixes_from_count_diff(5,5)), [
               PrefixModify(),
               PrefixModify(),
               PrefixModify(),
               PrefixModify(),
               PrefixModify()
            ]
        )

    def test_remove_count_greater_expected_count_return_nth_prefix_and_remove_surplus(self):
        self.assertEqual(list(build_prefixes_from_count_diff(2,3)), [
               PrefixModify(),
               PrefixModify(),
               PrefixRemove()
            ]
        )
        self.assertEqual(list(build_prefixes_from_count_diff(3,4)), [
               PrefixModify(),
               PrefixModify(),
               PrefixModify(),
               PrefixRemove()
            ]
        )
        self.assertEqual(list(build_prefixes_from_count_diff(2, 5)), [
               PrefixModify(),
               PrefixModify(),
               PrefixRemove(),
               PrefixRemove(),
               PrefixRemove()
            ]
        )

    def test_remote_count_lower_expected_count_return_nth_prefix_and_add_missing(self):
        self.assertEqual(list(build_prefixes_from_count_diff(1,0)), [
                PrefixAdd()
            ]
        )
        self.assertEqual(list(build_prefixes_from_count_diff(2,1)), [
               PrefixModify(),
               PrefixAdd()
            ]
        )
        self.assertEqual(list(build_prefixes_from_count_diff(3,1)), [
               PrefixModify(),
               PrefixAdd(),
               PrefixAdd()
            ]
        )
        self.assertEqual(list(build_prefixes_from_count_diff(5,2)), [
               PrefixModify(),
               PrefixModify(),
               PrefixAdd(),
               PrefixAdd(),
               PrefixAdd()
            ]
        )


class TestBuildDictToOptions(unittest.TestCase):

    def test_empty_dcit(self):
        self.assertEqual(
            build_dict_to_options({}),
            ""
        )

    def test_with_one_attribut(self):
        self.assertEqual(
            build_dict_to_options({"name":"test"}),
            "name=test"
        )

    def test_with_three_attributs(self):
        self.assertEqual(
            build_dict_to_options({"name":"test", "mode":"bridged","vlan":200}),
            "name=test,mode=bridged,vlan=200"
        )

    def test_with_none_attribut(self):
        self.assertEqual(
            build_dict_to_options({"name":"test", "vlan":None}),
            "name=test"
        )

    def test_with_only_none_attribut(self):
        self.assertEqual(
            build_dict_to_options({"name":None, "vlan":None}),
            ""
        )

    def test_with_empty_attribut(self):
        self.assertEqual(
            build_dict_to_options({"name":"", "vlan":200}),
            "name=,vlan=200"
        )

    def test_with_only_empty_attribut(self):
        self.assertEqual(
            build_dict_to_options({"name":"", "vlan":""}),
            "name=,vlan="
        )

class TestBuildGntInstanceAddListOptions(unittest.TestCase):

    def test_empty_list(self):
        self.assertEqual(
            build_dict_options_with_prefix(
                [], ""
            ),
            ""
        )

    def test_empty_option_name(self):
        with self.assertRaises(Exception):
            build_dict_options_with_prefix([1], "")

    def test_list_with_one_dict_one_attribut_without_prefix(self):
        self.assertEqual(
            build_dict_options_with_prefix(
                [
                    {"memory": "1024"}
                ],
                "backend-parameters"
            ),
            "--backend-parameters memory=1024"
        )

    def test_list_with_one_dict_two_attributs_without_prefix(self):
        self.assertEqual(
            build_dict_options_with_prefix(
                [
                    {"memory": "1024","vcpus": 2}
                ],
                "backend-parameters"
            ),
            "--backend-parameters memory=1024,vcpus=2"
        )

    def test_list_with_one_dict_two_attributs_with_prefix(self):
        self.assertEqual(
            build_dict_options_with_prefix(
                [
                    {"kernel_path": "","kernel_args": "test"}
                ],
                "hypervisor-parameters",
                PrefixStr("kvm")
            ),
            "--hypervisor-parameters kvm:kernel_path=,kernel_args=test"
        )

    def test_list_with_three_dict_two_attributs_with_one_prefix(self):
        self.assertEqual(
            build_dict_options_with_prefix(
                [
                    {"name": "nic0","vlan": 100},
                    {"name": "nic1","vlan": 200},
                    {"name": "nic2","vlan": 300}
                ],
                "net",
                [PrefixAdd()]
            ),
            "--net add:name=nic0,vlan=100 --net add:name=nic1,vlan=200 --net add:name=nic2,vlan=300"
        )

    def test_list_with_three_dict_nth_attributs_with_nth_prefixes(self):
        self.assertEqual(
            build_dict_options_with_prefix(
                [
                    {"name": "nic0"},
                    {"name": "nic1","vlan": 100},
                    {"name": "nic2","vlan": 200,"mode":"bridged"},
                    {"name": "nic3"},
                    {"name": "nic4", "mode": None},
                ],
                "net",
                [PrefixRemove(),PrefixAdd(), PrefixModify()]
            ),
            "--net 0:remove --net add:name=nic1,vlan=100 --net 2:modify:name=nic2,vlan=200,mode=bridged --net 3:modify:name=nic3 --net 4:modify:name=nic4"
        )