# -*- coding: utf-8 *-*
import os
import shutil
import tempfile
import subprocess
from spkg2deb.command import process_command


def make_tarball(tarball_fname, directory, cwd=None):
    "create a tarball from a directory"
    if tarball_fname.endswith('.gz'):
        opts = 'czf'
    else:
        opts = 'cf'
    args = ['/bin/tar', opts, tarball_fname, directory]
    process_command(args, cwd=cwd)


def expand_tarball(tarball_fname, cwd=None):
    "expand a tarball"
    if tarball_fname.endswith('.gz'):
        opts = 'xzf'
    elif tarball_fname.endswith('.bz2'):
        opts = 'xjf'
    elif tarball_fname.endswith('.spkg'):
        opts = 'xjf'
    else:
        opts = 'xf'
    args = ['/bin/tar', opts, tarball_fname]
    process_command(args, cwd=cwd)


def expand_zip(zip_fname, cwd=None):
    "expand a zip"
    args = ['/usr/bin/unzip', zip_fname]
    # Does it have a top dir
    res = subprocess.Popen(
        [args[0], '-l', args[1]], cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    contents = []
    for line in res.stdout.readlines()[3:-2]:
        contents.append(line.split()[-1])
    commonprefix = os.path.commonprefix(contents)
    if not commonprefix:
        extdir = os.path.join(cwd, os.path.basename(zip_fname[:-4]))
        args.extend(['-d', os.path.abspath(extdir)])

    process_command(args, cwd=cwd)


def expand_sdist_file(sdist_file, cwd=None):
    lower_sdist_file = sdist_file.lower()
    if lower_sdist_file.endswith('.zip'):
        expand_zip(sdist_file, cwd=cwd)
    elif lower_sdist_file.endswith('.tar.bz2'):
        expand_tarball(sdist_file, cwd=cwd)
    elif lower_sdist_file.endswith('.tar.gz'):
        expand_tarball(sdist_file, cwd=cwd)
    else:
        raise RuntimeError('could not guess format of original sdist file')


def repack_tarball_with_debianized_dirname(orig_sdist_file,
                                            repacked_sdist_file,
                                            debianized_dirname,
                                            original_dirname):
    working_dir = tempfile.mkdtemp()
    expand_sdist_file(orig_sdist_file, cwd=working_dir)
    fullpath_original_dirname = os.path.join(working_dir, original_dirname)
    fullpath_debianized_dirname = os.path.join(working_dir, debianized_dirname)

    # ensure sdist looks like sdist:
    assert os.path.exists(fullpath_original_dirname)
    assert len(os.listdir(working_dir)) == 1

    if fullpath_original_dirname != fullpath_debianized_dirname:
        # rename original dirname to debianized dirname
        os.rename(fullpath_original_dirname,
                  fullpath_debianized_dirname)
    make_tarball(repacked_sdist_file, debianized_dirname, cwd=working_dir)
    shutil.rmtree(working_dir)
