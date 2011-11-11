#!/usr/bin/python

from distutils.core import setup
#from setuptools import setup,find_packages

NAME = "keploy"
VERSION = "0.6"
SHORT_DESC = "%s cli ssh public key deployment utility" % NAME
LONG_DESC = """
%s is a python application that allows you to deploy your ssh
public key to remote systems without having to remember all the
little things, like file permissions.
""" % NAME


if __name__ == "__main__":
 
        manpath    = "share/man/man1/"
        setup(
                name = NAME,
                version = VERSION,
                author = "Greg Swift",
                author_email = "gregswift@gmail.com",
                url = "https://%s.googlecode.com/" % NAME,
                license = "GPLv3",
                scripts = ["scripts/%s" % NAME],
                package_dir = {NAME: NAME},
                packages = [NAME],
                data_files = [(manpath,  ["docs/%s.1.gz" % NAME])],
                description = SHORT_DESC,
                long_description = LONG_DESC
        )

