# Base the name of the software on the spec file
PACKAGE := $(shell basename *.spec .spec)
# Override this arch if the software is arch specific
ARCH = noarch

# Variables for clean build directory tree under repository
BUILDDIR = ./build
SDISTDIR = ${BUILDDIR}/sdist
RPMBUILDDIR = ${BUILDDIR}/rpm-build
RPMDIR = ${BUILDDIR}/rpms

# base rpmbuild command that utilizes the local buildroot
# not using the above variables on purpose.
# if you can make it work, PRs are welcome!
RPMBUILD = rpmbuild --define "_topdir %(pwd)/build" \
	--define "_sourcedir  %{_topdir}/sdist" \
	--define "_builddir %{_topdir}/rpm-build" \
	--define "_srcrpmdir %{_rpmdir}" \
	--define "_rpmdir %{_topdir}/rpms"

# Allow which python to be overridden at the environment level
PYTHON := $(shell which python)

all: rpms

clean:
	rm -rf ${BUILDDIR}/ *~
	rm -rf docs/*.gz
	rm -rf *.egg-info
	find . -name '*.pyc' -exec rm -f {} \;

manpage:
	gzip -c docs/${PACKAGE}.1 > docs/${PACKAGE}.1.gz

build: clean
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

prep_rpmbuild: sdist
	mkdir -p ${RPMBUILDDIR}
	mkdir -p ${RPMDIR}
	cp ${SDISTDIR}/*gz ${RPMBUILDDIR}/

rpms: prep_rpmbuild
	${RPMBUILD} -ba ${PACKAGE}.spec

srpm: prep_rpmbuild
	${RPMBUILD} -bs ${PACKAGE}.spec
