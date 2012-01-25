=================================
FEMhub HowTo: Tips for Developers
=================================
Following tips are useful for developers.

Clone Git Repository
--------------------

To clone the repository of FEMhub (script and the build system):
::
  \$ git clone git://github.com/femhub/femhub-distribution.git

To clone the reopsitory of Libfemhub:
::
  \$ git clone git://github.com/femhub/libfemhub.git


How to Test Patches
-------------------
Let's say that John asks you to pull the branch called ex_fem from git://github.com/andrsd/femhub-distribution.git and review.
First, add the remote link to John's repo by saying:
::
  \$ git remote add john git://github.com/john/femhub-distribution.git

Then, create in your repo a new local branch where the patches will be tested. Assuming that you are in your master branch, type:
::
  \$ git checkout -b test-john

Then, fetch John's repo by typing:
::
  \$ git fetch john

Next, merge the branch of interest into your local branch:
::
 \$ git merge john/ex_fem


How to Compile FEMhub from Git
------------------------------
To compile from git (as opposed to the tarball):
::
  \$ git clone git://github.com/femhub/femhub-distribution.git
  \$ cd femhub-distribution
  \$ ./femhub -d
  \$ make


Creating New FEMhub Release
---------------------------
How to create a new release:
::
  \$ git clone git://github.com/femhub/femhub-distribution.git
  \$ cd femhub-distribution
  \$ ./femhub -d
  \$ vim spkg/base/femhub-run  # edit the version & date in the banner
  \$ git ci -a -m "FEMhub version bumped to 0.9.9"
  \$ git tag femhub-0.9.9
  \$ git push --tags remote_repo:/home/git/repos/femhub-distribution.git master  #replace
  "remote_repo" with remote repository where you want to push
  \$ cd ..
  \$ cp -a femhub femhub-0.9.9
  \$ tar cf femhub-0.9.9.tar femhub-0.9.9


Binary Distribution
-------------------
Unpack the tarball of source code, and rename it (for example, to
**femhub-0.9.9-ubuntu64** or any platform for which you would like to release
the binary). Then build it on that corresponding platform following the
instructions above.
Immediately after the build is complete create **.tar.gz** of that directory.
This is the binary version of FEMhub for the particular platform.


Windows
-------
In cygwin, do
::
  make
  local/bin/sage-win-copy

and run femhub by double-cclicking on the `femhub-windows` (bat) file in the root directory. 


Create and Test FEMhub Packages
-------------------------------
If you have developed new codes to add new functionality to FEMhub you might
want to create a package instead of a regular patch. In order to develop any
FEMhub package, first install FEMhub as described `here <http://femhub.org/doc/src/install_run.html>`_.

FEMhub packages are .tar files but they have the extension .spkg to avoid
confusion. SPKG means "Software Package". You can see the list of current
standard packages included in FEMhub `here <http://femhub.org/codes.php>`_.
Alternatively, you can see FEMhub standard packages if you go to FEMhub top directory and do
::
  \$ cd spkg/standard

You can extract an spkg by typing
::
  \$ tar -jxvf packagename-version.spkg

After you extract you will see a script file named ``spkg-install`` which contains the install script.

The script ``spkg-install`` is run during installation of the FEMhub package. You can modify spkg-install according to your need.

There are two ways to create FEMhub packages:

(1) Canonical Way: This method works for any package in FEMhub

(2) Using Git: This method works just for some packages

**(1) Canonical Way**

You may follow the following steps to create a new FEMhub spkg package:

Create the package by typing:
::
  \$ /path/to/femhub/util/create_package.py -d /path/to/your/project/

This will create a package named project.spkg in your current working directory.
Create_package.py script will detect cmake, make or python project and create appropriate spkg-install for you. If you want to supply some custom build commandsor the script could not determine your build system, you have to create spkg-install script in your project directory manually.

After you create mypackage-version.spkg you can install it in FEMhub easily. To do so go to FEMhub top directory and type
::
  \$ ./femhub -i path/to/mypackage-version.spkg

A sample ``spkg-install`` script
::
  if [ "$FEMHUB_LOCAL" = "" ]; then
     echo "FEMHUB_LOCAL undefined ... exiting";
     echo "Maybe run 'femhub --shell'?"
     exit 1
  fi

  PACKAGE_NAME=hermes

  PY_VER=`python -c "import sys;print '%d.%d' % sys.version_info[:2]"`
  echo "Detected Python version: $PY_VER"

  cmake -DCMAKE_INSTALL_PREFIX="$FEMHUB_LOCAL" \
      -DPYTHON_INCLUDE_PATH="$FEMHUB_LOCAL/include/python$PY_VER" \
      -DPYTHON_LIBRARY="$FEMHUB_LOCAL/lib/python2.6/config/libpython2.6.dll.a" \
    .
  if [ $? -ne 0 ]; then
     echo "Error configuring $PACKAGE_NAME."
     exit 1
  fi

  make
  if [ $? -ne 0 ]; then
     echo "Error building $PACKAGE_NAME."
     exit 1
  fi

  make install
  if [ $? -ne 0 ]; then
     echo "Error installing $PACKAGE_NAME."
     exit 1
  fi

In the spkg-install script above you can see a variable FEMHUB_LOCAL which points to path/to/femhub/local.

**(2) Using Git**

First clone the appropriate repository:
::
   \$ git clone http://github.com/hpfem/PACKAGE_NAME.git
   \$ cd PACKAGE_NAME/

Currently, the packages developed via Git are:
::
    Libfemhub (PACKAGE_NAME = "libfemhub"), git repository.
    Hermes (PACKAGE_NAME = "hermes"), git repository.
    Mesh Editor (PACKAGE_NAME = "mesheditor-flex"), git repository.

Before editing any files, we recommend that you create a new branch by typing
::
    "git checkout -b new_branch_name".

After finishing and committing your changes to
the package that you are developing, update the package in your local FEMhub as
follows:
::
    path_to_femhub/femhub --shell # this launches a FEMhub subshell
    bash spkg-install
    CTRL+D # exits the FEMhub subshell

Now your local FEMhub contains the updated package and you are ready to test
your changes. Change dir to the main FEMhub directory "path_to_femhub/", run
FEMhub typing "./femhub", and run the GUI via the "lab()" command.

Installing SPKG Package
-----------------------
You can install any spkg package in femhub directly by typing
::
  \$ ./femhub -i path/to/spkg-package

You can install the package directly from the internet too. For example, to install FiPy package you can type
::
  \$ ./femhub -i http://femhub.org/stpack/fipy-2.1-51f1360.spkg

Then you can test whether your package worked correctly in FEMhub. You can test your patches without creating spkg tar by following the instructions below.

To force the installation of the new package, type the following:
::
    \$ ./femhub -i path/to/spkg-package -f

or to install from the internet:
::
   ./femhub -i http://femhub.org/stpack/http:/fipy-2.1-51f1360.spk -f


Testing Your Patches of FEMhub Package
--------------------------------------
You can test your patches of FEMhub packages without creating spkg tarball by following these steps:
::
 \$ cd mypackage-version
 \$ path_to_femhub/femhub --shell # this launches FEMhub shell
 \$ bash spkg-install
  CTRL+D # exits this shell after the previous command completes
