class Token

class String(Token):
    """ SymPy object representing a string. """
    __slots__ = ('text',)
    not_in_args = ['text'] # This is causing the problem
    is_Atom = True

    # ...