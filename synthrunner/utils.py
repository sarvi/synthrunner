import sys
import time
import logging

log = logging.getLogger(__name__)  # pylint: disable=locally-disabled, invalid-name

def formattimedelta(deltatime):
    ''' Format Delta time in hours:min:secs'''
    hours, rem = divmod(deltatime, 3600)
    minutes, seconds = divmod(rem, 60)
    return "%02d:%02d:%05.2f" % (int(hours), int(minutes), seconds)



def timethis(method):
    ''' Decorator to measure time of a function '''
    def timethis_wrapper(*args, **kw):
        ''' Time this decorator support wrapper '''
        global PROMPT_TIME
        PROMPT_TIME = 0
        tstart = time.time()
        try:
            result = method(*args, **kw)
        except (SystemExit, Exception) as e:
            tend = time.time()
            if '-json' not in sys.argv and '--json' not in sys.argv:
                print("Run time({}) {} {}    ({:05.2f} seconds)".format(
                    'synthrunner', 'SUCCESS' if (isinstance(e,SystemExit) and e.code == 0) else 'FAILURE', formattimedelta(tend - tstart - PROMPT_TIME), tend - tstart - PROMPT_TIME))
            raise
        tend = time.time()
        if '-json' not in sys.argv and '--json' not in sys.argv:
            print("Run time({}) {} {}    ({:05.2f} seconds)".format(
                'synthrunner', 'SUCCESS' if result == 0 else 'FAILURE', formattimedelta(tend - tstart - PROMPT_TIME), tend - tstart - PROMPT_TIME))
        return result
    return timethis_wrapper
