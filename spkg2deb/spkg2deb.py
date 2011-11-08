#!/usr/bin/env python
# -*- coding: utf-8 *-*
import os
import sys
import re
import argparse
import tempfile
import shutil
import platform
from spkg2deb.ex import CalledProcessError
from spkg2deb.settings import Settings
from spkg2deb.command import check_call
from spkg2deb.command import process_command
from spkg2deb.archive import expand_tarball

APP_VERSION = "0.2, Nov 6 2011"
# -better support for binary and source build methods for FEMhub
DISTRIB_ID = platform.linux_distribution()[0]
DISTRIB_RELEASE = platform.linux_distribution()[1]
DISTRIB_CODENAME = platform.linux_distribution()[2]
ARCH = platform.architecture()[0]

s = Settings()
femhub_deb = os.path.abspath(s.get_destination())
process_command(["mkdir", "-p", femhub_deb])
# create binary path for example ./femhub_deb/ubuntu/11.10/32bit/
inst_path_bin = os.path.abspath(os.path.join(femhub_deb, DISTRIB_ID.lower(), DISTRIB_RELEASE, ARCH))
process_command(["mkdir", "-p", inst_path_bin])
# create source path for example ./femhub_deb/ubuntu/source/
inst_path_src = os.path.abspath(os.path.join(femhub_deb, "source"))
process_command(["mkdir", "-p", inst_path_src])
PACKAGES_FAILED = []
PACKAGE_NAME = ""
VERSION = ""
AUTO_DEPS = True
BUILD_BINARY = False
BUILD_SOURCE = True


def get_script_path():
    return os.path.dirname(os.path.realpath(sys.argv[0]))


spkg2deb_home = get_script_path()


def process_command_quiet(args, cwd=None):
    if not isinstance(args, (list, tuple)):
        raise RuntimeError("args passed must be in a list")
    if s.get_debug() != "0":
        check_call(False, args, cwd=cwd)
    else:
        check_call(True, args, cwd=cwd)


def main():
    global AUTO_DEPS, BUILD_BINARY, BUILD_SOURCE
    print("")
    print("===========================================")
    print("FEMhub spkg to FEMhub deb packaging utility")
    print("===========================================")
    print("")
    print("ver.: " + APP_VERSION)
    print("")
    parser = argparse.ArgumentParser(description='Convert spkg to deb:')
    parser.add_argument('-b', '--binary', action='store_true',
    help='Builds only binary packages. Default is -s')
    parser.add_argument('-s', '--source', action='store_true',
    help='Builds only source packages.')
    parser.add_argument('-nodeps', '--nodeps', action='store_true',
    help='If you add this parameter to your command, it will not download' +
    ' any dependencies from apt-get repositories.')
    parser.add_argument('-dbg', '--debug', action='store_true',
    help='If you add this parameter to your command, it will overwrite debug' +
    ' from settings.xml and you can fix package dependencies quickly.')
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

    if args.debug == True:
        s.set_debug(True)

    if args.nodeps == True:
        AUTO_DEPS = False

    # default is true for both
    if args.binary == True and args.source == False:
        BUILD_BINARY = True
        BUILD_SOURCE = False
    elif args.binary == False and args.source == True:
        BUILD_BINARY = False
        BUILD_SOURCE = True
    elif args.binary == True and args.source == True:
        BUILD_BINARY = True
        BUILD_SOURCE = True

    if args.file != None:
        for file in args.file:
            if file.endswith(".spkg"):
                convert_file(file)
            else:
                print("File is not a spkg package! " + file)

    if args.dir != None:
        for dir in args.dir:
            for file in os.listdir(dir):
                if file.endswith(".spkg"):
                    convert_file(os.path.join(os.path.normpath(dir), file))

    for failed in PACKAGES_FAILED:
        print("Failed: " + failed)


def fix_src_path(src_path, file):
    retval = None
    f_src_path = os.path.join(src_path, file)
    if os.path.exists(f_src_path):
        retval = f_src_path
    return retval


