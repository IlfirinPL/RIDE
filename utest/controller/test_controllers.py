import unittest
from mock import Mock
from robot.parsing.settings import Fixture, Documentation, Timeout, Tags, Return
from robot.utils.asserts import assert_equals, assert_true, assert_false
from robot.parsing.model import TestCaseFile

from robotide.controller.filecontrollers import TestCaseFileController
from robotide.controller.settingcontrollers import (DocumentationController,
                                                    FixtureController,
                                                    TagsController, ImportController,
                                                    ReturnValueController,
                                                    TimeoutController,
                                                    )
from robotide.controller.tablecontrollers import (VariableTableController,
                                                  MetadataListController,
                                                  ImportSettingsController,
                                                  _WithListOperations)
from robotide.publish.messages import (RideImportSetting, RideImportSettingRemoved,
                                       RideImportSettingAdded,
                                       RideImportSettingChanged)
from robotide.context import SETTINGS
from resources.mocks import PublisherListener
from controller.base_command_test import _FakeChief


class _FakeParent(_FakeChief):
    def __init__(self):
        self.dirty = False
        self.datafile = None
    def mark_dirty(self):
        self.dirty = True


class DocumentationControllerTest(unittest.TestCase):

    def setUp(self):
        self.doc = Documentation('Documentation')
        self.doc.value = 'Initial doc'
        self.parent = _FakeParent()
        self.ctrl = DocumentationController(self.parent, self.doc)

    def test_creation(self):
        assert_equals(self.ctrl.display_value, 'Initial doc')
        assert_true(self.ctrl.datafile is None)
        ctrl = DocumentationController(self.parent, Documentation('[Documentation]'))
        assert_equals(ctrl.label, 'Documentation')

    def test_setting_value(self):
        self.ctrl.set_value('Doc changed')
        assert_equals(self.doc.value, 'Doc changed')
        self.ctrl.set_value('Doc changed | again')
        assert_equals(self.doc.value, 'Doc changed | again')

    def test_get_editable_value(self):
        self.doc.value = 'My doc \\n with enters \\\\\\r\\n and \\t tabs and escapes \\\\n \\\\\\\\r'
        assert_equals(self.ctrl.editable_value, 'My doc \n with enters \\\\\n'
                                                ' and \\t tabs and escapes \\\\n \\\\\\\\r')

    def test_set_editable_value(self):
        test_text = '''My doc
 with enters
 and \t tabs'''
        self.ctrl.editable_value = test_text
        assert_equals(self.doc.value, 'My doc\\n with enters\\n and \t tabs')
        assert_equals(self.ctrl.editable_value, test_text)

    def test_set_editable_value_should_escape_leading_hash(self):
        self.ctrl.editable_value = '# Not # Comment'
        assert_equals(self.doc.value, '\\# Not # Comment')
        assert_equals(self.ctrl.editable_value, '\\# Not # Comment')

    def test_get_visible_value(self):
        self.doc.value = 'My doc \\n with enters \\n and \t tabs'
        assert_equals(self.ctrl.visible_value, '''My doc <br />
with enters <br />
and &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; tabs''')

    def test_setting_value_informs_parent_controller_about_dirty_model(self):
        self.ctrl.set_value('Blaa')
        assert_true(self.ctrl.dirty)

    def test_set_empty_value(self):
        self.ctrl.set_value('')
        assert_equals(self.doc.value, '')
        assert_true(self.ctrl.dirty)

    def test_same_value(self):
        self.ctrl.set_value('Initial doc')
        assert_false(self.ctrl.dirty)

    def test_clear(self):
        self.ctrl.clear()
        assert_equals(self.doc.value, '')
        assert_true(self.ctrl.dirty)


class FixtureControllerTest(unittest.TestCase):

    def setUp(self):
        self.fix = Fixture('Suite Setup')
        self.fix.name = 'My Setup'
        self.fix.args = ['argh', 'urgh']
        self.parent = _FakeParent()
        self.ctrl = FixtureController(self.parent, self.fix)

    def test_creation(self):
        assert_equals(self.ctrl.display_value, 'My Setup | argh | urgh')
        assert_equals(self.ctrl.label, 'Suite Setup')
        assert_true(self.ctrl.is_set)

    def test_value_with_empty_fixture(self):
        assert_equals(FixtureController(self.parent, Fixture('Teardown')).display_value, '')

    def test_setting_value_changes_fixture_state(self):
        self.ctrl.set_value('Blaa')
        assert_equals(self.fix.name, 'Blaa')
        assert_equals(self.fix.args, [])
        self.ctrl.set_value('Blaa | a')
        assert_equals(self.fix.name, 'Blaa')
        assert_equals(self.fix.args, ['a'])

    def test_whitespace_is_ignored_in_value(self):
        self.ctrl.set_value('Name |   a    |    b      |     c')
        assert_equals(self.fix.name, 'Name')
        assert_equals(self.fix.args, ['a', 'b', 'c'])
        assert_equals(self.ctrl.display_value, 'Name | a | b | c')

    def test_setting_value_informs_parent_controller_about_dirty_model(self):
        self.ctrl.set_value('Blaa')
        assert_true(self.ctrl.dirty)

    def test_set_empty_value(self):
        self.ctrl.set_value('')
        assert_equals(self.fix.name, '')
        assert_equals(self.fix.args, [])
        assert_true(self.ctrl.dirty)

    def test_same_value(self):
        self.ctrl.set_value('My Setup | argh | urgh')
        assert_false(self.ctrl.dirty)

    def test_setting_comment(self):
        self.ctrl.set_comment('My comment')
        assert_equals(self.ctrl.comment, 'My comment')
        assert_true(self.ctrl.dirty)


