"""
.. module:: htmldiff.htmldiff
:synopsis: Utility to do inline and side-by-side diffs of html files.
.. moduleauthor:: Ian Bicking, Brant Watson <brant.watson@propylon.com>
"""
# Standard Imports
import cgi
import HTMLParser
import logging
import re
from copy import copy
from difflib import SequenceMatcher
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

# HtmlDiff
from font_lookup import get_spacing

LOG = logging.getLogger(__name__)


class TagStrip(HTMLParser.HTMLParser):
    """
    Subclass of HTMLParser used to strip html tags from strings
    """
    def __init__(self):
        self.reset()
        self.fed = []

    def handle_data(self, s):
        self.fed.append(s)

    def get_stripped_string(self):
        return ''.join(self.fed)


def strip_tags(html_string):
    """
    Remove all HTML tags from a given string of html

    :type html_string: string
    :param html_string: string of html
    :return: intial string stripped of html tags
    """
    st = TagStrip()
    st.feed(html_string)
    stripped = st.get_stripped_string()
    return stripped


def html_decode(s):
    """
    Given a string of html, decode entities

    :type s: string
    :param s: string of html to decode
    :return: string of html with decoded entities
    """
    h = HTMLParser.HTMLParser()
    return h.unescape(s)


def html_encode(s, esc=cgi.escape):
    return esc(s, 1)

########################################################################
#                        Variables and Regex                           #
########################################################################
commentRE = re.compile('<!--.*?-->', re.S)
tagRE = re.compile('<script.*?>.*?</script>|<.*?>', re.S)
headRE = re.compile('<\s*head\s*>', re.S | re.I)
wsRE = re.compile('^([ \n\r\t]|&nbsp;)+$')
split_re = re.compile(
    r'([^ \n\r\t,.&;/#=<>()-]+|(?:[ \n\r\t]|&nbsp;)+|[,.&;/#=<>()-])'
)
stopwords = frozenset((
    'I',
    'a',
    'about',
    'an',
    'and',
    'are',
    'as',
    'at',
    'be',
    'by',
    'for',
    'from',
    'have',
    'how',
    'in',
    'is',
    'it',
    'of',
    'on',
    'or',
    'that',
    'the',
    'this',
    'to',
    'was',
    'what',
    'when',
    'where',
    'who',
    'will',
    'with'
))


def is_junk(x):
    """
    Used for the faster but less accurate mode.  Original comment said:

    Note: Just returning false here gives a generally more accurate but
    much slower and more noisy result.

    False is now set with the -a switch so this function always returns
    the regex matches or lowercase.

    :type x: string
    :param x: string to match against
    :returns: regex matched or lowercased x
    """

    return wsRE.match(x) or x.lower() in stopwords


