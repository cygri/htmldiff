"""
.. module:: htmldiff.fontlookup
:synopsis: Terrible hack to generate whitespace with *more accuracy.
.. moduleauthor:: Brant Watson <brant.watson@propylon.com>
"""

#  Default
times_new_roman = {
    'a': 36,
    'b': 41,
    'c': 36,
    'd': 41,
    'e': 36,
    'f': 35,
    'g': 41,
    'h': 41,
    'i': 23,
    'j': 23,
    'k': 41,
    'l': 23,
    'm': 64,
    'n': 41,
    'o': 41,
    'p': 41,
    'q': 41,
    'r': 27,
    's': 32,
    't': 23,
    'u': 41,
    'v': 41,
    'w': 58,
    'x': 41,
    'y': 51,
    'z': 36,
    'A': 59,
    'B': 50,
    'C': 50,
    'D': 58,
    'E': 50,
    'F': 45,
    'G': 59,
    'H': 59,
    'I': 27,
    'J': 32,
    'K': 58,
    'L': 50,
    'M': 72,
    'N': 58,
    'O': 58,
    'P': 45,
    'Q': 58,
    'R': 55,
    'S': 45,
    'T': 50,
    'U': 58,
    'V': 58,
    'W': 76,
    'X': 58,
    'Y': 58,
    'Z': 50,
    '0': 41,
    '1': 41,
    '2': 41,
    '3': 41,
    '4': 41,
    '5': 41,
    '6': 41,
    '7': 41,
    '8': 41,
    '9': 41,
    ' ': 20,
    'non-breaking-space': 15,
}
fonts = {'times new roman': times_new_roman}


def get_spacing(string, font_type):
    """
    Given a string & font, return approximate spacing for making more
    appropriate whitespace than would be normally generated from just
    counting characters and replacing with spaces. Currently only has a
    lookup table for Times New Roman. Possible to add support for others
    at a later point just by adding them to the font dictionary. The
    font sizes are an arbitrary unit and merely approximates.

    This will get things closer, but outside of test rendering each and
    manually calculating space and doing the conversion with that, this
    at least works to get you close.

    :type string: string
    :param string: a string to calculate whitespace for
    :type font_tye: string
    :param font_type: type of font to calculate space for
    :returns: space characters to use
    :rtype: int
    """

    if font_type not in fonts.keys():
        raise Exception("Unsupported font type specified")

    lookup_table = fonts[font_type]
    whitespace = 0
    for character in lookup_table.keys():
        occurs = string.count(character)
        ws = occurs * lookup_table[character]
        whitespace = whitespace + ws

    spaces = whitespace / lookup_table['non-breaking-space']
    spaces = round(spaces, 0)
    return int(spaces)
