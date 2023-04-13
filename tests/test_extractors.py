import datetime
import unittest

from ansible_collections.lecontesteur.ganeti_cli.plugins.module_utils.builder_command_options import extractors

class TestBuildCommandOptionsExtractors(unittest.TestCase):
  def _test_extractor(self, extractor, data_set):
    for index, data_line in enumerate(data_set):
      with self.subTest(index=index):
        data, keys, expected = data_line
        self.assertEqual(extractor(data, keys), expected, msg='Error in line {} of data_set'.format(index+1))
    
  def test_recursive_get(self):
    self._test_extractor(
      extractor=extractors.recursive_get,
      data_set=[
        ({}, ['test'], None),
        ({'test': 'foo'}, [], None),
        ({'test': {'foo':'bar'}}, ['test', 'foo'], 'bar'),
        ({'test': {'foo':5}}, ['test', 'foo'], 5),
        ({'test': {'foo':{'bar':'5'}}}, ['test', 'foo'], {'bar':'5'}),
      ]
    )
  
  def test_value_info_extractor(self):
    self._test_extractor(
      extractor=extractors.value_info_extractor,
      data_set=[
        ({}, ['test'], None),
        ({'test': 'foo'}, [], None),
        ({'test': {'foo':'bar'}}, ['test', 'foo'], 'bar'),
        ({'test': {'foo':5}}, ['test', 'foo'], 5),
        ({'test': {'foo':'10'}}, ['test', 'foo'], 10),
        ({'test': {'foo':{'bar':'2023-02-01'}}}, ['test', 'foo', 'bar'], datetime.date(2023, 2, 1)),
      ]
    )

  def test_value_info_extractor_with_validator(self):
    self._test_extractor(
      extractor=extractors.value_info_extractor,
      data_set=[
        ({}, ['test'], None),
        ({'test': {'foo':{'bar':'2023-02-01'}}}, ['test', 'foo', 'bar'], datetime.date(2023, 2, 1)),
      ]
    )
    self.assertEqual(extractors.value_info_extractor({}, ['test'], lambda x:True), None)
    self.assertEqual(extractors.value_info_extractor({}, ['test'], lambda x:False), None)
    self.assertEqual(extractors.value_info_extractor({'test': {'foo':{'bar':'2023-02-01'}}}, ['test', 'foo', 'bar'], lambda x:True), None)
    self.assertEqual(extractors.value_info_extractor({'test': {'foo':{'bar':'2023-02-01'}}}, ['test', 'foo', 'bar'], lambda x:False), datetime.date(2023, 2, 1))

  def test_size_param_info_extractor(self):
    self._test_extractor(
      extractor=extractors.size_param_info_extractor,
      data_set=[
        ({}, ['test'], None),
        ({'test': 'foo'}, [], None),
        ({'test': {'foo':'bar'}}, ['test', 'foo'], None),
        ({'test': {'foo':5}}, ['test', 'foo'], None),
        ({'test': {'foo':'10'}}, ['test', 'foo'], None),
        ({'test': {'foo':'4G'}}, ['test', 'foo'], '4.0G'),
        ({'test': {'foo':'10G'}}, ['test', 'foo'], '10.0G'),
        ({'test': {'foo':'12.0G'}}, ['test', 'foo'], '12.0G'),
        ({'test': {'foo':'1234.15G'}}, ['test', 'foo'], '1234.15G'),
        ({'test': {'foo':'file, size 15.4G'}}, ['test', 'foo'], '15.4G'),
        ({'test': {'foo':'file, size  1.4G'}}, ['test', 'foo'], '1.4G'),
        ({'test': {'foo':'file,   size   1234.4G'}}, ['test', 'foo'], '1234.4G'),
      ]
    )

class TestBuildCommandOptionsDefaultValidator(unittest.TestCase):
  def _test_validator(self, validator, data_set):
    for index, data_line in enumerate(data_set):
      with self.subTest(index=index):
        value, expected = data_line
        self.assertEqual(validator(value), expected, msg='Error in line {} of data_set'.format(index+1))

  def test_info_default_validator(self):
    self._test_validator(
      validator=extractors.info_default_validator,
      data_set=[
        (None, False),
        ('', False),
        (' ', False),
        ('100', False),
        ('/path/path/foo', False),
        ('default (True)', True),
        ('default (False)', True),
        ('default ()', True),
        ('default (HIGH:-DES:-3DES:-EXPORT:-DH)', True),
      ]
    )

  def test_nic_default_validator(self):
    self._test_validator(
      validator=extractors.nic_default_validator,
      data_set=[
        (None, False),
        ('', True),
        (' ', True),
        ('100', False),
        ('/path/path/foo', False),
        ('default (False)', False),
        (' None ', True),
        ('None', True),
      ]
    )

if __name__ == '__main__':
    unittest.main()