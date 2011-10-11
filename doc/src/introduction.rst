============
Introduction
============

`FEMhub Distribution <http://femhub.org>`_ is an open source collection of finite element (FEM) 
codes with a unified Python interface. It is available for download as desktop application, 
but all codes are also automatically available in `NCLab <http://nclab.com>`_. This makes 
any code included in the Distribution automatically available via any web browser.

The FEMhub Distribution is available under the GPL license (Version 2, 1991).

In this documentation, "FEMhub Distribution" will be often abbreviated by "FEMhub"
for convenience.

Prior to reading FEMhub documentation, we recommend that you install FEMhub using instructions
in `this page <http://http://femhub.org/doc/src/install_run.html>`_, and subscribe to the 
`mailing list <http://groups.google.com/group/femhub/>`_.
Our mailing list is an active place where you should get all answers quickly.

The best way of reading this tutorial is to run the code at the same time.
After making your way through the tutorial, you may want to view the published
worksheets in `NCLab <http://nclab.com>`_. After you are there, click the
"Published worksheets" button at the bottom of the login window. There are a
variety of examples that may help you to get started. If you
create an interesting model using FEMhub packages, let us know and we
will be happy to add it to the existing examples.

The source code of the FEMhub Distribution can be viewed in the 
`git repository <git@github.com:femhub/femhub-distribution.git>`_.
All the default packages of FEMhub (including FEM Engines and
computing and visualization libraries) can be viewed and downloaded at 
`this page <http://femhub.org/codes.php>`_. The binaries of the FEMhub 
Distribution can be downloaded from `here <http://femhub.org/pub>`_.

Officially Supported Platforms
------------------------------

Building of FEMhub from source is regularly tested on different Linux distributions and  Mac OS X. Please `click here <http://femhub.org/doc/src/install_run.html>`_ for the instructions on installing FEMhub.

**FEMhub in Windows:** You can install FEMhub on Windows using Cygwin. Please `click here <http://femhub.org/doc/src/install_run.html#microsoft-windows>`_ to view the instructions for installing FEMhub in Windows.

FEMhub may not build in all operationg systems. We like all of the operating systems, but just haven't had
the time to make FEMhub work well on them.  Help wanted!

Implementation
--------------

FEMhub has significant components written in the following
languages: C/C++, Python, and Fortran.  Python is built as
part of FEMhub, and Fortran (g95) is included (x86 Linux and
OS X only), so you do not need them in order to build FEMhub.

Supported Compilers
-------------------
* FEMhub builds with GCC >= 3.x and GCC >= 4.1.x.
* FEMhub may not build with GCC 2.9.x.
* FEMhub has never been built without using GCC compiler.

Redistribution
--------------

Your local FEMhub install is almost exactly the same as any "developer"
install.  You can make changes to documentation, source, etc., and
very easily package up the complete results for redistribution just
like we do. You can make your own source tarball (femhub-x.y.z.tar)
of FEMhub or you can make a binary distribution with the packages you've
installed included. User's action must comply with terms of the license
under which FEMhub is distributed.

Changes to Included Softwares
-----------------------------

All software included with FEmhub is copyright by the respective
authors and released under an open source license that is GPL
compatible.  See the file COPYING.txt for more details.
(Note -- jsMath is licensed under the Apache license; Apache
claim their license is GPL compatible, but Stallman disagrees.)

Each spkg in FEMHUB_ROOT/spkg/standard/ is a bzip'd tarball.  You can
extract it with::

       tar jxvf name-*.spkg

Credit
------

The FEMhub Distribution is developed by the `hp-FEM group <http://hpfem.org>`_ at the Department 
of Mathematics ans Statistics, University of Nevada, Reno.

People who contributed to the FEMhub project, in the order of date of involvement:

* Pavel Solin (project leader, University of Nevada, Reno, USA)
* Ondrej Certik (University of Nevada, Reno, USA)
* Robert Cimrman (New Technologies Research Centre, Pilsen, Czech Republic)
* Sameer Regmi (University of Nevada, Reno, USA)
* Aayush Poudel (University of Nevada, Reno, USA)
* Ma Zhonghua (China University of Petroleum, Beijing)
* Mateusz Paprocki (University of Wroclaw, Poland)
* Matthew Dillon (University of Alaska - Fairbanks, USA)
* Jesse Robertson (The Australian National University Acton, Canberra, Australia)
* Christopher Kees (U.S. Army Engineer Research and Development Center, Vicksburg, MS, USA)
* Quan Zou (University of Nevada, Reno, USA)
* Pablo Angulo (Universidad Autonoma de Madrid)

A few packages and files in the FEMhub build system are taken from `Sage <http://www.sagemath.org>`_.

Distributed under the terms of the GNU General Public License (GPL).
