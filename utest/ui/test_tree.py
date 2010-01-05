#  Copyright 2008 Nokia Siemens Networks Oyj
#  
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#  
#      http://www.apache.org/licenses/LICENSE-2.0
#  
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

# This is needed to be able to create WX objects.

import unittest

from robot.utils.asserts import assert_equals, assert_none

from robotide.application import DataModel
from robotide.ui.actiontriggers import MenuBar, ToolBar, ShortcutRegistry
from robotide.ui.mainframe import ActionRegisterer
from resources import FakeSuite, FakeDirectorySuite, FakeUserKeyword,\
    FakeResource, FakeTestCase, PYAPP_REFERENCE

from robotide.ui import tree as st
st.FakeDirectorySuiteHandler = st.FakeUserKeywordHandler = \
    st.FakeSuiteHandler = st.FakeTestCaseHandler = \
    st.FakeResourceHandler = st.InitFileHandler
st.Editor = lambda *args: _FakeEditor()
from robotide.ui.tree import Tree
Tree._show_correct_editor = lambda self, x:None
Tree.get_active_datafile = lambda self: None
# wx needs to imported last so that robotide can select correct wx version.
import wx


class _FakeMainFrame(wx.Frame):
    _editor_panel = None
    def publish(self, *args):
        pass

class _FakeModel(DataModel):
    def __init__(self, suite=None, resources=[]):
        self.suite = suite
        self.resources = resources

class _FakeImageList(wx.ImageList):
    def __init__(self):
        wx.ImageList.__init__(self, 16, 16)
        self._image = _FakeImage(self)
    def __getitem__(self, name):
        return self._image

class _FakeImage(object):
    def __init__(self, imglist):
        self.normal = self.expanded = \
            imglist.Add(wx.ArtProvider_GetBitmap(wx.ART_FOLDER, wx.ART_OTHER, 
                                                 (16,16)))

class _FakeEditor(object):
    view = close = lambda *args: None


class _BaseSuiteTreeTest(unittest.TestCase):

    def setUp(self):
        frame = _FakeMainFrame(None)
        self._model = self._create_model()
        self._tree = Tree(frame, ActionRegisterer(MenuBar(frame), ToolBar(frame),
                                                  ShortcutRegistry(frame)))
        imgs =  _FakeImageList()
        self._tree._images = imgs
        self._tree.SetImageList(imgs)
        self._tree.populate(self._model)
        self._expand_all()

    def _create_model(self):
        suite = self._create_directory_suite('Top Suite', '/topsuite/__init__.html')
        suite.suites = [ self._create_file_suite('Sub Suite %d' % i, 'foo.html') 
                         for i in range(3) ]
        res = FakeResource()
        res.keywords.append(FakeUserKeyword(res, 'Resource Keyword'))
        return _FakeModel(suite, [res])

    def _create_directory_suite(self, name, path):
        return self._create_suite(FakeDirectorySuite, name, path)

    def _create_file_suite(self, name, path):
        suite = self._create_suite(FakeSuite, name, path)
        suite.tests.extend([ FakeTestCase(suite, '%s Fake Test %d' % (name, i))
                             for i in range(5) ])
        return suite

    def _create_suite(self, suite_class, name, path):
        suite = suite_class(name=name, path=path)
        suite.keywords.extend([ FakeUserKeyword(suite, '%s Fake UK %d' % (name, i))
                                for i in range(5) ])
        return suite

    def _expand_all(self):
        for node in self._tree._datafile_nodes[1:]:
            self._tree._expand_and_render_children(node)

    def _get_selected_label(self):
        return self._tree.GetItemText(self._tree.GetSelection())

    def _get_node(self, label):
        return self._tree._get_node_with_label(self._tree._root, label)

    def _select_node(self, label):
        self._tree.SelectItem(self._get_node(label))


class TestPopulating(_BaseSuiteTreeTest):

    def test_suite_count_and_names(self):
        assert_equals(len(self._tree._datafile_nodes), 5)
        for index, name in enumerate(['Top Suite'] + 
                                     ['Sub Suite %d' % i for i in range(3)]):
            assert_equals(self._tree.GetItemText(self._tree._datafile_nodes[index]),
                          name)

    def test_directory_suite_has_correct_subnodes(self):
        dir_suite = self._tree._datafile_nodes[0]
        item, cookie = self._tree.GetFirstChild(dir_suite)
        while item:
            item, cookie = self._tree.GetNextChild(dir_suite, cookie)
        nodes = ['Top Suite Fake UK 0', 'Top Suite Fake UK 1', 'Top Suite Fake UK 2',
                 'Top Suite Fake UK 3', 'Top Suite Fake UK 4', 'Sub Suite 0']
        self._assert_children(dir_suite, nodes)

    def test_file_suite_has_correct_subnodes(self):
        file_suite = self._tree._datafile_nodes[1]
        self._assert_children(file_suite, ['Sub Suite 0 Fake Test 0'])

    def _assert_children(self, parent, children):
        item, cookie = self._tree.GetFirstChild(parent)
        assert_equals(self._tree.GetItemText(item), children[0])
        for name in children[1:]:
            item, cookie = self._tree.GetNextChild(parent, cookie)
            assert_equals(self._tree.GetItemText(item), name)


