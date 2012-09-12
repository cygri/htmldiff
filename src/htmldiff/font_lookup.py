# Tool for generating whitespace with more accuracy.
times_new_roman = {
'a':36,
'b':40.5,
'c':36,
'd':40.5,
'e':36,
'f':35,
'g':40.5,
'h':40.5,
'i':22.5,
'j':22.5,
'k':40.5,
'l':22.5,
'm':63.5,
'n':40.5,
'o':40.5,
'p':40.5,
'q':40.5,
'r':27,
's':32,
't':22.5,
'u':40.5,
'v':40.5,
'w':58,
'x':40.5,
'y':50.5,
'z':36,
'A':59,
'B':50,
'C':50,
'D':58,
'E':50,
'F':45,
'G':59,
'H':59,
'I':26.5,
'J':32,
'K':58,
'L':49.5,
'M':72,
'N':58,
'O':58,
'P':45,
'Q':58,
'R':54.5,
'S':45,
'T':50,
'U':58,
'V':58,
'W':76,
'X':58,
'Y':58,
'Z':49.5,
'0':40.5,
'1':40.5,
'2':40.5,
'3':40.5,
'4':40.5,
'5':40.5,
'6':40.5,
'7':40.5,
'8':40.5,
'9':40.5,
' ':20.2,
}
fonts = {
'times new roman': times_new_roman,
}
def get_spacing(string, font_type):
    """
    Given a string & font, return approximate spacing for making more
    appropriate whitespace than would be normally generated from just
    counting characters and replacing with spaces. Currently only has a
    lookup table for Times New Roman. Possible to add support for others
    at a later point just by adding them to the font dictionary
    
    @type string: string
    @param string: a string to calculate whitespace for
    @type font_tye: string
    @param font_type: type of font to calculate space for
    @return: integer of space characters to use
    """
    
    if font_type not in fonts.keys():
        raise Exception("Unsupported font type specified")
    
    lookup_table = fonts[font_type]
    whitespace = 0
    for character in lookup_table.keys():
        occurs = string.count(character)
        ws = occurs * lookup_table[character]
        whitespace = whitespace + ws
    
    #print "Total Whitespace: %s" % str(whitespace)
    spaces = whitespace/lookup_table[' ']
    #print "Estimated space characters: %s" % str(spaces)
    #print "As Int: %s" % str(int(spaces))
    return int(spaces)
