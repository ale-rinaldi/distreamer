import BaseHTTPServer
import time,json
from SocketServer import ThreadingMixIn
import socket

class ShoutcastServerStatsManager():
    def __init__(self):
        self.counter = 0
    def add(self):
        self.counter += 1
    def rem(self):
        self.counter -= 1
    def get(self):
        return self.counter

class ShoutcastServerSendManager:

    # Initialize the class
    def __init__(self, wfile, icyint, icytitle):
        self.wfile = wfile
        self.icyint = icyint
        self.remaining = icyint
        self.icytitle = icytitle
        self.firstsent = False

class ShoutcastServerFragsManager:

    # Initializes the class
    def __init__(self, store, logger, config):
        self.store = store
        self.logger = logger
        self.config = config
        # Fragments are passed by reference
        self.fragments = store.getFragments()
        # Local list
        self.loclist = []
        self.reconn =- 1
        # Set variables for current fragment and position inside the fragment itself
        self.currfrag =- 1
        self.currpos = 0

    # Initializes the parameters on first call only
    def initialize(self):
        # Set the local source generation
        self.reconn = self.store.getSourceGen()
        # Get the first and the last available fragment
        firstfragment = min(self.loclist)
        lastfragment = max(self.loclist)
        # Calculate the fragment to start with, depending on the minfragments setting
        if self.config['minfragments'] > 0:
            # Calculate the current fragment so that we exactly have a number of fragments to stream equal to minfragments
            currfrag = lastfragment - self.config['minfragments'] + 1
            # If the calculated current fragment does not exist, fall back to the first one
            if not currfrag in self.loclist:
                currfrag = firstfragment
        # If minfragments is not set, always use the first one
        else:
            currfrag = firstfragment
        self.currfrag = currfrag

    # Update the local fragments list and check integrity with the store
    def updateLocalList(self):
        # If there are no fragments in the store, probably we're in the middle of an input restart. Keep everything as it is
        if len(self.fragments) == 0 or self.store.getSourceGen() == 0:
            return True
        # Update the local fragments list
        self.loclist = self.fragments.keys()
        self.loclist.sort()
        # Initialize if this is the first call
        if self.reconn < 0:
            self.initialize()
        # If the local source gen is different than the store one, stop
        if self.store.getSourceGen() != self.reconn:
            self.logger.log('Local source gen: ' + str(self.reconn) + ', source gen: ' + str(self.store.getSourceGen()), 'ShoutcastServer', 2)
            return False
        # If the current fragment is already out of the store, close
        if self.currfrag < min(self.loclist):
            self.logger.log('Current fragment ' + str(self.currfrag) + ' is lower than the first fragment in the store ' + str(min(self.loclist)), 'ShoutcastServer', 2)
            return False
        return True

    # Gets a custom number of bytes from the stream. The function always returns the exact number of bytes, waiting for them if they're not available. It logs to the logger and returns False in case of error.
    def getBytes(self, num, skiplog = False):
        tosend = ''
        lastsendtime = int(time.time())
        if num == 0:
            return ''
        while len(tosend) < num:
            # Detect a timeout
            if int(time.time()) - lastsendtime > self.config['timeout'] and self.config['timeout'] > 0:
                self.logger.log('Timeout reached','ShoutcastServer',2)
            # If the current fragment is not yet in the store, wait redo all the cycle
            if self.currfrag not in self.loclist:
                time.sleep(1)
                continue
            # Calculate how many bytes we need to get
            remaining = num - len(tosend)
            # Calculate the length of the remaining part of the current fragment
            fraglen = len(self.fragments[self.currfrag][self.currpos:])
            # If the current fragment has enough bytes in it to satisfy the request, we're done
            if fraglen >= remaining:
                if not skiplog:
                    self.logger.log('Sending fragment ' + str(self.currfrag) + ' from byte ' + str(self.currpos) + ' to byte ' + str(self.currpos + remaining),'ShoutcastServer', 4)
                # Extract the piece of fragment to send and concatenate it to tosend
                tosend += self.fragments[self.currfrag][self.currpos:self.currpos+remaining]
                # Increment the pointer
                self.currpos += remaining
                # If we are at the end of the fragment, move the pointer to the next one
                if self.currpos == len(self.fragments[self.currfrag]):
                    self.currfrag += 1
                    self.currpos = 0
                # Return
                return tosend
            # Else, append all the fragment to tosend and move the pointer to the next one
            else:
                self.logger.log('Sending fragment ' + str(self.currfrag) + ' from byte ' + str(self.currpos), 'ShoutcastServer', 4)
                tosend += self.fragments[self.currfrag][self.currpos:]
                lastsendtime = int(time.time())
                self.currfrag += 1
                self.currpos = 0

    # Gets all the available bytes from the stream. This function always returns immediately, if no new bytes are available it returns an empty string. It logs to the logger and returns False in case of error.
    def getAll(self):
