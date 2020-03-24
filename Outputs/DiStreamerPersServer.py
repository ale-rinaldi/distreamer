import BaseHTTPServer
import time,json
from SocketServer import ThreadingMixIn
import socket

class DiStreamerPersServerStatsManager():
    def __init__(self):
        self.counter = 0
    def add(self):
        self.counter += 1
    def rem(self):
        self.counter -= 1
    def get(self):
        return self.counter

class ThreadingSimpleServer(ThreadingMixIn, BaseHTTPServer.HTTPServer):
    pass

def makeServerHandler(store, logger, config, lisclosing, statmgr):
    class DiStreamerPersServerHandler(BaseHTTPServer.BaseHTTPRequestHandler, object):
        statpages = ['/stats', '/favicon.ico']
        def do_HEAD(s):
            s.added = False
            s.send_response(200)
            s.send_header("Server", "DiStreamer")
            icyheaders = store.getIcyHeaders()
            for header in icyheaders:
                s.send_header(header, icyheaders[header])
            if(store.getIcyInt() > 0):
                s.send_header("icy-metaint", str(store.getIcyInt()))

        def do_GET(s):
            s.added = False
            fragments = store.getFragments()
            if s.path in s.statpages:
                s.send_response(200)
                s.send_header('content-type', 'application/json')
                s.end_headers()
                s.wfile.write(json.dumps({
                    'connectedClients':statmgr.get(),
                    'fragmentsList':fragments.keys()
                    }))
                return None
            statmgr.add()
            s.added = True
            path = s.path[1:]
            sentlist = path.split('/')
            password = sentlist.pop(0)
            if config['password'] != '' and config['password'] != password:
                s.wfile.write('err|18\r\nPassword incorrect\r\n')
                return None
            if len(fragments.keys()) > 0:
                lastsent = min(fragments.keys()) - 1
            else:
                lastsent = 0
            while not lisclosing[0]:
                tosend = ''
                locallist = fragments.keys()
                locallist.sort()
                list = json.dumps({
                    'fragmentslist': locallist,
                    'icyint': store.getIcyInt(),
                    'icylist': store.getIcyList(),
                    'icyheaders': store.getIcyHeaders(),
                    'icytitle': store.getIcyTitle().encode('base64'),
                    'sourcegen': store.getSourceGen()
                })
                for fragn in locallist:
                    if fragn not in sentlist:
                        if fragn != lastsent + 1:
                            logger.log('Expected fragment: ' + str(lastsent + 1) + ', first available: ' + str(fragn) + '. Closing stream to client.', 'DiStreamerPersServer', 2)
                            return None
                        tosend += str(fragn) + '|' + str(len(fragments[fragn])) + '\r\n' + fragments[fragn] + '\r\n'
                        lastsent = fragn
                        sentlist.append(fragn)
                tosend += 'list|' + str(len(list)) + '\r\n' + list + '\r\n'
                for sentn in sentlist:
                    if not sentn in locallist:
                        sentlist.remove(sentn)
                        logger.log('Removed from sent list: ' + str(sentn), 'DiStreamerPersServer', 4)
                s.wfile.write(tosend)
                time.sleep(config['interval'])
        def log_message(self, format, *args):
            return
        
        def finish(s):
            if s.added:
                statmgr.rem()

    return DiStreamerPersServerHandler

class DiStreamerPersServer:
    def __init__(self, store, logger):
        self.store = store
        self.logger = logger
        self.config_set = False

    def getDefaultConfig(self):
        return {
            'hostname': '0.0.0.0',
            'port': 4080,
            'password': '',
            'interval': 1
        }

    def setConfig(self, config):
        self.config = config
        self.config_set = True

    def run(self):
        if not self.config_set:
            self.logger.log("Config not set", 'DiStreamerPersServer', 1)
            return None
        self.logger.log('Starting', 'DiStreamerPersServer', 2)
        self.lisclosing = [False]
        statmgr=DiStreamerPersServerStatsManager()
        handler=makeServerHandler(self.store, self.logger, self.config, self.lisclosing, statmgr)
        self.httpd = ThreadingSimpleServer((self.config['hostname'], self.config['port']), handler)
        self.httpd.socket.setsockopt(socket.IPPROTO_IP, socket.IP_TOS, 0x40)
        self.logger.log('Started', 'DiStreamerPersServer', 2)
        try:
            self.httpd.serve_forever()
        except:
            pass
        self.logger.log('Server terminated', 'DiStreamerPersServer', 2)

    def close(self):
        self.logger.log('Exiting normally', 'DiStreamerPersServer', 2)
        self.httpd.server_close()
        self.lisclosing[0] = True