class TagsControllerTest(unittest.TestCase):

    def setUp(self):
        self.tags = Tags('Force Tags')
        self.tags.value = ['f1', 'f2']
        self.parent = _FakeParent()
        self.ctrl = TagsController(self.parent, self.tags)

    def test_creation(self):
        assert_equals(self.ctrl.display_value, 'f1 | f2')
        assert_true(self.ctrl.is_set)

    def test_value_with_empty_fixture(self):
        assert_equals(TagsController(self.parent, Tags('Tags')).display_value, '')

    def test_setting_value_changes_fixture_state(self):
        self.ctrl.set_value('Blaa')
        assert_equals(self.tags.value, ['Blaa'])
        self.ctrl.set_value('a1 | a2 | a3')
        assert_equals(self.tags.value, ['a1', 'a2', 'a3'])

    def test_setting_value_informs_parent_controller_about_dirty_model(self):
        self.ctrl.set_value('Blaa')
        assert_true(self.ctrl.dirty)

    def test_set_empty_value(self):
        self.ctrl.set_value('')
        assert_equals(self.tags.value, [])
        assert_true(self.ctrl.dirty)

    def test_same_value(self):
        self.ctrl.set_value('f1 | f2')
        assert_false(self.ctrl.dirty)

    def test_escaping_pipes_in_value(self):
        self.ctrl.set_value('first \| second')
        assert_equals(self.tags.value, ['first | second'])
        assert_equals(self.ctrl.display_value, 'first \| second')

    def test_adding_tag(self):
        self.ctrl.add('new tag')
        assert_equals(self.tags.value, ['f1', 'f2', 'new tag'])


class TimeoutControllerTest(unittest.TestCase):

    def setUp(self):
        self.to = Timeout('Timeout')
        self.to.value = '1 s'
        self.to.message = 'message'
        self.parent = _FakeParent()
        self.ctrl = TimeoutController(self.parent, self.to)

    def test_creation(self):
        assert_equals(self.ctrl.display_value, '1 s | message')
        assert_true(self.ctrl.is_set)

    def test_value_with_empty_timeout(self):
        assert_equals(TimeoutController(self.parent,
                                        Timeout('Timeout')).display_value, '')

    def test_setting_value_changes_fixture_state(self):
        self.ctrl.set_value('3 s')
        assert_equals(self.to.value, '3 s')
        assert_equals(self.to.message, '')
        self.ctrl.set_value('3 s | new message')
        assert_equals(self.to.value, '3 s')
        assert_equals(self.to.message, 'new message')

    def test_setting_value_informs_parent_controller_about_dirty_model(self):
        self.ctrl.set_value('1 min')
        assert_true(self.ctrl.dirty)

    def test_set_empty_value(self):
        self.ctrl.set_value('')
        assert_equals(self.to.value, '')
        assert_equals(self.to.message, '')
        assert_true(self.ctrl.dirty)

    def test_same_value(self):
        self.ctrl.set_value('1 s | message')
        assert_false(self.ctrl.dirty)


class ReturnValueControllerTest(unittest.TestCase):

    def test_creation(self):
        ctrl = ReturnValueController(_FakeParent(), Return('[Return]'))
        assert_equals(ctrl.label, 'Return Value')


