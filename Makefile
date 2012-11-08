PACKAGE := $(shell basename *.spec .spec)
ARCH = noarch
RPMBUILD = rpmbuild --define "_topdir %(pwd)/rpm-build" \
	--define "_builddir %{_topdir}" \
	--define "_rpmdir %(pwd)/rpms" \
	--define "_srcrpmdir %{_rpmdir}" \
	--define "_sourcedir  %{_topdir}"


all: rpms

clean:
	rm -rf dist/ build/ rpm-build/ rpms/
	rm -rf docs/*.gz keploy/*.pyc MANIFEST *~

manpage:
	gzip -c docs/${PACKAGE}.1 > docs/${PACKAGE}.1.gz

build: clean manpage
	python setup.py build -f

install: build
	python setup.py install -f

reinstall: uninstall install

uninstall: clean
	rm -f /usr/bin/${PACKAGE}
	rm -rf /usr/lib/python2.*/site-packages/${PACKAGE}

uninstall_rpms: clean
	rpm -e ${PACKAGE}

sdist: manpage
	python setup.py sdist

prep_rpmbuild: build sdist
	mkdir -p rpm-build
	mkdir -p rpms
	cp dist/*.gz rpm-build/

rpms: prep_rpmbuild
	${RPMBUILD} -ba ${PACKAGE}.spec

srpm: prep_rpmbuild
	${RPMBUILD} -bs ${PACKAGE}.spec
