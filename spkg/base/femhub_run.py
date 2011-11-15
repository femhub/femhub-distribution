#! /usr/bin/env python

from time import sleep
from glob import glob
from os.path import expandvars
from optparse import OptionParser
import tempfile
import os
import sys
import subprocess
import time
import platform
import shutil

version = "1.0"
release_date = "November 6, 2011"

# -better support for binary and source build methods for FEMhub
DISTRIB_ID = platform.linux_distribution()[0]
DISTRIB_RELEASE = platform.linux_distribution()[1]
DISTRIB_CODENAME = platform.linux_distribution()[2]
ARCH = platform.architecture()[0]


def get_root_path():
    return os.environ.get("FEMHUB_ROOT")


http_host = "http://femhub.org/stpack/"
#http_host = "http://localhost/"
http_deb_bin_path = "femhub_deb/" + DISTRIB_ID.lower() + "/" + DISTRIB_RELEASE + "/" + ARCH + "/"
http_deb_src_path = "femhub_deb/source/"
http_spkg_path = "femhub_spkg/"
local_pkg_path = get_root_path() + os.sep + "spkg" + os.sep + "standard"
FEMHUB_LOCAL = get_root_path() + os.sep + "local"
USE_BINARY_DEB = False

class CmdException(Exception):
    pass


class PackageBuildFailed(Exception):
    pass


class PackageNotFound(Exception):
    pass


def main():
    create_local_bash()
    systemwide_python = (os.environ["FEMHUB_SYSTEMWIDE_PYTHON"] == "yes")
    if systemwide_python:
        print """\
***************************************************
FEMhub is not installed. Running systemwide Python.
Only use this mode to install FEMhub.
***************************************************"""

    parser = OptionParser(usage="[options] args")
    parser.add_option("-i", "--install",
            action="store", type="str", dest="install", metavar="PACKAGE",
            default="", help="install a spkg package")
    parser.add_option("-u", "--uninstall",
            action="store", type="str", dest="uninstall", metavar="PACKAGE",
            default="", help="uninstall a spkg package")
    parser.add_option("-f", "--force",
            action="store_true", dest="force",
            default=False, help="force the installation")
    parser.add_option("-d", "--download_packages",
            action="store_true", dest="download",
            default=False, help="download standard spkg packages")
    parser.add_option("-b", "--build",
            action="store_true", dest="build",
            default=False, help="build FEMhub")
    parser.add_option("-j",
            action="store", type="int", dest="cpu_count", metavar="NCPU",
            default=0, help="number of cpu to use (0 = all)")
    parser.add_option("--shell",
            action="store_true", dest="shell",
            default=False, help="starts a FEMhub shell")
    parser.add_option("-s", "--script",
            action="store", type="str", dest="script", metavar="SCRIPT",
            default=None, help="runs '/bin/bash SCRIPT' in a FEMhub shell")
    parser.add_option("--python",
            action="store", type="str", dest="python", metavar="SCRIPT",
            default=None, help="runs 'python SCRIPT' in a FEMhub shell")
    parser.add_option("--unpack",
            action="store", type="str", dest="unpack", metavar="PACKAGE",
            default=None, help="unpacks the PACKAGE into the 'devel/' dir")
    parser.add_option("--pack",
            action="store", type="str", dest="pack", metavar="PACKAGE",
            default=None, help="creates 'devel/PACKAGE.spkg' from 'devel/PACKAGE'")
    parser.add_option("--devel-install",
            action="store", type="str", dest="devel_install", metavar="PACKAGE",
            default=None, help="installs 'devel/PACKAGE' into FEMhub directly")
    parser.add_option("--create-package",
            action="store", type="str", dest="create_package",
            metavar="PACKAGE", default=None,
            help="creates 'PACKAGE.spkg' in the current directory using the official git repository sources")
    parser.add_option("--upload-package",
            action="store", type="str", dest="upload_package",
            metavar="PACKAGE", default=None,
            help="upload 'PACKAGE.spkg' from the current directory to the server (for FEMhub developers only)")
    parser.add_option("--release-binary",
            action="store_true", dest="release_binary",
            default=False, help="Creates a binary release using the current state (for FEMhub developers only)")
    parser.add_option("--lab",
            action="store_true", dest="run_lab",
            default=False, help="Runs lab(auth=False)")

    options, args = parser.parse_args()
    if len(args) == 1:
        arg, = args
        if arg == "update":
            command_update()
            return
        elif arg == "list":
            command_list()
            return
        print "Unknown command"
        sys.exit(1)
    elif len(args) == 2:
        arg1, arg2 = args
        if arg1 == "install":
            try:
                setup_cpu(options.cpu_count)
                install_package(arg2, force_install=options.force)
            except PackageBuildFailed:
                pass
            return
        print "Unknown command"
        sys.exit(1)
    elif len(args) == 0:
        pass
    else:
        print "Too many arguments"
        sys.exit(1)

    if options.download:
        #download_spkg_packages()
        #return
        setup_cpu(options.cpu_count)
        download_packages()
        return
    if options.install:
        try:
            setup_cpu(options.cpu_count)
            install_package(options.install, force_install=options.force)
        except PackageBuildFailed:
            pass
        return
    if options.uninstall:
        try:
            uninstall_package(options.uninstall)
        except:
            pass
        return
    if options.build:
        build(cpu_count=options.cpu_count)
        return
    if options.shell:
        print "Type CTRL-D to exit the FEMhub shell."
        cmd("cd $CUR; /bin/bash --rcfile $FEMHUB_ROOT/spkg/base/femhub-shell-rc")
        return
    if options.script:
        setup_cpu(options.cpu_count)
        try:
            cmd("cd $CUR; /bin/bash " + options.script)
        except CmdException:
            print "FEMhub script exited with an error."
        return
    if options.python:
        cmd("cd $CUR; /usr/bin/env python " + options.python)
        return
    if options.unpack:
        pkg = pkg_make_absolute(options.unpack)
        print "Unpacking '%(pkg)s' into 'devel/'" % {"pkg": pkg}
        cmd("mkdir -p $FEMHUB_ROOT/devel")
        cmd("cd $FEMHUB_ROOT/devel; tar xjf %s" % pkg)
        return
    if options.pack:
        dir = options.pack
        if not os.path.exists(dir):
            dir = expandvars("$FEMHUB_ROOT/devel/%s" % dir)
        if not os.path.exists(dir):
            raise Exception("Unknown package to pack")
        dir = os.path.split(dir)[1]
        print "Creating devel/%(dir)s.spkg from devel/%(dir)s" % {"dir": dir}
        cmd("cd $FEMHUB_ROOT/devel; tar cjf %(dir)s.spkg %(dir)s" % \
                {"dir": dir})
        return
    if options.devel_install:
        dir = options.devel_install
        if not os.path.exists(dir):
            dir = expandvars("$FEMHUB_ROOT/devel/%s" % dir)
        if not os.path.exists(dir):
            raise Exception("Unknown package to pack")
        dir = os.path.normpath(dir)
        dir = os.path.split(dir)[1]
        print "Installing devel/%(dir)s into FEMhub" % {"dir": dir}
        cmd("mkdir -p $FEMHUB_ROOT/spkg/build/")
        cmd("rm -rf $FEMHUB_ROOT/spkg/build/%(dir)s" % {"dir": dir})
        cmd("cp -r $FEMHUB_ROOT/devel/%(dir)s $FEMHUB_ROOT/spkg/build/" % \
                {"dir": dir})
        setup_cpu(options.cpu_count)
        cmd("cd $FEMHUB_ROOT/spkg/build/%(dir)s; /bin/bash spkg-install" % \
                {"dir": dir})
        cmd("rm -rf $FEMHUB_ROOT/spkg/build/%(dir)s" % {"dir": dir})
        return
    if options.create_package:
        create_package(options.create_package)
        return
    if options.upload_package:
        upload_package(options.upload_package)
        return
    if options.release_binary:
        release_binary()
        return
    if options.run_lab:
        run_lab(auth=False)
        return

    if systemwide_python:
        parser.print_help()
    else:
        start_femhub()


