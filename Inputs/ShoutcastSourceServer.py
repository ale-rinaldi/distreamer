import BaseHTTPServer, json, threading, urlparse, SocketServer
import socket
from datetime import datetime

class SourceServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass

class MetadataServer(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
    pass

class SourceConnectedManager:
    def __init__(self):
        self.connected = False
    def set(self,val):
        if type(val) is bool:
            self.connected = val
    def get(self):
        return self.connected

class ShoutcastSourceServerTitleQueue:
    def __init__(self):
        self.reset()
    def add(self,title):
        self.queue.append(title)
        self.current = title
    def get(self):
        if len(self.queue) > 0:
            return self.queue.pop(0)
        else:
            return ''
    def getCurrent(self):
        return self.current
    def reset(self):
        self.queue = []
        self.current = ''

class ShoutcastSourceServerFragmentsManager:
    def __init__(self, store, logger, config):
        self.store = store
        self.logger = logger
        self.config = config
        self.currentfrag = ''
        fragkeys = store.getFragments().keys()
        if len(fragkeys) > 0:
            self.fragcounter = max(fragkeys) + 1
        else:
            self.fragcounter = 1
        self.poscounter = 0
    def push(self,piece):
        while len(piece) >= self.config['fragmentsize'] - self.poscounter:
            last = self.config['fragmentsize'] - self.poscounter
            self.currentfrag = self.currentfrag + piece[:last]
            fragments = self.store.getFragments()
            fragments[self.fragcounter] = self.currentfrag
            self.logger.log('Created fragment ' + str(self.fragcounter), 'ShoutcastSourceServer', 3)
            self.deleteOldFragments(fragments)
            self.store.setFragments(fragments)
            self.currentfrag = ''
            self.fragcounter += 1
            self.poscounter = 0
            piece = piece[last:]
        self.currentfrag = self.currentfrag + piece
        self.poscounter += len(piece)
    def deleteOldFragments(self, fragments):
        icylist = self.store.getIcyList()
        while len(fragments) > self.config['fragmentsnumber']:
            todelete = min(fragments.keys())
            del fragments[todelete]
            if icylist.has_key(todelete):
                del icylist[todelete]
            self.logger.log("Deleted fragment " + str(todelete), 'ShoutcastSourceServer', 3)
        self.store.setIcyList(icylist)
    def setIcyPos(self):
        icylist = self.store.getIcyList()
        if not icylist.has_key(self.fragcounter):
            icylist[self.fragcounter] = []
        icylist[self.fragcounter].append(self.poscounter)
        self.store.setIcyList(icylist)

def makeMetadataServerHandler(store, logger, config, sourceconn, titlequeue):
    class ShoutcastSourceMetadataServerHandler(BaseHTTPServer.BaseHTTPRequestHandler, object):
        timeout = config['timeout']
        def do_HEAD(s):
            path = urlparse.urlparse('http://distreamer' + s.path).path
            if path == '/admin.cgi' and sourceconn.get():
                s.send_response(200)
                s.send_header('Server', 'DiStreamer')
            elif path == '/stats':
                s.send_response(200)
                s.send_header('Server', 'DiStreamer')
                s.send_header('Content-Type', 'text/plain')
            else:
                s.send_response(404)
                s.send_header('Server', 'DiStreamer')

        def do_GET(s):
            path = urlparse.urlparse('http://distreamer' + s.path).path
            if path == '/admin.cgi' and sourceconn.get():
                if config['icyint'] > 0:
                    params = urlparse.parse_qs(urlparse.urlparse('http://distreamer' + s.path).query)
                    if params['mode'][0] == 'updinfo' and params['pass'][0] == config['password']:
                        titlequeue.add(params['song'][0])
            elif path == '/stats':
                s.send_response(200)
                s.send_header('Server','DiStreamer')
                s.send_header('Content-Type','text/plain')
                s.end_headers()
                s.wfile.write(json.dumps({'sourceConnected':sourceconn.get()}))
            else:
                s.send_response(404)
                s.send_header("Server", "DiStreamer")

        def log_message(self, format, *args):
            return
    return ShoutcastSourceMetadataServerHandler

def makeSourceServerHandler(store, logger, config, sourceconn, titlequeue, lisclosing):
    class ShoutcastSourceServerHandler(SocketServer.StreamRequestHandler, object):
        timeout = config['timeout']

        def getTimestamp(self):
            return round((datetime.utcnow() - datetime(1970, 1, 1)).total_seconds(), 2)

        def formatTitle(s, song):
            if song == '':
                return ''
            formtitle = 'StreamTitle=\'' + song + '\';'
            if len(formtitle) > 4080:
                raise ValueError('Title too long')
            while len(formtitle) % 16 != 0:
                formtitle += '\0'
            return formtitle

        def readToString(self, end):
            buf = ''
            endlen = len(end)
            while buf[-endlen:] != end:
                buf += self.rfile.read(1)
            return buf

        def handle(self):
            ''' Set to false after all the verifications '''
            self.haderror = True
            password = self.rfile.readline().strip()
            if password != config['password']:
                self.wfile.write('invalid password\r\n')
                return None
            self.wfile.write('OK2\r\nicy-caps:11\r\n\r\n')
            headers = {}
            headerscount = 0
            while True:
                headerscount += 1
                if headerscount > 100:
                    self.close()
                    raise ValueError('Too many headers received')
                lheader = self.rfile.readline(65537)
                ''' The real Shoutcast Server closes connection with the source after it receives the first header if another source is already connected, so let's keep this strange behaviour '''
                if sourceconn.get():
                    self.close()
                    return None
                if len(lheader) > 65536:
                    self.close()
                    raise ValueError('Header too long')
                header = lheader.strip()
                if header == '':
                    logger.log("Empty header line, stream is beginning", 'ShoutcastSourceServer', 4)
                    break
                logger.log("Received header - " + header, 'ShoutcastSourceServer', 4)
                seppos = header.find(':')
                k = header[:seppos].strip()
                v = header[seppos + 1:].strip()
                if (k.lower()[:4] == 'icy-' or k.lower() == 'content-type') and k.lower() not in ['icy-metaint', 'icy-reset','icy-prebuffer']:
                    headers[k] = v
            if headerscount == 0:
                s.close()
                raise ValueError('No headers received')
            sourceconn.set(True)
            self.haderror = False
            logger.log('Source connected', 'ShoutcastSourceServer', 4)
            store.reset()
            store.incrementSourceGen()
            store.setIcyHeaders(headers)
            store.setIcyInt(config['icyint'])
            fmanager = ShoutcastSourceServerFragmentsManager(store, logger, config)
            icyint = config['icyint']
            if icyint > 0:
                toread = icyint
            else:
                toread = config['fragmentsize']
            # Search OGG header
            initialBuf = self.rfile.read(6)
            # Handle the additional newline that some clients like Rocket Broadcaster erroneusly send
            if initialBuf[:2] == "\r\n":
                logger.log('Additional newline removed', 'ShoutcastSourceServer', 4)
                initialBuf = initialBuf[2:]
            if initialBuf.strip()[:4] == 'OggS':
                logger.log('OGG format detected', 'ShoutcastSourceServer', 4)
                # The first two ones are the headers
                initialBuf = initialBuf + self.readToString('OggS')
                initialBuf = initialBuf + self.readToString('OggS')
                store.setOggHeader(initialBuf[:-4])
                initialBuf = 'OggS'
            # Set the initial time for the time key insertion
            lastTimekey = 0
            # Start receiving fragments
            while not lisclosing[0]:
                if len(initialBuf) >= toread:
                    buf = initialBuf[:toread]
                    initialBuf = initialBuf[toread:]
                else:
                    try:
                        buf = initialBuf + self.rfile.read(toread - len(initialBuf))
                    except:
                        if lisclosing[0]:
                            return None
                    initialBuf = ''
                if len(buf) != toread:
                    raise ValueError("Incomplete read of block")
                fmanager.push(buf)
                if icyint > 0:
                    # If no timekey is required, just add the title if there's a new one
                    if config['timekeyinterval'] < 0:
                        title = titlequeue.get()
                    else:
                        newTitle = titlequeue.get()
                        lastTitle = titlequeue.getCurrent()
                        if newTitle != "" or self.getTimestamp() - lastTimekey > config['timekeyinterval']:
                            title = lastTitle + ' {' + str(self.getTimestamp()) + '}'
                        else:
                            title = ""
                    formattedTitle = self.formatTitle(title)
                    chridx = len(formattedTitle) / 16
                    fmanager.setIcyPos()
                    fmanager.push(chr(chridx))
                    fmanager.push(formattedTitle)
                    if formattedTitle != '':
                        store.setIcyTitle(formattedTitle)
        def finish(self):
            if not self.haderror:
                titlequeue.reset()
                sourceconn.set(False)
    return ShoutcastSourceServerHandler

class MetadataServerThread(threading.Thread):
    def __init__(self, metadataserver, logger, lisclosing):
        threading.Thread.__init__(self)
        self.metadataserver = metadataserver
        self.logger = logger
        self.lisclosing = lisclosing
    def run(self):
        try:
            self.metadataserver.serve_forever()
        except:
            if self.lisclosing[0]:
                pass
        self.logger.log('Metadata server terminated', 'ShoutcastSourceServer', 2)
    def close(self):
        self.logger.log('Closing metadata server', 'ShoutcastSourceServer', 2)
        self.metadataserver.server_close()

class ShoutcastSourceServer:

    def __init__(self,store,logger):
        self.store = store
        self.logger = logger
        self.config_set = False
        self.lisclosing = [False]
        self.sourceserver = None

    def getDefaultConfig(self):
        return {
            'hostname': '0.0.0.0',
            'port': 8080,
            'password': 'distreamer',
            'fragmentsnumber': 5,
            'fragmentsize': 81920,
            'timeout': 5,
            'icyint': 8192,
            'timekeyinterval': -1,
        }

    def setConfig(self,config):
        self.config = config
        self.config_set = True

    def run(self):
        if not self.config_set:
            self.logger.log('Config not set','ShoutcastSourceServer',1)
            return None
        sourceconn = SourceConnectedManager()
        titlequeue = ShoutcastSourceServerTitleQueue()
        metadatahandler = makeMetadataServerHandler(self.store, self.logger, self.config, sourceconn, titlequeue)
        metadataserver = MetadataServer((self.config['hostname'], self.config['port']), metadatahandler)
        metadataserver.socket.setsockopt(socket.IPPROTO_IP, socket.IP_TOS, 0x40)
        self.metadatathread = MetadataServerThread(metadataserver, self.logger, self.lisclosing)
        self.logger.log('Metadata server initialized', 'ShoutcastSourceServer', 2)
        sourcehandler = makeSourceServerHandler(self.store, self.logger, self.config, sourceconn, titlequeue, self.lisclosing)
        self.sourceserver = SourceServer((self.config['hostname'], self.config['port'] + 1), sourcehandler)
        self.sourceserver.socket.setsockopt(socket.IPPROTO_IP, socket.IP_TOS, 0x40)
        self.logger.log('Source server initialized', 'ShoutcastSourceServer', 2)
        self.metadatathread.start()
        try:
            self.sourceserver.serve_forever()
        except:
            if self.lisclosing[0]:
                pass
        self.logger.log('Source server terminated', 'ShoutcastSourceServer', 2)

    def close(self):
        self.logger.log('Closing source server', 'ShoutcastSourceServer', 2)
        self.lisclosing[0] = True
        self.metadatathread.close()
        self.sourceserver.server_close()
