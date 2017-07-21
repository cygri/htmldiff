htmldiff
========
HTML Diffing utility.

- Original is from [Ian Bicking](https://github.com/ianb)
- Updates and improvements from [Richard Cyganiak] (https://github.com/cygri)
- Refactored for use with setup tools and adding side-by-side diffing by
  [Brant Watson](https://github.com/induane)

License: MIT

Installation
============
To build a source package::

    $ python setup.py sdist

To install into your current environment::

    $ python setup.py install

Or via pip::

    $ pip install .

Pip may also be used to install a built package::

    $ pip install htmldiff-1.0.0.dev6.tar.gz


Usage
=====

To produce a diff of two html files::

    $ htmldiff file1.html file2.html > diff_file.html

With custom output file::

    $ htmldiff file1.html file2.html -o myfile.html
    INFO: Selected inline diff
    INFO: Diffing files...
    INFO: Wrote file diff to /absolute/path/to/myfile.html

Produce a side-by-side diff instead of an inline diff::

    $ htmldiff file1.html file2.html -s > diff_file.html
    INFO: Selected inline diff
    INFO: Diffing files...


All options:

 * -a --accurate-mode Use accurate mode instead of risky mode
 * -s --side-by-side Generate a side-by-side comparison instead of inline
 * -o --output_file OUTPUT_FILE [Optional] Specify a custom output file
 * -l --log-level (DEBUG,INFO,WARNING,ERROR,CRITICAL)
 * -L --log-file Location to place logging output
 * -V --version Print the application version and exit
 * -h --help  - Prints command line help
