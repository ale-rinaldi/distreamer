import BaseHTTPServer
import time,json
from SocketServer import ThreadingMixIn

class ShoutcastServerStatsManager():
    def __init__(self):
        self.counter=0
    def add(self):
        self.counter+=1
    def rem(self):
        self.counter-=1
    def get(self):
        return self.counter

class ThreadingSimpleServer(ThreadingMixIn, BaseHTTPServer.HTTPServer):
    pass

def makeServerHandler(store,logger,config,lisclosing,statmgr):
    class shoutcastServerHandler(BaseHTTPServer.BaseHTTPRequestHandler,object):
        statpages=['/stats','/favicon.ico']
        def do_HEAD(s):
            s.added=False
            s.send_response(200)
            s.send_header("Server", "DiStreamer")
            icyheaders=store.getIcyHeaders()
            for header in icyheaders:
                s.send_header(header,icyheaders[header])
            if(store.getIcyInt()>0):
                s.send_header("icy-metaint", str(store.getIcyInt()))
                
        def do_GET(s):
            # The stream has not been added to the counter yet
            s.added=False
            # Get stream information from the store
            fragments=store.getFragments()
            reconnect=store.getSourceGen()
            # Send statistics if required (TODO: manage favicon in a different way...)
            if s.path in s.statpages:
                s.send_response(200)
                s.send_header('content-type','application/json')
                s.end_headers()
                s.wfile.write(json.dumps({
                    'connectedClients':statmgr.get(),
                    'fragmentsList':fragments.keys(),
                    'storeAge': int(time.time())-store.getLastUpdate()
                    }))
                return None
            # Check if the URL matches the required one from the config
            if config['requireurl']!='' and s.path!='/'+config['requireurl']:
                s.send_response(403)
                s.send_header('Server','DiStreamer')
                s.end_headers()
                s.wfile.write('Not authorized')
                return None
            # Return 404 if we don't have enough fragments, if the stream is not started yet, or if we need ICY metadata and we still don't have them
            if len(fragments)<config['minfragments'] or store.getIcyInt()<0 or reconnect<=0 or (store.getIcyInt()>0 and len(store.getIcyList().keys())==0):
                s.send_response(404)
                s.send_header('Server','DiStreamer')
                s.end_headers()
                s.wfile.write('No stream yet')
                return None
            # Alright, we go!
            s.send_response(200)
            s.send_header('Server','DiStreamer')
            # Add the streaming to the counter for stats management
            statmgr.add()
            s.added=True
            # Get stream headers and send them to the client
            icyheaders=store.getIcyHeaders()
            for header in icyheaders:
                s.send_header(header,icyheaders[header])
            if(store.getIcyInt()>0):
                s.send_header("icy-metaint", str(store.getIcyInt()))
            s.end_headers()
            # Get info from the store
            sentlist=[]
            locallist=fragments.keys()
            locallist.sort()
            # If set, use only the last MINFRAGMENTS fragments (consider the other ones as already sent)
            if config['minfragments']>0:
                excfragments=len(locallist)-config['minfragments']
                if excfragments>0:
                    sentlist=locallist[:excfragments]
            # Memorize the current stream reconnection number
            locreconnect=reconnect
            icytitle=store.getIcyTitle()
            icyint=store.getIcyInt()
            # Let's start: we didn't send anything yet but we set a fake last sent time and last sent fragment to pass the checks the first time
            lastsenttime=int(time.time())
            if len(sentlist)>0:
                lastsent=max(sentlist)
            else:
                lastsent=min(locallist)-1
            firstsent=False
            # If we are managing ICY title...
            if icyint>0:
                # If we already have a title, let's immediately send it (preceded by a fake block with repeated character 255)
                if icytitle!='':
                    s.wfile.write(''.join(chr(255) for i in xrange(icyint)))
                    chridx=len(icytitle)/16
                    s.wfile.write(chr(chridx))
                    s.wfile.write(icytitle)
                # Get the list of metadata blocks from the store
                icylist=store.getIcyList()
                # To keep the metadata sending in sync, we start streaming immediately after the first metadata block we have
                while not firstsent:
                    # Close the stream if the source has reconnected
                    reconnect=store.getSourceGen()
                    if locreconnect!=reconnect or reconnect<=0:
                        logger.log('Local source gen: '+str(locreconnect)+', source gen: '+str(reconnect)+'. Closing stream to client.','ShoutcastServer',2)
                        return None
                    # Get the current fragments list
                    locallist=fragments.keys()
                    locallist.sort()
                    # For each fragment...
                    for fragn in locallist:
                        # ... if we didn't already send it...
                        if fragn not in sentlist:
                            # If this block has a metadata in it, let's start from here (excluding the part before the metadata), else skip it considering it as sent
                            if icylist.has_key(fragn):
                                icyblkmin=min(icylist[fragn])
                                # Close the stream if the fragment we have is not what we excepted to have!
                                if fragn!=lastsent+1:
                                    logger.log('Expected fragment: '+str(lastsent+1)+', first available: '+str(fragn)+'. Closing stream to client.','ShoutcastServer',2)
                                    return None
                                lastsent=fragn
                                logger.log('Sent last part of fragment '+str(fragn)+' to client','ShoutcastServer',4)
                                s.wfile.write(fragments[fragn][icyblkmin:])
                                sentlist.append(fragn)
                                firstsent=True
                                lastsenttime=int(time.time())
                                break
                            else:
                                if fragn!=lastsent+1:
                                    logger.log('Expected fragment: '+str(lastsent+1)+', first available: '+str(fragn)+'. Closing stream to client.','ShoutcastServer',2)
                                    return None
                                lastsent=fragn
                                sentlist.append(fragn)
                            if lisclosing[0]:
                                break
                    if firstsent or lisclosing[0]:
                        break
                    time.sleep(0.5)
                    # We waited too much for a fragment that never arrived. We give up.
                    if int(time.time())-lastsenttime>config['timeout'] and config['timeout']>0:
                        logger.log('Timeout reached while waiting for first send. Closing stream to client.','ShoutcastServer',2)
                        return None
            # Ok we initialized everything. Now let's stream 'till the end of the world!
            while not lisclosing[0]:
                # Close the stream if the source has reconnected
                reconnect=store.getSourceGen()
                if locreconnect!=reconnect or reconnect<=0:
                    logger.log('Local source gen: '+str(locreconnect)+', source gen: '+str(reconnect)+'. Closing stream to client.','ShoutcastServer',2)
                    return None
                # We put everything we have to send in this big variable and we write to the socket only at the end. Otherwise, if the write takes too much time, the store situation may change in the middle! Too hard to handle it!
                tosend=''
                # Get the current fragments list
                locallist=fragments.keys()
                locallist.sort()
                # For each fragment...
                for fragn in locallist:
                    # ... if we didn't already send it...
                    if fragn not in sentlist:
                        # Close the stream if the fragment we have is not what we excepted to have!
                        if fragn!=lastsent+1:
                            logger.log('Expected fragment: '+str(lastsent+1)+', first available: '+str(fragn)+'. Closing stream to client.','ShoutcastServer',2)
                            return None
                        # Add the fragment to that big tosend variable and consider it as sent
                        lastsent=fragn
                        tosend=tosend+fragments[fragn]
                        logger.log('Sent fragment '+str(fragn)+' to client','ShoutcastServer',4)
                        sentlist.append(fragn)
                # Memory cleanup: if a fragment is not in the store anymore, we have no reason to keep it in the sent list
                for sentn in sentlist:
                    if not sentn in locallist:
                        sentlist.remove(sentn)
                        logger.log('Removed from sent list: '+str(sentn),'ShoutcastServer',4)
                # If we have something to write to the socket... well, we write
                if len(tosend)>0:
                    s.wfile.write(tosend)
                    lastsenttime=int(time.time())
                # Sooooo tired!
                time.sleep(1)
                # We waited too much for a fragment that never arrived. We give up.
                if int(time.time())-lastsenttime>config['timeout'] and config['timeout']>0:
                    logger.log('Timeout reached. Closing stream to client.','ShoutcastServer',2)
                    return None
        def log_message(self, format, *args):
            return
        
        def finish(s):
            if s.added:
                statmgr.rem()

    return shoutcastServerHandler

class ShoutcastServer:
    def __init__(self,store,logger):
        self.store=store
        self.logger=logger
        self.config_set=False

    def getDefaultConfig(self):
        return {
            'hostname': '0.0.0.0',
            'port': 8080,
            'minfragments': 5,
            'requireurl': '',
            'timeout': 30
        }
        
    def setConfig(self,config):
        self.config=config
        self.config_set=True
    
    def run(self):
        if not self.config_set:
            self.logger.log("Config not set",'ShoutcastServer',1)
            return None
        self.logger.log('Starting','ShoutcastServer',2)
        self.lisclosing=[False]
        statmgr=ShoutcastServerStatsManager()
        handler=makeServerHandler(self.store,self.logger,self.config,self.lisclosing,statmgr)
        self.httpd = ThreadingSimpleServer((self.config['hostname'], self.config['port']), handler)
        self.logger.log('Started','ShoutcastServer',2)
        try:
            self.httpd.serve_forever()
        except:
            pass
        self.logger.log('Server terminated','ShoutcastServer',2)

    def close(self):
        self.logger.log('Exiting normally','ShoutcastServer',2)
        self.httpd.server_close()
        self.lisclosing[0]=True
