#!/usr/bin/env python
# -*- coding: utf-8 *-*
import os
import re
import argparse
import tempfile
import shutil
from spkg2deb.archive import make_tarball
from spkg2deb.archive import expand_tarball
from spkg2deb.command import process_command


def main():
    print("")
    print("========================================")
    print("$SPKG_LOCAL to $FEMHUB_LOCAL rename tool")
    print("========================================")
    print("")
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', action='append',
    help='input.spkg' +
    ', You can also supply more files.' +
    ' Example: -f package1.spkg -f package2.spkg')
    parser.add_argument('-d', '--dir', action='append',
    help='input directory containing .spkg files' +
    ', You can also supply more directories.' +
    ' Example: -d dir1 -d dir2')

    args = parser.parse_args()

    if (args.file == None and args.dir == None):
        print("You must specify an input file or directory!\n")
        print("Type -h for help\n")
        exit(1)

    if args.file != None:
        for file in args.file:
            if file.endswith(".spkg"):
                abs_dir = os.path.abspath(os.path.normpath(os.path.dirname(file)))
                convert_archive(abs_dir, file)
            else:
                print("File is not a spkg package! " + file)

    if args.dir != None:
        for dir in args.dir:
            for file in os.listdir(dir):
                if file.endswith(".spkg"):
                    abs_dir = os.path.abspath(os.path.normpath(dir))
                    convert_archive(abs_dir, os.path.join(os.path.normpath(dir), file))


def rewrite_file(file):
    fin = open(file)
    lines = []
    for line in fin:
        line = line.replace("SPKG_LOCAL", "FEMHUB_LOCAL")
        line = line.replace("SAGE_LOCAL", "FEMHUB_LOCAL")
        line = line.replace("SAGE_ROOT", "FEMHUB_ROOT")
        line = line.replace("sage -sh", "femhub --shell")
        lines.append(line)
    fin.close()
    os.remove(file)
    fout = open(file, "w")
    for line in lines:
        fout.write(line)
    fout.close()


def convert_archive(dest_dir, spkg_file):
    working_dir = tempfile.mkdtemp()
    try:
        expand_tarball(os.path.abspath(spkg_file), cwd=working_dir)
    except:
            print(spkg_file)
            print("....Bad archive! Skipping file!")
            print("....removing tmp: " + working_dir)
            shutil.rmtree(working_dir)
            return

    dir = os.listdir(working_dir)
    working_dir_project = os.path.join(os.path.normpath(working_dir), dir[0])

    f_spkg_install = None

    # look in package root
    for file in os.listdir(working_dir_project):
        if file == "spkg-install":
            f_spkg_install = os.path.join(working_dir_project, "spkg-install")

    if f_spkg_install != None:
        rewrite_file(f_spkg_install)
        make_tarball(os.path.basename(spkg_file), os.path.basename(working_dir_project), cwd=working_dir)
        process_command(["cp", os.path.basename(spkg_file), dest_dir], cwd=working_dir)
        print("Processed: " + f_spkg_install)
    else:
        print("....No spkg-install found! Skipping this package!")

    print("....removing tmp: " + working_dir)
    shutil.rmtree(working_dir)


if __name__ == '__main__':
    main()