def setup_cpu(cpu_count):
    if cpu_count == 0:
        try:
            import multiprocessing
            cpu_count = multiprocessing.cpu_count() + 1
        except ImportError:
            cpu_count = 1
    if cpu_count > 1:
        os.environ["MAKEFLAGS"] = "-j %d" % cpu_count
    return cpu_count


def cmd(s, capture=False):
    s = expandvars(s)
    if capture:
        p = subprocess.Popen(s, shell=True, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT)
        output = p.communicate()[0]
        r = p.returncode
    else:
        output = None
        r = os.system(s)
    if r != 0:
        raise CmdException("Command '%s' failed with err=%d." % (s, r))
    return output


def check_call(quiet, *popenargs, **kwargs):
    if quiet == True:
        fnull = open(os.devnull, 'w')
        retcode = subprocess.call(stdout=fnull, stderr=fnull,
                                    *popenargs, **kwargs)
        fnull.close()
    else:
        retcode = subprocess.call(*popenargs, **kwargs)
    if retcode == 0:
        return
    raise CmdException(retcode)


def process_command(args, cwd=None):
    if not isinstance(args, (list, tuple)):
        raise RuntimeError("args passed must be in a list")
    check_call(False, args, cwd=cwd)


def process_command_quiet(args, cwd=None):
    if not isinstance(args, (list, tuple)):
        raise RuntimeError("args passed must be in a list")
    check_call(True, args, cwd=cwd)


