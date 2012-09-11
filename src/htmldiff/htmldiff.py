from optparse import OptionParser
from os.path import abspath, split, join
from copy import copy
import os
import re
from difflib import SequenceMatcher
import cgi
import HTMLParser
import sys
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

def htmlDecode(s):
    h = HTMLParser.HTMLParser()
    return h.unescape(s)

def htmlEncode(s, esc=cgi.escape):
    return esc(s, 1)

commentRE = re.compile('<!--.*?-->', re.S)
tagRE = re.compile('<script.*?>.*?</script>|<.*?>', re.S)
headRE = re.compile('<\s*head\s*>', re.S | re.I)
wsRE = re.compile('^([ \n\r\t]|&nbsp;)+$')
stopwords = ['I', 'a', 'about', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from', 'have', 'how', 'in', 'is', 'it', 'of', 'on', 'or', 'that', 'the', 'this', 'to', 'was', 'what', 'when', 'where', 'who', 'will', 'with']

# Note: Just returning false here gives a generally more accurate,
# but much slower and more noisy result.
def isJunk(x):
#    return False
    return wsRE.match(x) or x.lower() in stopwords

class HTMLMatcher(SequenceMatcher):

    def __init__(self, source1, source2, accurate_mode):
        if accurate_mode==False:
            SequenceMatcher.__init__(self, isJunk, source1, source2, False)
        if accurate_mode==True:
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
        return re.findall(r'([^ \n\r\t,.&;/#=<>()-]+|(?:[ \n\r\t]|&nbsp;)+|[,.&;/#=<>()-])', t)

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
        return '''
.insert { background-color: #aaffaa }
.delete { background-color: #ff8888; text-decoration: line-through }
.tagInsert { background-color: #007700; color: #ffffff }
.tagDelete { background-color: #770000; color: #ffffff }
'''

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
        return '<span class="tagInsert">insert: <tt>%s</tt></span>' % htmlEncode(tag)

    def formatDeleteTag(self, tag):
        return '<span class="tagDelete">delete: <tt>%s</tt></span>' % htmlEncode(tag)

class NoTagHTMLMatcher(HTMLMatcher):
    def formatInsertTag(self, tag):
        return ''
    def formatDeleteTag(self, tag):
        return ''

def htmldiff(source1, source2, accurate_mode, addStylesheet=False):
    """
    Return the difference between two pieces of HTML

        >>> htmldiff('test1', 'test2')
        '<span class="delete">test1 </span> <span class="insert">test2 </span> '
        >>> htmldiff('test1', 'test1')
        'test1 '
        >>> htmldiff('<b>test1</b>', '<i>test1</i>')
        '<span class="tagDelete">delete: <tt>&lt;b&gt;</tt></span> <span class="tagInsert">insert: <tt>&lt;i&gt;</tt></span> <i> test1 <span class="tagDelete">delete: <tt>&lt;/b&gt;</tt></span> <span class="tagInsert">insert: <tt>&lt;/i&gt;</tt></span> </i> '
    """
    #h = HTMLMatcher(source1, source2, accurate_mode)
    h = NoTagHTMLMatcher(source1, source2, accurate_mode)
    return h.htmlDiff(True)

def diffFiles(f1, f2, accurate_mode):
    # Open the files
    source1 = open(f1).read()
    source2 = open(f2).read()

    # Decode the html entities and then encode to utf-8
    source1 = htmlDecode(source1)
    source1 = source1.encode("utf-8")
    source2 = htmlDecode(source2)
    source2 = source2.encode("utf-8")
    return htmldiff(source1, source2, True, accurate_mode)

class SimpleHTMLMatcher(HTMLMatcher):
    """
    Like HTMLMatcher, but returns a simpler diff
    """
    def startInsertText(self):
        return '+['
    def endInsertText(self):
        return ']'
    def startDeleteText(self):
        return '-['
    def endDeleteText(self):
        return ']'
    def formatInsertTag(self, tag):
        return '+[%s]' % tag
    def formatDeleteTag(self, tag):
        return '-[%s]' % tag

def simplehtmldiff(source1, source2):
    """
    Simpler form of htmldiff; mostly for testing, like:

        >>> simplehtmldiff('test1', 'test2')
        '-[test1 ]+[test2 ]'
        >>> simplehtmldiff('<b>Hello world!</b>', '<i>Hello you!</i>')
        '-[<b>]+[<i>]<i> Hello -[world! ]-[</b>]+[you! ]+[</i>]</i> '
    """
    h = SimpleHTMLMatcher(source1, source2)
    return h.htmlDiff()

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

    @type spaces: integer
    @param spaces: Number of html space entities to return as string
    @return string containing html space entities (&nbsp;)
    """
    s = ""
    for i in xrange(spaces):
        s = s + "&nbsp;"
    return s

def span_to_whitespace(html_string, span):
    """
    Given an html string and a span tag name, parse the html and find
    the document areas containing those pieces and then replace them
    with nonbreaking whitespace html entities.

    @type html_string: string
    @param html_string: string of html to parse
    @type span: string
    @param string: the span class to parse for
    @return: html string with specified span replaced with whitespace
    """
    start = "<span class=\"%s\">" % span
    stop = "</span>"
    sub_length = len(start) + len(stop)
    while True:
        try:
            s = html_string.index(start)
            f = html_string.index(stop, s) + 7
        except ValueError:
            # No more occurances of this span exist in the file.
            break

        strip = html_string[s:f]
        cr = strip.count('</p>')
        cr = "<br />" * cr
        chars = whitespacegen(len(strip))
        chars = chars + cr
        html_string = html_string.replace(strip, chars)
    return html_string

def gen_side_by_side(file_string):
    """
    Given an html file as a string, return a new html file with side by
    side differences displayed in a single html file.

    @type file_string: string
    @param file_string: string of html to convert
    @return: string of html with side-by-side diffs
    """

    container_div = """<div id="container style="width: 100%;">"""
    orig_div_start = """<div id="left" style="clear: left; display: inline; float: left; width: 48%; border-right: 1px solid black; padding-right: 15px; margin-right: 5px;">"""
    new_div_start  = """<div id="right" style="float: right; width: 48%; display: inline; padding-left: 5px; padding-right: 10px;">"""
    div_end = """</div>"""
    start, body, ending = split_html(file_string)
    left_side = copy(body)
    right_side = copy(body)
    left = span_to_whitespace(left_side, "insert")
    right = span_to_whitespace(right_side, "delete")
    sbs_diff = start + container_div + orig_div_start + left + div_end + new_div_start + right + div_end + div_end + ending
    return sbs_diff

def split_html(html_string):
    i = html_string.index("<body")
    j = html_string.index(">", html_string.index("<body")) + 1
    k = html_string.index("</body")
    start = html_string[:j]
    body = html_string[j:k]
    ending = html_string[k:]
    return start, body, ending

def diff_files():
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

    parser = OptionParser(usage = use)
    parser.add_option('-o', '--output_file', action='store', dest='output_file', default=None,
                      help='[OPTIONAL] Name of output file')
    parser.add_option('-a', '--accurate-mode', help='Use accurate mode instead of risky mode', dest='mode',
                      default=False, action='store_true')
    parser.add_option('-s', '--side-by-side', help='generate a side-by-side comparision instead of inline', dest='sbs',
                      default=False, action='store_true')

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
        print "Error: could not find the specified file. Please check your filename and path."
        exit()

    if not os.path.exists(input_file2):
        print "Error: could not find the specified file. Please check your filename and path."
        exit()

    if output_file == None:
        output_file = 'diff_%s'%split(abspath(input_file1))[1]
    else:
        sbs_file = 'diff_%s' % output

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
    diff_files()

if __name__=="__main__":
    main()
