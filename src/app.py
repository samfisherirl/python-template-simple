
from .. import standardlog
import time

__version__ = "1.0.0"
__development__ = ''


class TemplateApp(threading.Thread):
    def __init__(self, config=None, service_handle=None, options=None):
        self.config = config
        self.service_handle = service_handle
        self.options = options
        
        super(TemplateApp, self).__init__()

    def run(self):

        self.log = StandardLog()

        self.log.setup(module='templateapp',
                          path='c:\\approot\\log\\templateapp\\',
                          file='templateapp.log')


        self.running = True
        self.log.info("Starting up TemplateApp %s%s" % (__version__,
                                                                __development__))
 
        self.main()

    def main(self):
        """ Main loop for the transport. """
        while self.running:
            # Do something
            time.sleep(10)

if __name__ == '__main__':
    parser = OptionParser(version="%s%s" %(__version__, __development__))
    parser.add_option("--display-config", action="store_true", help="Display parsed configuration and exit")
    OPTIONS, AARGS = parser.parse_args()
    APP = TemplateApp(options=OPTIONS).run()