def create_package(package):
    packages = {
        "libfemhub": "git://github.com/hpfem/libfemhub.git",
        "femhub_online_lab_sdk": "git://github.com/femhub/femhub-online-lab-sdk.git",
        "phaml": "git://github.com/hpfem/phaml.git",
        "arpack": "git://github.com/hpfem/arpack.git",
        "mesheditorflex": "git://github.com/femhub/mesheditor-flex.git",
        "cython": "git://github.com/hpfem/cython.git",
        "hermes2d": "git://github.com/hpfem/hermes.git",
        }
    if package not in packages:
        raise Exception("Unknown package")
    git_repo = packages[package]
    a = git_repo.rfind("/") + 1
    b = git_repo.rfind(".git")
    dir_name = git_repo[a:b]
    print "Creating a package in the current directory."
    print "Package name:", package
    print "Git repository:", git_repo
    tmp = tempfile.mkdtemp()
    print "Using temporary directory:", tmp
    cur = cmd("echo $CUR", capture=True).strip()
    cmd("cd %s; git clone %s" % (tmp, git_repo))
    commit = cmd("cd %s/%s; git rev-parse HEAD" % (tmp, dir_name),
            capture=True).strip()
    sha = commit[:7]
    if os.path.exists("%s/%s/spkg-prepare" % (tmp, dir_name)):
        print "spkg-prepare found, running it..."
        cmd("cd %s/%s; sh spkg-prepare" % (tmp, dir_name))
    # hermes packages require special handling:
    if package == "hermes2d":
        # The spkg-prepare script is in the "hermes2d" subdirectory:
        print "Preparing the hermes2d package..."
        cmd("cd %s/%s; rm -rf hermes1d hermes3d doc .git" % (tmp, dir_name))
        cmd("cd %s/%s; cp hermes2d/spkg-install ." % (tmp, dir_name))
    datetimestr = time.strftime("%Y%m%d%M%S")
    new_dir_name = "%s-%s_%s" % (package, datetimestr, sha)
    pkg_filename = "%s.spkg" % (new_dir_name)
    cmd("cd %s; mv %s %s" % (tmp, dir_name, new_dir_name))
    print "Creating the spkg package..."
    cmd("cd %s; tar cjf %s %s" % (tmp, pkg_filename, new_dir_name))
    cmd("cp %s/%s %s/%s" % (tmp, pkg_filename, cur, pkg_filename))
    print
    print "Package created: %s" % (pkg_filename)


def upload_package(package):
    cmd("cd $CUR; scp %s spilka.math.unr.edu:/var/www3/femhub.org/packages/femhub_st/" % (package))
    print "Package uploaded: %s" % (package)


def release_binary():
    tmp = tempfile.mkdtemp()
    femhub_dir = "femhub-%s" % version
    print "Using temporary directory:", tmp
    cmd("echo $CUR", capture=True).strip()
    cmd("mkdir %s/%s" % (tmp, femhub_dir))
    print "Copying femhub into the temporary directory..."
    cmd("cp -r * %s/%s/" % (tmp, femhub_dir))
    print "Removing source SPKG packages"
    cmd("rm -f %s/%s/spkg/standard/*" % (tmp, femhub_dir))
    print "Creating a binary tarball"
    cmd("cd %s; tar czf %s.tar.gz %s" % (tmp, femhub_dir, femhub_dir))
    cmd("cp %s/%s.tar.gz ." % (tmp, femhub_dir))
    print
    print "Package created: %s.tar.gz" % (femhub_dir)


def start_femhub(debug=False):
    if debug:
        print "Loading IPython..."
    try:
        import IPython
    except ImportError:
        raise Exception("You need to install 'ipython'")
    if debug:
        print "  Done."
    banner_length = 70
    l = "| FEMhub Version %s, Release Date: %s" % (version, release_date)
    l += " " * (banner_length - len(l) - 1) + "|"
    banner = "-" * banner_length + "\n" + l + "\n"
    l = "| Type lab() for the GUI."
    l += " " * (banner_length - len(l) - 1) + "|"
    banner += l + "\n" + "-" * banner_length + "\n"

    def lab_wrapper(old=False, auth=True, *args, **kwargs):
        if old:
            from sagenb.notebook.notebook_object import lab
            lab(*args, **kwargs)
        else:
            run_lab(auth=auth)
    namespace = {"lab": lab_wrapper}

    os.environ["IPYTHONDIR"] = expandvars("$DOT_SAGE/ipython")
    os.environ["IPYTHONRC"] = "ipythonrc"
    if not os.path.exists(os.environ["IPYTHONRC"]):
        cmd('mkdir -p "$DOT_SAGE"')
        cmd('cp -r "$FEMHUB_ROOT/spkg/base/ipython" "$DOT_SAGE/"')
    os.environ["MPLCONFIGDIR"] = expandvars("$DOT_SAGE/matplotlib")
    if not os.path.exists(os.environ["MPLCONFIGDIR"]):
        cmd('cp -r "$FEMHUB_ROOT/spkg/base/matplotlib" "$DOT_SAGE/"')

    if debug:
        print "Starting the main loop..."
    IPython.Shell.start(user_ns=namespace).mainloop(banner=banner)


