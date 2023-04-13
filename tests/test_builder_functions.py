import datetime
import unittest

from ansible_collections.lecontesteur.ganeti_cli.plugins.module_utils.builder_command_options import builder_functions
from ansible_collections.lecontesteur.ganeti_cli.plugins.module_utils.builder_command_options.prefixes import PrefixAdd, PrefixModify, PrefixRemove, PrefixStr

class TestBuildCmmandOptionsExtractors(unittest.TestCase):
  def _test_builder_functions(self, function, data_set):
    for index, data_line in enumerate(data_set):
      key, value, expected = data_line
      self.assertEqual(function(key, value), expected, msg='Error in line {} of data_set'.format(index+1))
  
  def test_build_state_option(self):
    self._test_builder_functions(
      function=builder_functions.build_state_option,
      data_set=[
        (None, None, ''),
        ('test', None, ''),
        ('test', True, '--test'),
        ('test', False, ''),
      ]
    )

  def test_build_no_state_option(self):
    self._test_builder_functions(
      function=builder_functions.build_no_state_option,
      data_set=[
        (None, None, ''),
        ('test', None, ''),
        ('test', True, ''),
        ('test', False, '--no-test'),
      ]
    )
  

  def test_build_single_option(self):
    self._test_builder_functions(
      function=builder_functions.build_single_option,
      data_set=[
          (None, None, ''),
          ('test', None, ''),
          (None, 'test', ''),
          ('test', 'None', '--test=None'),
          ('test', True, '--test=True'),
          ('test', 'foo', '--test=foo'),
          ('bar', 5, '--bar=5'),
      ]
    )
    
  def test_build_sub_dict_options(self):
    self._test_builder_functions(
      function=builder_functions.build_sub_dict_options,
      data_set=[
          (None, None, ''),
          ('test', None, ''),
          (None, 'test', ''),
          ('test', 'None', 'test=None'),
          ('test', True, 'test=True'),
          ('test', 'foo', 'test=foo'),
          ('bar', 5, 'bar=5'),
      ]
    )

class TestBuildPrefixesFromCountDiff(unittest.TestCase):

    def test_count_equal_0_return_remove(self):
        self.assertEqual(list(builder_functions.build_prefixes_from_count_diff(0,0)), [])
        self.assertEqual(list(builder_functions.build_prefixes_from_count_diff(0,1)), [PrefixRemove()])
        self.assertEqual(list(builder_functions.build_prefixes_from_count_diff(0,3)), [PrefixRemove(),PrefixRemove(),PrefixRemove()])

    def test_count_lower_0_return_empty(self):
        self.assertEqual(list(builder_functions.build_prefixes_from_count_diff(-1,0)), [])
        self.assertEqual(list(builder_functions.build_prefixes_from_count_diff(-1,1)), [])
        self.assertEqual(list(builder_functions.build_prefixes_from_count_diff(-1,-1)), [])

    def test_remote_count_equal_lower_0_raise_exception(self):
        with self.assertRaises(ValueError):
            builder_functions.build_prefixes_from_count_diff(0,-1)
        with self.assertRaises(ValueError):
            builder_functions.build_prefixes_from_count_diff(2,-3)



    def test_remote_count_equal_expected_count_return_nth_prefix(self):
        self.assertEqual(list(builder_functions.build_prefixes_from_count_diff(1,1)), [PrefixModify()])
        self.assertEqual(list(builder_functions.build_prefixes_from_count_diff(3,3)), [
               PrefixModify(),
               PrefixModify(),
               PrefixModify()
            ]
        )
        self.assertEqual(list(builder_functions.build_prefixes_from_count_diff(5,5)), [
               PrefixModify(),
               PrefixModify(),
               PrefixModify(),
               PrefixModify(),
               PrefixModify()
            ]
        )

    def test_remove_count_greater_expected_count_return_nth_prefix_and_remove_surplus(self):
        self.assertEqual(list(builder_functions.build_prefixes_from_count_diff(2,3)), [
               PrefixModify(),
               PrefixModify(),
               PrefixRemove()
            ]
        )
        self.assertEqual(list(builder_functions.build_prefixes_from_count_diff(3,4)), [
               PrefixModify(),
               PrefixModify(),
               PrefixModify(),
               PrefixRemove()
            ]
        )
        self.assertEqual(list(builder_functions.build_prefixes_from_count_diff(2, 5)), [
               PrefixModify(),
               PrefixModify(),
               PrefixRemove(),
               PrefixRemove(),
               PrefixRemove()
            ]
        )

    def test_remote_count_lower_expected_count_return_nth_prefix_and_add_missing(self):
        self.assertEqual(list(builder_functions.build_prefixes_from_count_diff(1,0)), [
                PrefixAdd()
            ]
        )
        self.assertEqual(list(builder_functions.build_prefixes_from_count_diff(2,1)), [
               PrefixModify(),
               PrefixAdd()
            ]
        )
        self.assertEqual(list(builder_functions.build_prefixes_from_count_diff(3,1)), [
               PrefixModify(),
               PrefixAdd(),
               PrefixAdd()
            ]
        )
        self.assertEqual(list(builder_functions.build_prefixes_from_count_diff(5,2)), [
               PrefixModify(),
               PrefixModify(),
               PrefixAdd(),
               PrefixAdd(),
               PrefixAdd()
            ]
        )


