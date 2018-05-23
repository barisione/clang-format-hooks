#! /usr/bin/env python3
#
# Copyright (C) 2017-2018 Marco Barisione
# Copyright (C) 2018      Undo Ltd.

import os
import sys
import unittest


# Keep this ordered from the fast and more low level ones to the ones which
# require a full image build/run/etc.
ALL_TESTS = [
    'test_apply_format',
    'test_hook',
    ]


def main(argv):
    '''
    Run tests with the specified command line options.

    argv:
        The arguments to use to run tests, for instance `sys.argv`. If no tests are specified,
        then all tests are run.
    Return value:
        True if all the specified tests passed, False oterwise.
    '''
    has_test_name = False
    for arg in argv[1:]:
        if not arg.startswith('-'):
            has_test_name = True

    if not has_test_name:
        # No test name was explicitly passed, so we just run everything.
        argv.extend(ALL_TESTS)

    # We use an environment variable as it's the most convenient way of setting the option
    # when executing make.
    if os.environ.get('V'):
        # Add -v after the script name.
        argv.insert(1, '-v')

    # To avoid adding "tests." in front of all the modules, we just change directory to the
    # test one and add the top-level directory to the paths so karton can be imported easily.
    #os.chdir('tests')

    # Let unittest run the tests as normal.
    test_program = unittest.main(module=None, exit=False, argv=argv)
    return test_program.result.wasSuccessful()


if __name__ == '__main__':
    if not main(sys.argv):
        raise SystemExit(1)