<<<<<<< HEAD
        if not self.updateLocalList():
            self.logger.log('Got error in local list update', 'ShoutcastServer', 2)
            return ''
=======
>>>>>>> Fix Winamp compatibility
        tosend = ''
        while self.currfrag in self.loclist:
            self.logger.log('Sending fragment ' + str(self.currfrag) + ' from byte ' + str(self.currpos), 'ShoutcastServer', 4)
            tosend += self.fragments[self.currfrag][self.currpos:]
            self.currfrag += 1
            self.currpos = 0
        return tosend

    # Returns everything until the beginning of the next metadata block
    def getToBeforeNextMeta(self):
        inittime = int(time.time())
        toret = ''
        while int(time.time())-inittime <= self.config['timeout'] or self.config['timeout'] <= 0:
            icylist = self.store.getIcyList()
            icykeys = icylist.keys()
            icykeys.sort()
            for key in icykeys:
                if key < self.currfrag:
                    continue
                keylist = icylist[key]
                keylist.sort()
                for meta in keylist:
                    if key > self.currfrag:
                        toreadbytes = len(self.fragments[self.currfrag][self.currpos:])
                        for frag in range(self.currfrag + 1, key):
                            toreadbytes += len(self.fragments[frag])
                        toreadbytes += len(self.fragments[key][:meta])
                        return self.getBytes(toreadbytes)
                    elif key == self.currfrag and meta >= self.currpos:
                        toreadbytes = meta - self.currpos
                        return self.getBytes(toreadbytes)
            time.sleep(1)
        self.logger.log('Timeout reached','ShoutcastServer',2)
        return False

    # Returns everything until the beginning of the block after the next available metadata.
    def getToAfterNextMeta(self):
        toret = self.getToBeforeNextMeta()
        if toret == False:
            self.logger.log('Error getting to before next meta', 'ShoutcastServer', 2)
            return False
        ordicylen = self.getBytes(1)
        if not ordicylen:
            self.logger.log('Incomplete read of metadata length', 'ShoutcastServer', 2)
            return False
        toret += ordicylen
        icylen = ord(ordicylen) * 16
        if icylen > 0:
            title = self.getBytes(icylen)
            if len(title) != icylen:
                self.logger.log('Incomplete read of title', 'ShoutcastServer', 2)
                return False
            toret += title
        return toret

    def getToAfterNextOGGHeader(self):
        inittime = int(time.time())
        toret = ''
        while int(time.time())-inittime <= self.config['timeout'] or self.config['timeout'] <= 0:
            toret = toret + self.getBytes(1, True)
            if toret[-4:] == "OggS":
                return toret
        self.logger.log('Timeout reached','ShoutcastServer',2)
        return False



class ThreadingSimpleServer(ThreadingMixIn, BaseHTTPServer.HTTPServer):
    pass