class TestBuildGntInstanceAddListOptions(unittest.TestCase):

    def test_empty_list(self):
        self.assertEqual(
            builder_functions.build_options_with_prefixes(
                [], ""
            ),
            ""
        )

    def test_empty_option_name(self):
        with self.assertRaises(Exception):
            builder_functions.build_options_with_prefixes([1], "")

    def test_list_with_one_dict_no_attribut_without_prefix(self):
        self.assertEqual(
            builder_functions.build_options_with_prefixes(
                [
                ],
                "backend-parameters"
            ),
            ""
        )
        
    def test_list_with_one_dict_empty_attribut_without_prefix(self):
        self.assertEqual(
            builder_functions.build_options_with_prefixes(
                [
                  "",
                ],
                "backend-parameters"
            ),
            ""
        )

    def test_list_with_one_dict_one_attribut_without_prefix(self):
        self.assertEqual(
            builder_functions.build_options_with_prefixes(
                [
                    "memory=1024"
                ],
                "backend-parameters"
            ),
            "--backend-parameters memory=1024"
        )

    def test_list_with_one_dict_two_attributs_without_prefix(self):
        self.assertEqual(
            builder_functions.build_options_with_prefixes(
                [
                    "memory=1024,vcpus=2"
                ],
                "backend-parameters"
            ),
            "--backend-parameters memory=1024,vcpus=2"
        )

    def test_list_with_one_dict_two_attributs_with_prefix(self):
        self.assertEqual(
            builder_functions.build_options_with_prefixes(
                [
                    "kernel_path=,kernel_args=test"
                ],
                "hypervisor-parameters",
                PrefixStr("kvm")
            ),
            "--hypervisor-parameters kvm:kernel_path=,kernel_args=test"
        )

    def test_list_with_three_dict_two_attributs_with_one_prefix(self):
        self.assertEqual(
            builder_functions.build_options_with_prefixes(
                [
                    "name=nic0,vlan=100",
                    "name=nic1,vlan=200",
                    "name=nic2,vlan=300"
                ],
                "net",
                [PrefixAdd()]
            ),
            "--net 0:add,name=nic0,vlan=100 --net 1:add,name=nic1,vlan=200 --net 2:add,name=nic2,vlan=300"
        )
  
    def test_list_with_three_dict_so_one_empty_two_attributs_with_one_prefix(self):
        self.assertEqual(
            builder_functions.build_options_with_prefixes(
                [
                    "",
                    "name=nic1,vlan=200",
                    "name=nic2,vlan=300"
                ],
                "net",
                [PrefixAdd()]
            ),
            "--net 1:add,name=nic1,vlan=200 --net 2:add,name=nic2,vlan=300"
        )

    def test_list_with_three_dict_nth_attributs_with_nth_prefixes(self):
        self.assertEqual(
            builder_functions.build_options_with_prefixes(
                [
                    "name=nic0",
                    "name=nic1,vlan=100",
                    "name=nic2,vlan=200,mode=bridged",
                    "name=nic3",
                    "name=nic4",
                ],
                "net",
                [PrefixRemove(),PrefixAdd(), PrefixModify()]
            ),
            "--net 0:remove --net 1:add,name=nic1,vlan=100 --net 2:modify,name=nic2,vlan=200,mode=bridged --net 3:modify,name=nic3 --net 4:modify,name=nic4"
        )

if __name__ == '__main__':
    unittest.main()