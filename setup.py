# SPDX-FileCopyrightText: Copyright (c) 2022 Gautam Bhatnagar for n/a
#
# SPDX-License-Identifier: MIT

"""A setuptools based setup module.

See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

from setuptools import setup, find_packages

# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, "README.rst"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    # Community Bundle Information
    name="circuitpython-wifi-manager",
    use_scm_version={
        # This is needed for the PyPI version munging in the Github Actions release.yml
        "git_describe_command": "git describe --tags --long",
        "local_scheme": "no-local-version",
    },
    setup_requires=["setuptools_scm"],
    description="Circuitpython helper library for managing wifi for iot devices",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    # The project's main homepage.
    url="https://github.com/theboyknowsclass/CircuitPython_wifi_manager.git",
    # Author details
    author="Gautam Bhatnagar",
    author_email="",  # TODO: Add your email here
    install_requires=[
        "Adafruit-Blinka",
        "adafruit-circuitpython-httpserver",
        "ipaddress",
        "socketpool",
        "wifi",
    ],
    # Choose your license
    license="MIT",
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries",
        "Topic :: System :: Hardware",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
    ],
    # What does your project relate to?
    keywords="adafruit blinka circuitpython micropython wifi_manager circuitpython, wifi, iot",
    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    # TODO: IF LIBRARY FILES ARE A PACKAGE FOLDER,
    #       CHANGE `py_modules=['...']` TO `packages=['...']`
    py_modules=["wifi_manager"],
)
