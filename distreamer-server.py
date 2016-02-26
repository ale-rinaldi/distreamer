import time
import BaseHTTPServer
import threading
import urllib2
import sys
import ConfigParser
import traceback
from SocketServer import ThreadingMixIn

VERSION='1.0.4'

fragments={}
counter=1
reconnect=1

try:
	config = ConfigParser.ConfigParser({
		'HOST_NAME': '0.0.0.0',
		'PORT_NUMBER': 7080,
		'STREAMURL': '',
		'FRAGMENTSNUMBER': 5,
		'FRAGMENTSIZE': 81920,
		'GETMETADATA': True,
		'HTTPTIMEOUT': 5,
		'DEBUG': False
	})
	if len(sys.argv)>1:
		file=sys.argv[1]
		config.read([file])
	else:
		config.read(['distreamer.conf'])
except:
	print "Cannot read configuration file. Aborting."
	if DEBUG:
		print traceback.format_exc(sys.exc_info())
	sys.exit(1)
	
HOST_NAME=config.get('SERVER','HOST_NAME')
PORT_NUMBER=config.getint('SERVER','PORT_NUMBER')
STREAMURL=config.get('SERVER','STREAMURL')
FRAGMENTSNUMBER=config.getint('SERVER','FRAGMENTSNUMBER')
FRAGMENTSIZE=config.getint('SERVER','FRAGMENTSIZE')
GETMETADATA=config.getboolean('SERVER','GETMETADATA')
HTTPTIMEOUT=config.getint('SERVER','HTTPTIMEOUT')
DEBUG=config.getboolean('SERVER','DEBUG')

if STREAMURL=='':
	print "Stream URL not defined. Aborting."
	sys.exit(1)

class ThreadingSimpleServer(ThreadingMixIn, BaseHTTPServer.HTTPServer):
    pass

class distreamerServerHandler(BaseHTTPServer.BaseHTTPRequestHandler):
	global fragments, DEBUG, icylist, icyheaders, reconnect
	def do_HEAD(s):
		try:
			if(s.path=='/list'):
				s.send_response(200)
				s.send_header("Content-Type", "text/plain")
			else:
				key=int(s.path[1:])
				if fragments.has_key(key):
					s.send_response(200)
				else:
					s.send_response(404)
		except:
			print str(time.asctime())+": HEAD error"
			if DEBUG:
				print traceback.format_exc(sys.exc_info())
			pass
			
	def do_GET(s):
		try:
			if s.path=='/list':
				s.send_response(200)
				s.send_header("Server", "DiStreamer/"+VERSION)
				s.send_header("Content-Type", "text/plain")
				flist=fragments.keys()
				flist.sort()
				tosend=','.join(map(str,flist))
				tosend=tosend+'|'+str(icyint)+'|'
				tmplist=[]
				for frag in icylist:
					tmplist.append(str(frag)+':'+'-'.join(map(str,icylist[frag])))
				tosend=tosend+','.join(tmplist)+'|'
				tmplist=[]
				for metaidx in icyheaders:
					tmplist.append(metaidx+':'+icyheaders[metaidx])
				tosend=tosend+','.join(tmplist)+'|'+str(reconnect)
				s.send_header("Content-Length", str(len(tosend)))
				s.end_headers()
				s.wfile.write(tosend)
			else:
				key=int(s.path[1:])
				if fragments.has_key(key):
					s.send_response(200)
					s.send_header("Server", "DiStreamer/"+VERSION)
					s.send_header("Content-Length", str(len(fragments[key])))
					s.end_headers()
					s.wfile.write(fragments[key])
				else:
					s.send_response(404)
					s.send_header("Server", "DiStreamer/"+VERSION)
					s.end_headers()
					s.wfile.write("Invalid fragment "+str(key))
		except:
			print str(time.asctime())+": GET error"
			if DEBUG:
				print traceback.format_exc(sys.exc_info())
			pass
	if not DEBUG:
		def log_message(self, format, *args):
			return

def distreamerServerThread():
	global VERSION, STREAMURL, HOST_NAME, PORT_NUMBER, FRAGMENTSNUMBER, FRAGMENTSIZE, HTTPTIMEOUT
	server_class = ThreadingSimpleServer
	httpd = server_class((HOST_NAME, PORT_NUMBER), distreamerServerHandler)
	print str(time.asctime())+": Distreamer Server "+VERSION+" started"
	print str(time.asctime())+": Stream URL: "+STREAMURL
	print str(time.asctime())+": Buffering "+str(FRAGMENTSNUMBER)+" blocks of "+str(FRAGMENTSIZE)+" bytes"
	print str(time.asctime())+": Listening on "+HOST_NAME+", port "+str(PORT_NUMBER)
	print str(time.asctime())+": HTTP timeout: "+str(HTTPTIMEOUT)
	try:
		httpd.serve_forever()
	except KeyboardInterrupt:
		pass
	httpd.server_close()
	print str(time.asctime())+": Distreamer Server Stopped"
	
t = threading.Thread(target=distreamerServerThread)
t.daemon=True
t.start()



while True:
	fragments={}
	icyint=0
	icyread=0
	icylist={}
	icyheaders={}
	icynbstart=0
	try:
		if GETMETADATA:
			stream=urllib2.urlopen(urllib2.Request(STREAMURL,headers={'Icy-MetaData':'1','User-Agent':'DiStreamer/'+VERSION}), timeout=HTTPTIMEOUT)
			if stream.headers.has_key('icy-metaint'):
				icyint=int(stream.headers['icy-metaint'])
			for metaidx in stream.headers.keys():
				if ( metaidx[:4]=='icy-' and metaidx!='icy-metaint' ) or metaidx.lower()=='content-type':
					icyheaders[metaidx]=stream.headers[metaidx]
		else:
			stream=urllib2.urlopen(urllib2.Request(STREAMURL,headers={'User-Agent':'DiStreamer/'+VERSION}), timeout=HTTPTIMEOUT)
		while True:
			fragment=stream.read(FRAGMENTSIZE)
			if len(fragment)!=FRAGMENTSIZE:
				raise ValueError("Incomplete read of block")
			idx=counter
			if icyint>0:
				if FRAGMENTSIZE<icyint-icyread:
					icyread=icyread+FRAGMENTSIZE
				else:
					if icynbstart>0:
						x=icynbstart
					else:
						x=0
					icynbstart=0
					while x<FRAGMENTSIZE:
						if icyread==icyint:
							icylen=ord(fragment[x])*16+1
							icytpos=x+icylen
							icytblock=idx
							while icytpos>FRAGMENTSIZE:
								icytblock=icytblock+1
								icytpos=icytpos-FRAGMENTSIZE
								icynbstart=icytpos+1
							icyblock=icytblock
							icypos=icytpos
							if not icylist.has_key(icyblock):
								icylist[icyblock]=[]
							icylist[icyblock].append(icypos)
							x=x+icylen
							icyread=0
						icyread=icyread+1
						x=x+1
			counter=counter+1
			fragments[idx]=fragment
			if DEBUG:
				print str(time.asctime())+": Created fragment",idx
			while len(fragments)>FRAGMENTSNUMBER:
				todelete=min(fragments.keys())
				del fragments[todelete]
				if icylist.has_key(todelete):
					del icylist[todelete]
				if DEBUG:
					print str(time.asctime())+": Deleted fragment",todelete
	except:
		pass
	print str(time.asctime())+": Error reading from source server. Restarting connection."
	if DEBUG:
		print traceback.format_exc(sys.exc_info())
	time.sleep(1)
	reconnect=reconnect+1
