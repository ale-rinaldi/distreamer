import time
import BaseHTTPServer
import threading
import urllib2
import sys
import ConfigParser
import traceback
from SocketServer import ThreadingMixIn

VERSION='1.1.0'

fragments={}
reconnect=0

try:
	config = ConfigParser.ConfigParser({
		'HOST_NAME': '0.0.0.0',
		'PORT_NUMBER': 8080,
		'SERVERURL': '',
		'HTTPTIMEOUT': 5,
		'HTTPINTERVAL': 3,
		'DEBUG': False
	})
	if len(sys.argv)>1:
		file=sys.argv[1]
		config.read([file])
	else:
		config.read(['distreamer.conf'])
except:
	print "Cannot read configuration file"
	if DEBUG:
		print traceback.format_exc(sys.exc_info())
	sys.exit(1)
	
HOST_NAME=config.get('CLIENT','HOST_NAME')
PORT_NUMBER=config.getint('CLIENT','PORT_NUMBER')
SERVERURL=config.get('CLIENT','SERVERURL')
HTTPTIMEOUT=config.getint('CLIENT','HTTPTIMEOUT')
HTTPINTERVAL=config.getint('CLIENT','HTTPINTERVAL')
DEBUG=config.getboolean('CLIENT','DEBUG')
if SERVERURL=='':
	print "Server URL not defined. Aborting."
	sys.exit(1)

class ThreadingSimpleServer(ThreadingMixIn, BaseHTTPServer.HTTPServer):
    pass

class distreamerServerHandler(BaseHTTPServer.BaseHTTPRequestHandler):
	global fragments, DEBUG, icyint, icyheaders, reconnect, icytitle
	def do_HEAD(s):
		s.send_response(200)
		s.send_header("Server", "DiStreamer/"+VERSION)
		for header in icyheaders:
			s.send_header(header,icyheaders[header])
		if(icyint>0):
			s.send_header("icy-metaint", str(icyint))
			
	def do_GET(s):
		s.send_response(200)
		s.send_header("Server", "DiStreamer/"+VERSION)
		for header in icyheaders:
			s.send_header(header,icyheaders[header])
		if(icyint>0):
			s.send_header("icy-metaint", str(icyint))
		s.end_headers()
		if reconnect<=0:
			return None
		sentlist=[]
		locreconnect=reconnect
		firstsent=False
		if icyint>0:
			if locreconnect!=reconnect or reconnect<=0:
				return None
			if icytitle!='':
				s.wfile.write(''.join(chr(255) for i in xrange(icyint)))
				chridx=len(icytitle)/16
				s.wfile.write(chr(chridx))
				s.wfile.write(icytitle)
			while not firstsent:
				try:
					locallist=fragments.keys()
					locallist.sort()
					for fragn in locallist:
						if icylist.has_key(fragn):
							icyblkmin=min(icylist[fragn])
							lastsent=fragn
							s.wfile.write(fragments[fragn][icyblkmin:])
							sentlist.append(fragn)
							firstsent=True
							break
						else:
							sentlist.append(fragn)
				except:
					time.sleep(1)
					pass
		else:
			lastsent=min(fragments.keys())-1
		while True:
			try:
				if locreconnect!=reconnect or reconnect<=0:
					return None
				tosend=''
				locallist=fragments.keys()
				locallist.sort()
				for fragn in locallist:
					if fragn not in sentlist:
						if fragn!=lastsent+1:
							return None
						lastsent=fragn
						tosend=tosend+fragments[fragn]
						sentlist.append(fragn)
				for sentn in sentlist:
					if not fragments.has_key(sentn):
						sentlist.remove(sentn)
						if DEBUG:
							print str(time.asctime())+": Removed from sent list", sentn
			except:
				pass
			s.wfile.write(tosend)
			time.sleep(1)
	if not DEBUG:
		def log_message(self, format, *args):
			return

def distreamerServerThread():
	global VERSION, SERVERURL, HOST_NAME, PORT_NUMBER, HTTPTIMEOUT
	server_class = ThreadingSimpleServer
	httpd = server_class((HOST_NAME, PORT_NUMBER), distreamerServerHandler)
	print str(time.asctime())+": Distreamer Client "+VERSION+" started"
	print str(time.asctime())+": Server URL: "+str(SERVERURL)
	print str(time.asctime())+": Listening on "+HOST_NAME+", port "+str(PORT_NUMBER)
	print str(time.asctime())+": HTTP timeout: "+str(HTTPTIMEOUT)
	print str(time.asctime())+": HTTP interval: "+str(HTTPINTERVAL)
	try:
		httpd.serve_forever()
	except KeyboardInterrupt:
		pass
	httpd.server_close()
	print str(time.asctime())+": Distreamer Client Stopped"
	
t = threading.Thread(target=distreamerServerThread)
t.daemon=True
t.start()

icyint=0
icylist={}
icytitle=""
icyheaders={}
while True:
	try:
		result=urllib2.urlopen(urllib2.Request(SERVERURL+'/list',headers={'User-Agent':'DiStreamer/'+VERSION}), timeout=HTTPTIMEOUT)
		exclen=result.headers['Content-Length']
		cslist=result.read()
		if len(cslist)!=int(exclen):
			print str(time.asctime())+": Incomplete read of list"
			raise ValueError("Incomplete read of list")
		infolist=cslist.split('|')
		icyint=int(infolist[1])
		if icyint>0:
			sicylist=infolist[2].split(',')
			for icyfrag in sicylist:
				aicylist=icyfrag.split(':')
				if aicylist[0]!='':
					icyidx=int(aicylist[0])
					icylist[icyidx]=map(int,aicylist[1].split('-'))
		aicyheaders=infolist[3].split(',')
		tmplist={}
		for header in aicyheaders:
			seppos=header.find(':')
			key=header[:seppos]
			val=header[seppos+1:]
			tmplist[key]=val
		icyheaders=tmplist
		reconnect=int(infolist[4])
		icytitle=infolist[5]
		cslist=infolist[0]
		slist=cslist.split(',')
		list=map(int,slist)
		for fragn in list:
			if not(fragments.has_key(fragn)) or fragments[fragn]=='':
				result=urllib2.urlopen(urllib2.Request(SERVERURL+'/'+str(fragn),headers={'User-Agent':'DiStreamer/'+VERSION}), timeout=HTTPTIMEOUT)
				exclen=result.headers['Content-Length']
				fragment=result.read()
				if len(fragment)!=int(exclen):
					print str(time.asctime())+": Incomplete read of block"
					raise ValueError("Incomplete read of block")
				fragments[fragn]=fragment
				if DEBUG:
					print str(time.asctime())+": Downloaded fragment",fragn
		locallist=fragments.keys()
		for localfragn in locallist:
			if(localfragn not in list):
				del fragments[localfragn]
				if DEBUG:
					print str(time.asctime())+": Deleted fragment ",localfragn
	except:
		print str(time.asctime())+": Read error"
		if DEBUG:
			print traceback.format_exc(sys.exc_info())
		pass
	time.sleep(HTTPINTERVAL)
