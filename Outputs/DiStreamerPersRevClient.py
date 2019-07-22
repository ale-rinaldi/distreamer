import socket,urlparse,json,time


class DiStreamerPersRevClient():

    def __init__(self,store,logger):
        self.store=store
        self.logger=logger
        self.config_set=False
        self.isclosing=False
        self.socket=None
        self.socketfile=None

    def _PersRevServerConnect(self, url, timeout):
        u = urlparse.urlparse(url)
        server = u.netloc.split(':')[0]
        port = -1
        if len(u.netloc.split(':')) > 1:
            port = int(u.netloc.split(':')[1])
        if port < 0:
            port = 80
        self.logger.log('Connecting to ' + server + ' on port ' + str(port),'DiStreamerPersRevClient', 4)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.IPPROTO_IP, socket.IP_TOS, 0x40)
        # Set the timeout a first time for the connection
        s.settimeout(timeout)
        s.connect((server, port))
        s.setblocking(1)
        self.logger.log('Connected','DiStreamerPersRevClient',4)
        f = s.makefile()
        # Set the timeout again after setting blocking mode
        s.settimeout(timeout)
        self.socket = s
        self.socketfile = f
        return f

    def getDefaultConfig(self):
        return {
            'serverurl': '',
            'password': '',
            'timeout': 5,
            'interval': 1
        }

    def setConfig(self, config):
        self.config = config
        self.config_set = True

    def run(self):
        if not self.config_set:
            self.logger.log('Config not set', 'DiStreamerPersRevClient', 1)
            return None

        if self.config['serverurl'] == '':
            self.logger.log('Server URL not defined', 'DiStreamerPersRevClient', 1)
            return None

        self.logger.log('Started', 'DiStreamerPersRevClient', 2)

        stream = self._PersRevServerConnect(self.config['serverurl'] + '/', self.config['timeout'])
        self.socket.sendall(self.config['password'] + '\r\n')
        ans = stream.readline()
        aans = ans.split('|')
        if aans[0] != 'ok':
            self.logger.log('Error from server: ' + aans[1], 'DiStreamerPersRevClient', 2)
            return None
        self.logger.log("Connected to server", 'DiStreamerPersRevClient', 3)
        sentlist = aans[1].split('/')

        fragments = self.store.getFragments()
        if len(fragments.keys()) > 0:
            lastsent = min(fragments.keys()) - 1
        else:
            lastsent = 0
        localoggheader = ""
        while not self.isclosing:
            localfrags = {}
            fkeys = fragments.keys()
            fkeys.sort()
            list = json.dumps({
                'fragmentslist': fkeys,
                'icyint': self.store.getIcyInt(),
                'icylist': self.store.getIcyList(),
                'icyheaders': self.store.getIcyHeaders(),
                'icytitle': self.store.getIcyTitle().encode('base64'),
                'sourcegen': self.store.getSourceGen()
            })

            # OGG headers
            if self.store.getOggHeader() != localoggheader:
                localoggheader = self.store.getOggHeader()
                self.socket.sendall('oggheader|' + str(len(localoggheader)) + '\r\n' + localoggheader + '\r\n')

            for fragn in fkeys:
                if self.isclosing:
                    break
                if fragn not in sentlist:
                    if fragn != lastsent + 1:
                        self.logger.log('Expected fragment: ' + str(lastsent + 1) + ', next available: ' + str(fragn) + '. Closing stream to server.', 'DiStreamerPersRevClient', 2)
                        return None
                    localfrags[fragn] = fragments[fragn]
                    lastsent = fragn
            locfkeys = localfrags.keys()
            locfkeys.sort()
            for fragn in locfkeys:
                if min(fragments.keys()) > max(locfkeys) + 1:
                    self.logger.log('Expected fragment: ' + str(max(locfkeys)) + ', first available: ' + str(min(fragments.keys())) + '. Closing stream to server.', 'DiStreamerPersRevClient', 2)
                    return None
                tosend = str(fragn) + '|' + str(len(localfrags[fragn])) + '\r\n' + localfrags[fragn] + '\r\n'
                time1 = time.time()
                self.socket.sendall(tosend)
                time2 = time.time()
                if time2 - time1 > 0:
                    speed = str(round((len(tosend)/(time2-time1))/1024.0,2))
                else:
                    speed = 'inf.'
                self.logger.log('Sent fragment ' + str(fragn) + ' in ' + str(round(time2 - time1, 2)) + 's (' + speed + ' kB/s)', 'DiStreamerPersRevClient', 3)
                sentlist.append(fragn)
            self.socket.sendall('list|' + str(len(list)) + '\r\n' + list + '\r\n')
            for sentn in sentlist:
                if not sentn in fkeys:
                    sentlist.remove(sentn)
                    self.logger.log('Removed from sent list: ' + str(sentn), 'DiStreamerPersRevClient', 4)
            time.sleep(self.config['interval'])
        self.logger.log('DiStreamerPersRevClient terminated normally', 'DiStreamerPersRevClient', 2)

    def close(self):
        self.isclosing = True
        self.logger.log('DiStreamerPersRevClient is terminating, this could need some time', 'DiStreamerPersRevClient', 2)
        if self.socket:
            self.socket.close()
