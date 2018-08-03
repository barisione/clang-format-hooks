# Copyright (C) 2017-2018 Marco Barisione
# Copyright (C) 2018      Undo Ltd.

import errno
import os


def makedirs(dir_path):
    '''
    Create a directory and all the intermediate parent directories.

    This behavers like `os.makedirs` but doesn't raise an exception if the
    directory already exists.
    '''
    try:
        os.makedirs(dir_path)
    except OSError as exc:
        if exc.errno != errno.EEXIST or not os.path.isdir(dir_path):
            raise


class WorkDir():
    '''
    Temporarily change the current working directory.

    This is supposed to be used to be used with a `with` block. Inside the
    block, the directory is changed, but the previous one is restored when
    the block exits.
    '''

    def __init__(self, new_work_dir):
        '''
        Initialize a `WorkDir`.

        new_work_dir:
        '''
        self._old_work_dir = None
        self._new_work_dir = new_work_dir

    def __enter__(self):
        assert self._old_work_dir is None
        assert self._new_work_dir is not None

        self._old_work_dir = os.getcwd()
        os.chdir(self._new_work_dir)

        return self

    def __exit__(self, exception_type, exception_value, traceback):
        assert self._old_work_dir is not None

        os.chdir(self._old_work_dir)
        self._old_work_dir = None


class EnvAdder():
    '''
    Add a directory to `$PATH`.

    This is supposed to be used to be used with a `with` block.
    '''

    def __init__(self, overwrite_env):
        '''
        Initialize an `EnvAdder`.

        overwrite_env:
            A dictionary of environment variables to overwrite.
        '''
        self.overwrite_env = overwrite_env
        self._saved = None

    def __enter__(self):
        assert self._saved is None

        self._saved = {}
        for name, value in self.overwrite_env.items():
            self._saved[name] = os.environ.get(name)
            os.environ[name] = value

        return self

    def __exit__(self, exception_type, exception_value, traceback):
        assert self._saved is not None

        for name, value in self._saved.items():
            if value is None:
                del os.environ[name]
            else:
                os.environ[name] = value

        self._saved = None
