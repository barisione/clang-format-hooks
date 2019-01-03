# Copyright (C) 2018 Marco Barisione
# Copyright (C) 2018 Undo Ltd.

import os
import shutil

from mixin_git import (
    GitMixin,
    GitRepository,
    )
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

        # This class's config_repo doesn't return, but the derived ones do.
        self.repo = self.config_repo() # pylint: disable=assignment-from-no-return

        assert self.repo

        # If case we cloned the current repo but there's unstaged content.
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
            shutil.copy(os.path.join(src_dir, 'git-pre-commit-format'), self.pre_commit_hook_path)

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
        return self._get_script_path('git-pre-commit-format')

    def write_style(self, style_dict):
        content_list = ['{}: {}'.format(k, v) for k, v in style_dict.items()]
        content = '\n'.join(content_list)
        self.repo.write_file('.clang-format', content)


class ScriptsWorkTreeRepoMixin(ScriptsRepoMixin):
    '''
    A mixin used to represent a git repository which uses work trees.

    How the scripts end up in the repo is decided by derived classes.
    By using classes derived from this mixin, you can get your tests to run in various
    configuration.
    '''

    def setUp(self):
        super(ScriptsWorkTreeRepoMixin, self).setUp()

        # Now the repo should be setup, but we create an alternative worktree dir
        # and use that one instead of the main one.

        assert self.repo

        # checkout -f in case there are modified scripts (copied by update_scripts).
        # We will re-update the scipts anyway later.
        self.repo.git_check_output('checkout', '-f')

        # We don't know on which branch we are. It could be master, a work branch
        # or some branch created by GitHub.
        # We need a branch to use for the worktree and a different one on which
        # the old repo should be, so we just create too.
        worktree_branch = 'other-for-worktree'
        self.repo.git_check_output('checkout', '-b', worktree_branch)
        main_repo_branch = 'main-repo'
        self.repo.git_check_output('checkout', '-b', main_repo_branch)

        worktree_branch_path = os.path.join(self.make_tmp_sub_dir(),
                                            'worktree-dir-for-branch--' + worktree_branch)
        self.repo.git_check_output('worktree', 'add', worktree_branch_path, worktree_branch)

        self.repo = GitRepository(worktree_branch_path)

        # The new module may have submodules, make sure they are synced.
        self.repo.git_check_output('submodule', 'update', '--init', '--recursive')

        # If case we cloned the current repo but there's unstaged content.
        self.update_scripts()


class CloneRepoMixin():
    '''
    A mixin representing a git repository cloned from this git repository.
    '''

    def config_repo(self):
        self.scripts_dir = '.'
        return self.clone_this_repo()

    def clone_this_repo(self):
        return self.clone_repo(self.this_repo_path())


class SubmoduleMixin():
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


class CopiedFilesMixin():
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
