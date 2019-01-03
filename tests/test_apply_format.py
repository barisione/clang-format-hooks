# Copyright (C) 2018 Marco Barisione
# Copyright (C) 2018 Undo Ltd.

import os
import subprocess
import unittest

import data

from mixin_scripts_repo import (
    ScriptsRepoMixin,
    ScriptsWorkTreeRepoMixin,
    CloneRepoMixin,
    SubmoduleMixin,
    CopiedFilesMixin,
    )


class FormatTestCaseBase():
    '''
    Test the apply-format script.
    '''

    def apply_format_call(self, *args):
        assert self.repo
        return self.repo.check_call(os.path.join('.', self.apply_format_path), *args)

    def apply_format_output(self, *args):
        assert self.repo
        return self.repo.check_output(os.path.join('.', self.apply_format_path), *args)

    def test_nothing(self):
        output = self.apply_format_output()
        self.assertEqual(output, '')

    def test_help(self):
        output = self.apply_format_output('--help')
        self.assertIn('SYNOPSIS', output)

    def test_invalid(self):
        try:
            self.apply_format_output('--foobar')
            self.assertTrue(False)
        except subprocess.CalledProcessError as exc:
            self.assertIn('Unknown argument', exc.output)

    def test_one_file(self):
        self.repo.write_file(data.FILENAME, data.CODE)
        self.repo.add(data.FILENAME)
        # There's nothing unstaged to format.
        output = self.apply_format_output()
        self.assertEqual(output, '')

        # But the stuff to format is staged.
        output = self.apply_format_output('--staged')
        self.assertEqual(self.simplify_diff(output), data.PATCH)

        # Adding more stuff doesn't check what's staged.
        self.repo.write_file(data.FILENAME, data.MODIFIED)
        output = self.apply_format_output('--staged')
        self.assertEqual(self.simplify_diff(output), data.PATCH)

        # Adding more stuff doesn't check what'
        # But adding more stuff will change the output.
        self.repo.add(data.FILENAME)
        output = self.apply_format_output('--staged')
        self.assertNotEqual(self.simplify_diff(output), data.PATCH)

        # Committing makes everythig goes away.
        self.repo.commit()
        output = self.apply_format_output()
        self.assertEqual(output, '')
        output = self.apply_format_output('--staged')
        self.assertEqual(output, '')

    def test_in_place_unstaged(self):
        # Add unstaged content.
        self.repo.write_file(data.FILENAME, '')
        self.repo.add(data.FILENAME)
        self.repo.write_file(data.FILENAME, data.CODE)
        output = self.apply_format_output()
        self.assertEqual(self.simplify_diff(output), data.PATCH)
        output = self.apply_format_output('--staged')
        self.assertEqual(output, '')

        # Fix the file in place.
        output = self.apply_format_output('-i')
        self.assertEqual(output, '')

        # The file should be fixed, so nothing left to format.
        output = self.apply_format_output()
        self.assertEqual(output, '')
        output = self.apply_format_output('--staged')
        self.assertEqual(output, '')

    def test_in_place_staged(self):
        # Add staged content.
        self.repo.write_file(data.FILENAME, data.CODE)
        self.repo.add(data.FILENAME)
        output = self.apply_format_output()
        self.assertEqual(output, '')
        output = self.apply_format_output('--staged')
        self.assertEqual(self.simplify_diff(output), data.PATCH)

        # Try fixing the file in place, but nothing should happen as --staged in not used.
        output = self.apply_format_output('-i')
        self.assertEqual(output, '')
        output = self.apply_format_output()
        self.assertEqual(output, '')
        output = self.apply_format_output('--staged')
        self.assertEqual(self.simplify_diff(output), data.PATCH)

        # Now try fixing in place the staged content.
        output = self.apply_format_output('-i', '--staged')
        self.assertEqual(output, '')

        # The file should be fixed, so nothing left to format.
        output = self.apply_format_output()
        self.assertEqual(output, '')
        output = self.apply_format_output('--staged')
        self.assertEqual(output, '')

    def test_in_place_staged_modified(self):
        # Write the original file and stage it.
        self.repo.write_file(data.FILENAME, data.CODE)
        self.repo.add(data.FILENAME)

        # Now modify it without staging it.
        self.repo.write_file(data.FILENAME, data.MODIFIED)

        # Fix the staged part.
        output = self.apply_format_output('--staged', '-i')
        self.assertEqual(output, '')

        # The staged part should be fixed, but not the other unstaged one.
        output = self.apply_format_output()
        self.assertEqual(self.simplify_diff(output), data.MODIFIED_PART_PATCH)
        output = self.apply_format_output('--staged')
        self.assertEqual(output, '')

    def test_two_files(self):
        # One empty file does nothing.
        self.repo.write_file(data.FILENAME, '')
        self.repo.add(data.FILENAME)
        output = self.apply_format_output('--staged')
        self.assertEqual(output, '')

        # Another empty file does nothing.
        self.repo.write_file(data.FILENAME_ALT, '')
        self.repo.add(data.FILENAME_ALT)
        output = self.apply_format_output('--staged')
        self.assertEqual(output, '')

        # If only one file contains content which needs formatting, then we only get that.
        self.repo.write_file(data.FILENAME, data.CODE)
        output = self.apply_format_output()
        self.assertEqual(self.simplify_diff(output), data.PATCH)

        # Two files need changes.
        self.repo.write_file(data.FILENAME_ALT, data.CODE)
        output = self.apply_format_output()
        douple_patch = data.PATCH + data.PATCH.replace(data.FILENAME, data.FILENAME_ALT)
        self.assertEqual(self.simplify_diff(output), douple_patch)

        # Stage the second file. Two need changes, one is staged the other isn't.
        self.repo.add(data.FILENAME_ALT)
        output = self.apply_format_output()
        self.assertEqual(self.simplify_diff(output), data.PATCH)
        output = self.apply_format_output('--cached') # --cached == --staged
        self.assertEqual(self.simplify_diff(output),
                         data.PATCH.replace(data.FILENAME, data.FILENAME_ALT))

        # Commit the second one. There's still the first file (unstaged) neeeding formatting.
        self.repo.commit()
        output = self.apply_format_output()
        self.assertEqual(self.simplify_diff(output), data.PATCH)
        output = self.apply_format_output('--staged')
        self.assertEqual(output, '')

    def test_files_on_cmd_line(self):
        # Write and add both.
        self.repo.write_file(data.FILENAME, data.CODE)
        self.repo.add(data.FILENAME)
        self.repo.write_file(data.FILENAME_ALT, data.CODE)
        self.repo.add(data.FILENAME_ALT)

        # Get the diff only for one file.
        output = self.apply_format_output('--staged', data.FILENAME)
        self.assertEqual(self.simplify_diff(output), data.PATCH)

    def test_pass_args_to_git(self):
        self.repo.write_file(data.FILENAME, data.CODE)
        self.repo.add(data.FILENAME)

        output = self.apply_format_output('--staged', '--', data.FILENAME)
        self.assertEqual(self.simplify_diff(output), data.PATCH)

        # Same but --staged is passed to git without going through our script.
        # Not very useful, just for testing.
        output = self.apply_format_output('--', '--staged', data.FILENAME)
        self.assertEqual(self.simplify_diff(output), data.PATCH)

        # "HEAD" is passed to git.
        output = self.apply_format_output('HEAD')
        self.assertEqual(self.simplify_diff(output), data.PATCH)

        output = self.apply_format_output('--', 'HEAD')
        self.assertEqual(self.simplify_diff(output), data.PATCH)

        # The second "--" is passed to git, so it splits revisions from file names.
        output = self.apply_format_output('--', '--', '--staged', data.FILENAME)
        # "git diff -- --WHATEVER FOO" just ignores --WHATEVER.
        self.assertEqual(output, '')


    def test_style_llvm(self):
        self.write_style({
            'BasedOnStyle': 'llvm',
            })

        self.repo.write_file(data.FILENAME, data.CODE)
        self.repo.add(data.FILENAME)
        output = self.apply_format_output('--staged', data.FILENAME)
        self.assertEqual(self.simplify_diff(output), data.PATCH)

    def test_style_webkit(self):
        self.write_style({
            'BasedOnStyle': 'WebKit',
            })

        self.repo.write_file(data.FILENAME, data.CODE)
        self.repo.add(data.FILENAME)
        output = self.apply_format_output('--staged', data.FILENAME)
        self.assertEqual(self.simplify_diff(output), data.PATCH_WEBKIT)

    def test_style_webkit_command_line(self):
        self.repo.write_file(data.FILENAME, data.CODE)
        self.repo.add(data.FILENAME)
        output = self.apply_format_output('--staged', data.FILENAME, '--style', 'WebKit')
        self.assertEqual(self.simplify_diff(output), data.PATCH_WEBKIT)

    def test_style_llvm_indent8(self):
        self.write_style({
            'BasedOnStyle': 'llvm',
            'IndentWidth': '8',
            })

        self.repo.write_file(data.FILENAME, data.CODE)
        self.repo.add(data.FILENAME)
        output = self.apply_format_output('--staged', data.FILENAME)
        self.assertEqual(self.simplify_diff(output), data.PATCH_LLVM_INDENT8)

    def test_invalid_config(self):
        self.write_style({
            'BasedOnStyle': 'llvm',
            'ThisIsAnInvalidKey': 'true',
            })

        self.repo.write_file(data.FILENAME, data.CODE)
        self.repo.add(data.FILENAME)

        # On old versions of clang-format an invalid config makes the program exit with
        # a 0 return code...
        try:
            output = self.apply_format_output('--staged', '--', data.FILENAME)
        except subprocess.CalledProcessError as exc:
            output = exc.output

        self.assertIn('unknown key', output)

    def test_whole_file(self):
        for opt in ('--whole-file', '-f'):
            self.repo.write_file(data.FILENAME, data.CODE)
            output = self.apply_format_output(opt, data.FILENAME)
            self.assertEqual(output, data.FIXED)


class FormatClonedTestCase(CloneRepoMixin,
                           ScriptsRepoMixin,
                           FormatTestCaseBase,
                           unittest.TestCase):
    pass


class FormatSubmoduleTestCase(SubmoduleMixin,
                              ScriptsRepoMixin,
                              FormatTestCaseBase,
                              unittest.TestCase):
    pass


class FormatCopiedScriptsTestCase(CopiedFilesMixin,
                                  ScriptsRepoMixin,
                                  FormatTestCaseBase,
                                  unittest.TestCase):
    pass


class FormatClonedWorkTreeTestCase(CloneRepoMixin,
                                   ScriptsWorkTreeRepoMixin,
                                   FormatTestCaseBase,
                                   unittest.TestCase):
    pass


class FormatSubmoduleWorkTreeTestCase(SubmoduleMixin,
                                      ScriptsWorkTreeRepoMixin,
                                      FormatTestCaseBase,
                                      unittest.TestCase):
    pass


class FormatCopiedScriptsWorkTreeTestCase(CopiedFilesMixin,
                                          ScriptsWorkTreeRepoMixin,
                                          FormatTestCaseBase,
                                          unittest.TestCase):
    pass
