#!/usr/bin/env python
# -*- coding: utf-8 *-*
import os
import sys
import argparse
from spkg2deb.archive import make_tarball


def get_script_path():
    return os.path.dirname(os.path.realpath(sys.argv[0]))


def main():
    print("")
    print("=========================================")
    print("Create FEMhub package from project source")
    print("=========================================")
    print("")
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--dir', action='append',
    help='input directory containing source files')

    args = parser.parse_args()

    if args.dir == None:
        print("You must specify input source directory!\n")
        print("Type -h for help\n")
        exit(1)

    installScriptFound = False

    if args.dir != None:
        for dir in args.dir:
            for file in os.listdir(dir):
                if file == "spkg-install":
                    rewrite_file(os.path.join(dir, file))
                    installScriptFound = True

            try:
                if installScriptFound:
                    print("spkg-install found!")
                    generate_package(dir)
                else:
                    print("spkg-install not found, trying to autogenerate...")
                    generate_install_script(dir)
                    generate_package(dir)
            except RuntimeError as e:
                print(e)
                print('Skipping source: ' + dir)


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


def generate_package(dir):
    make_tarball(os.path.basename(dir) + ".spkg", os.path.abspath(dir))


def generate_install_script(dir):
    makeLines = []
    canBuild = False

    for entry in os.listdir(dir):
        if entry.startswith("cmake"):
            makeLines.append("cmake -DCMAKE_INSTALL_PREFIX=\"$FEMHUB_LOCAL\" .")
            makeLines.append("make")
            makeLines.append("make install")
            canBuild = True
            break
        elif entry.startswith("configure"):
            makeLines.append("./configure --prefix=\"$FEMHUB_LOCAL\"")
            makeLines.append("make")
            makeLines.append("make install")
            canBuild = True
            break
        elif entry.startswith("setup.py"):
            makeLines.append("python setup.py install")
            canBuild = True
            break

    if canBuild == False:
        for entry in os.listdir(dir):
            if entry.startswith("Makefile"):
                makeLines.append("make")
                makeLines.append("make install")
                canBuild = True
                break

    if canBuild == False:
        raise RuntimeError('Could not determine source build system!')

    fin = open(os.path.join(get_script_path(), "spkg-install.tpl"))
    lines = []
    for line in fin:
        lines.append(line)
    fin.close()

    spkgInstall = os.path.join(dir, "spkg-install")

    fout = open(spkgInstall, "w")
    for line in lines:
        fout.write(line)
    for line in makeLines:
        fout.write(line)
    fout.close()


if __name__ == '__main__':
    main()
