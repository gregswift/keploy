#!/usr/bin/python

from distutils.core import setup
#from setuptools import setup,find_packages

NAME = "keploy"
VERSION = "0.5"
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
                url = "https://keploy.googlecode.com/",
                license = "GPLv3",
		scripts = ["scripts/keploy"],
                package_dir = {NAME: NAME},
		packages = [NAME],
                data_files = [(manpath,  ["docs/keploy.1.gz"])]
                description = SHORT_DESC,
                long_description = LONG_DESC
        )

