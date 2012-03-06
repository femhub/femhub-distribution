#!/usr/bin/env python
# -*- coding: utf-8 *-*
import os
import sys
import argparse
from spkg2deb.archive import make_tarball
from spkg2deb.command import process_command

def get_script_path():
    return os.path.dirname(os.path.realpath(sys.argv[0]))


def main():
    print("")
    print("=========================================")
    print("Create FEMhub package from project source")
    print("=========================================")
    print("")
    print("Example: ./create_package.py -d /project/source -u user@femhub.org")
    print("")
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--dir', action='append',
    help='input directory containing source files'),
    parser.add_argument('-u', '--upload', action='append',
    help='-u {username} , uploads the package on femhub.org')

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

            if args.upload != None:
                for account in args.upload:
                    process_command(["scp", getPackageName(dir) + ".spkg",account + "@spilka.math.unr.edu:/var/www3/femhub.org/packages/femhub_st/femhub_spkg/"])
                

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


def getPackageName(dir):
    (head, tail) = os.path.split(dir)
    return tail


def generate_package(dir):
    if (dir.endswith("/")):
        dir = dir[:-1]

    finalArgument = getPackageName(dir)
    try:
        make_tarball(getPackageName(dir) + ".spkg", finalArgument)
    except:
        print("OK: tar did not find the path %s" % finalArgument)
        (head, tail) = os.path.split(dir)
        print("Found project directory under: %s" % head)
        print("Continuing...this may take a while!")
        make_tarball(getPackageName(dir) + ".spkg", finalArgument, head)
        process_command(["mv",os.path.join(head,getPackageName(dir) + ".spkg"),"./"]) 

    print("Created package using: tar -cjf " + getPackageName(dir) + ".spkg " + finalArgument) 

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