class ImportControllerTest(unittest.TestCase):
    class FakeParent(_FakeChief):

        @property
        def directory(self):
            return 'tmp'

        def resource_import_modified(self, path, directory):
            pass

    def setUp(self):
        self.tcf = TestCaseFile()
        self.tcf.setting_table.add_library('somelib', ['foo', 'bar'])
        self.tcf.setting_table.add_resource('resu')
        self.tcf.setting_table.add_library('BuiltIn', ['WITH NAME', 'InBuilt'])
        self.tcf_ctrl = TestCaseFileController(self.tcf, ImportControllerTest.FakeParent())
        self.tcf_ctrl.data.directory = 'tmp'
        self.parent = ImportSettingsController(self.tcf_ctrl, self.tcf.setting_table)
        self.add_import_listener = PublisherListener(RideImportSettingAdded)
        self.changed_import_listener = PublisherListener(RideImportSettingChanged)
        self.removed_import_listener = PublisherListener(RideImportSettingRemoved)
        self.import_listener = PublisherListener(RideImportSetting)

    def tearDown(self):
        self.add_import_listener.unsubscribe()
        self.changed_import_listener.unsubscribe()
        self.import_listener.unsubscribe()

    def test_creation(self):
        self._assert_import(0, 'somelib', ['foo', 'bar'])
        self._assert_import(1, 'resu')
        self._assert_import(2, 'BuiltIn', exp_alias='InBuilt')

    def test_display_value(self):
        assert_equals(self.parent[0].display_value, 'foo | bar')
        assert_equals(self.parent[1].display_value, '')
        assert_equals(self.parent[2].display_value, 'WITH NAME | InBuilt')

    def test_editing(self):
        ctrl = ImportController(self.parent, self.parent[1]._import)
        ctrl.set_value('foo')
        self._assert_import(1, 'foo')
        assert_true(self.parent.dirty)

    def test_editing_with_args(self):
        ctrl = ImportController(self.parent, self.parent[0]._import)
        ctrl.set_value('bar', 'quux')
        self._assert_import(0, 'bar', ['quux'])
        assert_true(self.parent.dirty)
        ctrl.set_value('name', 'a1 | a2')
        self._assert_import(0, 'name', ['a1', 'a2'])

    def test_editing_with_alias(self):
        ctrl = ImportController(self.parent, self.parent[0]._import)
        ctrl.set_value('newname', '', 'namenew')
        self._assert_import(0, 'newname', exp_alias='namenew')
        ctrl.set_value('again')
        self._assert_import(0, 'again')

    def test_publishing_change(self):
        ctrl = ImportController(self.parent, self.parent[1]._import)
        ctrl.set_value('new name')
        self._test_listener('new name', 'resource', self.changed_import_listener)

    def test_publishing_remove(self):
        self.parent.delete(1)
        self._test_listener('resu', 'resource', self.removed_import_listener)
        self.parent.delete(0)
        self._test_listener('somelib', 'library', self.removed_import_listener, 1)

    def test_publish_adding_library(self):
        self.parent.add_library('name', 'argstr', None)
        self._test_listener('name', 'library', self.add_import_listener)

    def test_publish_adding_resource(self):
        self.parent.add_resource('path')
        self._test_listener('path', 'resource', self.add_import_listener)

    def test_publish_adding_variables(self):
        self.parent.add_variables('path', 'argstr')
        self._test_listener('path', 'variables', self.add_import_listener)

    def _test_listener(self, name, type, listener, index=0):
        data = listener.data[index]
        assert_equals(data.name, name)
        assert_equals(data.type, type)
        assert_equals(data.datafile, self.tcf_ctrl)
        assert_equals(self.import_listener.data[index].name, name)

    def _assert_import(self, index, exp_name, exp_args=[], exp_alias=''):
        item = self.parent[index]
        assert_equals(item.name, exp_name)
        assert_equals(item.args, exp_args)
        assert_equals(item.alias, exp_alias)


class ImportSettingsControllerTest(unittest.TestCase):

    def setUp(self):
        self.tcf = TestCaseFile()
        filectrl = TestCaseFileController(self.tcf)
        filectrl.resource_import_modified = Mock()
        self.ctrl = ImportSettingsController(filectrl, self.tcf.setting_table)

    def test_addding_library(self):
        self.ctrl.add_library('MyLib', 'Some | argu | ments', 'alias')
        self._assert_import('MyLib', ['Some', 'argu', 'ments'], 'alias')

    def test_adding_resource(self):
        self.ctrl.add_resource('/a/path/to/file.txt')
        self._assert_import('/a/path/to/file.txt')

    def test_adding_variables(self):
        self.ctrl.add_variables('varfile.py', 'an arg')
        self._assert_import('varfile.py', ['an arg'])

    def _assert_import(self, exp_name, exp_args=[], exp_alias=None):
        imp = self.tcf.setting_table.imports[-1]
        assert_equals(imp.name, exp_name)
        assert_equals(imp.args, exp_args)
        assert_true(self.ctrl.dirty)

    def test_creation(self):
        assert_true(self.ctrl._items is not None)


