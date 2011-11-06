#!/usr/bin/make -f
# -*- makefile -*-
configure: configure-stamp
configure-stamp:
	dh_testdir
	touch configure-stamp
build: build-stamp
build-stamp: configure-stamp
	dh_testdir
	$(MAKE)
	touch $@
clean:
	dh_testdir
	dh_testroot
	rm -f build-stamp configure-stamp
	dh_clean
install: build
	dh_testdir
	dh_testroot
	dh_prep
	dh_installdirs
	$(MAKE) DESTDIR=$(CURDIR)/debian/#{package} install
binary-arch: build install
	# emptyness
binary-indep: build install
	dh_testdir
	dh_testroot
	dh_installchangelogs
	dh_installdocs
	dh_installexamples
	dh_pysupport
	dh_link
	dh_fixperms
	dh_installdeb
	dh_shlibdeps
	dh_gencontrol
	dh_md5sums
	dh_builddeb
binary: binary-indep
.PHONY: build clean binary-indep binary install configure