def debianize_name(name):
    "make name acceptable as a Debian (binary) package name"
    name = name.replace('_', '')
    name = name.lower()
    return name


def source_debianize_name(name):
    "make name acceptable as a Debian source package name"
    name = name.replace('_', '')
    name = name.replace('.', '-')
    name = name.lower()
    return name


def debianize_version(name):
    "make name acceptable as a Debian package name"
    name = name.replace('_', '-')

    name = name.replace('.dev', '~dev')

    name = name.lower()
    return name


def install_deps(package):
    "Install missing dependencies silently."

    if AUTO_DEPS == False or BUILD_BINARY == False:
        return

    print("Installing dependencies for " + package)
    try:
        process_command(["sudo", "apt-get", "build-dep", package, "-y"])
    except:
        pass


def convert_file(file):
    global PACKAGE_NAME, VERSION
    print("Processing " + file)
    PACKAGE_NAME = os.path.basename(file.replace('.spkg', ''))
    PACKAGE_NAME = PACKAGE_NAME.split('-')

    if len(PACKAGE_NAME) == 2 and PACKAGE_NAME[1][0].isdigit():
        VERSION = PACKAGE_NAME[1]
    else:
        print("....filename does not contain version?")
        VERSION = s.get_version()
        print("....using default version from settings.xml: " + VERSION)

    PACKAGE_NAME = PACKAGE_NAME[0]
    working_dir = tempfile.mkdtemp()
    try:
        expand_tarball(os.path.abspath(file), cwd=working_dir)
    except:
            print("....Bad archive! Skipping file!")
            print("....removing tmp: " + working_dir)
            shutil.rmtree(working_dir)
            return

    dir = os.listdir(working_dir)
    working_dir_project = os.path.join(os.path.normpath(working_dir), dir[0])

    src_path = working_dir_project
    if os.path.exists(os.path.join(working_dir_project, "src")):
        src_path = os.path.join(working_dir_project, "src")
        # uncomment those 3 lines, if you want to disable dpkg dir name warnings
        #new_src = working_dir_project + os.sep + PACKAGE_NAME + "-" + VERSION
        #os.rename(src_path, new_src)
        #src_path = os.path.join(working_dir_project, new_src)

    f_spkg_install = None
    f_setup_py = None
    f_makefile = None
    f_configure = None
    f_config = None

    # look in package root
    for file in os.listdir(working_dir_project):
        if file == "spkg-install":
            f_spkg_install = os.path.join(working_dir_project, "spkg-install")
        elif file == "setup.py":
            f_setup_py = os.path.join(working_dir_project, "setup.py")
        elif file == "Makefile":
            f_makefile = os.path.join(working_dir_project, "Makefile")
        elif file == "configure":
            f_configure = os.path.join(working_dir_project, "configure")
        elif file == "config":
            f_config = os.path.join(working_dir_project, "config")

    # look in src_path in case it wasn't found in the root
    if f_setup_py == None and src_path != working_dir_project:
        "setup.py is not in package's root, but can be in src subdirectory!"
        f_setup_py = fix_src_path(src_path, "setup.py")
    if f_makefile == None and src_path != working_dir_project:
        f_makefile = fix_src_path(src_path, "Makefile")
    if f_configure == None and src_path != working_dir_project:
        f_configure = fix_src_path(src_path, "configure")
    if f_config == None and src_path != working_dir_project:
        f_config = fix_src_path(src_path, "config")

    if f_spkg_install != None:
        print("....Found spkg-install! Building deb package.")

        # ./configure or ./config is the first option
        # setup.py is the second option
        # custom Makefile is the last option as it will mostly fail
        if f_configure != None:
            install_deps(PACKAGE_NAME)
            PACKAGE_NAME = source_debianize_name(PACKAGE_NAME)
            VERSION = debianize_version(VERSION)
            try:
                if BUILD_BINARY == True:
                    print("....Found configure script.")
                    process_command_quiet(["./configure"], cwd=src_path)
                build_deb(working_dir, working_dir_project,
                                    src_path, f_setup_py)
            except:
                print("....Error in configure script! Skipping this package!")
        elif f_config != None:
            install_deps(PACKAGE_NAME)
            PACKAGE_NAME = source_debianize_name(PACKAGE_NAME)
            VERSION = debianize_version(VERSION)
            try:
                if BUILD_BINARY == True:
                    print("....Found config script.")
                    process_command_quiet(["./config"], cwd=src_path)
                build_deb(working_dir, working_dir_project,
                                    src_path, f_setup_py)
            except:
                print("....Error in configure script! Skipping this package!")

        elif f_setup_py != None:
            install_deps("python-" + PACKAGE_NAME)
            PACKAGE_NAME = source_debianize_name(PACKAGE_NAME)
            VERSION = debianize_version(VERSION)
            print("....Found setup.py => building deb control file.")
            generate_deb_from_python(working_dir, working_dir_project,
                                    src_path, f_setup_py)
        elif f_makefile != None:
            install_deps(PACKAGE_NAME)
            PACKAGE_NAME = source_debianize_name(PACKAGE_NAME)
            VERSION = debianize_version(VERSION)
            print("....Found custom Makefile script.")
            build_deb(working_dir, working_dir_project,
                                    src_path, f_setup_py)
        else:
            install_deps(PACKAGE_NAME)
            PACKAGE_NAME = source_debianize_name(PACKAGE_NAME)
            VERSION = debianize_version(VERSION)
            print("....No Makefile or setup.py found => build source .deb")
            generate_src_deb_from_source(working_dir, working_dir_project,
                                    src_path, f_setup_py)

    else:
        print("....No spkg-install found! Skipping this package!")

    print("....removing tmp: " + working_dir)
    shutil.rmtree(working_dir)