def download_spkg_packages():
    print "Downloading standard spkg packages"
    cmd("mkdir -p $FEMHUB_ROOT/spkg/standard")
    packages = get_build_list()
    for p in packages:
        cmd("cd $FEMHUB_ROOT/spkg/standard; ../base/femhub-wget %s" % p)


def uninstall_package(pkg):
    femhub_root = os.getenv('FEMHUB_ROOT')

    path = os.path.join(femhub_root, "spkg/installed", pkg)

    def get_items2remove(path):
        items2remove = {'DIR': [], 'FILE': []}
        f = open(path)

        try:
            line = f.readline().strip()
            ndir = int(line.split('=')[1])

            for n in range(ndir):
                line = f.readline().strip()
                items2remove['DIR'].append(line)

            line = f.readline().strip()
            nfile = int(line.split('=')[1])

            for n in range(nfile):
                line = f.readline().strip()
                items2remove['FILE'].append(line)

        except Exception:
            items2remove = None
        finally:
            f.close()
            return items2remove

    if os.path.exists(path):
        items2remove = get_items2remove(path)

        if items2remove == None:
            print "This Package do not support uninstall, delete it manually .."
        else:
            print "Unistalling package ..."

            try:
                for d in items2remove['DIR']:
                    print d
                    shutil.rmtree(d, ignore_errors=True)

                for f in items2remove['FILE']:
                    print f
                    os.unlink(f)

                os.unlink(path)

                print "Package Uninstalled .."
            except Exception:
                print "Error while uninstalling, file may not exixts or permission isssue ..."
    else:
        print pkg, ": Package not installed ... !"


def install_package_old(pkg, install_dependencies=True, force_install=False,
        cpu_count=0):
    """
    Installs the package "pkg".

    "pkg" can be either a full path, or just the name of the package (with or
    without a version).

    "install_dependencies" ... if True, it will also install all dependencies

    "force_install" ... if True, it will install the package even if it has
                    been already installed

    "cpu_count" ... number of processors to use (0 means the number of
            processors in the  machine)

    Examples:
    >>> install_package("http://femhub.org/stpack/python-2.6.4.p9.spkg")
    >>> install_package("spkg/standard/readline-6.0.spkg")
    >>> install_package("readline-6.0.spkg")
    >>> install_package("readline")

    """
    if pkg.startswith("http") or pkg.startswith("www"):
        remote = True
        tmpdir = tempfile.mkdtemp()
        cmd("wget --directory-prefix=" + tmpdir + " " + pkg)
        pkg_name = os.path.split(pkg)
        pkg = os.path.join(tmpdir, pkg_name[1])
    else:
        remote = False
        try:
            pkg = pkg_make_absolute(pkg)
        except PackageNotFound, p:
            print p
            sys.exit(1)

    if is_installed(pkg):
        if not force_install:
            print "Package '%s' is already installed" % pkg_make_relative(pkg)
            return

    if install_dependencies:
        print "Installing dependencies for %s..." % pkg
        for dep in get_dependencies(pkg):
            install_package_old(dep, install_dependencies=False,
                    cpu_count=cpu_count)

        print "Installing %s..." % pkg
        femhub_scripts = ["femhub-env", "femhub-make_relative"]
        setup_cpu(cpu_count)
        # Create the standard POSIX directories:
        for d in ["bin", "doc", "include", "lib", "man", "share"]:
            cmd("mkdir -p $FEMHUB_ROOT/local/%s" % d)
        for script in femhub_scripts:
            cmd("cp $FEMHUB_ROOT/spkg/base/%s $FEMHUB_ROOT/local/bin/" % script)
        try:
            if pkg.endswith(".spkg"):
                print("Installing FEMhub spkg: " + pkg)
                cmd("$FEMHUB_ROOT/spkg/base/femhub-spkg %s" % pkg)
            else:
                print("Installing FEMhub deb: " + pkg)
                install_deb_package_old(pkg)
            cmd("touch $FEMHUB_ROOT/spkg/installed/%s" % pkg_make_relative(pkg))
        except CmdException:
            #print "Package %s failed to install" % pkg
            raise PackageBuildFailed()

    if remote:
        shutil.rmtree(tmpdir)


def install_deb_package_old(pkg):
    # works only for source deb package with spkg-install script
    cmd("dpkg -i %s" % pkg)


def is_installed(pkg):
    candidates = glob(expandvars("$FEMHUB_ROOT/spkg/installed/%s" % pkg))
    if len(candidates) == 1:
        return True
    elif len(candidates) == 0:
        return False
    else:
        raise Exception("Internal error: got more candidates in is_installed")


def pkg_make_absolute(pkg):
    if pkg.endswith(".spkg") or pkg.endswith(".deb"):
        if os.path.exists(pkg):
            return os.path.abspath(pkg)

        pkg_current = expandvars("$CUR/%s" % pkg)
        if os.path.exists(pkg_current):
            return pkg_current

        raise PackageNotFound("Package '%s' not found in the current directory" % pkg)

    candidates = glob(expandvars("$FEMHUB_ROOT/spkg/standard/*.spkg"))
    if len(candidates) == 0:
        raise PackageNotFound("Package '%s' not found" % pkg)
    cands = []
    for p in candidates:
        name, version = extract_name_version_from_path(p)
        if name == pkg:
            return p
        if pkg in name:
            cands.append(p)
    if len(cands) == 0:
        raise PackageNotFound("Package '%s' not found" % pkg)
    elif len(cands) == 1:
        return cands[0]

    print "Too many candidates:"
    print "    " + "\n    ".join(cands)

    raise PackageNotFound("Ambiguous package name.")