class VariablesControllerTest(unittest.TestCase):

    def setUp(self):
        self.tcf = TestCaseFile()
        self._add_var('${foo}', 'foo')
        self._add_var('@{bar}', ['b', 'a', 'r'])
        self.ctrl = VariableTableController(TestCaseFileController(self.tcf),
                                            self.tcf.variable_table)

    def _add_var(self, name, value):
        self.tcf.variable_table.add(name, value)

    def test_creation(self):
        assert_equals(self.ctrl[0].name, '${foo}')
        assert_equals(self.ctrl[1].name, '@{bar}')

    def test_adding_scalar(self):
        self.ctrl.add_variable('${blaa}', 'value')
        assert_true(self.ctrl.dirty)
        self._assert_var_in_model(2, '${blaa}', ['value'])

    def test_editing(self):
        self.ctrl[0].set_value('${blaa}', 'quux')
        self._assert_var_in_ctrl(0, '${blaa}', ['quux'])
        self.ctrl[1].set_value('@{listvar}', ['a', 'b', 'c'])
        self._assert_var_in_ctrl(1, '@{listvar}', ['a', 'b', 'c'])
        assert_true(self.ctrl.dirty)

    def _assert_var_in_ctrl(self, index, name, value):
        assert_equals(self.ctrl[index].name, name)
        assert_equals(self.ctrl[index].value, value)

    def _assert_var_in_model(self, index, name, value):
        assert_equals(self.tcf.variable_table.variables[index].name, name)
        assert_equals(self.tcf.variable_table.variables[index].value, value)


class MetadataListControllerTest(unittest.TestCase):

    def setUp(self):
        self.tcf = TestCaseFile()
        self.tcf.setting_table.add_metadata('Meta name', 'Some value')
        self.ctrl = MetadataListController(TestCaseFileController(self.tcf),
                                           self.tcf.setting_table)
        SETTINGS['metadata style'] = 'new'

    def test_creation(self):
        self._assert_meta_in_ctrl(0, 'Meta name', 'Some value')

    def test_editing(self):
        self.ctrl[0].set_value('New name', 'another value')
        self._assert_meta_in_model(0, 'New name', 'another value')
        assert_true(self.ctrl[0].dirty)

    def test_serialization(self):
        assert_equals(self._get_metadata(0).as_list(),
                      ['Metadata', 'Meta name', 'Some value'])

    def _assert_meta_in_ctrl(self, index, name, value):
        assert_equals(self.ctrl[index].name, name)
        assert_equals(self.ctrl[index].value, value)

    def _assert_meta_in_model(self, index, name, value):
        assert_equals(self._get_metadata(index).name, name)
        assert_equals(self._get_metadata(index).value, value)

    def _get_metadata(self, index):
        return self.tcf.setting_table.metadata[index]


class TestOldStyleMetadata(unittest.TestCase):

    def setUp(self):
        self.tcf = TestCaseFile()
        self.tcf.setting_table.add_metadata('Meta name', 'Some value')
        self.ctrl = MetadataListController(TestCaseFileController(self.tcf),
                                           self.tcf.setting_table)
        SETTINGS['metadata style'] = 'old'

    def tearDown(self):
        SETTINGS['metadata style'] = 'new'

    def test_old_style_serialization(self):
        assert_equals(self.tcf.setting_table.metadata[0].as_list(),
                      ['Meta: Meta name', 'Some value'])



class FakeListController(_WithListOperations):

    def __init__(self):
        self._itemslist = ['foo', 'bar', 'quux']
        self.dirty = False

    @property
    def _items(self):
        return self._itemslist

    def mark_dirty(self):
        self.dirty = True


class WithListOperationsTest(unittest.TestCase):

    def setUp(self):
        self._list_operations = FakeListController()

    def test_move_up(self):
        self._list_operations.move_up(1)
        assert_true(self._list_operations.dirty)
        self._assert_item_in(0, 'bar')
        self._assert_item_in(1, 'foo')

    def test_move_down(self):
        self._list_operations.move_down(0)
        assert_true(self._list_operations.dirty)
        self._assert_item_in(0, 'bar')
        self._assert_item_in(1, 'foo')

    def test_moving_first_item_up_does_nothing(self):
        self._list_operations.move_up(0)
        assert_false(self._list_operations.dirty)
        self._assert_item_in(0, 'foo')

    def test_moving_last_item_down_does_nothing(self):
        self._list_operations.move_down(2)
        assert_false(self._list_operations.dirty)
        self._assert_item_in(2, 'quux')

    def test_delete(self):
        self._list_operations.delete(0)
        self._assert_item_in(0, 'bar')

    def _assert_item_in(self, index, name):
        assert_equals(self._list_operations._items[index], name)


if __name__ == "__main__":
    unittest.main()
