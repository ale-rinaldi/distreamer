import urllib2,time,json

class DiStreamerRevClient():
    def __init__(self, store, logger):
        self.store = store
        self.logger = logger
        self.config_set = False
        self.isclosing = False
        

    def getDefaultConfig(self):
        return {
            'serverurl': '',
            'httptimeout': 5,
            'httpinterval': 3,
            'password': ''
        }

    def setConfig(self,config):
        self.config = config
        self.config_set = True

    def run(self):
        # Close immediately if config has not been set by the main thread (should never happen, anyway)
        if not self.config_set:
            self.logger.log('Config not set', 'DiStreamerRevClient', 1)
            return None
        # Close immediately if the server URL was not specified in configuration
        if self.config['serverurl'] == '':
            self.logger.log('Server URL not defined', 'DiStreamerRevClient', 1)
            return None
        # The close() method sets self.isclosing to True to allow exiting the loop
        while not self.isclosing:
            # Make a local copy of the fragments
            fragments = self.store.getFragments()
            # Get the remote list (include the password in request if set)
            if self.config['password'] != '':
                result = urllib2.urlopen(urllib2.Request(self.config['serverurl'] + '/list/' + self.config['password'], headers = {'User-Agent':'DiStreamer'}), timeout = self.config['httptimeout'])
            else:
                result = urllib2.urlopen(urllib2.Request(self.config['serverurl'] + '/list', headers = {'User-Agent':'DiStreamer'}), timeout = self.config['httptimeout'])
            # Read expected length and actual content
            exclen = result.headers['Content-Length']
            cslist = result.read()
            # Stop if the length is different than expected
            if len(cslist) != int(exclen):
                self.logger.log("Incomplete read of list", 'DiStreamerRevClient', 2)
                return None
            # Parse JSON
            infolist = json.loads(cslist)
            # Get the remote fragments list and its keys, and sort it
            remotelist = infolist['fragmentslist']
            fkeys = fragments.keys()
            fkeys.sort()
            # Create an empty list to contain the fragments to be sent
            localfrags = {}
            for fragn in fkeys:
                # Save a copy of every fragment that is not in the remote list but is in the local list (keep local copy to avoid deleting from source while processing)
                if self.isclosing:
                    break
                if not fragn in remotelist:
                    localfrags[fragn] = fragments[fragn]
            # Get the keys of the fragments to be sent and sort it
            locfkeys = localfrags.keys()
            locfkeys.sort()
            # Prepare a JSON to post to the server (to update metadata and to delete old fragments)
            tosend = json.dumps({
                    'fragmentslist': fkeys,
                    'icyint': self.store.getIcyInt(),
                    'icylist': self.store.getIcyList(),
                    'icyheaders': self.store.getIcyHeaders(),
                    'icytitle': self.store.getIcyTitle().encode('base64'),
                    'sourcegen': self.store.getSourceGen()
                })
            # Calculate the first fragment the server expects to receive (the higher one in its list +1)
            if len(remotelist) > 0:
                expfirst = max(remotelist) + 1
            else:
                expfirst = 1
            # If we don't have that fragment anymore, send the list immediately and set listsent to True to avoid sending the same list twice
            if expfirst != 1 and expfirst not in locfkeys:
                if self.config['password'] != '':
                    result = urllib2.urlopen(urllib2.Request(self.config['serverurl'] + '/list/' + self.config['password'], tosend, headers = {'User-Agent':'DiStreamer'}), timeout = self.config['httptimeout'])
                else:
                    result = urllib2.urlopen(urllib2.Request(self.config['serverurl'] + '/list', tosend, headers = {'User-Agent':'DiStreamer'}), timeout = self.config['httptimeout'])
                listsent = True
            else:
                listsent = False
            # Send every fragment in the local list
            for fragn in locfkeys:
                # Calculate the minimum expected fragment in the global list
                expminfrag = max(locfkeys) + 1
                # If it has already been deleted from the global list, don't waste time and give up
                if len(self.store.getFragments().keys()) > 0 and min(self.store.getFragments().keys()) > expminfrag:
                    self.logger.log('Fragment ' + str(expminfrag) + ' is not in the global list. Closing.', 'DiStreamerRevClient', 2)
                    return None
                if self.config['password']:
                    result = urllib2.urlopen(urllib2.Request(self.config['serverurl'] + '/' + str(fragn) + '/' + self.config['password'], localfrags[fragn], headers = {'User-Agent':'DiStreamer'}), timeout = self.config['httptimeout'])
                else:
                    result = urllib2.urlopen(urllib2.Request(self.config['serverurl'] + '/' + str(fragn), localfrags[fragn], headers = {'User-Agent':'DiStreamer'}), timeout = self.config['httptimeout'])
                res = result.read()
                if res != 'OK':
                    self.logger.log('Failed to send fragment ' + str(fragn), 'DiStreamerRevClient', 2)
                    return None
                self.logger.log('Sent fragment ' + str(fragn), 'DiStreamerRevClient', 3)
            # If the list has not been sent (and the server is not closing) send it
            if not (listsent or self.isclosing):
                if self.config['password'] != '':
                    result = urllib2.urlopen(urllib2.Request(self.config['serverurl'] + '/list/' + self.config['password'], tosend, headers = {'User-Agent':'DiStreamer'}), timeout = self.config['httptimeout'])
                else:
                    result = urllib2.urlopen(urllib2.Request(self.config['serverurl'] + '/list', tosend, headers = {'User-Agent':'DiStreamer'}), timeout = self.config['httptimeout'])
            # Sleep a while before starting over
            time.sleep(self.config['httpinterval'])
        # Log normal shutdown
        self.logger.log('DiStreamerRevClient terminated normally', 'DiStreamerRevClient', 2)

    def close(self):
        self.isclosing = True
        self.logger.log('DiStreamerRevClient is terminating, this could need some time', 'ShoutcastClient', 2)
