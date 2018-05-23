# Copyright (C) 2018 Marco Barisione
# Copyright (C) 2018 Undo Ltd.

import os
import subprocess
import unittest

from mixin_scripts_repo import (
    ScriptsRepoMixin,
    CloneRepoMixin,
    #SubmoduleMixin,
    #CopiedFilesMixin,
    )

SIMPLE = '''\
int main() {
  if (a) {
  return a;
  }
  return 0;
}
'''

SIMPLE_FIXED = '''\
int main() {
  if (a) {
    return a;
  }
  return 0;
}
'''

SIMPLE_FIXED_COMMIT = '''\
--- /dev/null
+++ b/foo.c
@@ ... @@
+int main() {
+  if (a) {
+    return a;
+  }
+  return 0;
+}
'''

SIMPLE_NON_FIXED_COMMIT = '''\
--- /dev/null
+++ b/foo.c
@@ ... @@
+int main() {
+  if (a) {
+  return a;
+  }
+  return 0;
+}
'''


class HookTestCaseBase(ScriptsRepoMixin):
    '''
    Test the git hook script.
    '''

    def hook_call(self, *args):
        assert self.repo
        return self.repo.check_call(os.path.join('.', self.pre_commit_hook_path), *args)

    def hook_output(self, *args):
        assert self.repo
        return self.repo.check_output(os.path.join('.', self.pre_commit_hook_path), *args)

    def install(self, allow_errors=False):
        try:
            return True, self.hook_output('install')
        except subprocess.CalledProcessError as exc:
            if not allow_errors:
                raise
            return False, exc.output

    def test_install(self):
        res, output = self.install()
        self.assertTrue(res)
        self.assertEqual(output.strip(), 'Pre-commit hook installed.')

    def test_install_twice(self):
        self.install()

        res, _ = self.install(allow_errors=True)
        self.assertFalse(res)
        #self.assertEqual(output.strip(), 'The hook is already installed.')

    def test_install_already_exists(self):
        self.repo.write_file(os.path.join('.git', 'hooks', 'pre-commit'), '')

        res, _ = self.install(allow_errors=True)
        self.assertFalse(res)
        #self.assertEqual(output.strip(),
        #                 'There\'s already an existing pre-commit hook, but for something else.')

    def test_commit_no_errors(self):
        self.install()

        filename = 'foo.c'
        self.repo.write_file(filename, SIMPLE_FIXED)
        self.repo.add(filename)

        self.repo.commit()

    def test_commit_fix_errors(self):
        self.install()

        filename = 'foo.c'
        self.repo.write_file(filename, SIMPLE)
        self.repo.add(filename)

        old_head = self.repo.git_get_head()

        output = self.repo.commit(input_text='a\n')
        self.assertIn('The staged content is not formatted correctly.\n', output)
        self.assertIn('patching file {}'.format(filename), output)
        self.assertEqual(output.count('What would you like to do?'), 1)

        # The file on disk is updated.
        self.assertEqual(self.repo.read_file(filename), SIMPLE_FIXED)
        # There was a commit.
        self.assertNotEqual(old_head, self.repo.git_get_head())
        # The commit contains the fixed file.
        commit_diff = self.simplify_diff(self.repo.git_show())
        self.assertIn(SIMPLE_FIXED_COMMIT, commit_diff)

    def test_commit_force(self):
        self.install()

        filename = 'foo.c'
        self.repo.write_file(filename, SIMPLE)
        self.repo.add(filename)

        old_head = self.repo.git_get_head()

        output = self.repo.commit(input_text='f\n')
        self.assertEqual(output.count('What would you like to do?'), 1)
        self.assertIn('Will commit anyway!', output)
        self.assertIn('Press return to continue.', output)

        # The file on disk is unchanged.
        self.assertEqual(self.repo.read_file(filename), SIMPLE)
        # There was a commit.
        self.assertNotEqual(old_head, self.repo.git_get_head())
        # The commit contains the original non-fixed file.
        commit_diff = self.simplify_diff(self.repo.git_show())
        self.assertIn(SIMPLE_NON_FIXED_COMMIT, commit_diff)

    def test_commit_cancel(self):
        self.install()

        filename = 'foo.c'
        self.repo.write_file(filename, SIMPLE)
        self.repo.add(filename)

        old_head = self.repo.git_get_head()

        try:
            self.repo.commit(input_text='c\n')
            self.assertTrue(False)
        except subprocess.CalledProcessError as exc:
            output = exc.output

        self.assertEqual(output.count('What would you like to do?'), 1)
        self.assertIn('Commit aborted as requested.', output)

        # The file on disk is unchanged.
        self.assertEqual(self.repo.read_file(filename), SIMPLE)
        # There is no commit.
        self.assertEqual(old_head, self.repo.git_get_head())


class HookClonedTestCase(CloneRepoMixin,
                         HookTestCaseBase,
                         unittest.TestCase):
    pass


# Not working yet:

#class HookSubmoduleTestCase(SubmoduleMixin,
#                            HookTestCaseBase,
#                            unittest.TestCase):
#    pass


#class HookCopiedScriptsTestCase(CopiedFilesMixin,
#                                HookTestCaseBase,
#                                unittest.TestCase):
#    pass
