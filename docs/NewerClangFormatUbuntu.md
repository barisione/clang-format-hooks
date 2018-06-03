Installing `clang-format` 6 on Ubuntu
=====================================

Some versions of Ubuntu have a very old `clang-format`. You can install a newer one (version 6.0) following these instructions.

For Ubuntu 16.04 (Xenial) add this to `/etc/apt/sources.list`:

```
deb http://apt.llvm.org/xenial/ llvm-toolchain-xenial-6.0 main
```

For other versions check [apt.llvm.org](http://apt.llvm.org/).

In a terminal, execute these commands:

```
$ # Add the GPG key for the repository.
$ wget -O - http://apt.llvm.org/llvm-snapshot.gpg.key | sudo apt-key add -
$ # Install clang-format
$ apt-get update
$ apt-get install clang-format-6.0
$ # Make /usr/bin/clang-format point to the newly installed one.
$ update-alternatives --install /usr/bin/clang-format clang-format /usr/bin/clang-format-6.0 100
```
