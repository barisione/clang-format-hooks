# Copyright (C) 2018 Marco Barisione
# Copyright (C) 2018 Undo Ltd.

import os
import subprocess
import unittest

import data

from mixin_scripts_repo import (
    ScriptsRepoMixin,
    CloneRepoMixin,
    SubmoduleMixin,
    CopiedFilesMixin,
    )


class FormatTestCaseBase(ScriptsRepoMixin):
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
        filename = 'foo.c'
        self.repo.write_file(filename, data.CODE)
        self.repo.add(filename)
        # There's nothing unstaged to format.
        output = self.apply_format_output()
        self.assertEqual(output, '')

        # But the stuff to format is staged.
        output = self.apply_format_output('--staged')
        self.assertEqual(self.simplify_diff(output), data.PATCH)

        # Adding more stuff doesn't check what's staged.
        self.repo.write_file(filename, data.MODIFIED)
        output = self.apply_format_output('--staged')
        self.assertEqual(self.simplify_diff(output), data.PATCH)

        # Adding more stuff doesn't check what'
        # But adding more stuff will change the output.
        self.repo.add(filename)
        output = self.apply_format_output('--staged')
        self.assertNotEqual(self.simplify_diff(output), data.PATCH)

        # Committing makes everythig goes away.
        self.repo.commit()
        output = self.apply_format_output()
        self.assertEqual(output, '')
        output = self.apply_format_output('--staged')
        self.assertEqual(output, '')

    def test_in_place_unstaged(self):
        filename = 'foo.c'

        # Add unstaged content.
        self.repo.write_file(filename, '')
        self.repo.add(filename)
        self.repo.write_file(filename, data.CODE)
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
        filename = 'foo.c'

        # Add staged content.
        self.repo.write_file(filename, data.CODE)
        self.repo.add(filename)
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
        filename = 'foo.c'

        # Write the original file and stage it.
        self.repo.write_file(filename, data.CODE)
        self.repo.add(filename)

        # Now modify it without staging it.
        self.repo.write_file(filename, data.MODIFIED)

        # Fix the staged part.
        output = self.apply_format_output('--staged', '-i')
        self.assertEqual(output, '')

        # The staged part should be fixed, but not the other unstaged one.
        output = self.apply_format_output()
        self.assertEqual(self.simplify_diff(output), data.MODIFIED_PART_PATCH)
        output = self.apply_format_output('--staged')
        self.assertEqual(output, '')

    def test_two_files(self):
        filename1 = 'foo.c'
        filename2 = 'bar.c'

        # One empty file does nothing.
        self.repo.write_file(filename1, '')
        self.repo.add(filename1)
        output = self.apply_format_output('--staged')
        self.assertEqual(output, '')

        # Another empty file does nothing.
        self.repo.write_file(filename2, '')
        self.repo.add(filename2)
        output = self.apply_format_output('--staged')
        self.assertEqual(output, '')

        # If only one file contains content which needs formatting, then we only get that.
        self.repo.write_file(filename1, data.CODE)
        output = self.apply_format_output()
        self.assertEqual(self.simplify_diff(output), data.PATCH)

        # Two files need changes.
        self.repo.write_file(filename2, data.CODE)
        output = self.apply_format_output()
        douple_patch = data.PATCH + data.PATCH.replace(filename1, filename2)
        self.assertEqual(self.simplify_diff(output), douple_patch)

        # Stage the second file. Two need changes, one is staged the other isn't.
        self.repo.add(filename2)
        output = self.apply_format_output()
        self.assertEqual(self.simplify_diff(output), data.PATCH)
        output = self.apply_format_output('--cached') # --cached == --staged
        self.assertEqual(self.simplify_diff(output),
                         data.PATCH.replace(filename1, filename2))

        # Commit the second one. There's still the first file (unstaged) neeeding formatting.
        self.repo.commit()
        output = self.apply_format_output()
        self.assertEqual(self.simplify_diff(output), data.PATCH)
        output = self.apply_format_output('--staged')
        self.assertEqual(output, '')

    def test_files_on_cmd_line(self):
        filename1 = 'foo.c'
        filename2 = 'bar.c'

        # Write and add both.
        self.repo.write_file(filename1, data.CODE)
        self.repo.add(filename1)
        self.repo.write_file(filename2, data.CODE)
        self.repo.add(filename2)

        # Get the diff only for one file.
        output = self.apply_format_output('--staged', filename1)
        self.assertEqual(self.simplify_diff(output), data.PATCH)

    def test_dash_dash(self):
        filename = 'foo.c'

        self.repo.write_file(filename, data.CODE)
        self.repo.add(filename)
        output = self.apply_format_output('--staged', '--', filename)
        self.assertEqual(self.simplify_diff(output), data.PATCH)

        output = self.apply_format_output('--', '--staged', filename)
        # "git diff -- --invalid FOO" just ignores --invalid.
        self.assertEqual(output, '')

    def test_style_llvm(self):
        filename = 'foo.c'

        self.write_style({
            'BasedOnStyle': 'llvm',
            })

        self.repo.write_file(filename, data.CODE)
        self.repo.add(filename)
        output = self.apply_format_output('--staged', filename)
        self.assertEqual(self.simplify_diff(output), data.PATCH)

    def test_style_webkit(self):
        filename = 'foo.c'

        self.write_style({
            'BasedOnStyle': 'WebKit',
            })

        self.repo.write_file(filename, data.CODE)
        self.repo.add(filename)
        output = self.apply_format_output('--staged', filename)
        self.assertEqual(self.simplify_diff(output), data.PATCH_WEBKIT)

    def test_style_llvm_indent8(self):
        filename = 'foo.c'

        self.write_style({
            'BasedOnStyle': 'llvm',
            'IndentWidth': '8',
            })

        self.repo.write_file(filename, data.CODE)
        self.repo.add(filename)
        output = self.apply_format_output('--staged', filename)
        self.assertEqual(self.simplify_diff(output), data.PATCH_LLVM_INDENT8)

    def test_invalid_config(self):
        filename = 'foo.c'

        self.write_style({
            'BasedOnStyle': 'llvm',
            'ThisIsAnInvalidKey': 'true',
            })

        self.repo.write_file(filename, data.CODE)
        self.repo.add(filename)

        try:
            self.apply_format_output('--staged', '--', filename)
            self.assertTrue(False)
        except subprocess.CalledProcessError as exc:
            self.assertIn('unknown key', exc.output)

    def test_whole_file(self):
        filename = 'foo.c'

        for opt in ('--whole-file', '-f'):
            self.repo.write_file(filename, data.CODE)
            output = self.apply_format_output(opt, filename)
            self.assertEqual(output, data.FIXED)


class FormatClonedTestCase(CloneRepoMixin,
                           FormatTestCaseBase,
                           unittest.TestCase):
    pass


class FormatSubmoduleTestCase(SubmoduleMixin,
                              FormatTestCaseBase,
                              unittest.TestCase):
    pass


class FormatCopiedScriptsTestCase(CopiedFilesMixin,
                                  FormatTestCaseBase,
                                  unittest.TestCase):
    pass
