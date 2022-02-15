#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Setup for bout."""

import io
import os
import sys
from shutil import rmtree

from setuptools import setup, Command

# Package meta-data.
NAME = "bout"
DESCRIPTION = "Parse and liberate data from csv based bank statements."
URL = "https://github.com/codito/bout"
EMAIL = "arun@codito.in"
AUTHOR = "Arun Mahapatra"
VERSION = (1, 0, 2)

# Dependencies required for execution
REQUIRED = [
    "click>=6.7"
]

here = os.path.abspath(os.path.dirname(__file__))

# Import the README and use it as the long-description.
# Note: this will only work if "README.md" is present in your MANIFEST.in file!
with io.open(os.path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = "\n" + f.read()

# Load the package"s __version__.py module as a dictionary.
about = {}
about["__version__"] = '.'.join(map(str, VERSION))


class UploadCommand(Command):
    """Support setup.py upload."""

    description = "Build and publish the package."
    user_options = []

    @staticmethod
    def status(s):
        """Print things in bold."""
        print("\033[1m{0}\033[0m".format(s))

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        try:
            self.status("Removing previous builds…")
            rmtree(os.path.join(here, "dist"))
        except OSError:
            pass

        self.status("Building Source and Wheel (universal) distribution…")
        os.system("{0} setup.py sdist bdist_wheel --universal"
                  .format(sys.executable))

        self.status("Uploading the package to PyPi via Twine…")
        os.system("twine upload dist/*")

        sys.exit()


# Where the magic happens:
setup(
    name=NAME,
    version=about["__version__"],
    description=DESCRIPTION,
    long_description=long_description,
    author=AUTHOR,
    author_email=EMAIL,
    url=URL,
    # packages=find_packages(exclude=("tests",)),
    # If your package is a single module, use this instead of "packages":
    py_modules=["bout"],

    entry_points={
        "console_scripts": ["bout=bout:start"],
    },
    install_requires=REQUIRED,
    include_package_data=True,
    license="MIT",
    classifiers=[
        # Trove classifiers
        # Full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy"
    ],
    # $ setup.py publish support.
    cmdclass={
        "upload": UploadCommand,
    },
)