def pkg_make_relative(pkg):
    pkg = pkg_make_absolute(pkg)
    name, version = extract_name_version_from_path(pkg)
    return name


def make_unique(l):
    m = []
    for item in l:
        if item not in m:
            m.append(item)
    return m


def get_dependencies(pkg_name):
    """
    Gets all (including indirect) dependencies for the package "pkg_name".

    For simplicity, the dependency graph is currently hardwired in this
    function.
    """

    dependency_graph = {
            "python": ["termcap", "zlib", "bzip2", "gnutls",
                "libpng"],
            "ipython": ["python"],
            "cython": ["python"],
            "sympy": ["python"],
            "lapack": ["fortran"],
            "arpack": ["fortran"],
            "blas": ["fortran", "lapack"],
            "numpy": ["python", "lapack", "blas"],
            "scipy": ["numpy"],
            "matplotlib": ["freetype", "libpng", "python", "numpy"],
            "hermes1d": ["scipy", "cython", "matplotlib"],
            "hermes2d": ["scipy", "judy", "cython", "matplotlib"],
            "vtk-cvs": ["mesa"],
            "mayavi": ["python", "configobj", "vtk-cvs", "setuptools"],
            "pyparsing": ["python"],
            "pysparse": ["python"],
            "swig": ["python"],
            "sfepy": ["swig", "scipy"],
            "py": ["setuptools"],
            "setuptools": ["python"],
            "fipy": ["pysparse", "setuptools"],
            "libfemhub": ["python", "matplotlib"],
            "libgcrypt": ["libgpg_error"],
            "opencdk": ["zlib", "libgcrypt"],
            "gnutls": ["libgcrypt", "opencdk"],
            "python_gnutls": ["gnutls"],
            "python_django": ["python", ],
            "simplejson": ["python", "setuptools"],
            "sqlite": ["python", ],
            "pysqlite": ["python", "sqlite", ],
            "python_tornado": ["python_pycurl"],
            "python_pycurl": ["curl"],
            #"femhub_online_lab_sdk": ["python", "python_django", "simplejson", "pysqlite",
            #    "pyinotify", "python_lockfile", "python_daemon", "python_psutil",
            #    "python_tornado", "docutils", "pygments",
            #    ],
            "trilinos": ["python", "blas"],
            "proteus": ["numpy", "cython"],
            "phaml": ["blas", "lapack", "numpy", "arpack"],
            "umfpack": ["blas"],
            "pyplasm": ["PyOpenGL"]
            }
    deps = []
    for dep in dependency_graph.get(pkg_name, []):
        deps.extend(get_dependencies(dep))
        deps.append(dep)
    deps = make_unique(deps)
    return deps


def get_build_list():
    #FEMHUB_STANDARD = "http://femhub.org/stpack"
    femhub_packages = [
            "termcap-1.3.1.p1",
            "zlib-1.2.5",
            "python-2.7.2",
            "cython-0.14.1.p3",
            "twisted-9.0.p2",
            "jinja-1.2.p0",
            "jinja2-2.5.5",
            "python_gnutls-1.1.4.p7",
            "docutils-0.7.p0",
            "pygments-1.4",
            "sphinx-1.0.4.p6",
            "lapack-20071123.p1",
            "blas-20070724",
            "scipy-0.9",
            "freetype-2.3.5.p3",
            "libpng-1.2.35.p3",
            "opencdk-0.6.6.p5",

            "ipython-0.10.2.p0",
            "bzip2-1.0.5",
            "pexpect-2.0.p3",
            "setuptools-0.6.16",
            "libgpg_error-1.6.p3",
            "libgcrypt-1.4.4.p3",
            "gnutls-2.2.1.p5",

            "pyinotify-0.7.2",
            "python_lockfile-0.8",
            "python_daemon-1.5.5",
            "python_psutil-0.1.3",
            "python_tornado-f732f98",

            "py-1.3.1",

            "fortran-814646f",
            "f2py-9de8d45",
            "numpy-1.6.1",
            "matplotlib-1.0.1.p0",
            "sympy-0.6.4.p0",

            #"cmake-2.8.1.p2",
            "judy-1.0.5.p1",
            "mesa-7.8.2",
            "configobj-4.5.3",
            "pyparsing-1.5.2",
            "swig-2.0.0",
            "sfepy-2010.3",
            "hermes1d-qw1zxc",
            "hermes2d-1.0",
            "pysparse-1.1-6301cea",
            "phaml-201011190816_71974f0",
            "arpack-201011191133_0ea3296",
            "fipy-2.1-51f1360",
            "libfemhub-201011294106_6e289eb",
            "hdf5-1.8.5.p1",
            "h5py-1.2.1.p1",
            "pytables-2.1",
            "nose-0.11.1.p0",
            "python_django-1.2.1",
            "simplejson-2.1.1",
            "sqlite-3.7.5",
            "pysqlite-2.6.0",
            "curl",
            "python_pycurl-7.19.0",
            "umfpack-5.5.0",
            "PyOpenGL-3.0.2a1",
            "pyplasm-1.0",
            ]
    #packages = [FEMHUB_STANDARD + os.sep + p + ".spkg" for p in femhub_packages]
    return femhub_packages


