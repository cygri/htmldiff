Original version is from [Ian Bicking](https://github.com/ianb)
with changes from [Richard Cyganiak](https://github.com/cygri).
License: MIT

Project forked by Brant Watson for setuptools changes and maintaince.

Installation
============
As with a lot of packages, it's often much nicer to work
in a virtual environment instead of installing everything to
your global python installation. Running these commands
when not in a virtualenv will require root access. Setting up
a python virtual environment is beyond the scope of this document
but I'd recommend a quick google for virtualenvwrapper as it
makes managing these much easier.

To build a source package which gets placed in the dist subfolder::

    $ python setup.py sdist

To install into your current environment::

    $ python setup.py install

Or via pip::

    $ pip install .

Pip may also be used to install a built package::

    $ pip install htmldiff-1a.0.0.dev5.tar.gz


Usage
=====

To produce a diff of two html files::

    $ htmldiff file1.html file2.html
    Wrote file diff to /absolute/path/to/diff_file1.html

With custom output file::

    $ htmldiff file1.html file2.html -o myfile.html
    Wrote file diff to /absolute/path/to/myfile.html

All options:

 * -a --accurate-mode [Optional] Use accurate mode instead of risky mode
 * -s --side-by-side  [Optional] Generate a side-by-side comparison instead of inline
 * -o --output OUTPUT_FILE [Optional] Specify a custom output file
 * -h --help  - Prints command line help
