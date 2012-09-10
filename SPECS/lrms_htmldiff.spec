%define project lrms
%define raw_name htmltest
%define unmangled_version 1a.1.0.dev1
%define release_type snapshot
%define release 1
%define python_version python2.6

Summary: htmldiff: A tool for creating html diffs
Name: %{project}-%{raw_name}
Version: %{unmangled_version}
Release: %{release}
Source0: %{raw_name}-%{unmangled_version}
License: Open Source
Group: Development/Libraries
BuildRoot: ~/build-buildroot
Prefix: %{_prefix}
BuildArch: noarch
Requires: python-setuptools
Provides: htmldiff
AutoReqProv: no

%description
A tool for html diff creations

%prep

%build

%install

%clean

%files
