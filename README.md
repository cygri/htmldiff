htmldiff.py
-----------

Usage: `htmldiff version1.html version2.html > diff.html`

htmldiff outputs HTML that shows the differences in text between
two versions of an HTML document. Differences in markup are not
shown.

Original version is from [Ian Bicking][1].

Using with Mercurial
--------------------

Put `htmldiff` on the path, and add the following to `~/.hgrc`:

    [extensions]
    hgext.extdiff =

    [extdiff]
    cmd.htmldiff = htmldiff

Then you can do: `hg htmldiff index.html > diff.html`

   [1]: https://github.com/ianb