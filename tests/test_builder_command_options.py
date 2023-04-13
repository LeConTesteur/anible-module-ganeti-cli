from typing import Dict, List, Tuple
import unittest

from ansible_collections.lecontesteur.ganeti_cli.plugins.module_utils.builder_command_options.builders import BuilderCommandOptionsSpecAbstract, CommandType
from ansible_collections.lecontesteur.ganeti_cli.plugins.module_utils.builder_command_options import builders
from ansible_collections.lecontesteur.ganeti_cli.plugins.module_utils.builder_command_options.prefixes import PrefixStr

# To args spec

class MockBuilderToArgsSpec:
  def __init__(self, name, value) -> None:
    self.name = name
    self.value = value

  def to_args_spec(self):
    return {'value':self.value}

class BuilderToArgsSpec(unittest.TestCase):

  def _test_to_args_spec(self, data_set:List[Tuple[BuilderCommandOptionsSpecAbstract, dict]]):
    for index, data_line in enumerate(data_set):
      with self.subTest(index=index):
        builder: BuilderCommandOptionsSpecAbstract = data_line[0]
        expected:dict = data_line[1]
        self.assertEqual(builder.to_args_spec(), expected, msg='Error in line {} of data_set'.format(index+1))

  def test_BuilderCommandOptionsSpec(self):
    self._test_to_args_spec(
      [
        (builders.BuilderCommandOptionsSpec(name='root'), {}),
        (builders.BuilderCommandOptionsSpec(MockBuilderToArgsSpec('test', 'foo'), name='root'), {'test':{'value':'foo'}}),
        (builders.BuilderCommandOptionsSpec(
          MockBuilderToArgsSpec('test1', 'foo'),
          MockBuilderToArgsSpec('test2', 'bar'),
          name='root'), 
          {'test1':{'value':'foo'}, 'test2':{'value':'bar'}}
        ),
        (builders.BuilderCommandOptionsSpec(
          MockBuilderToArgsSpec('test1', 'foo'),
          MockBuilderToArgsSpec('test2', 'bar'),
          MockBuilderToArgsSpec('test3', '5'),
          MockBuilderToArgsSpec('test4', '10'),
          name='root'), 
          {'test1':{'value':'foo'}, 'test2':{'value':'bar'}, 'test3':{'value':'5'}, 'test4':{'value':'10'}}
        ),
      ]
    )
    
  def test_BuilderCommandOptionsRootSpec(self):
    self._test_to_args_spec(
      [
        (builders.BuilderCommandOptionsRootSpec(), {'options': {}, 'required': False, 'type': 'dict'}),
        (builders.BuilderCommandOptionsRootSpec(MockBuilderToArgsSpec('test', 'foo')), {'options': {'test':{'value':'foo'}}, 'required': False, 'type': 'dict'}),
        (builders.BuilderCommandOptionsRootSpec(
            MockBuilderToArgsSpec('test1', 'foo'),
            MockBuilderToArgsSpec('test2', 'bar'),
          ), 
          {'options': {'test1':{'value':'foo'}, 'test2':{'value':'bar'}}, 'required': False, 'type': 'dict'}
        ),
        (builders.BuilderCommandOptionsRootSpec(
            MockBuilderToArgsSpec('test1', 'foo'),
            MockBuilderToArgsSpec('test2', 'bar'),
            MockBuilderToArgsSpec('test3', '5'),
            MockBuilderToArgsSpec('test4', '10'),
          ), 
          {'options': {'test1':{'value':'foo'}, 'test2':{'value':'bar'}, 'test3':{'value':'5'}, 'test4':{'value':'10'}}, 'required': False, 'type': 'dict'}
        ),
      ]
    )

  def test_BuilderCommandOptionsSpecDict(self):
    self._test_to_args_spec(
      [
        (builders.BuilderCommandOptionsSpecDict(name='root'), {'type': 'dict', 'required':False, 'options':{}}),
        (builders.BuilderCommandOptionsSpecDict(
            MockBuilderToArgsSpec('test', 'foo'),
            name='root'
          ), 
         {'type': 'dict', 'required':False, 'options':{'test':{'value':'foo'}}}
        ),
        (builders.BuilderCommandOptionsSpecDict(
            MockBuilderToArgsSpec('test1', 'foo'),
            MockBuilderToArgsSpec('test2', 'bar'),
            name='root'
          ), 
          {'type': 'dict', 'required':False, 'options':{'test1':{'value':'foo'}, 'test2':{'value':'bar'}}}
        ),
        (builders.BuilderCommandOptionsSpecDict(
            MockBuilderToArgsSpec('test1', 'foo'),
            MockBuilderToArgsSpec('test2', 'bar'),
            MockBuilderToArgsSpec('test3', '5'),
            MockBuilderToArgsSpec('test4', '10'),
            name='root'
          ), 
          {'type': 'dict', 'required':False, 'options':{'test1':{'value':'foo'}, 'test2':{'value':'bar'}, 'test3':{'value':'5'}, 'test4':{'value':'10'}}}
        ),
      ]
    )

  def test_BuilderCommandOptionsSpecList(self):
    self._test_to_args_spec(
      [
        (builders.BuilderCommandOptionsSpecList(name='root'), {'type': 'list', 'required':False, 'options':{}}),
        (builders.BuilderCommandOptionsSpecList(
            MockBuilderToArgsSpec('test', 'foo'),
            name='root'
          ), 
         {'type': 'list', 'required':False, 'options':{'test':{'value':'foo'}}}
        ),
        (builders.BuilderCommandOptionsSpecList(
            MockBuilderToArgsSpec('test1', 'foo'),
            MockBuilderToArgsSpec('test2', 'bar'),
            name='root'
          ), 
          {'type': 'list', 'required':False, 'options':{'test1':{'value':'foo'}, 'test2':{'value':'bar'}}}
        ),
        (builders.BuilderCommandOptionsSpecList(
            MockBuilderToArgsSpec('test1', 'foo'),
            MockBuilderToArgsSpec('test2', 'bar'),
            MockBuilderToArgsSpec('test3', '5'),
            MockBuilderToArgsSpec('test4', '10'),
            name='root'
          ), 
          {'type': 'list', 'required':False, 'options':{'test1':{'value':'foo'}, 'test2':{'value':'bar'}, 'test3':{'value':'5'}, 'test4':{'value':'10'}}}
        ),
      ]
    )

  def test_BuilderCommandOptionsSpecElement(self):
    self._test_to_args_spec(
      [
        (builders.BuilderCommandOptionsSpecElement(name='root', type='test'), {'type': 'test'}),
        (builders.BuilderCommandOptionsSpecElement(
            type='int',
            name='root',
            required=True
          ), 
         {'type': 'int', 'required':True}
        ),
        (builders.BuilderCommandOptionsSpecElement(
            type='bool',
            name='root',
            required=False,
            default='foo'          ), 
          {'type': 'bool', 'required':False, 'default':'foo'}
        ),
      ]
    )
    
  def test_args_spec_generation(self):
    spec = builders.BuilderCommandOptionsRootSpec(
            builders.BuilderCommandOptionsSpecElement(name='disk_template', type='str'),
            builders.BuilderCommandOptionsSpecList(
              builders.BuilderCommandOptionsSpecListSubElement(name='name', type='str'),
              builders.BuilderCommandOptionsSpecListSubElement(name='size', type='str', info_key='disk/{}', required=True),
              name="disks",
              info_key = 'Disks'
             ),
            builders.BuilderCommandOptionsSpecDict(
              builders.BuilderCommandOptionsSpecSubElement(name='memory', type='int'),
              builders.BuilderCommandOptionsSpecSubElement(name='vcpus', type='int'),
              name='backend_param',
              info_key = 'Back-end parameters',
            )
          )
    builder = builders.BuilderCommand(spec=spec)
    self.assertEqual(builder.generate_args_spec(), {
      'type': 'dict', 'required': False, 'options':       {
        'disk_template': {'type':'str'},
        'disks': {'type':'list', 'required':False, 'options': {
          'name':{'type':'str'},
          'size':{'type':'str', 'required':True},
        }},
        'backend_param': {'type':'dict', 'required':False, 'options': {
          'memory':{'type':'int'},
          'vcpus':{'type':'int'},
        }}
      }
    })

