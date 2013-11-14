""" 

"""

import errno
import logging
import logging.handlers
import multiprocessing
import os
import threading
import traceback
import sys
import time


def singleton(cls):
    """ PEP318 says we should use a decorator for singletons """

    instances = {}

    def getinstance():
        if cls not in instances:
            instances[cls] = cls()
        return instances[cls]
    return getinstance

def corelog(handle, msg):
    try:
        handle.write('%s - %s\n' % (str(datetime.datetime.now()), msg))
        handle.flush()
    except:
        pass

def get_logger():
    return StandardLog()

@singleton
class StandardLog(object):
    """ The 'Standardlog' attempts to masquerade as a standard Python
        logging class, exposing many of the same methods.  We do this to
        allow a threaded logger that can take messages from child threads
        in a way that will not cause multiple file handles to be open.
    """

    file_level = logging.INFO
    screen_level = logging.DEBUG

    def __init__(self):
        self.queue = multiprocessing.Queue(-1)
        self.log = None

    def setup(self, module, path, file):
        self.path = path
        self.file = file
        self.setup_logger(module)
        self.init_thread()

    def init_thread(self):
        self.log_thread = threading.Thread(target=self.receive)
        self.log_thread.daemon = True   # Daemon threads die when the parent dies.
        self.log_thread.start()

    # Masquerade over the standard logging methods.
    def debug(self, msg):
        self.queue.put_nowait(('debug', msg))

    def info(self, msg):
        self.queue.put_nowait(('info', msg))

    def warning(self, msg):
        self.queue.put_nowait(('warning', msg))

    def error(self, msg):
        self.queue.put_nowait(('error', msg))

    def critical(self, msg):
        self.queue.put_nowait(('critical', msg))

    def receive(self):
        while True:
            try:
                record = self.queue.get()
                getattr(self.log, record[0])(record[1])
            except (KeyboardInterrupt, SystemExit):
                raise
            except EOFError, ex:
                break
            except:
                import traceback
                traceback.print_exc(file=sys.stderr)

    def setup_logger(self, module):
        """ A common method to obtain a logger """

        if not self.log:
            self.log = logging.getLogger(module)

        log = self.log

        log.module = module

        if not log.handlers:
            formatter = logging.Formatter('%(asctime)s -- %(name)s|%(levelname)-8s|%(message)s', '%Y-%m-%dT%H:%M:%S')
            console = logging.StreamHandler()
            console.setFormatter(formatter)
            log.setLevel(self.screen_level)
            log.addHandler(console)
            log_path = self.path + self.file

            import os
            if not os.path.exists(self.path):
                os.makedirs(self.path)

            self.filehandler = CustomExtensionTimedRotatingFileHandler(
                filename=log_path,
                when='midnight',
                interval=1,
                backupCount=14,
                utc=True
            )

            self.filehandler.setLevel(self.file_level)
            self.filehandler.setFormatter(formatter)
            log.addHandler(self.filehandler)

            #longhandle.setFormatter(formatter)
            #log.addHandler(longhandle)


