# Copyright (C) 2018 Marco Barisione
# Copyright (C) 2018 Undo Ltd.

import os
import shutil

from mixin_git import GitMixin
import testutils


class ScriptsRepoMixin(GitMixin):
    '''
    A mixin used to represent a git repository which contains the clang-format-related scripts.

    How the scripts end up in the repo is decided by derived classes.
    By using classes derived from this mixin, you can get your tests to run in various
    configuration.
    '''

    def __init__(self, *args, **kwargs):
        super(ScriptsRepoMixin, self).__init__(*args, **kwargs)

        self.repo = None
        self.scripts_dir = None

    def setUp(self):
        super(ScriptsRepoMixin, self).setUp()

        assert not self.repo
        assert not self.scripts_dir

        self.repo = self.config_repo()

        assert self.repo

        # If case we clone the current repo but there's unstaged content.
        self.update_scripts()

    def update_scripts(self):
        '''
        Overwrite the scripts in the repo with the current version (including uncommitted changes).
        '''
        assert self.repo

        src_dir = self.this_repo_path()
        with self.repo.work_dir():
            if self.scripts_dir:
                testutils.makedirs(self.scripts_dir)
            shutil.copy(os.path.join(src_dir, 'apply-format'), self.apply_format_path)
            shutil.copy(os.path.join(src_dir, 'git-pre-commit'), self.pre_commit_hook_path)

    def tearDown(self):
        super(ScriptsRepoMixin, self).tearDown()

        self.repo = None
        self.scripts_dir = None

    def config_repo(self):
        '''
        Configure a git repository containing the scripts.

        Derived classes need to overwrite this.

        If the derived class puts the script in a subdirectory, then it should set
        `self.scripts_dir` to the relative path of the subdirectory.

        Return value:
            The newly configured GitRepository instance.
        '''
        assert not self.repo
        raise Exception('This method needs to be overwritten by derived classes.')

    def _get_script_path(self, script_name):
        if self.scripts_dir:
            return os.path.join(self.scripts_dir, script_name)

        return script_name

    @property
    def apply_format_path(self):
        '''
        The path of the apply-format script, relative to the repository top level dir.
        '''
        return self._get_script_path('apply-format')

    @property
    def pre_commit_hook_path(self):
        '''
        The path of the git pre-commit hook script, relative to the repository top level dir.
        '''
        return self._get_script_path('git-pre-commit')

    def write_style(self, style_dict):
        content_list = ['{}: {}'.format(k, v) for k, v in style_dict.items()]
        content = '\n'.join(content_list)
        self.repo.write_file('.clang-format', content)


class CloneRepoMixin(ScriptsRepoMixin):
    '''
    A mixin representing a git repository cloned from this git repository.
    '''

    def config_repo(self):
        self.scripts_dir = '.'
        return self.clone_this_repo()

    def clone_this_repo(self):
        return self.clone_repo(self.this_repo_path())


class SubmoduleMixin(ScriptsRepoMixin):
    '''
    A mixin representing a git repository in which this git repository is added as a submodule.
    '''

    SUBMODULE_DIR = 'submodule'

    def config_repo(self):
        self.scripts_dir = self.SUBMODULE_DIR
        return self.new_repo_with_submodule()

    def new_repo_with_submodule(self):
        repo = self.new_repo()
        repo.git_check_output('submodule', 'add', self.this_repo_path(), self.SUBMODULE_DIR)
        repo.commit()
        return repo


class CopiedFilesMixin(ScriptsRepoMixin):
    '''
    A mixin representing a git repository in which the scripts from this git repository are
    directly copied.
    '''

    SCRIPTS_DIR = os.path.join('foo', 'bar', 'scripts')

    def config_repo(self):
        self.scripts_dir = self.SCRIPTS_DIR
        return self.new_repo_with_copied_scripts()

    def new_repo_with_copied_scripts(self):
        # The scripts will be copied by self.update_scripts.
        return self.new_repo()