def add_version_to_generic_name(pkg):
    packages = get_build_list()
    for p in packages:
        if p.startswith(pkg) and p != pkg:
            return p
    return pkg


def get_standard_packages(just_names=False):
    """
    Returns the list of standard packages.

    just_names ... if True, only the names of the packages are returned

    Packages are copied from various sources (see the *_STANDARD variables
    below).  You can also check (and update) the versions on the web:

    FEMhub: http://femhub.org/stpack

    """

    FEMHUB_STANDARD = "http://femhub.org/stpack"

    femhub_packages = []

    for file in os.listdir("spkg/standard"):
        if file.endswith(".spkg"):
            femhub_packages.append(file.replace(".spkg", ""))

    if just_names:
        packages = \
                [p + ".spkg" for p in femhub_packages]
    else:
        packages = \
                [FEMHUB_STANDARD + os.sep + p + ".spkg" for p in femhub_packages]
    return packages


def download_pkg_from_our_repo(pkg, force_install=False):
    path = os.path.dirname(pkg)
    inst_dir = os.path.join(local_pkg_path, path)
    process_command(["mkdir", "-p", inst_dir], cwd=get_root_path())
    if force_install == True:
        try:
            print("forced redownload of %s" %pkg)
            process_command(["rm", "-f", os.path.join(inst_dir, pkg)], cwd=get_root_path())
        except:
            pass
    try:
        #print(http_host + pkg)
        process_command_quiet(["wget", "-c", http_host + pkg], cwd=inst_dir)
        return True
    except CmdException:
        return False


def install_package(pkg, force_install=False, install_dependencies=True):
    # 1) test if already installed
    # 2) test if already downloaded
    # 3) download (deb bin, deb src, spkg src, apt-get src)
    # 4) install
    pkg_name, pkg_version = extract_name_version_from_path(os.path.basename(pkg))
    if len(pkg_name) == 0:
        pkg_name = pkg

    if force_install == False and is_installed(pkg_name):
        print "Package '%s' is already installed" % pkg_name
        return

    print "Installing %s..." % pkg
    if install_dependencies == True:
        print "Installing dependencies for %s..." % pkg_name
        for dep in get_dependencies(pkg_name):
            install_package(dep, force_install)

    if pkg.endswith(".spkg") or pkg.endswith(".deb"):
        without_ext = os.path.splitext(os.path.basename(pkg))[0]
    else:
        pkg = add_version_to_generic_name(pkg)
        without_ext = pkg

    try:
        local_deb_bin=os.path.join(local_pkg_path, http_deb_bin_path, without_ext + ".deb")
        local_deb = os.path.join(local_pkg_path, http_deb_src_path, without_ext + ".deb")
        local_spkg = os.path.join(local_pkg_path, http_spkg_path, without_ext + ".spkg")
        if (force_install == False):
            # test if package has been already downloaded in local path
            if (os.path.exists(local_deb_bin)):
                install_binary_deb(local_deb_bin)
                cmd("touch $FEMHUB_ROOT/spkg/installed/%s" % pkg_name)
                return
            if (os.path.exists(local_deb)):
                install_source_deb(local_deb)
                cmd("touch $FEMHUB_ROOT/spkg/installed/%s" % pkg_name)
                return
            if (os.path.exists(local_spkg)):
                install_source_spkg(local_spkg)
                cmd("touch $FEMHUB_ROOT/spkg/installed/%s" % pkg_name)
                return

        if USE_BINARY_DEB == True and download_pkg_from_our_repo(http_deb_bin_path + without_ext + ".deb", force_install):
            print("binary package found")
            install_binary_deb(local_deb_bin)
            cmd("touch $FEMHUB_ROOT/spkg/installed/%s" % pkg_name)
        elif download_pkg_from_our_repo(http_deb_src_path + without_ext + ".deb", force_install):
            print("source package found (deb)")
            install_source_deb(local_deb)
            cmd("touch $FEMHUB_ROOT/spkg/installed/%s" % pkg_name)
        elif download_pkg_from_our_repo(http_spkg_path + without_ext + ".spkg", force_install):
            print("source package found (spkg)")
            install_source_spkg(local_spkg)
            cmd("touch $FEMHUB_ROOT/spkg/installed/%s" % pkg_name)
        else:
            #apt-get
            print("package not found, trying apt-get repo")
            working_dir = tempfile.mkdtemp()
            process_command(["apt-get", "source", pkg_name], cwd=working_dir)
            dir = os.listdir(working_dir)
            working_dir_project = os.path.join(os.path.normpath(working_dir), dir[0])
            try:
                process_command(["./configure","--prefix=$FEMHUB_LOCAL"], cwd=working_dir_project)
                process_command(["make"], cwd=working_dir_project)
                process_command(["make install"], cwd=working_dir_project)
            except CmdException:
                try:
                    process_command(["./config","--prefix=$FEMHUB_LOCAL"], cwd=working_dir_project)
                    process_command(["make"], cwd=working_dir_project)
                    process_command(["make install"], cwd=working_dir_project)
                except CmdException:
                    print("Build from apt-get failed, error in configure script!")
                    shutil.rmtree(working_dir)
                    raise CmdException()
            shutil.rmtree(working_dir)
            cmd("touch $FEMHUB_ROOT/spkg/installed/%s" % pkg_name)

    except CmdException:
        print "Package %s failed to install" % pkg
        raise PackageBuildFailed()

