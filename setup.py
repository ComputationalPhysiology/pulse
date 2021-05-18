#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Note: To use the 'upload' functionality of this file, you must:
#   $ pipenv install twine --dev

import io
import os
import sys
from shutil import rmtree

from setuptools import Command, find_packages, setup

# Package meta-data.
NAME = "fenics-pulse"
DESCRIPTION = (
    "A python library based on FEniCS that aims to solve "
    "problems in continuum mechanics, in particular "
    "cardiac mechanics."
)
URL = "https://github.com/finsberg/pulse"
EMAIL = "henriknf@simula.no"
AUTHOR = "Henrik Finsberg"
REQUIRES_PYTHON = ">=3.6"
VERSION = "2020.2.1"

# What packages are required for this module to be executed?
REQUIRED = ["h5py", "numpy", "scipy", "daiquiri"]

# What packages are optional?
EXTRAS = {
    "test": ["jupytext", "flake8", "pytest", "pytest-cov", "black", "mypy"],
    "plot": ["matplotlib", "fenics-plotly"],
    "docs": [
        "pandoc",
        "Sphinx",
        "sphinx_rtd_theme",
        "nbsphinx",
        "sphinx-gallery",
        "ipywidgets",
    ],
    "dev": [
        "pre-commit",
        "bump2version",
        "isort",
        "flake8",
        "black",
        "mypy",
        "ipython",
    ],
}

EXTRAS.update({"all": list(set([val for values in EXTRAS.values() for val in values]))})


# The rest you shouldn't have to touch too much :)
# ------------------------------------------------
# Except, perhaps the License and Trove Classifiers!
# If you do change the License, remember to change the Trove Classifier for that!

here = os.path.abspath(os.path.dirname(__file__))

# Import the README and use it as the long-description.
# Note: this will only work if 'README.md' is present in your MANIFEST.in file!
try:
    with io.open(os.path.join(here, "README.md"), encoding="utf-8") as f:
        long_description = "\n" + f.read()
except FileNotFoundError:
    long_description = DESCRIPTION

# Load the package's __version__.py module as a dictionary.
about = {}
with open(os.path.join(here, "pulse/__version__.py")) as f:
    exec(f.read(), about)
about["__version__"] = VERSION


class ReleaseCommand(Command):
    """Support setup.py upload."""

    description = "Build and publish the package."
    user_options = []

    @staticmethod
    def status(s):
        """Prints things in bold."""
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

        self.status("Pushing git tags…")
        os.system("git tag v{0}".format(about["__version__"]))
        os.system("git push finsberg master --tags")

        sys.exit()


# Where the magic happens:
setup(
    name=NAME,
    version=about["__version__"],
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type="text/markdown",
    author=AUTHOR,
    author_email=EMAIL,
    python_requires=REQUIRES_PYTHON,
    url=URL,
    packages=find_packages(exclude=["tests", "demos"]),
    # If your package is a single module, use this instead of 'packages':
    # py_modules=['mypackage'],
    # entry_points={
    #     'console_scripts': ['mycli=mymodule:cli'],
    # },
    install_requires=REQUIRED,
    extras_require=EXTRAS,
    include_package_data=True,
    license="LGPL version 3 or later",
    package_data={"pulse.example_meshes": ["*.h5"]},
    classifiers=[
        # Trove classifiers
        # Full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
        # 'License :: OSI Approved :: LGPL version 3 or later',
        # 'Programming Language :: Python',
        # 'Programming Language :: Python :: 3',
        # 'Programming Language :: Python :: Implementation :: CPython',
    ],
    # $ setup.py publish support.
    cmdclass={"release": ReleaseCommand},
)
