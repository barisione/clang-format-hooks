# Copyright (C) 2017-2018 Marco Barisione
# Copyright (C) 2018      Undo Ltd.

import os
import shutil
import tempfile

import testutils


class TempDirMixin:
    '''
    Mixin taking care of having a temporary directory for various files which is
    cleaned in `tearDown`.
    '''

    def setUp(self):
        super(TempDirMixin, self).setUp()
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        super(TempDirMixin, self).tearDown()

        shutil.rmtree(self.tmp_dir)

    def make_tmp_sub_dir(self, intermediate=None):
        '''
        Create a directory inside this test's temporary directory.

        intermediate:
            If not None, the new directory will be a sub directory of intermediate
            which will be a subdirectory of the tests' temporary directory.
        Return value:
            The path to an existing empty temporary directory.
        '''
        if intermediate is None:
            base_dir = self.tmp_dir
        else:
            assert False, 'XXX UNUSED' # FIXME: REMOVE TIS OR THIS BRANCH
            base_dir = os.path.join(self.tmp_dir, intermediate)
            testutils.makedirs(base_dir)

        return tempfile.mkdtemp(dir=base_dir)