def download_package(pkg, force_install=False, install_dependencies=True):
    # 1) test if already installed
    # 2) test if already downloaded
    # 3) download (deb bin, deb src, spkg src, apt-get src)
    # 4) install
    pkg_name, pkg_version = extract_name_version_from_path(os.path.basename(pkg))
    if len(pkg_name) == 0:
        pkg_name = pkg

    if force_install == False and is_installed(pkg_name):
        print "Package '%s' is already installed" % pkg_name
        return

    print "Installing %s..." % pkg
    if install_dependencies == True:
        print "Installing dependencies for %s..." % pkg_name
        for dep in get_dependencies(pkg_name):
            download_package(dep, force_install)

    if pkg.endswith(".spkg") or pkg.endswith(".deb"):
        without_ext = os.path.splitext(os.path.basename(pkg))[0]
    else:
        pkg = add_version_to_generic_name(pkg)
        without_ext = pkg

    try:
        if USE_BINARY_DEB == True and download_pkg_from_our_repo(http_deb_bin_path + without_ext + ".deb", force_install):
            print("binary package found")
            pkg_path = os.path.join(local_pkg_path, http_deb_bin_path, without_ext + ".deb")
            #install_binary_deb(pkg_path)
            #cmd("touch $FEMHUB_ROOT/spkg/installed/%s" % pkg_name)
        elif download_pkg_from_our_repo(http_deb_src_path + without_ext + ".deb", force_install):
            print("source package found (deb)")
            pkg_path = os.path.join(local_pkg_path, http_deb_src_path, without_ext + ".deb")
            #install_source_deb(pkg_path)
            #cmd("touch $FEMHUB_ROOT/spkg/installed/%s" % pkg_name)
        elif download_pkg_from_our_repo(http_spkg_path + without_ext + ".spkg", force_install):
            print("source package found (spkg)")
            pkg_path = os.path.join(local_pkg_path, http_spkg_path, without_ext + ".spkg")
            #install_source_spkg(pkg_path)
            #cmd("touch $FEMHUB_ROOT/spkg/installed/%s" % pkg_name)
        else:
            #apt-get
            print("package not found, maybe try apt-get repo")

    except CmdException:
        print "Package %s failed to download" % pkg
        raise PackageBuildFailed()


def install_binary_deb(filepath):
    process_command(["dpkg", "-x", filepath, FEMHUB_LOCAL], cwd=FEMHUB_LOCAL)


def install_source_deb(filepath):
    #process_command(["sudo","dpkg", "-i", filepath], cwd=FEMHUB_LOCAL)
    working_dir = tempfile.mkdtemp()
    #cmd("$FEMHUB_ROOT/spkg/base/femhub-deb %s %s" % filepath % working_dir)
    process_command(["./spkg/base/femhub-deb", filepath, working_dir], cwd=get_root_path())
    #process_command(["dpkg", "-e", filepath, working_dir], cwd=working_dir)
    #process_command(["dpkg", "-x", filepath, working_dir], cwd=working_dir)
    #process_command(["cat", "postinst"], cwd=working_dir)
    #process_command(["sh", "postinst"], cwd=working_dir)
    shutil.rmtree(working_dir)


def install_source_spkg(filepath):
    cmd("$FEMHUB_ROOT/spkg/base/femhub-spkg %s" % filepath)


def create_local_bash():
    femhub_scripts = ["femhub-env", "femhub-make_relative"]
    # Create the standard POSIX directories:
    for d in ["bin", "doc", "include", "lib", "man", "share", "usr"]:
        cmd("mkdir -p $FEMHUB_ROOT/local/%s" % d)

    try:
        cmd("ln -s $FEMHUB_ROOT/local/include $FEMHUB_ROOT/local/usr/include")
    except:
        pass
    try:
        cmd("ln -s $FEMHUB_ROOT/local/lib $FEMHUB_ROOT/local/usr/lib")
    except:
        pass

    for script in femhub_scripts:
        cmd("cp $FEMHUB_ROOT/spkg/base/%s $FEMHUB_ROOT/local/bin/" % script)


