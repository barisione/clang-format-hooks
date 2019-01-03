# Copyright (C) 2018 Marco Barisione
# Copyright (C) 2018 Undo Ltd.

import os
import re
import subprocess
import tempfile

import mixin_tempdir
import testutils


class GitRepository:
    '''
    A class representing a git repository.
    '''

    def __init__(self, repo_dir):
        '''
        Initialize a GitRepository

        repo_dir:
            The path to the directory where an initialized git repository is.
        '''
        self.repo_dir = repo_dir

    @property
    def git_dir(self):
        '''
        The path for the `.git` directory for this repository.

        NOTE: This is broken for submodules as we don't really need support for
        that at the moment!
        '''
        with self.work_dir():
            # Simple, this is a normal .git repo with a .git directory.
            if os.path.isdir('.git'):
                return os.path.abspath('.git')

            # A worktree or a submodule! Damn!
            with open('.git') as git_file:
                content = git_file.read().rstrip()
            intro = 'gitdir: '
            assert content.startswith(intro), \
                'Unexpected content of .git file: {}'.format(content)
            worktree_git_dir = content[len(intro):]

            # Now we have the git directory for this worktree's branch, it should
            # be something like PROJECT/.git/worktrees/WORKTREE-DIR-NAME.
            # We just rely on the path structure to extract the main dir, this is
            # good enough for tests.
            # Note that we ignore submodules for now as we don't really need to
            # support them.
            worktree_git_dir = os.path.normpath(worktree_git_dir)
            components = worktree_git_dir.split(os.path.sep)
            assert components[-2] == 'worktrees'
            # Everything before the worktrees directory.
            return os.path.sep.join(components[:-2])

    def work_dir(self):
        return testutils.WorkDir(self.repo_dir)

    def check_call(self, *args):
        with self.work_dir():
            return subprocess.check_call(args, stderr=subprocess.STDOUT)

    def check_output(self, *args, **kwargs):
        kwargs['stderr'] = subprocess.STDOUT
        kwargs['universal_newlines'] = True
        with self.work_dir():
            return subprocess.check_output(args, **kwargs)

    def git_check_call(self, *args):
        return self.check_call('git', *args)

    def git_check_output(self, *args):
        return self.check_output('git', *args)

    def abs_path_in_repo(self, rel_path):
        return os.path.join(self.repo_dir, rel_path)

    def add(self, rel_path):
        self.git_check_call('add', rel_path)

    def write_file(self, rel_path, content):
        abs_path = self.abs_path_in_repo(rel_path)
        with open(abs_path, 'w') as content_file:
            content_file.write(content)

    def read_file(self, rel_path):
        abs_path = self.abs_path_in_repo(rel_path)
        with open(abs_path, 'r') as content_file:
            return content_file.read()

    def commit(self, verify=True, input_text=None):
        args = ['-m', 'test']
        if not verify:
            args.append('--no-verify')

        tmp_path = None

        try:
            overwrite_env = {}
            if input_text is not None:
                tmp_path = tempfile.mktemp()
                if input_text:
                    with open(tmp_path, 'w') as tmp_file:
                        tmp_file.write(input_text)
                overwrite_env['PRE_COMMIT_HOOK_TTY'] = tmp_path

            with testutils.EnvAdder(overwrite_env):
                return self.git_check_output('commit', *args)

        finally:
            if tmp_path is not None:
                os.unlink(tmp_path)

    def git_show(self):
        return self.git_check_output('show')

    def git_get_head(self):
        return self.git_check_output('rev-parse', 'HEAD').strip()


class GitMixin(mixin_tempdir.TempDirMixin):
    '''
    Mixin which allow to manage git repositories.
    '''

    def new_repo(self):
        repo_dir = os.path.join(self.make_tmp_sub_dir(), 'new')
        subprocess.check_output(['git', 'init', repo_dir],
                                stderr=subprocess.STDOUT)
        repo = GitRepository(repo_dir)

        # This is just so there is at least one commit so git commands don't break
        # randomly.
        dummy = 'dummy'
        repo.write_file(dummy, 'Dummy file. Ignore this.')
        repo.add(dummy)
        repo.commit()

        return repo

    def clone_repo(self, original_repo):
        repo_dir = os.path.join(self.make_tmp_sub_dir(), 'cloned')
        subprocess.check_output(['git', 'clone', original_repo, repo_dir],
                                stderr=subprocess.STDOUT)
        return GitRepository(repo_dir)

    @staticmethod
    def this_repo_path():
        with testutils.WorkDir(os.path.dirname(__file__)):
            path = subprocess.check_output(['git', 'rev-parse', '--show-toplevel'],
                                           universal_newlines=True).strip()
            assert path
            assert os.path.isdir(path)
            return path

    @staticmethod
    def simplify_diff(diff):
        '''
        Given a unified-format diff, simplifies it only keeping changed lines and removing line
        numbers.

        diff:
            The diff text.
        Return value:
            A string contianing a simplified version of `diff`.
        '''
        line_count_re = re.compile('^@@.*@@$')

        result = []
        for line in diff.split('\n'):
            line = line.rstrip()

            if line_count_re.match(line):
                line = '@@ ... @@'

            if not line or line.startswith(' '):
                continue

            result.append(line)

        return '\n'.join(result) + '\n'