class HTMLMatcher(SequenceMatcher):

    def __init__(self, source1, source2, accurate_mode):
        if accurate_mode is False:
            SequenceMatcher.__init__(self, is_junk, source1, source2, False)
        if accurate_mode is True:
            SequenceMatcher.__init__(self, False, source1, source2, False)

    def set_seq1(self, a):
        SequenceMatcher.set_seq1(self, self.split_html(a))

    def set_seq2(self, b):
        SequenceMatcher.set_seq2(self, self.split_html(b))

    def split_tags(self, t):
        result = []
        pos = 0
        while 1:
            match = tagRE.search(t, pos=pos)
            if not match:
                result.append(t[pos:])
                break
            result.append(t[pos:match.start()])
            result.append(match.group(0))
            pos = match.end()
        return result

    def split_words(self, t):
        return split_re.findall(t)

    def split_html(self, t):
        t = commentRE.sub('', t)
        r = self.split_tags(t)
        result = []
        for item in r:
            if item.startswith('<'):
                result.append(item)
            else:
                result.extend(self.split_words(item))
        return result

    def diff_html(self, add_stylesheet=True):
        opcodes = self.get_opcodes()
        a = self.a
        b = self.b
        out = StringIO()
        for tag, i1, i2, j1, j2 in opcodes:
            if tag == 'equal':
                for item in a[i1:i2]:
                    out.write(item)
            if tag == 'delete':
                self.text_delete(a[i1:i2], out)
            if tag == 'insert':
                self.text_insert(b[j1:j2], out)
            if tag == 'replace':
                if (self.is_invisible_change(a[i1:i2], b[j1:j2])):
                    for item in b[j1:j2]:
                        out.write(item)
                else:
                    self.text_delete(a[i1:i2], out)
                    self.text_insert(b[j1:j2], out)
        html = out.getvalue()
        out.close()
        if add_stylesheet:
            html = self.add_stylesheet(html, self.stylesheet)
        return html

    def is_invisible_change(self, seq1, seq2):
        if len(seq1) != len(seq2):
            return False
        for i in range(0, len(seq1)):
            if seq1[i][0] == '<' and seq2[i][0] == '<':
                continue
            if wsRE.match(seq1[i]) and wsRE.match(seq2[i]):
                continue
            if seq1[i] != seq2[i]:
                return False
        return True

    def text_delete(self, lst, out):
        text = ''
        for item in lst:
            if item.startswith('<'):
                self.out_delete(text, out)
                text = ''
                out.write(self.format_delete_tag(item))
            else:
                text += item
        self.out_delete(text, out)

    def text_insert(self, lst, out):
        text = ''
        for item in lst:
            if item.startswith('<'):
                self.out_insert(text, out)
                text = ''
                out.write(self.format_insert_tag(item))
                out.write(item)
            else:
                text += item
        self.out_insert(text, out)

    def out_delete(self, s, out):
        if s.strip() == '':
            out.write(s)
        else:
            out.write(self.start_delete_text)
            out.write(s)
            out.write(self.end_span_text)

    def out_insert(self, s, out):
        if s.strip() == '':
            out.write(s)
        else:
            out.write(self.start_insert_text)
            out.write(s)
            out.write(self.end_span_text)

    @property
    def stylesheet(self):
        return (
            '.insert {\n\tbackground-color: #AFA\n}\n'
            '.delete {\n'
            '\tbackground-color: #F88;\n'
            '\ttext-decoration: line-through;\n'
            '}\n'
            '.tagInsert {\n\tbackground-color: #070;\n\tcolor: #FFF\n}\n'
            '.tagDelete {\n\tbackground-color: #700;\n\tcolor: #FFF\n}\n'
        )

    def add_stylesheet(self, html, stylesheet):
        """
        Add the stylesheet to the given html strings header. Attempt to find
        the head tag and insert it after it, but if it doesn't exist then
        insert at the beginning of the string.

        :type html: str
        :param html: string of html text to add the stylesheet to
        :type stylesheet: str
        :param stylesheet: css stylesheet to include in document header
        :returns: modified html string with stylesheet added to the header
        """
        match = headRE.search(html)
        pos = match.end() if match else 0

        # Note: The sheet used to be commented out, but I'm not sure why
        return ('%s\n<style type="text/css">\n%s</style>%s'
                % (html[:pos], stylesheet, html[pos:]))

    start_insert_text = '<span class="insert">'
    end_span_text = '</span>'
    start_delete_text = '<span class="delete">'

    def format_insert_tag(self, tag):
        return ('<span class="tagInsert">insert: <tt>%s</tt>'
                '</span>' % html_encode(tag))

    def format_delete_tag(self, tag):
        return ('<span class="tagDelete">delete: <tt>%s</tt>'
                '</span>' % html_encode(tag))


class NoTagHTMLMatcher(HTMLMatcher):
    """I forgot what I had this in here for"""
    def format_insert_tag(self, tag):
        return ''

    def format_delete_tag(self, tag):
        return ''


class TextMatcher(HTMLMatcher):

    def set_seq1(self, a):
        SequenceMatcher.set_seq1(self, a.split('\n'))

    def set_seq2(self, b):
        SequenceMatcher.set_seq2(self, b.split('\n'))

    def diff_html(self, add_stylesheet=False):
        opcodes = self.get_opcodes()
        a = self.a
        b = self.b
        out = StringIO()
        for tag, i1, i2, j1, j2 in opcodes:
            if tag == 'equal':
                self.writeLines(a[i1:i2], out)
            if tag == 'delete' or tag == 'replace':
                out.write(self.start_delete_text)
                self.writeLines(a[i1:i2], out)
                out.write(self.end_span_text)
            if tag == 'insert' or tag == 'replace':
                out.write(self.start_insert_text)
                self.writeLines(b[j1:j2], out)
                out.write(self.end_span_text)
        html = out.getvalue()
        out.close()
        if add_stylesheet:
            html = self.add_stylesheet(html, self.stylesheet)
        return html

    def writeLines(self, lines, out):
        for line in lines:
            line = html_encode(line)
            line = line.replace('  ', '&nbsp; ')
            line = line.replace('\t', '&nbsp; &nbsp; &nbsp; &nbsp; ')
            if line.startswith(' '):
                line = '&nbsp;' + line[1:]
            out.write('<tt>%s</tt><br>\n' % line)


def htmldiff(source1, source2, accurate_mode, add_stylesheet=False):
    """
    Return the difference between two pieces of HTML::

        res = htmldiff('test1', 'test2')
    """
    h = NoTagHTMLMatcher(source1, source2, accurate_mode)
    return h.diff_html(True)


