"""
.. module:: setup
:synopsis: Setup htmldiff tool
.. moduleauthor:: Ian Bicking, Brant Watson <brant.watson@propylon.com>
"""
from setuptools import setup, find_packages

setup(
    name="htmldiff",
    version="1a.0.0.dev5",
    author="Ian Bicking - https://github.com/ianb",
    description=("Utility to create html diffs"),
    packages=find_packages('src'),
    package_dir={"": "src"},
    test_suite="tests",
    entry_points={
        "console_scripts": [
            "htmldiff = htmldiff.entry_point:main",
        ]
    }
)