def makeServerHandler(store, logger, config, lisclosing, statmgr):
    class shoutcastServerHandler(BaseHTTPServer.BaseHTTPRequestHandler,object):
        statpages = ['/stats','/favicon.ico']

        def generateDummyOggPages(self, size, streamid):
            newsize = size
            toret = ""
            # To improve compatibility, we generate multiple pages no longer than 255 bytes (28 bytes of header and 227 bytes of dummy data)
            # 283 = 255+28. 28 is the header size.
            while newsize > 283:
                # A 255 byte OGG page
                toret += 'OggS' + chr(0) * 10 + streamid + chr(1) + chr(0) * 2 + chr(1) + chr(0) * 4 + chr(1) + chr(227) + chr(0) * 227
                newsize -= 255
            # Here we generate the last page size
            newsize -= 28
            toret += 'OggS' + chr(0) * 10 + streamid + chr(1) + chr(0) * 2 + chr(1) + chr(0) * 4 + chr(1) + chr(newsize) + chr(0) * newsize
            return toret

        def do_HEAD(s):
            s.added = False
            s.send_response(200)
            s.send_header("Server", "DiStreamer")
            icyheaders = store.getIcyHeaders()
            for header in icyheaders:
                s.send_header(header,icyheaders[header])
            if(store.getIcyInt() > 0):
                s.send_header("icy-metaint", str(store.getIcyInt()))

        def do_GET(s):
            # The stream has not been added to the counter yet
            s.added = False
            # Get stream information from the store
            fragments = store.getFragments()
            reconnect = store.getSourceGen()
            # Send statistics if required (TODO: manage favicon in a different way...)
            if s.path in s.statpages:
                s.send_response(200)
                s.send_header('content-type','application/json')
                s.end_headers()
                s.wfile.write(json.dumps({
                    'connectedClients':statmgr.get(),
                    'fragmentsList':fragments.keys(),
                    'storeAge': int(time.time()) - store.getLastUpdate()
                    }))
                return None
            # Check if the URL matches the required one from the config
            if config['requireurl'] != '' and s.path != '/' + config['requireurl']:
                s.send_response(403)
                s.send_header('Server','DiStreamer')
                s.end_headers()
                s.wfile.write('Not authorized')
                return None
            # Return 404 if we don't have enough fragments, if the stream is not started yet, or if we need ICY metadata and we still don't have them
            if len(fragments) < config['minfragments'] or store.getIcyInt() < 0 or reconnect <= 0 or (store.getIcyInt() > 0 and len(store.getIcyList().keys()) == 0):
                s.send_response(404)
                s.send_header('Server','DiStreamer')
                s.end_headers()
                s.wfile.write('No stream yet')
                return None
            # If no icy is required, but we have it, discard the request
            if not s.headers.get('Icy-MetaData') and store.getIcyInt() > 0:
                s.send_response(500)
                s.end_headers()
                s.wfile.write('You must require Icy-MetaData')
                return None
            # Alright, we go!
            s.send_response(200)
            s.send_header('Server','DiStreamer')
            # Add the streaming to the counter for stats management
            statmgr.add()
            s.added = True
            # Get stream headers and send them to the client
            icyheaders = store.getIcyHeaders()
            for header in icyheaders:
                s.send_header(header,icyheaders[header])
            if(store.getIcyInt() > 0):
                s.send_header("icy-metaint", str(store.getIcyInt()))
            s.end_headers()
            # Get info from the store
            icytitle = store.getIcyTitle()
            icyint = store.getIcyInt()
            # Create the fragments manager
            fragsmanager = ShoutcastServerFragsManager(store, logger, config)
            if not fragsmanager.updateLocalList():
                self.logger.log('Got error in local list update','ShoutcastServer',2)
                return False
            # Let's start: we didn't send anything yet but we set a fake last sent time to pass the timeout check the first time
            lastsenttime = int(time.time())
            # Handle OGG headers
            if store.getOggHeader() != "":
                oggheader = store.getOggHeader()
                if icyint > 0:
                    while len(oggheader) > icyint:
                        s.wfile.write(oggheader[:icyint])
                        chridx = len(icytitle) / 16
                        s.wfile.write(chr(chridx))
                        s.wfile.write(icytitle)
                        oggheader = oggheader[icyint:]
                    padding = icyint - len(oggheader)
                    fragsmanager.getToAfterNextOGGHeader()
                    headtoicy = 'OggS' + fragsmanager.getToBeforeNextMeta()
                    originalPadding = padding
                    padding = padding - len(headtoicy)
                    while padding < 28:
                        padding += icyint
                    s.wfile.write(oggheader)
                    logger.log('Generating a ' + str(padding) + ' byte dummy OGG page', 'ShoutcastServer', 4)
                    paddingPages = s.generateDummyOggPages(padding, oggheader[14:18])
                    if padding > originalPadding:
                        s.wfile.write(paddingPages[:originalPadding])
                        chridx = len(icytitle) / 16
                        s.wfile.write(chr(chridx))
                        s.wfile.write(icytitle)
                        paddingPages = paddingPages[originalPadding:]
                        while len(paddingPages) > icyint:
                            s.wfile.write(paddingPages[:icyint])
                            chridx = len(icytitle) / 16
                            s.wfile.write(chr(chridx))
                            s.wfile.write(icytitle)
                            paddingPages = paddingPages[icyint:]
                    s.wfile.write(paddingPages)
                    s.wfile.write(headtoicy)
                    s.wfile.write(fragsmanager.getToAfterNextMeta())
                else:
                    s.wfile.write(oggheader)
                    s.wfile.write('OggS')
                    fragsmanager.getToAfterNextOGGHeader()

            # If we are managing ICY title and the hard work hasn't already be done by the OGG handler...
            if icyint > 0:
                # Align to after the next meta if the OGG handler hasn't already done it
                if store.getOggHeader() == '':
                    fragsmanager.getToAfterNextMeta()
                # Always start from after a title block
                toNextMeta = fragsmanager.getToBeforeNextMeta()
                if toNextMeta == False:
                    logger.log('Error returned from getToBeforeNextMeta. Closing stream to client.', 'ShoutcastServer', 2)
                    return None
                s.wfile.write(toNextMeta)
                # Let's immediately send a title after the first valid block
                chridx = len(icytitle) / 16
                s.wfile.write(chr(chridx))
                s.wfile.write(icytitle)
                if not fragsmanager.getToAfterNextMeta():
                    logger.log('Error returned from getToAfterNextMeta. Closing stream to client.', 'ShoutcastServer', 2)
                    return None
            # Ok we initialized everything. Now let's stream 'till the end of the world!
            while not lisclosing[0]:
                tosend = fragsmanager.getAll()
                # If we have something to write to the socket... well, we write
                if len(tosend) > 0:
                    s.wfile.write(tosend)
                    lastsenttime = int(time.time())
                # Sooooo tired!
                time.sleep(1)
                # We waited too much for a fragment that never arrived. We give up.
                if int(time.time()) - lastsenttime > config['timeout'] and config['timeout'] > 0:
                    logger.log('Timeout reached. Closing stream to client.', 'ShoutcastServer', 2)
                    return None
                if not fragsmanager.updateLocalList():
                    self.logger.log('Got error in local list update','ShoutcastServer',2)
                    return False
        def log_message(self, format, *args):
            return

        def finish(s):
            if s.added:
                statmgr.rem()

    return shoutcastServerHandler