def tpl(fin_path, fout_path):
    fin = open(fin_path)
    fout = open(fout_path, "wt")
    for line in fin:
        line = line.replace("#{package}", PACKAGE_NAME)
        line = line.replace("#{source}", PACKAGE_NAME)
        line = line.replace("#{name}", s.get_name())
        line = line.replace("#{email}", s.get_email())
        line = line.replace("#{architecture}", s.get_architecture())
        line = line.replace("#{version}", VERSION)
        line = line.replace("#{homepage}", s.get_homepage())
        line = line.replace("#{description}", s.get_description())
        line = line.replace("#{depends}", s.get_depends())
        fout.write(line)
    fin.close()
    fout.close()

    os.chmod(fout_path, 0755)
    print("....generated " + fout_path)


def build_deb(working_dir, working_dir_project,
                                src_path, f_setup_py):
    if BUILD_BINARY == True:
        try:
            build_deb_binary(working_dir, working_dir_project, src_path, f_setup_py)
        except CalledProcessError as e:
            print e
            PACKAGES_FAILED.append(PACKAGE_NAME + "-" + VERSION + " (binary)")
    if BUILD_SOURCE == True:
        try:
            build_deb_source(working_dir, working_dir_project, src_path, f_setup_py)
        except CalledProcessError as e:
            print e
            PACKAGES_FAILED.append(PACKAGE_NAME + "-" + VERSION + " (source)")


def generate_src_deb_from_source(working_dir, working_dir_project,
                                src_path, f_setup_py):
    build_deb_source(working_dir, working_dir_project,
                                src_path, f_setup_py)


