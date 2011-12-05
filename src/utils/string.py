def compare(str1, str2, len):
    '''
        str1 and st2 are c_uint32.
        len is the length in bytes.
    '''
    pass

def convert_to_string(str, len):
    characters = ''
    for index in xrange(len / 4):
        characters = characters + chr(str[index].value & 0xFF)
        characters = characters + chr((str[index].value >> 8) & 0xFF)
        characters = characters + chr((str[index].value >> 16) & 0xFF)
        characters = characters + chr((str[index].value >> 24) & 0xFF)
        
    remaining = len % 4
    if remaining:
        for x in xrange(remaining):
            characters = characters + chr((str[index + 1].value >> (x * 8)) & 0xFF)

    return characters