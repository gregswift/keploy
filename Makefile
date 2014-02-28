# Base the name of the software on the spec file
PACKAGE := $(shell basename *.spec .spec)
# Override this arch if the software is arch specific
ARCH = noarch

# Variables for clean build directory tree under repository
BUILDDIR = ./build
ARTIFACTDIR = ./artifacts
SDISTDIR = ${ARTIFACTDIR}/sdist
RPMBUILDDIR = ${BUILDDIR}/rpm-build
RPMDIR = ${ARTIFACTDIR}/rpms
DEBBUILDDIR = ${BUILDDIR}/deb-build
DEBDIR = ${ARTIFACTDIR}/debs

# base rpmbuild command that utilizes the local buildroot
# not using the above variables on purpose.
# if you can make it work, PRs are welcome!
RPMBUILD = rpmbuild --define "_topdir %(pwd)/build" \
	--define "_sourcedir  %(pwd)/artifacts/sdist" \
	--define "_builddir %{_topdir}/rpm-build" \
	--define "_srcrpmdir %{_rpmdir}" \
	--define "_rpmdir %(pwd)/artifacts/rpms"

# Allow which python to be overridden at the environment level
PYTHON := $(shell which python)

all: rpms

clean:
	rm -rf ${BUILDDIR}/ *~
	rm -rf docs/*.gz
	rm -rf *.egg-info
	find . -name '*.pyc' -exec rm -f {} \;

clean_all: clean
	rm -rf ${ARTIFACTDIR}/

manpage:
	gzip -c docs/${PACKAGE}.1 > docs/${PACKAGE}.1.gz

build: clean manpage
	${PYTHON} setup.py build -f

install: build
	${PYTHON} setup.py install -f --root ${DESTDIR}

install_rpms: rpms
	yum install ${RPMDIR}/${ARCH}/${PACKAGE}*.${ARCH}.rpm

reinstall: uninstall install

uninstall: clean
	rm -f /usr/bin/${PACKAGE}
	rm -rf /usr/lib/python*/site-packages/${PACKAGE}

uninstall_rpms: clean
	rpm -e ${PACKAGE}

sdist:
	${PYTHON} setup.py sdist -d "${SDISTDIR}"

prep_rpmbuild: prep_build
	mkdir -p ${RPMBUILDDIR}
	mkdir -p ${RPMDIR}
	cp ${SDISTDIR}/*gz ${RPMBUILDDIR}/

rpms: prep_rpmbuild
	${RPMBUILD} -ba ${PACKAGE}.spec

srpm: prep_rpmbuild
	${RPMBUILD} -bs ${PACKAGE}.spec

prep_build: manpage sdist
	mkdir -p ${BUILDDIR}

prep_debbuild: prep_build
	mkdir -p ${DEBBUILDDIR}
	mkdir -p ${DEBDIR}
	SDISTPACKAGE=`ls ${SDISTDIR}`; \
	BASE=`basename $$SDISTPACKAGE .tar.gz`; \
	DEBBASE=`echo $$BASE | sed 's/-/_/'`; \
	TARGET=${DEBBUILDDIR}/$$DEBBASE.orig.tar.gz; \
	ln -f -s ../../${SDISTDIR}/$$SDISTPACKAGE $$TARGET; \
	tar -xz -f $$TARGET -C ${DEBBUILDDIR}; \
	rm -rf ${DEBBUILDDIR}/$$BASE/debian; \
	cp -pr debian/ ${DEBBUILDDIR}/$$BASE

debs: prep_debbuild
	SDISTPACKAGE=`ls ${SDISTDIR}`; \
	BASE=`basename $$SDISTPACKAGE .tar.gz`; \
	cd ${DEBBUILDDIR}/$$BASE; \
	debuild -uc -us
	mv ${DEBBUILDDIR}/*.deb ${DEBDIR}/

