#!/usr/bin/env python
"""
htmldiff.py
(C) Ian Bicking <ianb@colorstudy.com>

Finds the differences between two HTML files.  *Not* line-by-line
comparison (more word-by-word).

Command-line usage:
  ./htmldiff.py test1.html test2.html

Better results if you use mxTidy first.  The output is HTML.
"""

from difflib import SequenceMatcher
import re
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
import cgi

def htmlEncode(s, esc=cgi.escape):
    return esc(s, 1)

commentRE = re.compile('<!--.*?-->', re.S)
tagRE = re.compile('<.*?>', re.S)
headRE = re.compile('<\s*head\s*>', re.S | re.I)

class HTMLMatcher(SequenceMatcher):

    def __init__(self, source1, source2):
        SequenceMatcher.__init__(self, None, source1, source2)

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
        return t.strip().split()

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

    def htmlDiff(self, addStylesheet=False):
        opcodes = self.get_opcodes()
        a = self.a
        b = self.b
        out = StringIO()
        #print [o[0] for o in opcodes]
        for tag, i1, i2, j1, j2 in opcodes:
            if tag == 'equal':
                for item in a[i1:i2]:
                    out.write(item)
                    out.write(' ')
            if tag == 'delete' or tag == 'replace':
                self.textDelete(a[i1:i2], out)
            if tag == 'insert' or tag == 'replace':
                self.textInsert(b[j1:j2], out)
        html = out.getvalue()
        out.close()
        if addStylesheet:
            html = self.addStylesheet(html, self.stylesheet())
        return html

    def textDelete(self, lst, out):
        inSpan = False
        for item in lst:
            if item.startswith('<'):
                if inSpan:
                    out.write(self.endDeleteText())
                    inSpan = False
                out.write(self.formatDeleteTag(item))
            else:
                if not inSpan:
                    out.write(self.startDeleteText())
                    inSpan = True
                out.write(item)
                out.write(' ')
        if inSpan:
            out.write(self.endDeleteText())

    def textInsert(self, lst, out):
        inSpan = False
        for item in lst:
            if item.startswith('<'):
                if inSpan:
                    out.write(self.endInsertText())
                    inSpan = False
                out.write(self.formatInsertTag(item))
                out.write(item)
                out.write(' ')
            else:
                if not inSpan:
                    out.write(self.startInsertText())
                    inSpan = True
                out.write(item)
                out.write(' ')
        if inSpan:
            out.write(self.endInsertText())

    def stylesheet(self):
        return '''
.insert { background-color: #aaffaa }
.delete { background-color: #ff8888 }
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
        return '</span> '
    def startDeleteText(self):
        return '<span class="delete">'
    def endDeleteText(self):
        return '</span> '
    def formatInsertTag(self, tag):
        return ('<span class="tagInsert">insert: <tt>%s</tt></span> '
                % htmlEncode(tag))
    def formatDeleteTag(self, tag):
        return ('<span class="tagDelete">delete: <tt>%s</tt></span> '
                % htmlEncode(tag))

class NoTagHTMLMatcher(HTMLMatcher):
    def formatInsertTag(self, tag):
        return ''
    def formatDeleteTag(self, tag):
        return ''

def htmldiff(source1, source2, addStylesheet=False):
    """
    Return the difference between two pieces of HTML

        >>> htmldiff('test1', 'test2')
        '<span class="delete">test1 </span> <span class="insert">test2 </span> '
        >>> htmldiff('test1', 'test1')
        'test1 '
        >>> htmldiff('<b>test1</b>', '<i>test1</i>')
        '<span class="tagDelete">delete: <tt>&lt;b&gt;</tt></span> <span class="tagInsert">insert: <tt>&lt;i&gt;</tt></span> <i> test1 <span class="tagDelete">delete: <tt>&lt;/b&gt;</tt></span> <span class="tagInsert">insert: <tt>&lt;/i&gt;</tt></span> </i> '
    """
    h = HTMLMatcher(source1, source2)
    return h.htmlDiff(addStylesheet)

def diffFiles(f1, f2):
    source1 = open(f1).read()
    source2 = open(f2).read()
    return htmldiff(source1, source2, True)

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

if __name__ == '__main__':
    import sys
    if not sys.argv[1:]:
        print "Usage: %s file1 file2" % sys.argv[0]
        print "or to test: %s test" % sys.argv[0]
    elif sys.argv[1] == 'test' and not sys.argv[2:]:
        import doctest
        doctest.testmod()
    else:
        print diffFiles(sys.argv[1], sys.argv[2])
    
