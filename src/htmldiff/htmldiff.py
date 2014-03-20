"""
Utility to do inline and side-by-side diffs of html files.
"""
# Standard Imports
import os
import re
import cgi
import HTMLParser
from copy import copy
from optparse import OptionParser
from os.path import (
    abspath,
    split,
    join
)
from difflib import SequenceMatcher
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

# HtmlDiff
from font_lookup import get_spacing


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


def htmlDecode(s):
    """
    Given a string of html, decode entities

    :type s: string
    :param s: string of html to decode
    :return: string of html with decoded entities
    """
    h = HTMLParser.HTMLParser()
    return h.unescape(s)


def htmlEncode(s, esc=cgi.escape):
    return esc(s, 1)

########################################################################
#                        Variables and Regex                           #
########################################################################
commentRE = re.compile('<!--.*?-->', re.S)
tagRE = re.compile('<script.*?>.*?</script>|<.*?>', re.S)
headRE = re.compile('<\s*head\s*>', re.S | re.I)
wsRE = re.compile('^([ \n\r\t]|&nbsp;)+$')
stopwords = [
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
]


def isJunk(x):
    """
    Used for the faster but less accurate mode.  Original comment said:

    Note: Just returning false here gives a generally more accurate but
    much shower and more noisy result.

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
            SequenceMatcher.__init__(self, isJunk, source1, source2, False)
        if accurate_mode is True:
            SequenceMatcher.__init__(self, False, source1, source2, False)

    def set_seq1(self, a):
        SequenceMatcher.set_seq1(self, self.splitHTML(a))

    def set_seq2(self, b):
        SequenceMatcher.set_seq2(self, self.splitHTML(b))

    def splitTags(self, t):
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

    def splitWords(self, t):
        exp = r'([^ \n\r\t,.&;/#=<>()-]+|(?:[ \n\r\t]|&nbsp;)+|[,.&;/#=<>()-])'
        return re.findall(exp, t)

    def splitHTML(self, t):
        t = commentRE.sub('', t)
        r = self.splitTags(t)
        result = []
        for item in r:
            if item.startswith('<'):
                result.append(item)
            else:
                result.extend(self.splitWords(item))
        return result

    def htmlDiff(self, addStylesheet=True):
        opcodes = self.get_opcodes()
        a = self.a
        b = self.b
        out = StringIO()
        for tag, i1, i2, j1, j2 in opcodes:
            if tag == 'equal':
                for item in a[i1:i2]:
                    out.write(item)
            if tag == 'delete':
                self.textDelete(a[i1:i2], out)
            if tag == 'insert':
                self.textInsert(b[j1:j2], out)
            if tag == 'replace':
                if (self.isInvisibleChange(a[i1:i2], b[j1:j2])):
                    for item in b[j1:j2]:
                        out.write(item)
                else:
                    self.textDelete(a[i1:i2], out)
                    self.textInsert(b[j1:j2], out)
        html = out.getvalue()
        out.close()
        if addStylesheet:
            html = self.addStylesheet(html, self.stylesheet())
        return html

    def isInvisibleChange(self, seq1, seq2):
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

    def textDelete(self, lst, out):
        text = ''
        for item in lst:
            if item.startswith('<'):
                self.outDelete(text, out)
                text = ''
                out.write(self.formatDeleteTag(item))
            else:
                text += item
        self.outDelete(text, out)

    def textInsert(self, lst, out):
        text = ''
        for item in lst:
            if item.startswith('<'):
                self.outInsert(text, out)
                text = ''
                out.write(self.formatInsertTag(item))
                out.write(item)
            else:
                text += item
        self.outInsert(text, out)

    def outDelete(self, s, out):
        if s.strip() == '':
            out.write(s)
        else:
            out.write(self.startDeleteText())
            out.write(s)
            out.write(self.endDeleteText())

    def outInsert(self, s, out):
        if s.strip() == '':
            out.write(s)
        else:
            out.write(self.startInsertText())
            out.write(s)
            out.write(self.endInsertText())

    def stylesheet(self):
#         return '''
# .insert { background-color: #aaffaa }
# .delete { background-color: #ff8888; text-decoration: line-through }
# .tagInsert { background-color: #007700; color: #ffffff }
# .tagDelete { background-color: #770000; color: #ffffff }
# '''
        return (
            '.insert {background-color: #aaffaa}\n'
            '.delete {\n'
            '\tbackground-color: #ff8888;\n'
            '\ttext-decoration: line-through;\n'
            '}\n'
            '.tagInsert {background-color: #007700; color: #ffffff}\n'
            '.tagDelete {background-color: #770000; color: #ffffff}\n'
        )

    def addStylesheet(self, html, ss):
        match = headRE.search(html)
        if match:
            pos = match.end()
        else:
            pos = 0
        return ('%s<style type="text/css"><!--\n%s\n--></style>%s'
                % (html[:pos], ss, html[pos:]))

    def startInsertText(self):
        return '<span class="insert">'

    def endInsertText(self):
        return '</span>'

    def startDeleteText(self):
        return '<span class="delete">'

    def endDeleteText(self):
        return '</span>'

    def formatInsertTag(self, tag):
        return ('<span class="tagInsert">insert: <tt>%s</tt>'
                '</span>' % htmlEncode(tag))

    def formatDeleteTag(self, tag):
        return ('<span class="tagDelete">delete: <tt>%s</tt>'
                '</span>' % htmlEncode(tag))


class NoTagHTMLMatcher(HTMLMatcher):
    """I forgot what I had this in here for"""
    def formatInsertTag(self, tag):
        return ''

    def formatDeleteTag(self, tag):
        return ''


def htmldiff(source1, source2, accurate_mode, addStylesheet=False):
    """
    Return the difference between two pieces of HTML::

        res = htmldiff('test1', 'test2')
    """
    #h = HTMLMatcher(source1, source2, accurate_mode)
    h = NoTagHTMLMatcher(source1, source2, accurate_mode)
    return h.htmlDiff(True)


def diffStrings(orig, new, accurate_mode):
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

    # Decode the html entities and then encode to utf-8
    orig = htmlDecode(orig)
    orig = orig.encode("utf-8")
    new = htmlDecode(new)
    new = new.encode("utf-8")
    return htmldiff(orig, new, True, accurate_mode)


def diffFiles(f1, f2, accurate_mode):
    """
    Given two files, open them to variables and pass them to diffStrings
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
    source1 = open(f1).read()
    source2 = open(f2).read()
    return diffStrings(source1, source2, accurate_mode)