def build_deb_binary(working_dir, working_dir_project,
                            src_path, f_setup_py):
    debian_dir = os.path.join(src_path, "debian")
    process_command(["mkdir", "-p", debian_dir], cwd=src_path)
    tpl(os.path.join(spkg2deb_home, "control.bin.tpl"),
        os.path.join(debian_dir, "control"))
    tpl(os.path.join(spkg2deb_home, "rules.tpl"),
        os.path.join(debian_dir, "rules"))
    tpl(os.path.join(spkg2deb_home, "changelog.tpl"),
        os.path.join(debian_dir, "changelog"))

    try:
        process_command_quiet(["dpkg-buildpackage", "-rfakeroot", "-uc",
                            "-us", "-b"], cwd=src_path)
    except CalledProcessError:
        raise CalledProcessError("....making binaries failed! (bad Makefile or missing deps)")

    try:
        deb_file = PACKAGE_NAME + "_" + VERSION + "_all.deb"
        deb_renamed = PACKAGE_NAME + "-" + VERSION + ".deb"
        build_text = "....created binary package: "

        if (os.path.exists(os.path.join(working_dir_project, deb_file))):
            deb_file = os.path.join(working_dir_project, deb_file)
        else:
            deb_file = os.path.join(working_dir, deb_file)

        process_command(["cp",
            os.path.abspath(deb_file), os.path.join(inst_path_bin, deb_renamed)], cwd=working_dir)
        os.chmod(os.path.join(inst_path_bin, deb_renamed), 0664)
        print(build_text + os.path.basename(deb_renamed))

    except CalledProcessError:
        print("....error copying binary package to final destination!")


def build_deb_source(working_dir, working_dir_project,
                            src_path, f_setup_py):
    debian_dir = os.path.join(working_dir_project, "DEBIAN")
    process_command(["mkdir", "-p", debian_dir], cwd=working_dir_project)
    tpl(os.path.join(spkg2deb_home, "control.src.tpl"),
        os.path.join(debian_dir, "control"))
    tpl(os.path.join(spkg2deb_home, "rules.tpl"),
        os.path.join(debian_dir, "rules"))
    tpl(os.path.join(spkg2deb_home, "changelog.tpl"),
        os.path.join(debian_dir, "changelog"))

    process_command(["cp",
        os.path.join(spkg2deb_home, "preinst.spkg.tpl"),
        os.path.join(debian_dir, "preinst")], cwd=working_dir)
    os.chmod(os.path.join(debian_dir, "preinst"), 0755)
    print("....generated " + os.path.join(debian_dir, "preinst"))

    fin = open(os.path.join(working_dir_project, "spkg-install"))
    data = fin.read()
    fin.close()
    fout = open(os.path.join(debian_dir, "postinst"), "wt")
    data = re.sub("SPKG_LOCAL", "FEMHUB_LOCAL", data)
    data = re.sub("SAGE_LOCAL", "FEMHUB_LOCAL", data)
    data = re.sub("SAGE_ROOT", "FEMHUB_ROOT", data)
    fout.write(data)
    fout.close()
    os.chmod(os.path.join(debian_dir, "postinst"), 0755)
    print("....generated " + os.path.join(debian_dir, "postinst"))

    try:
        process_command_quiet(["dpkg-deb", "--build", working_dir_project], cwd=working_dir)
    except CalledProcessError:
        raise CalledProcessError("....making source package failed!")

    try:
        deb_file = PACKAGE_NAME + "-" + VERSION + ".deb"
        deb_renamed = PACKAGE_NAME + "-" + VERSION + ".deb"
        build_text = "....created source package: "

        if (os.path.exists(os.path.join(working_dir_project, deb_file))):
            deb_file = os.path.join(working_dir_project, deb_file)
        elif (os.path.exists(os.path.join(working_dir, deb_file))):
            deb_file = os.path.join(working_dir, deb_file)

        process_command(["cp",
            os.path.abspath(deb_file), os.path.join(inst_path_src, deb_renamed)], cwd=working_dir)
        os.chmod(os.path.join(inst_path_src, deb_renamed), 0664)
        print(build_text + os.path.basename(deb_renamed))

    except CalledProcessError:
        print("....error copying package to final destination!")
        print(working_dir_project)
        print(deb_file)


