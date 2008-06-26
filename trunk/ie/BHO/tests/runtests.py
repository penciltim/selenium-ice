import sys
sys.path.append("system")

# TODO: refactor to add support for running unit tests.

if __name__ == '__main__':
    if (len(sys.argv) == 2) and (sys.argv[1] == 'system'):
      print '\nIce Tester'
      print '----------------------------------------------------------------------\n'
      import doctest, unittest
      
      test_suite_type =  sys.argv[1]
    
      if test_suite_type in ['system']:
          print '** Running system tests - system_test.txt'
          suite = doctest.DocFileSuite('system/system_test.txt', optionflags=doctest.ELLIPSIS)
          unittest.TextTestRunner().run(suite)
    else:
      print """
  Ice Tester 
       
  Usage: 
    When run as a script, testing options are available:
    $ python runtests.py [system]
  """
