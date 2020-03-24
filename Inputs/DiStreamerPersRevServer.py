import BaseHTTPServer, json, threading, urlparse, SocketServer
import socket

class SourceServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass

class MetadataServer(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
    pass

class persRevServerActiveRequestManager:
    def __init__(self):
        self.object = None
    def set(self, object):
        self.object = object
    def get(self):
        return self.object

def makePersRevServerHandler(store, logger, config, actreq, lisclosing):
    class DiStreamerPersRevServerHandler(SocketServer.StreamRequestHandler, object):
        timeout = config['timeout']
        
        def keysToInt(s, dictionary):
            ''' THANKS!!! http://stackoverflow.com/questions/1254454/fastest-way-to-convert-a-dicts-keys-values-from-unicode-to-str '''
            if not isinstance(dictionary, dict):
                return dictionary
            return dict((int(k), s.keysToInt(v)) for k, v in dictionary.items())

        def handle(self):
            password = self.rfile.readline().strip()
            if config['password'] != '' and password != config['password']:
                self.wfile.write('err|Invalid password\r\n')
                return None
            fragments = store.getFragments()
            fkeys = fragments.keys()
            fkeys.sort()
            self.wfile.write('ok|' + '/'.join(map(str, fkeys)) + '\r\n')
            actreq.set(self)
            while not lisclosing[0]:
                info = ''
                try:
                    info = self.rfile.readline().strip()
                except:
                    if lisclosing[0]:
                        pass
                    else:
                        logger.log('Incomplete read of line', 'DiStreamerPersRevServer', 2)
                        return None
                aline = info.split('|')
                action = aline[0]
                try:
                    length = int(aline[1])
                except:
                    if lisclosing[0]:
                        pass
                    else:
                        logger.log('Error in length conversion', 'DiStreamerPersRevServer', 2)
                        return None
                content = ''
                try:
                    content = self.rfile.read(length)
                except:
                    if lisclosing[0]:
                        pass
                    else:
                        logger.log('Error redading ' + action, 'DiStreamerPersRevServer', 2)
                        return None
                if len(content) != length:
                    logger.log('Incomplete read of ' + action, 'DiStreamerPersRevServer', 2)
                    return None
                try:
                    self.rfile.read(2)
                except:
                    if lisclosing[0]:
                        pass
                    else:
                        logger.log('Error in reading final bytes', 'DiStreamerPersRevServer', 2)
                        return None
                if actreq.get() is not self:
                    logger.log('I am an old instance. I quit.', 'DiStreamerPersRevServer', 4)
                    return None
                if action == 'err':
                    logger.log('Error from client: ' + content, 'DiStreamerPersRevServer', 2)
                    return None
                if action == 'list':
                    infolist = json.loads(content)
                    store.setIcyInt(infolist['icyint'])
                    store.setIcyList(self.keysToInt(infolist['icylist']))
                    store.setIcyHeaders(infolist['icyheaders'])
                    store.setSourceGen(infolist['sourcegen'])
                    store.setIcyTitle(infolist['icytitle'].decode('base64'))
                    list = infolist['fragmentslist']
                    for localfragn in fragments.keys():
                        if(localfragn not in list):
                            del fragments[localfragn]
                            logger.log('Deleted fragment ' + str(localfragn), 'DiStreamerPersRevServer', 3)
                else:
                    x = -1
                    try:
                        x = int(action)
                    except:
                        pass
                    if x >= 0:
                        if len(fragments.keys()) > 0 and x > max(fragments.keys()) + 1:
                            logger.log('Expected fragment: ' + str(max(fragments.keys())) + ', received: ' + str(x) + '. Clearing fragments in store.', 'DiStreamerPersRevServer', 2)
                            store.clearFragmentsList()
                        fragments[x] = content
                        logger.log('Received fragment ' + str(x), 'DiStreamerPersRevServer', 3)
    return DiStreamerPersRevServerHandler

class DiStreamerPersRevServer:

    def __init__(self, store, logger):
        self.store = store
        self.logger = logger
        self.config_set = False
        self.lisclosing = [False]
        self.srv = None

    def getDefaultConfig(self):
        return {
            'hostname': '0.0.0.0',
            'port': 3080,
            'password': '',
            'timeout': 5
        }

    def setConfig(self, config):
        self.config = config
        self.config_set = True

    def run(self):
        if not self.config_set:
            self.logger.log('Config not set','DiStreamerPersRevServer',1)
            return None
        actreq = persRevServerActiveRequestManager()
        srvhandler = makePersRevServerHandler(self.store, self.logger, self.config, actreq, self.lisclosing)
        self.srv = SourceServer((self.config['hostname'], self.config['port']), srvhandler)
        self.srv.socket.setsockopt(socket.IPPROTO_IP, socket.IP_TOS, 0x40)
        self.logger.log('Server initialized', 'DiStreamerPersRevServer', 2)
        try:
            self.srv.serve_forever()
        except:
            if self.lisclosing[0]:
                pass
        self.logger.log('Server terminated', 'DiStreamerPersRevServer', 2)

    def close(self):
        self.logger.log('Closing server', 'DiStreamerPersRevServer', 2)
        self.lisclosing[0] = True
        self.srv.server_close()