def generate_deb_from_python(working_dir, working_dir_project,
                            src_path, f_setup_py):
    try:
        # another bug fix for bad spkg folder structure, duh!
        f_setup_py_path = os.path.dirname(f_setup_py)

        #process_command(["find", ".", "-name", "'*.pyc'", "-delete"],
        #                cwd=f_setup_py_path)
        process_command(["python", "setup.py",
        "--command-packages=stdeb.command", "bdist_deb"],
        cwd=f_setup_py_path)
        if (os.path.exists(os.path.join(f_setup_py_path, "deb_dist"))):
            try:
                deb_file = get_stdeb_package_name(f_setup_py_path)
                process_command(["cp",
                    os.path.abspath(os.path.join(
                    f_setup_py_path, "deb_dist", deb_file)), inst_path_src],
                    cwd=f_setup_py_path)
                os.chmod(os.path.join(inst_path_src, deb_file), 0664)
                print("....created package: " + deb_file)
            except CalledProcessError:
                print("....error copying deb to final destination!")
        else:
            print("....stdb failed in creating deb! Missing deps for Makefile?")
            raise Exception
    except:
        print("....error in creating python deb using stdeb!")
        print("....proceeding in python => deb with brute force")
        debian_dir = os.path.join(working_dir_project, "DEBIAN")
        process_command(["mkdir", "-p", debian_dir], cwd=working_dir)
        tpl(os.path.join(spkg2deb_home, "control.py.tpl"),
            os.path.join(debian_dir, "control"))
        tpl(os.path.join(spkg2deb_home, "rules.tpl"),
            os.path.join(debian_dir, "rules"))
        tpl(os.path.join(spkg2deb_home, "changelog.tpl"),
            os.path.join(debian_dir, "changelog"))

        process_command(["cp",
            os.path.join(spkg2deb_home, "preinst.spkg.tpl"),
            os.path.join(debian_dir, "preinst")], cwd=working_dir)
        os.chmod(os.path.join(debian_dir, "preinst"), 0755)
        print("....generated " + os.path.join(debian_dir, "preinst"))
        process_command(["cp",
                        os.path.join(working_dir_project, "spkg-install"),
                        os.path.join(debian_dir, "postinst")], cwd=working_dir)
        os.chmod(os.path.join(debian_dir, "postinst"), 0755)
        print("....generated " + os.path.join(debian_dir, "postinst"))
        #deb_file = PACKAGE_NAME + "_" + VERSION + "_all.deb"
        deb_file = working_dir_project
        build_text = "....created sources package only: "
        process_command_quiet(["dpkg-deb", "--build", deb_file],
            cwd=working_dir_project)

        deb_file = deb_file + ".deb"
        if (os.path.exists(os.path.join(working_dir_project, deb_file))):
            deb_file = os.path.join(working_dir_project, deb_file)
        else:
            deb_file = os.path.join(working_dir, deb_file)

        process_command(["cp",
            os.path.abspath(deb_file), inst_path_src], cwd=working_dir)
        os.chmod(os.path.join(inst_path_src, deb_file), 0664)
        print(build_text + os.path.basename(deb_file))


def get_stdeb_control_path(src_path):
    deb_dist_dir = None
    if (os.path.exists(os.path.join(src_path, "deb_dist"))):
        for d in os.listdir(os.path.join(src_path, "deb_dist")):
                if os.path.isdir(
                                os.path.join(src_path, "deb_dist", d)
                                ) == True:
                    deb_dist_dir = d
    return deb_dist_dir


def get_stdeb_package_name(src_path):
    deb_file = None
    if (os.path.exists(os.path.join(src_path, "deb_dist"))):
        for f in os.listdir(os.path.join(src_path, "deb_dist")):
                if os.path.isfile(
                                os.path.join(src_path, "deb_dist", f)
                                ) == True and f.endswith(".deb"):
                    deb_file = f
    return deb_file


if __name__ == '__main__':
    main()
