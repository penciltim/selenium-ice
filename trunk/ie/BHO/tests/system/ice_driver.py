import win32com.client
import win32gui
import win32process
import win32con
import win32api
import winGuiAuto as wga

import pythoncom
from threading import Thread
import time

DEBUG = False

"""
TODO:
* Cancel requests if a dialog is visible and expecting input.
  Otherwise, requests get "stacked" up waiting for the dialog to be closed.
  And we might not want to do some actions if we have to deal with a dialog first.
  

"""

settings = {
    "dialog.all.logging": "Warn",     # "Error" | "Warn" | "None"
    "dialog.all.action":  "None"         # "OK" | "Cancel" | "Close" | None
}

class UnexpectedDialogBox(Exception):
    def __init__(self, value):
        self.value = value
    
    def __str__(self):
        return repr(self.value)

class MessageDispatcher(Thread):
    def __init__ (self, istream, message):
        Thread.__init__(self)
        self.istream = istream
        self.message= message
    
    def run(self):
        pythoncom.CoInitialize()
        d=pythoncom.CoGetInterfaceAndReleaseStream(self.istream, pythoncom.IID_IDispatch)
        self.browser=win32com.client.Dispatch(d)
        self.waitUntilReady()
        # TODO: convert this into an "apply" call instead
        eval("self.browser." + self.message)
        pythoncom.CoUninitialize()
    
    def waitUntilReady(self):
        while self.browser.Busy:
            # this is a naive approach, but works in the very simple cases
            # should also add a wait for "readyState == 'complete'", too.
            time.sleep(.20)    

class Browser:
    def __init__(self):
        if DEBUG:
            # threadlist is useful for analyzing blocked threads during debugging..
            self.threadlist = []
        self._timeout = 3      # wait no more than 5 seconds before responding
        self._sleep_increment = .2  # sleep in 1/5 second increments
        
        # just a shortcut for .script
        #self.js = self.script
        
        self.app = win32com.client.Dispatch('internetexplorer.application')
        self.app.Visible = 1
        self.handle = self.app.HWND
        self.focus()
        self.should_wait = True
        self.dialog = Dialog(self.app)
        self.settings = settings
    
    def focus(self):
        # this doesn't always work... :-(
        win32gui.SetForegroundWindow(self.handle)         
    
    def quit(self):
        # The Old Way
        #   It didn't work if an alert box was present.
        #message = "Quit()"
        #self._dispatch_message(message)
        
        # The New Way
        #   Kills the browser -- no matter what!
        #   See http://www.velocityreviews.com/forums/t363843-kill-process-based-on-window-name-win32.html
        
        # Get the window's process id's
        t, p = win32process.GetWindowThreadProcessId(self.handle)
        
        # Ask window nicely to close
        win32gui.PostMessage(self.handle, win32con.WM_CLOSE, 0, 0)
        
        # Allow some time for app to close
        time.sleep(2)
        
        # If app didn't close, force close
        try:
            handle = win32api.OpenProcess(win32con.PROCESS_TERMINATE, 0, p)
            if handle:
                win32api.TerminateProcess(handle,0)
                win32api.CloseHandle(handle)
        except:   # FIXME: NAKED exception...
            # If we got here, IE most likely had already closed cleanly. 
            #print "Got to the naked exception!"
            pass
    
    def goto(self, url):
        message = 'Navigate("' + url + '")'        
        self._dispatch_message(message)
    
    def script(self, code):
        javascript_code = 'Document.parentWindow.execScript("' + code + '")'
        self._dispatch_message(javascript_code)        
    
    def alert(self, text_message):
        alert_message = "alert('" + text_message + "')"
        self.script(alert_message)
    
    
    # Private methods
    def _dispatch_message(self, message):
        s=pythoncom.CoMarshalInterThreadInterfaceInStream(pythoncom.IID_IDispatch,self.app)
        new_message = MessageDispatcher(s, message)
        
        new_message.setDaemon(True)
        new_message.start()
        if DEBUG:
            self.threadlist.append(new_message)
        
        counter = 0
        i_should_keep_trying = True
        while i_should_keep_trying:         
            counter += 1   
            
            if new_message.isAlive() and (counter >= (self._timeout / self._sleep_increment)):
                
                if self.dialog.list() > 0:
                    if self.settings['dialog.all.logging'] == 'Error':
                        raise UnexpectedDialogBox("Error: unexpected dialog box")
                        #print "Error: Unexpected dialog box"
                    elif self.settings['dialog.all.logging'] == 'Warn':  
                        print "Warn: Unexpected dialog box"
                    elif self.settings['dialog.all.logging'] == 'None':  
                        pass                       

                    if self.settings['dialog.all.action'] == 'OK':
                        self.dialog.click("OK")
                    elif self.settings['dialog.all.action'] == 'Cancel':
                        print "Placeholder for action: Cancel"
                    elif self.settings['dialog.all.action'] == 'None':
                        pass
                
                i_should_keep_trying = False
                break            
            
            if not new_message.isAlive():
                # the thread ended cleanly, no more need to wait...
                if DEBUG:
                    self.threadlist.remove( self.threadlist[-1] )
                i_should_keep_trying = False
                break
                          
            time.sleep( self._sleep_increment )

class Dialog:
    def __init__(self, app_instance):
        self.app = app_instance

    def list(self):
        return win32gui.FindWindow("#32770","Microsoft Internet Explorer")
        
    def click(self, button_text):
        handle = win32gui.FindWindow("#32770","Microsoft Internet Explorer")
        button = wga.findControl(handle,
                                 wantedClass = "Button",
                                 wantedText = "OK")
        wga.clickButton(button)

if __name__ == '__main__':
    browser = Browser()
    browser.goto("http://localhost:8000/bho-tests.html")
    browser.script("document.getElementById('set-file-field').click()")  
    browser.script("document.getElementById('say-hello').click()")      
    browser.script("document.getElementById('show-message').click()") 
    browser.quit()


"""
doctests:

>>> from ice_driver import Browser
>>> browser = Browser()
>>> browser.alert("hello")
>>> browser.goto("http://localhost:8000/bho-tests.html")
>>> browser.quit()

"""

"""

alert:
    1 button - "OK"
    
    Things to test:
    actions - * error, leave dialog up (take no action) 
              * error, take default action  
              * log warning, take default action
              * take default action,                           
"""