# StopptableHttpServer
# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/336012
# With the addition of suppressing log output.

import thread
import httplib
import SimpleHTTPServer, BaseHTTPServer

PORT = 8080

class StoppableHttpRequestHandler (SimpleHTTPServer.SimpleHTTPRequestHandler):
    """http request handler with QUIT stopping the server"""
    
    def do_QUIT (self):
        self.send_response(200)
        self.end_headers()
        self.server.stop = True

    def log_request(self, code='-', size='-'):
        """ Suppressing log output, so that server output doesn't display
        during the running of doctests. """
        pass


class StoppableHttpServer (BaseHTTPServer.HTTPServer):
    """http server that reacts to self.stop flag"""

    def serve_forever (self):
        """Handle one request at a time until stopped."""
        self.stop = False
        while not self.stop:
            self.handle_request()


def stop (port=PORT):
    """send QUIT request to http server running on localhost:<port>"""
    conn = httplib.HTTPConnection("localhost:%d" % port)
    conn.request("QUIT", "/")
    conn.getresponse()


def start(port=PORT):
    server_address = ('', port)  
    httpd = StoppableHttpServer(server_address, StoppableHttpRequestHandler)
    thread.start_new_thread(httpd.serve_forever,())