class ShoutcastServer:
    def __init__(self, store, logger):
        self.store = store
        self.logger = logger
        self.config_set = False

    def getDefaultConfig(self):
        return {
            'hostname': '0.0.0.0',
            'port': 8080,
            'minfragments': 5,
            'requireurl': '',
            'timeout': 30
        }

    def setConfig(self, config):
        self.config = config
        self.config_set = True

    def run(self):
        if not self.config_set:
            self.logger.log("Config not set", 'ShoutcastServer', 1)
            return None
        self.logger.log('Starting', 'ShoutcastServer', 2)
        self.lisclosing = [False]
        statmgr = ShoutcastServerStatsManager()
        handler = makeServerHandler(self.store, self.logger, self.config, self.lisclosing,statmgr)
        self.httpd = ThreadingSimpleServer((self.config['hostname'], self.config['port']), handler)
        self.httpd.socket.setsockopt(socket.IPPROTO_IP, socket.IP_TOS, 0x40)
        self.logger.log('Started', 'ShoutcastServer', 2)
        try:
            self.httpd.serve_forever()
        except:
            pass
        self.logger.log('Server terminated', 'ShoutcastServer', 2)

    def close(self):
        self.logger.log('Exiting normally', 'ShoutcastServer' ,2)
        self.httpd.server_close()
        self.lisclosing[0] = True
