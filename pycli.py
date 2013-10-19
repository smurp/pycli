#!/usr/bin/env python
__version__='1.0.3'
__doc__ = """
pycli.py is python boilerplate code written by
Shawn Murphy<smurp@smurp.com> to act as a starting point for his
command-line programs.  It offers basic features such as:
  - doctest testing
  - automatic manual creation
  - version inspection
See it on github at:
  http://github.com/smurp/pycli/
"""

def dummy_meth(a):
    """
    >>> dummy_meth('a')
    'a'
    
    """
    return a

if __name__ == "__main__":        
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("--doctest",
                      action = 'store_true',
                      help = "perform doc tests")
    parser.add_option("--man",
                      action = 'store_true',
                      help = "show the manual for this program")
    parser.add_option("-v","--verbose",
                      action = 'store_true',
                      help = "be verbose in all things, go with god")
    parser.add_option("-V","--version",
                      action = 'store_true',
                      help = "show version")
    parser.add_option("--int",
                      type="int",
                      help = "accept an integer")
    parser.add_option("--str",
                      help = "accept a string")
    parser.version = __version__
    parser.usage =  """
    e.g.
       %prog --doctest
          Perform unit tests on the %prog
    """
    (options,args) = parser.parse_args()
    show_usage = True
    if options.doctest:
        show_usage = False
        import doctest
        doctest.testmod(verbose=options.verbose)
    if options.version:
        show_usage = False
        if options.verbose:
            print __cvs_id__
        else:
            print parser.version
    if options.man:
        show_usage = False
        import pydoc
        pydoc.help(__import__(__name__))
    if show_usage:
        parser.print_help()