# To options
class MockBuilderToOptions:
  def __init__(self, value) -> None:
    self.value = value
    
  def set_index(self, index):
    if index is not None:
      self.index = index

  def to_options(self, param, info, create): # pylance: disable=
    return ['value={},index={}'.format(self.value,self.index)]
  

class BuilderToOptions(unittest.TestCase):

  def _test_to_options(self, data_set:List[Tuple[BuilderCommandOptionsSpecAbstract, dict]], to_command:CommandType=None):
    for index, data_line in enumerate(data_set):
      with self.subTest(index=index):
        builder: BuilderCommandOptionsSpecAbstract = data_line[0]
        param:Dict = data_line[1]
        info:Dict = data_line[2]
        expected:dict = data_line[3]
        self.assertEqual(builder.to_options(param, info, to_command), expected, msg='Error in line {} of data_set'.format(index+1))

  def test_BuilderCommandOptionsSpecSubElement(self):
    self._test_to_options([
      (builders.BuilderCommandOptionsSpecSubElement(type='', index=0,name='test',info_key='Test'), {}, {}, []),
      (builders.BuilderCommandOptionsSpecSubElement(type='', index=0,name='test',info_key='Test'), {'test':1}, {}, ['test=1']),
      (builders.BuilderCommandOptionsSpecSubElement(type='', index=0,name='test',info_key='Test'), {}, {'Test':1}, ['test=default']),
      (builders.BuilderCommandOptionsSpecSubElement(type='', index=0,name='test',info_key='Test', default_ganeti=builders.NONE_VALUE), {}, {'Test':1}, ['test=None']),
      (builders.BuilderCommandOptionsSpecSubElement(type='', index=0,name='test',info_key='Test'), {'test':1}, {'Test':1}, []),
      (builders.BuilderCommandOptionsSpecSubElement(type='', index=0,name='test',info_key='Test'), {'test':1}, {'Test':2}, ['test=1']),
      (builders.BuilderCommandOptionsSpecSubElement(type='', index=0,name='test',info_key='Test/{}'), {'test':1}, {'Test':1}, ['test=1']),
      (builders.BuilderCommandOptionsSpecSubElement(type='', index=0,name='test',info_key='Test/{}'), {'test':1}, {'Test/0':1}, []),
      (builders.BuilderCommandOptionsSpecSubElement(type='', index=0,name='test',info_key='Test/{}'), {'test':1}, {'Test/1':1}, ['test=1']),
      (builders.BuilderCommandOptionsSpecSubElement(type='', index=0,name='test',info_key='Test/{}'), {}, {'Test/0':1}, ['test=default']),
    ])

  def test_BuilderCommandOptionsSpec_Only(self):
    self._test_to_options([
      (builders.BuilderCommandOptionsSpecElement(type='', name='test',info_key='Test', only=CommandType.CREATE), {}, {}, []),
      (builders.BuilderCommandOptionsSpecElement(type='', name='test',info_key='Test', only=CommandType.CREATE), {'test':1}, {}, ['--test=1']),
      (builders.BuilderCommandOptionsSpecElement(type='', name='test',info_key='Test', only=CommandType.CREATE), {}, {'Test':1}, ['--test=default']),
    ],
    CommandType.CREATE)
    self._test_to_options([
      (builders.BuilderCommandOptionsSpecElement(type='', name='test',info_key='Test', only=CommandType.CREATE), {}, {}, []),
      (builders.BuilderCommandOptionsSpecElement(type='', name='test',info_key='Test', only=CommandType.CREATE), {'test':1}, {}, []),
      (builders.BuilderCommandOptionsSpecElement(type='', name='test',info_key='Test', only=CommandType.CREATE), {}, {'Test':1}, []),
    ],
    CommandType.MODIFY)
  
  def test_BuilderCommandOptionsSpecElement(self):
    self._test_to_options([
      (builders.BuilderCommandOptionsSpecElement(type='', name='test',info_key='Test'), {}, {}, []),
      (builders.BuilderCommandOptionsSpecElement(type='', name='test',info_key='Test'), {'test':1}, {}, ['--test=1']),
      (builders.BuilderCommandOptionsSpecElement(type='', name='test',info_key='Test'), {}, {'Test':1}, ['--test=default']),
      (builders.BuilderCommandOptionsSpecElement(type='', name='test',info_key='Test', default_ganeti=builders.NONE_VALUE), {}, {'Test':1}, ['--test=None']),
      (builders.BuilderCommandOptionsSpecElement(type='', name='test',info_key='Test'), {'test':1}, {'Test':1}, []),
      (builders.BuilderCommandOptionsSpecElement(type='', name='test',info_key='Test'), {'test':1}, {'Test':2}, ['--test=1']),
      (builders.BuilderCommandOptionsSpecElement(type='', name='test',info_key='Test/{}'), {'test':1}, {'Test':1}, ['--test=1']),
    ])
    
  def test__BuilderCommandOptionsSpecListElement(self):
    self._test_to_options([
      (builders._BuilderCommandOptionsSpecListElement(index=0), {}, {}, ['']),
      (builders._BuilderCommandOptionsSpecListElement(MockBuilderToOptions(value=0), index=0), {}, {}, ['value=0,index=0']),
      (builders._BuilderCommandOptionsSpecListElement(MockBuilderToOptions(value=0),MockBuilderToOptions(value=2), index=3), {}, {}, ['value=0,index=3,value=2,index=3']),
    ])
    
  def test_BuilderCommandOptionsSpecListCreate(self):
    self._test_to_options([
      (builders.BuilderCommandOptionsSpecList(name='test', info_key='Tests'), {}, {}, []),
      (
        builders.BuilderCommandOptionsSpecList(
          builders.BuilderCommandOptionsSpecSubElement(type='', name='name',info_key='name'),
          name='test', info_key='Tests', no_option='--no-options'
        ), 
        {}, 
        {}, 
        ['--no-options']
      ),
      (
        builders.BuilderCommandOptionsSpecList(
          builders.BuilderCommandOptionsSpecSubElement(type='', name='name',info_key='name'),
          name='test', info_key='Tests', no_option='--no-options'
        ), 
        {'test':[]}, 
        {}, 
        ['--no-options']
      ),
      (
        builders.BuilderCommandOptionsSpecList(
          builders.BuilderCommandOptionsSpecSubElement(type='', name='name',info_key='name'),
          name='test', info_key='Tests', no_option='--no-options'
        ), 
        {'test':[]}, 
        {'Tests':[{'name':'foo'}]}, 
        ['--no-options']
      ),
      (
        builders.BuilderCommandOptionsSpecList(
          builders.BuilderCommandOptionsSpecSubElement(type='', name='name',info_key='name'),
          name='test', info_key='Tests'
        ), 
        {'test':None}, 
        {'Tests':[{'name':'foo'}]}, 
        []
      ),
      (
        builders.BuilderCommandOptionsSpecList(
          builders.BuilderCommandOptionsSpecSubElement(type='', name='name',info_key='name'),
          name='test', info_key='Tests', no_option='--no-options'
        ), 
        {'test':[{'name':'foo'}]}, 
        {}, 
        ['--test 0:name=foo']
      ),
      (
        builders.BuilderCommandOptionsSpecList(
          builders.BuilderCommandOptionsSpecSubElement(type='', name='name',info_key='name'),
          builders.BuilderCommandOptionsSpecSubElement(type='', name='size',info_key='Size'),
          name='test', info_key='Tests', no_option='--no-options'
        ), 
        {'test':[{'name':'foo'},{'name':'bar', 'size':'10'}]}, 
        {}, 
        ['--test 0:name=foo --test 1:name=bar,size=10']
      ),
    ],
    CommandType.CREATE)

  def test_BuilderCommandOptionsSpecListModify(self):
    self._test_to_options([
      (builders.BuilderCommandOptionsSpecList(name='test', info_key='Tests'), {}, {}, []),
      (
        builders.BuilderCommandOptionsSpecList(
          builders.BuilderCommandOptionsSpecSubElement(type='', name='name',info_key='name'),
          name='test', info_key='Tests', no_option='--no-options'
        ), 
        {}, 
        {}, 
        []
      ),
      (
        builders.BuilderCommandOptionsSpecList(
          builders.BuilderCommandOptionsSpecSubElement(type='', name='name',info_key='name'),
          name='test', info_key='Tests', no_option='--no-options'
        ), 
        {'test':[]}, 
        {}, 
        []
      ),
      (
        builders.BuilderCommandOptionsSpecList(
          builders.BuilderCommandOptionsSpecSubElement(type='', name='name',info_key='name'),
          name='test', info_key='Tests', no_option='--no-options'
        ), 
        {'test':[]}, 
        {'Tests':[{'name':'foo'}]}, 
        []
      ),
      (
        builders.BuilderCommandOptionsSpecList(
          builders.BuilderCommandOptionsSpecSubElement(type='', name='name',info_key='name'),
          name='test', info_key='Tests'
        ), 
        {'test':None}, 
        {'Tests':[{'name':'foo'}]}, 
        []
      ),
      (
        builders.BuilderCommandOptionsSpecList(
          builders.BuilderCommandOptionsSpecSubElement(type='', name='name',info_key='name'),
          name='test', info_key='Tests', no_option='--no-options'
        ), 
        {'test':[{'name':'foo'}]}, 
        {}, 
        ['--test 0:add,name=foo']
      ),
      (
        builders.BuilderCommandOptionsSpecList(
          builders.BuilderCommandOptionsSpecSubElement(type='', name='name',info_key='name'),
          builders.BuilderCommandOptionsSpecSubElement(type='', name='size',info_key='Size'),
          name='test', info_key='Tests', no_option='--no-options'
        ), 
        {'test':[{'name':'foo'},{'name':'bar', 'size':'10'}]}, 
        {}, 
        ['--test 0:add,name=foo --test 1:add,name=bar,size=10']
      ),
      (
        builders.BuilderCommandOptionsSpecList(
          builders.BuilderCommandOptionsSpecSubElement(type='', name='name',info_key='name'),
          builders.BuilderCommandOptionsSpecSubElement(type='', name='size',info_key='Size'),
          name='test', info_key='Tests', no_option='--no-options'
        ), 
        {'test':[{'name':'foo'},{'name':'bar', 'size':'10'}]}, 
        {'Tests':[{'name':'bar'}]}, 
        ['--test 0:modify,name=foo --test 1:add,name=bar,size=10']
      ),
      (
        builders.BuilderCommandOptionsSpecList(
          builders.BuilderCommandOptionsSpecSubElement(type='', name='name',info_key='name'),
          builders.BuilderCommandOptionsSpecSubElement(type='', name='size',info_key='Size'),
          name='test', info_key='Tests', no_option='--no-options'
        ), 
        {'test':[{'name':'foo','size':'10'},{'name':'bar', 'size':'10'}]}, 
        {'Tests':[{'name':'foo'}]}, 
        ['--test 0:modify,size=10 --test 1:add,name=bar,size=10']
      ),
      (
        builders.BuilderCommandOptionsSpecList(
          builders.BuilderCommandOptionsSpecSubElement(type='', name='name',info_key='name'),
          builders.BuilderCommandOptionsSpecSubElement(type='', name='size',info_key='Size'),
          name='test', info_key='Tests', no_option='--no-options'
        ), 
        {'test':[{'name':'foo','size':'10'},{'name':'bar', 'size':'10'}]}, 
        {'Tests':[{'name':'foo','Size':'10'}]}, 
        ['--test 0:modify,size=10 --test 1:add,name=bar,size=10']
      ),
      (
        builders.BuilderCommandOptionsSpecList(
          builders.BuilderCommandOptionsSpecSubElement(type='', name='name',info_key='name'),
          builders.BuilderCommandOptionsSpecSubElement(type='', name='size',info_key='Size'),
          name='test', info_key='Tests', no_option='--no-options'
        ), 
        {'test':[{'name':'bar', 'size':'5'},{'name':'foo','size':'20'}]}, 
        {'Tests':[{'name':'foo','Size':'10'}]}, 
        ['--test 0:modify,name=bar,size=5 --test 1:add,name=foo,size=20']
      ),
      (
        builders.BuilderCommandOptionsSpecList(
          builders.BuilderCommandOptionsSpecSubElement(type='', name='name',info_key='name'),
          builders.BuilderCommandOptionsSpecSubElement(type='', name='size',info_key='Size'),
          name='test', info_key='Tests', no_option='--no-options'
        ), 
        {'test':[{'name':'bar', 'size':'5'}]}, 
        {'Tests':[{'name':'foo','Size':'10'},{'name':'foo','Size':'10'}]}, 
        ['--test 0:modify,name=bar,size=5 --test 1:remove']
      ),
      (
        builders.BuilderCommandOptionsSpecList(
          builders.BuilderCommandOptionsSpecSubElement(type='', name='name',info_key='name'),
          builders.BuilderCommandOptionsSpecSubElement(type='', name='size',info_key='Size'),
          name='test', info_key='Tests', no_option='--no-options'
        ), 
        {'test':[{'name':'bar', 'size':'5'}]}, 
        {'Tests':[{'name':'foo','Size':'10'},{'name':'foo','Size':'10'}]}, 
        ['--test 0:modify,name=bar,size=5 --test 1:remove']
      ),
    ],
    CommandType.MODIFY)
    
  def test_BuilderCommandOptionsSpecDict(self):
        self._test_to_options([
      (builders.BuilderCommandOptionsSpecDict(name='test', info_key='Tests'), {}, {}, ['']),
      (
        builders.BuilderCommandOptionsSpecDict(
          builders.BuilderCommandOptionsSpecSubElement(type='', name='name',info_key='name'),
          name='test', info_key='Tests'
        ), 
        {'test':{'name':'5'}}, 
        {}, 
        ['--test name=5']
      ),
      (
        builders.BuilderCommandOptionsSpecDict(
          builders.BuilderCommandOptionsSpecSubElement(type='', name='name',info_key='name'),
          name='test', info_key='Tests', prefix_builder=lambda x,y: PrefixStr('foo')
        ), 
        {'test':{'name':'bar'}}, 
        {}, 
        ['--test foo:name=bar']
      ),
      (
        builders.BuilderCommandOptionsSpecDict(
          builders.BuilderCommandOptionsSpecSubElement(type='', name='name',info_key='name'),
          builders.BuilderCommandOptionsSpecSubElement(type='', name='size',info_key='size'),
          name='test', info_key='Tests'
        ), 
        {'test':{'name':'bar', 'size':'10'}}, 
        {'Tests':{'name':'bar'}}, 
        ['--test size=10']
      ),
      (
        builders.BuilderCommandOptionsSpecDict(
          builders.BuilderCommandOptionsSpecSubElement(type='', name='name',info_key='name'),
          builders.BuilderCommandOptionsSpecSubElement(type='', name='size',info_key='size'),
          name='test', info_key='Tests'
        ), 
        {'test':{}}, 
        {'Tests':{'name':'bar'}}, 
        ['--test name=default']
      ),
      (
        builders.BuilderCommandOptionsSpecDict(
          builders.BuilderCommandOptionsSpecSubElement(type='', name='name',info_key='name'),
          builders.BuilderCommandOptionsSpecSubElement(type='', name='size',info_key='size'),
          name='test', info_key='Tests'
        ), 
        {'test':{}}, 
        {'Tests':{'name':None}}, 
        ['']
      ),
      (
        builders.BuilderCommandOptionsSpecDict(
          builders.BuilderCommandOptionsSpecSubElement(type='', name='name',info_key='name'),
          builders.BuilderCommandOptionsSpecSubElement(type='', name='size',info_key='size'),
          name='test', info_key='Tests'
        ), 
        {'test':{'name':'bar'}}, 
        {'Tests':{'name':None}}, 
        ['--test name=bar']
      ),
    ])

if __name__ == '__main__':
    unittest.main()