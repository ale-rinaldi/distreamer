import socket,urlparse,json

class DiStreamerPersClient():

    def __init__(self, store, logger):
        self.store = store
        self.logger = logger
        self.config_set = False
        self.isclosing = False
        self.socket = None

    def _PersServerConnect(self, url, timeout):
        u = urlparse.urlparse(url)
        server = u.netloc.split(':')[0]
        port =- 1
        if len(u.netloc.split(':')) > 1:
            port = int(u.netloc.split(':')[1])
        if port < 0:
            port = 80
        self.logger.log('Connecting to ' + server + ' on port ' + str(port), 'DiStreamerPersClient', 4)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.IPPROTO_IP, socket.IP_TOS, 0x40)
        s.setblocking(1)
        s.connect((server, port))
        self.logger.log('Connected', 'DiStreamerPersClient', 4)
        f = s.makefile()
        s.settimeout(timeout)
        s.sendall('GET ' + u.path +  ' HTTP/1.1\r\n')
        s.sendall('\r\n')
        self.socket = s
        self.socketfile = f
        return f

    def keysToInt(s, dictionary):
            ''' THANKS!!! http://stackoverflow.com/questions/1254454/fastest-way-to-convert-a-dicts-keys-values-from-unicode-to-str '''
            if not isinstance(dictionary, dict):
                return dictionary
            return dict((int(k), s.keysToInt(v)) for k, v in dictionary.items())

    def getDefaultConfig(self):
        return {
            'serverurl': '',
            'password': '',
            'httptimeout': 5
        }

    def setConfig(self, config):
        self.config = config
        self.config_set = True

    def run(self):
        if not self.config_set:
            self.logger.log('Config not set', 'DiStreamerPersClient', 1)
            return None

        if self.config['serverurl'] == '':
            self.logger.log('Server URL not defined', 'DiStreamerPersClient', 1)
            return None

        self.logger.log('Started', 'DiStreamerPersClient', 2)
        
        fragments = self.store.getFragments()
        fkeys = fragments.keys()
        path = '/'.join(map(str,fkeys))
        stream = self._PersServerConnect(self.config['serverurl'] + '/' + self.config['password'] + '/' + path, self.config['httptimeout'])
        
        self.logger.log("Connected to DiStreamer Persistent Server", 'DiStreamerPersClient', 3)
        
        while not self.isclosing:
            info = ''
            try:
                info = stream.readline().strip()
            except:
                if self.isclosing:
                    pass
                else:
                    self.logger.log('Incomplete read of line', 'DiStreamerPersClient', 2)
                    return None
            aline = info.split('|')
            action = aline[0]
            try:
                length = int(aline[1])
            except:
                if self.isclosing:
                    pass
                else:
                    self.logger.log('Error in length conversion', 'DiStreamerPersClient', 2)
                    return None
            content = ''
            try:
                content = stream.read(length)
            except:
                if self.isclosing:
                    pass
                else:
                    self.logger.log('Error redading ' + action, 'DiStreamerPersClient', 2)
                    return None
            if len(content) != length:
                self.logger.log('Incomplete read of ' + action, 'DiStreamerPersClient', 2)
                return None
            try:
                stream.read(2)
            except:
                if self.isclosing:
                    pass
                else:
                    self.logger.log('Error in reading final bytes', 'DiStreamerPersClient', 2)
                    return None
            if action == 'err':
                self.logger.log('Error from server: ' + content, 'DiStreamerPersClient', 2)
                return None
            if action == 'list':
                infolist = json.loads(content)
                self.store.setIcyInt(infolist['icyint'])
                self.store.setIcyList(self.keysToInt(infolist['icylist']))
                self.store.setIcyHeaders(infolist['icyheaders'])
                self.store.setSourceGen(infolist['sourcegen'])
                self.store.setIcyTitle(infolist['icytitle'].decode('base64'))
                list = infolist['fragmentslist']
                for localfragn in fragments.keys():
                    if(localfragn not in list):
                        del fragments[localfragn]
                        self.logger.log('Deleted fragment ' + str(localfragn), 'DiStreamerPersClient', 3)
            else:
                x =- 1
                try:
                    x = int(action)
                except:
                    pass
                if x >= 0:
                    if len(fragments.keys()) > 0 and x > max(fragments.keys()) + 1:
                        self.logger.log('Expected fragment: ' + str(max(fragments.keys())) + ', received: ' + str(x) + '. Clearing fragments in store.', 'DiStreamerPersClient', 2)
                        self.store.clearFragmentsList()
                    fragments[x] = content
                    self.logger.log('Received fragment ' + str(x), 'DiStreamerPersClient', 3)

        self.logger.log('DiStreamerPersClient terminated normally', 'DiStreamerPersClient', 2)

    def close(self):
        self.isclosing = True
        self.logger.log('DiStreamerPersClient is terminating, this could need some time', 'DiStreamerPersClient', 2)
        if self.socket:
            self.socket.close()
