import urllib2

class ShoutcastClient():
	def __init__(self,store,logger):
		self.store=store
		'''
		Store will contain sourcegen, fragments, icyint, icylist, icyheaders and icytitle
		'''
		self.logger=logger
		self.counter=1
		self.reconnect=1
		self.config_set=False
		

	def getDefaultConfig(self):
		return {
			'STREAMURL': '',
			'FRAGMENTSNUMBER': 5,
			'FRAGMENTSIZE': 81920,
			'GETMETADATA': True,
			'HTTPTIMEOUT': 5,
		}
	
	def setConfig(self):
		self.config=config
		self.config_set=True

	def run(self):
		if self.conf['STREAMURL']=='':
			raise ValueError("Configuration not set")

		if self.conf['STREAMURL']=='':
			raise ValueError("Stream URL not defined")

		self.store.incrementSourceGen()
		self.store.reset()
		
		icyread=0
		icynbstart=0
		icyreadfromblock=0
		icyreadingtitle=False
		icytemptitle=""
		
		fragments=self.store.getFragments()
		icylist=self.store.getIcyList()
		icyheaders=self.store.getIcyHeaders()
		
		if self.config['GETMETADATA']:
			stream=urllib2.urlopen(urllib2.Request(self.conf['STREAMURL'],headers={'Icy-MetaData':'1','User-Agent':'DiStreamer/'+VERSION}), timeout=HTTPTIMEOUT)
			if stream.headers.has_key('icy-metaint'):
				self.store.setIcyInt(int(stream.headers['icy-metaint']))
			for metaidx in stream.headers.keys():
				if ( metaidx[:4]=='icy-' and metaidx!='icy-metaint' ) or metaidx.lower()=='content-type':
					icyheaders[metaidx]=stream.headers[metaidx]
		else:
			stream=urllib2.urlopen(urllib2.Request(self.conf['STREAMURL'],headers={'User-Agent':'DiStreamer/'+VERSION}), timeout=HTTPTIMEOUT)
		
		self.store.setIcyHeaders(icyheaders)
		
		while True:
			fragment=stream.read(self.conf['FRAGMENTSIZE'])
			if len(fragment)!=self.conf['FRAGMENTSIZE']:
				raise ValueError("Incomplete read of block")
			idx=counter
			if self.store.getIcyInt()>0:
				if idx==icyreadfromblock:
					icytemptitle=icytemptitle+fragment[:icynbstart-1]
					icyreadingtitle=False
				if not icyreadingtitle and icytemptitle!='':
					self.store.setIcyTitle(icytemptitle)
					icytemptitle=""
				if idx<icyreadfromblock and icyreadingtitle:
					icytemptitle=icytemptitle+fragment
				if idx>=icyreadfromblock:
					if icynbstart>0:
						x=icynbstart
					else:
						x=0
					icynbstart=0
					while x<self.conf['FRAGMENTSIZE']:
						if icyread==self.store.getIcyInt():
							icylen=ord(fragment[x])*16+1
							icystart=x+1
							icytpos=x+icylen
							icytblock=idx
							while icytpos>=self.conf['FRAGMENTSIZE']:
								icytblock=icytblock+1
								icytpos=icytpos-self.conf['FRAGMENTSIZE']
								icynbstart=icytpos+1
							icyblock=icytblock
							icypos=icytpos
							icyreadfromblock=icyblock
							if icylen>1:
								if icyblock==idx:
									icyreadingtitle=False
									icytemptitle=fragment[icystart:icypos]
								else:
									icyreadingtitle=True
									icytemptitle=fragment[icystart:]
							if not icylist.has_key(icyblock):
								icylist[icyblock]=[]
							icylist[icyblock].append(icypos)
							x=x+icylen
							icyread=0
						icyread=icyread+1
						x=x+1
			counter=counter+1
			fragments[idx]=fragment
			self.logger.log("Created fragment "+str(idx),2)
			while len(fragments)>self.conf['FRAGMENTSNUMBER']:
				todelete=min(fragments.keys())
				del fragments[todelete]
				if icylist.has_key(todelete):
					del icylist[todelete]
				print str("Deleted fragment "+str(todelete),2)
			
			self.store.setFragments(fragments)
			self.store.setIcyList(icylist)
