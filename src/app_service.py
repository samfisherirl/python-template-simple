'''

Service Template

'''

# pylint: disable=C0301, C0103


import win32serviceutil
import win32service
import win32event
import win32evtlogutil

from app import templateapp


class TemplateService(win32serviceutil.ServiceFramework):
   
    _svc_name_ = "TemplateServiecName"
    _svc_display_name_ = "Template Service Name"   
    _svc_deps_ = ["EventLog"]

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        import servicemanager
        # Write a 'started' event to the event log...
        win32evtlogutil.ReportEvent(self._svc_name_,
                                    servicemanager.PYS_SERVICE_STARTED,
                                    0, # category
                                    servicemanager.EVENTLOG_INFORMATION_TYPE,
                                    (self._svc_name_, ''))

        self.app = templateapp()
        self.app.daemon = True
        self.app.start()

        # wait for beeing stopped...
        win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)

        # and write a 'stopped' event to the event log.
        win32evtlogutil.ReportEvent(self._svc_name_,
                                    servicemanager.PYS_SERVICE_STOPPED,
                                    0, # category
                                    servicemanager.EVENTLOG_INFORMATION_TYPE,
                                    (self._svc_name_, ''))

                                
if __name__ == '__main__':   
    win32serviceutil.HandleCommandLine(templateapp)

