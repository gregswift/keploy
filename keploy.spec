%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Name:           keploy
Version:        0.5
Release:        1%{?dist}
Summary:        cli ssh public key deployment utility

Group:          Applications/Internet
License:        GPLv3
URL:            http://keploy.googlecode.com
Source0:        http://keploy.googlecode.com/files/%{name}-%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildRequires:  python-setuptools
Requires:       openssh-clients

%description
Keploy is a python application that allows you to deploy your ssh
public key to remote systems without having to remember all the
little things, like file permissions.


%prep
%setup -q


%build
%{__python} setup.py build


%install
rm -rf %{buildroot}
%{__python} setup.py install --root=%{buildroot} --record=INSTALLED_FILES


%clean
rm -rf %{buildroot}


%files -f INSTALLED_FILES
%defattr(755,root,root,-)



%changelog
* Tue Mar 16 2010 Greg Swift <gregswift@gmail.com> 0.5-1
- initial rpm build
