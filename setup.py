from setuptools import setup, find_packages

setup(
    name="htmldiff",
    version="1.0.0.dev6",
    author="Ian Bicking - https://github.com/ianb",
    description=("Utility to create html diffs"),
    packages=find_packages('src'),
    package_dir={"": "src"},
    install_requires=["boltons>=17.1.0", "six"],
    test_suite="tests",
    entry_points={
        "console_scripts": [
            "htmldiff = htmldiff.entry_point:main",
        ]
    }
)