class TestAddingItems(_BaseSuiteTreeTest):

    def test_adding_user_keyword(self):
        suite = self._model.suite
        new_uk = FakeUserKeyword(suite, 'New Fake UK', 'Something')
        self._tree.add_keyword(self._get_node(suite.name), new_uk)
        assert_equals(self._get_selected_label(), 'New Fake UK')

    def test_adding_test(self):
        suite = self._model.suite.suites[0]
        new_test = FakeTestCase(suite, 'New Fake Test', 'Test Doc')
        self._tree.add_test(self._get_node(suite.name), new_test)
        assert_equals(self._get_selected_label(), 'New Fake Test')
        
    def test_adding_suite(self):
        new_suite = FakeSuite('New Fake Suite')
        self._tree.add_suite(self._model.suite, new_suite)
        assert_equals(self._get_selected_label(), 'New Fake Suite')


class TestNodeSearchAndSelection(_BaseSuiteTreeTest):

    def test_topsuite_node_should_be_selected_by_default(self):
        assert_equals(self._get_selected_label(), 'Top Suite')

    def test_searching_matching_uk_node(self):
        self._select_and_assert_selection(self._model.suite.keywords[0])
        self._select_and_assert_selection(self._model.suite.suites[1].keywords[2])

    def _select_and_assert_selection(self, uk):
        self._tree.select_user_keyword_node(uk)
        assert_equals(self._get_selected_label(), uk.name)

    def test_get_active_suite_or_resource(self):
        exp = [('Top Suite Fake UK 2', 'Top Suite'), 
               ('Sub Suite 1 Fake Test 1', 'Sub Suite 1'),
               ('Resource Keyword', 'Fake Resource')]
        for node, parent_name in exp:
            self._select_node_and_assert_parent(node, parent_name)

    def _select_node_and_assert_parent(self, label, expected_parent_name):
        self._select_node(label)
        suite_or_resource = self._tree.get_selected_datafile()
        assert_equals(suite_or_resource.name, expected_parent_name)


class TestNodeRemoval(_BaseSuiteTreeTest):

    def test_removing_user_keyword(self):
        name = self._model.suite.suites[1].keywords[1].name
        root = self._tree._root
        self._tree.delete_node(self._tree._get_node_with_label(root, name))
        assert_none(self._tree._get_node_with_label(root, name))


class TestNavigationHistory(_BaseSuiteTreeTest):

    def test_go_back_one_level(self):
        self._select_node('Top Suite Fake UK 2')
        self._go_back_and_assert_selection('Top Suite')

    def test_go_back_two_levels(self):
        nodes = ['Top Suite Fake UK 1', 'Sub Suite 1', 'Sub Suite 1 Fake UK 0']
        for name in nodes:
            self._select_node(name)
        nodes.reverse()
        for name in nodes[1:]:
            self._go_back_and_assert_selection(name)

    def test_it_is_not_possible_to_go_back_farther_than_history(self):
        nodes = ['Top Suite Fake UK 1', 'Sub Suite 1', 'Sub Suite 1 Fake UK 0']
        for name in nodes:
            self._select_node(name)
        nodes.reverse()
        for name in nodes[1:] + ['Top Suite']:
            self._go_back_and_assert_selection(name)
        self._go_back_and_assert_selection('Top Suite')

    def test_go_back_with_selecting_in_between(self):
        nodes = ['Top Suite Fake UK 1', 'Sub Suite 1', 'Sub Suite 1 Fake UK 0']
        for name in nodes:
            self._select_node(name)
        self._go_back_and_assert_selection('Sub Suite 1')
        self._select_node('Sub Suite 2 Fake UK 0')
        self._go_back_and_assert_selection('Sub Suite 1')

    def test_go_forward(self):
        nodes = ['Top Suite Fake UK 1', 'Sub Suite 1', 'Sub Suite 1 Fake UK 0']
        for name in nodes:
            self._select_node(name)
        for _ in range(3):
            self._tree.OnGoBack(None)
        for name in nodes:    
            self._go_forward_and_assert_selection(name)

    def test_go_back_and_forward_between_suite_and_resource(self):
        nodes = ['Top Suite Fake UK 0', 'Resource Keyword', 'Sub Suite 0 Fake UK 2']
        for name in nodes:
            self._select_node(name)
        self._go_back_and_assert_selection('Resource Keyword')
        self._go_back_and_assert_selection('Top Suite Fake UK 0')
        self._go_forward_and_assert_selection('Resource Keyword')
        self._go_forward_and_assert_selection('Sub Suite 0 Fake UK 2')

    def _go_back_and_assert_selection(self, expected_selection):
        self._tree.OnGoBack(None)
        assert_equals(self._get_selected_label(), expected_selection)

    def _go_forward_and_assert_selection(self, expected_selection):
        self._tree.OnGoForward(None)
        assert_equals(self._get_selected_label(), expected_selection)


class TestRefreshingDataNode(_BaseSuiteTreeTest):

    def test_refreshing_suite(self):
        orig_node_lenght = len(self._tree._datafile_nodes)
        new_name = 'Modified name'
        suite = self._model.suite.suites[0]
        suite.tests[0].rename(new_name)
        self._tree.refresh_datafile(suite, None)
        self._expand_all()
        snode = self._get_node(suite.name)
        tnode = self._tree.GetFirstChild(snode)[0]
        assert_equals(self._tree.GetItemText(tnode), new_name)
        assert_equals(orig_node_lenght, len(self._tree._datafile_nodes))

    def test_refreshing_resource(self):
        orig_node_lenght = len(self._tree._datafile_nodes)
        new_name = 'Ninjaed Uk Name'
        resource = self._model.resources[0]
        resource.keywords[0].rename(new_name)
        self._tree.refresh_datafile(resource, None)
        self._expand_all()
        rnode = self._get_node(resource.name)
        knode = self._tree.GetFirstChild(rnode)[0]
        assert_equals(self._tree.GetItemText(knode), new_name)
        assert_equals(orig_node_lenght, len(self._tree._datafile_nodes))


if __name__ == '__main__':
    unittest.main()