def download_packages():
    print "Downloading FEMhub"

    # Only add the packages that you want to have in FEMhub. Don't add
    # dependencies (those are handled in the get_dependencies() function)
    packages_list = [
            "ipython",
            "hermes1d",
            #"hermes2d",
            # requires: setupdocs>=1.0, doesn't work without a net...
            #"mayavi",
            "phaml",
            "libfemhub",
            "fipy",
            "sfepy",
            "sympy",
            "hdf5",
            "h5py",
            "pytables",
            "nose",
            "pyplasm",
            #"femhub_online_lab_sdk",
            ]
    try:
        for pkg in packages_list:
            download_package(pkg)
        print
        print "Download finished."
    except PackageBuildFailed:
        print "Download failed."


def build(cpu_count=0):
    print "Building FEMhub"

    create_local_bash()
    setup_cpu(cpu_count)

    # Only add the packages that you want to have in FEMhub. Don't add
    # dependencies (those are handled in the get_dependencies() function)
    packages_list = [
            "ipython",
            "hermes1d",
            #"hermes2d",
            # requires: setupdocs>=1.0, doesn't work without a net...
            #"mayavi",
            "phaml",
            "libfemhub",
            "fipy",
            "sfepy",
            "sympy",
            "hdf5",
            "h5py",
            "pytables",
            "nose",
            "pyplasm",
            #"femhub_online_lab_sdk",
            ]
    try:
        for pkg in packages_list:
            install_package(pkg)
        print
        print "Finished building FEMhub."
    except PackageBuildFailed:
        print "FEMhub build failed."


def wait_for_ctrl_c():
    try:
        while 1:
            sleep(1)
    except KeyboardInterrupt:
        pass


def run_lab(auth=False):
    """
    Runs the online lab.
    """
    print "Starting Online Lab: Open your web browser at http://localhost:8000/"
    print "Press CTRL+C to kill it"
    print

    if auth:
        cmd("onlinelab sdk start --no-daemon --auth=True --home=$FEMHUB_LOCAL/share/onlinelab/sdk-home")
    else:
        cmd("onlinelab sdk start --no-daemon --auth=False --home=$FEMHUB_LOCAL/share/onlinelab/sdk-home")

    try:
        wait_for_ctrl_c()
    finally:
        """
        cmd("onlinelab core stop --home=$FEMHUB_LOCAL/share/onlinelab/core-home")
        cmd("onlinelab service stop --home=$FEMHUB_LOCAL/share/onlinelab/service-home")
        """
        cmd("onlinelab sdk stop --home=$FEMHUB_LOCAL/share/onlinelab/sdk-home")


def extract_version(package_name):
    """
    Extracts the version from the package_name.

    The version is defined as one of the following:

    -3245s
    -ab434
    -1.1-343s
    -2.3-4
    -134-minimal-24

    but not:

    -ab-13
    -ab-ab
    -m14-m16

    The leading "-" is discarded.

    Example:

    >>> extract_version("jinja-2.5")
    '2.5'

    """
    def numeric(c):
        if c in ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]:
            return True
        return False

    first_dash = package_name.find("-")
    last_dash = package_name.rfind("-")
    if first_dash == last_dash:
        return package_name[first_dash + 1:]
    while not numeric(package_name[first_dash + 1]):
        package_name = package_name[first_dash + 1:]
        first_dash = package_name.find("-")
        last_dash = package_name.rfind("-")
        if first_dash == last_dash:
            return package_name[first_dash + 1:]
    return package_name[first_dash + 1:]


def extract_name_version(package_name):
    """
    Extracts the name and the version.

    Example:

    >>> extract_name_version("jinja-2.5")
    ('jinja', '2.5')

    """
    version = extract_version(package_name)
    name = package_name[:-len(version) - 1]
    return name, version


def extract_name_version_from_path(p):
    """
    Extracts the name and the version from the full path.

    Example:

    >> extract_name_version_from_path("/home/bla/jinja-2.5.spkg")
    ('jinja', '2.5')

    """
    path, ext = os.path.splitext(p)
    directory, filename = os.path.split(path)
    return extract_name_version(filename)


def command_update():
    # This doesn't work, because of the following error:
    # git-remote-https: relocation error: /usr/lib/libldap_r-2.4.so.2: symbol gnutls_certificate_get_x509_cas, version GNUTLS_1_4 not defined in file libgnutls.so.26 with link time reference
    # The only solution is to ship our own git version, which we will do in the
    # future, but for now we just keep this option commented out
    #print "Updating the git repository"
    #cmd("git pull https://github.com/hpfem/femhub.git master")

    download_spkg_packages()
    print "Done."


def command_list():
    print "List of installed packages:"
    cmd("ls spkg/installed")


if __name__ == "__main__":
    main()