def diff_strings(orig, new, accurate_mode):
    """
    Given two strings of html, return a diffed string.

    :type orig: string
    :param orig: original string for comparison
    :type new: string
    :param new: new string for comparision against original string
    :type accurate_moode: boolean
    :param accurate_moode: use accurate mode or not
    :returns: string containing diffed html
    """
    # Decode the data if it was utf-8 encoded to begin with
    try:
        orig = orig.decode('utf-8')
    except Exception:
        pass
    try:
        new = new.decode('utf-8')
    except Exception:
        pass

    # Decode the html entities and then encode to utf-8
    orig = html_decode(orig)
    orig = orig.encode("utf-8")

    new = html_decode(new)
    new = new.encode("utf-8")
    return htmldiff(orig, new, True, accurate_mode)


def diff_files(f1, f2, accurate_mode):
    """
    Given two files, open them to variables and pass them to diff_strings
    for diffing.

    :type f1: object
    :param f1: initial file to diff against
    :type f2: object
    :param f2: new file to compare to f1
    :type accurate_mode: boolean
    :param accurate_mode: use accurate mode or not
    :returns: string containing diffed html from f1 and f2
    """
    # Open the files
    with open(f1) as f:
        LOG.debug("Reading file: {0}".format(f1))
        source1 = f.read()

    with open(f2) as f:
        LOG.debug("Reading file: {0}".format(f2))
        source2 = f.read()

    return diff_strings(source1, source2, accurate_mode)


def whitespacegen(spaces):
    """
    From a certain number of spaces, provide an html entity for non breaking
    spaces in an html document.

    :type spaces: integer
    :param spaces: Number of html space entities to return as string
    :returns: string containing html space entities (&nbsp;) wrapped in
              a html span that properly wraps the whitespace.
    """
    # The average length of a word is 5 letters.. I guess
    words = spaces / 5
    s = "&nbsp;&nbsp;&nbsp;&nbsp; " * int(words)

    # s = " " * spaces
    return '<span style="white-space: pre-wrap;">{0}</span>'.format(s)


def span_to_whitespace(html_string, span):
    """
    Given an html string and a span tag name, parse the html and find
    the document areas containing those pieces and then replace them
    with nonbreaking whitespace html entities.

    :type html_string: string
    :param html_string: string of html to parse
    :type span: string
    :param string: the span class to parse for
    :returns: html string with specified span replaced with whitespace
    """
    start = "<span class=\"%s\">" % span
    stop = "</span>"
    while True:
        try:
            s = html_string.index(start)
            f = html_string.index(stop, s) + 7
        except ValueError:
            # No more occurances of this span exist in the file.
            break

        strip = html_string[s:f]
        stripped = strip_tags(strip)
        chars = whitespacegen(get_spacing(stripped, "times new roman"))
        html_string = html_string.replace(strip, chars)
    return html_string


def gen_side_by_side(file_string):
    """
    Given an html file as a string, return a new html file with side by
    side differences displayed in a single html file.

    :type file_string: string
    :param file_string: string of html to convert
    :returns: string of html with side-by-side diffs
    """

    container_div = """<div id="container style="width: 100%;">"""

    orig_div_start = ('<div id="left" style="clear: left; display: inline; '
                      'float: left; width: 47%; border-right: 1px solid black;'
                      ' padding: 10px;">')

    new_div_start = ('<div id="right" style="float: right; width: 47%; '
                     'display: inline; padding: 10px;">')
    div_end = '</div>'
    start, body, ending = split_html(file_string)
    left_side = copy(body)
    right_side = copy(body)
    left = span_to_whitespace(left_side, "insert")
    right = span_to_whitespace(right_side, "delete")

    # Create side-by-side diff
    sbs_diff = (
        '%(start)s%(container)s%(orig_start)s%(left)s%(div_end)s%(new_start)s'
        '%(right)s%(div_end)s%(ending)s' % {
            'start': start,
            'container': container_div,
            'orig_start': orig_div_start,
            'left': left,
            'div_end': div_end,
            'new_start': new_div_start,
            'right': right,
            'ending': ending

        }
    )
    return sbs_diff


def split_html(html_string):
    """
    Divides an html document into three seperate strings and returns
    each of these. The first part is everything up to and including the
    <body> tag. The next is everything inside of the body tags. The
    third is everything outside of and including the </body> tag.

    :type html_string: string
    :param html_string: html document in string form
    :returns: three strings start, body, and ending
    """

    try:
        i = html_string.index("<body")
        j = html_string.index(">", i) + 1
        k = html_string.index("</body")
    except ValueError:
        raise ValueError("This is not a full html document.")
    start = html_string[:j]
    body = html_string[j:k]
    ending = html_string[k:]
    return start, body, ending
