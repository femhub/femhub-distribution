================================
Sage to Debian packaging utility
================================

Step 1: Prerequisities
----------------------

Install required dependencies:
::
  sudo apt-get install build-essential autoconf automake autotools-dev dpkg dh-make debhelper devscripts fakeroot xutils lintian pbuilder
    
  sudo apt-get install python-stdeb


Step 2: Customizing settings.xml
--------------------------------

Packaging utility will try to get all the information from spkg.
If it fails, defaults from settings.xml are used.

You can also enable debug output by changing <debug>0</debug> to 1.
This will echo stdout and stderr from configure and make scripts to
troubleshoot missing dependencies for failed source packages.

You can also set the directory, where deb packages will be created.
Default is: <destination>./femhub_deb</destination>
Which creates a femhub_deb folder in your current directory.


Step 3: Customizing templates
-----------------------------

In script's directory, there are files with .tpl extension.
They provide basic, but usable templates for creating packages.
    
You don't have to edit them in order to make it work!

For example: control.py.tpl is for spkg containing only Python source,
             control.spkg.tpl is for spkg containing other sources,
             rules.tpl is the same for both.


Step 4: Running the packaging utility
-------------------------------------

You can run spkg2deb.py from it's directory:
::
  \$ spkg2deb.py -h

Or you can run it with absolute path, where you extracted it:
::
  \$ /home/lab/spkg2deb/spkg2deb.py -h

When <destination>./femhub_deb</destination> is set in settings.xml,
it will always create the femhub_deb folder in your current directory,
not in script's directory, which can be useful if you don't want to copy
all the script sources to your project folder.

All parameters can occur multiple times:
::
  \$ spkg2deb.py -f path/to/package1.spkg -f path/to/package2.spkg
Or:
::
  \$ spkg2deb.py -d path/to/spkg_dir_1 -d path/to/spkg_dir_2

The rest of the build process is automatic and will not require any input.
It even tries to automatically install all the dependencies for you!


Step 5: Troubleshooting
-----------------------
    
If some package fails, it will be skipped.
You can solve the problems by adding a -dbg or --debug parameter and try to 
build just this failed package with the -f parameter.

Why could some package fail?
  1) package.spkg can be invalid archive
  2) spkg-install was not found in this package
  3) configure script in the package could fail with fatal error
  4) Makefile script could fail with fatal error

In case of fatal error in configure or Makefile script, it will mostly mean
that you have to install some dependencies for the package or there is some
custom badly written Makefile which doesn't support fakeroot. 
    
In that case package.tar.gz is built including the sources (same as     
package.spkg just with debian control and rules files) and needs to be
installed as root.

Try to build .deb as root on deployment server:
::
  \$ tar xzvf mypackage-1.0.tar.gz
  \$ cd mypackage-1.0
  \$ sudo dh_make -f ../mypackage-1.0.tar.gz

This will build the package and process the Makefile, which can rewrite some
system files or folders and therefore this approach is not recommended!