class CustomExtensionTimedRotatingFileHandler(logging.handlers.TimedRotatingFileHandler):
    """
    Copied from the Python standard TimedRotatingFileHandler, extended
    to allow a file extension to be passed.  Defaults to '.log'.

    """
    def __init__(self, *args, **kwargs):
        # TimedRotatingFileHandler init:
        # def __init__(self, filename, when='h', interval=1, backupCount=0, encoding=None, delay=0, utc=0):
        self.extension = kwargs.get('extension') or 'log'
        # not using super since the logging classes arent new style classes
        logging.handlers.TimedRotatingFileHandler.__init__(self, *args, **kwargs)

    def getFilesToDelete(self):
        """
        Determine the files to delete when rolling over.

        More specific than the earlier method, which just used glob.glob().
        """
        dirName, baseName = os.path.split(self.baseFilename)
        fileNames = os.listdir(dirName)
        result = []
        prefix = baseName[:-4]
        plen = len(prefix)
        suffixlen = len(self.extension)
        for fileName in fileNames:
            if prefix in fileName:
                suffix = fileName[:len(fileName)-suffixlen-1][plen+1:]
                if self.extMatch.match(suffix):
                    # The stdout handle is not available.
                    #print os.path.join(dirName, fileName)
                    result.append(os.path.join(dirName, fileName))
        result.sort()
        if len(result) < self.backupCount:
            result = []
        else:
            result = result[:len(result) - self.backupCount]
        return result

    def doRollover(self):
        try:
            """
            do a rollover; in this case, a date/time stamp is appended to the filename
            when the rollover happens.  However, you want the file to be named for the
            start of the interval, not the current time.  If there is a backup count,
            then we have to get a list of matching filenames, sort them and remove
            the one with the oldest suffix.
            """

            logfile = open(LOG_DIR + r'\rollover.log','a+')

            corelog(logfile, 'starting rollover process')

            if self.stream:
                corelog(logfile, 'closing active stream')
                try:
                    self.stream.flush()
                except:
                    corelog(logfile, 'Log file flush excepted')
                    corelog(logfile, traceback.format_exc())

                try:
                    self.stream.close()
                except:
                    corelog(logfile, 'Stream close failed')
                    corelog(logfile, traceback.format_exc())


            # get the time that this sequence started at and make it a TimeTuple
            t = self.rolloverAt - self.interval
            if self.utc:
                timeTuple = time.gmtime(t)
            else:
                timeTuple = time.localtime(t)


            dfn = self.baseFilename.replace('.log','') + "." + time.strftime(self.suffix, timeTuple) + "." + self.extension
            corelog(logfile, 'dfn is %s' % dfn)

            if os.path.exists(dfn):
                corelog(logfile, 'Deleting DFN')
                os.remove(dfn)

            corelog(logfile, 'Renaming %s to %s' % (self.baseFilename, dfn))
            try:
                os.rename(self.baseFilename, dfn)
            except:
                corelog(logfile, 'Stream rename failed')
                corelog(logfile, traceback.format_exc())

            if self.backupCount > 0:
                # find the oldest log file and delete it
                #s = glob.glob(self.baseFilename + ".20*")
                #if len(s) > self.backupCount:
                #    s.sort()
                #    os.remove(s[0])
                for s in self.getFilesToDelete():
                    corelog(logfile, 'About to delete %s' % s)
                    os.remove(s)

            #print "%s -> %s" % (self.baseFilename, dfn)

            self.mode = 'w'
            corelog(logfile, 'About to reopen the logging stream')
            time.sleep(2) # sleep two second to attempt to mitigate file handle closing delays?
            self.stream = self._open()

            corelog(logfile, 'Logging stream open')
            currentTime = int(time.time())
            newRolloverAt = self.computeRollover(currentTime)

            while newRolloverAt <= currentTime:
                newRolloverAt = newRolloverAt + self.interval
            #If DST changes and midnight or weekly rollover, adjust for this.
            if (self.when == 'MIDNIGHT' or self.when.startswith('W')) and not self.utc:
                dstNow = time.localtime(currentTime)[-1]
                dstAtRollover = time.localtime(newRolloverAt)[-1]
                if dstNow != dstAtRollover:
                    if not dstNow:  # DST kicks in before next rollover, so we need to deduct an hour
                        newRolloverAt = newRolloverAt - 3600
                    else:           # DST bows out before next rollover, so we need to add an hour
                        newRolloverAt = newRolloverAt + 3600
            self.rolloverAt = newRolloverAt
            corelog(logfile, 'next rollover at %s' % str(self.rolloverAt))

        except Exception, ex:
            import traceback
            corelog(logfile, 'exception occured')
            corelog(logfile, traceback.format_exc())

        finally:
            corelog(logfile, 'closing logfile')
            logfile.close()