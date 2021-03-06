#  Copyright 2008-2011 Nokia Siemens Networks Oyj
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

from robot import utils

from tags import Tags
from keyword import Keyword, Keywords
from modelobject import ModelObject


class TestCase(ModelObject):
    __slots__ = ['parent', 'name', 'doc', 'timeout']
    keyword_class = Keyword

    def __init__(self, name='', doc='', tags=None, timeout=''):
        self.parent = None
        self.name = name
        self.doc = doc
        self.tags = tags
        self.timeout = timeout
        self.keywords = []

    @utils.setter
    def tags(self, tags):
        return Tags(tags)

    @utils.setter
    def keywords(self, keywords):
        return Keywords(self.keyword_class, keywords, parent=self)

    @property
    def id(self):
        if not self.parent:
            return 't1'
        return '%s-t%d' % (self.parent.id, self.parent.tests.index(self)+1)

    @property
    def longname(self):
        if not self.parent:
            return self.name
        return '%s.%s' % (self.parent.longname, self.name)

    @property
    def critical(self):
        # TODO: yes/no -> True/False
        if not self.parent:
            return 'yes'
        return 'yes' if self.parent.criticality.test_is_critical(self) else 'no'

    def visit(self, visitor):
        visitor.visit_test(self)