class TextMatcher(HTMLMatcher):

    def set_seq1(self, a):
        SequenceMatcher.set_seq1(self, a.split('\n'))

    def set_seq2(self, b):
        SequenceMatcher.set_seq2(self, b.split('\n'))

    def htmlDiff(self, addStylesheet=False):
        opcodes = self.get_opcodes()
        a = self.a
        b = self.b
        out = StringIO()
        for tag, i1, i2, j1, j2 in opcodes:
            if tag == 'equal':
                self.writeLines(a[i1:i2], out)
            if tag == 'delete' or tag == 'replace':
                out.write(self.startDeleteText())
                self.writeLines(a[i1:i2], out)
                out.write(self.endDeleteText())
            if tag == 'insert' or tag == 'replace':
                out.write(self.startInsertText())
                self.writeLines(b[j1:j2], out)
                out.write(self.endInsertText())
        html = out.getvalue()
        out.close()
        if addStylesheet:
            html = self.addStylesheet(html, self.stylesheet())
        return html

    def writeLines(self, lines, out):
        for line in lines:
            line = htmlEncode(line)
            line = line.replace('  ', '&nbsp; ')
            line = line.replace('\t', '&nbsp; &nbsp; &nbsp; &nbsp; ')
            if line.startswith(' '):
                line = '&nbsp;' + line[1:]
            out.write('<tt>%s</tt><br>\n' % line)


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

    #s = " " * spaces
    s = "<span style=\"white-space: pre-wrap;\">" + s + "</span>"
    return s


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
        raise Exception("This is not a full html document.")
    start = html_string[:j]
    body = html_string[j:k]
    ending = html_string[k:]
    return start, body, ending


def diff():
    command_name = "htmldiff"
    """
    Given two html files, create an output html diff of the two versions
    showing the differences between them.
    """
    use = """%s INPUT_FILE1 INPUT_FILE2 [-o OUTPUT_FILE]

    INPUT_FILE
        This is the master document to read in and be converted to named styles

    -o --output OUTPUT_FILE
        [Optional] Specify a custom filename for output

    -a --accurate-mode
        [Optional] Use accurate mode instead of risky mode

    -s --side-by-side
        [Optional] generate a side-by-side comparision instead of inline

    -use
        Will print this message.""" % command_name

    parser = OptionParser(usage=use)
    parser.add_option(
        '-o',
        '--output_file',
        action='store',
        dest='output_file',
        default=None,
        help='[OPTIONAL] Name of output file'
    )
    parser.add_option(
        '-a',
        '--accurate-mode',
        help='Use accurate mode instead of risky mode',
        dest='mode',
        default=False,
        action='store_true'
    )
    parser.add_option(
        '-s',
        '--side-by-side',
        help='generate a side-by-side comparision instead of inline',
        dest='sbs',
        default=False,
        action='store_true'
    )

    (options, args) = parser.parse_args()
    if len(args) < 2:
        print use
        exit()
    if len(args) > 2:
        print use
        exit()

    output_file = vars(options)['output_file']
    accurate_mode = vars(options)['mode']
    sbs = vars(options)['sbs']
    input_file1 = args[0]
    input_file2 = args[1]

    # Get the actual path
    path = split(abspath(input_file1))[0]

    if not os.path.exists(input_file1):
        print('Error: could not find specified file: %s' % input_file1)
        exit()

    if not os.path.exists(input_file2):
        print('Error: could not find specified file: %s' % input_file2)
        exit()

    if output_file is None:
        output_file = 'diff_%s' % split(abspath(input_file1))[1]

    output = join(path, output_file)

    try:
        diffed_html = diffFiles(input_file1, input_file2, accurate_mode)
        if sbs:
            diffed_html = gen_side_by_side(diffed_html)
    except Exception, ex:
        print ex
        exit()

    try:
        dhtml = open(output, 'w')
        dhtml.write(diffed_html)
        dhtml.close()
    except Exception, ex:
        print ex
        exit()


def main():
    diff()

if __name__ == "__main__":
    main()
