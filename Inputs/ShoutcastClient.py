import urllib2

class ShoutcastClient():
	def __init__(self,store,logger):
		self.store=store
		'''
		Store will contain sourcegen, fragments, icyint, icylist, icyheaders and icytitle
		'''
		self.logger=logger
		self.config_set=False
		self.isclosing=False
		

	def getDefaultConfig(self):
		return {
			'streamurl': '',
			'fragmentsnumber': 5,
			'fragmentsize': 81920,
			'getmetadata': True,
			'httptimeout': 5,
		}
	
	def setConfig(self,config):
		self.config=config
		self.config_set=True

	def run(self):
		if not self.config_set:
			raise ValueError("Configuration not set")

		if self.config['streamurl']=='':
			raise ValueError("Stream URL not defined")

		self.store.incrementSourceGen()
		self.store.reset()
		
		counter=1
		icyread=0
		icynbstart=0
		icyreadfromblock=0
		icyreadingtitle=False
		icytemptitle=""
		
		fragments=self.store.getFragments()
		icylist=self.store.getIcyList()
		icyheaders=self.store.getIcyHeaders()
		
		self.logger.log("Connecting to stream: "+self.config['streamurl'],'ShoutcastClient',3)
		if self.config['getmetadata']:
			stream=urllib2.urlopen(urllib2.Request(self.config['streamurl'],headers={'Icy-MetaData':'1','User-Agent':'DiStreamer'}), timeout=self.config['httptimeout'])
			if stream.headers.has_key('icy-metaint'):
				self.store.setIcyInt(int(stream.headers['icy-metaint']))
			for metaidx in stream.headers.keys():
				if ( metaidx[:4]=='icy-' and metaidx!='icy-metaint' ) or metaidx.lower()=='content-type':
					icyheaders[metaidx]=stream.headers[metaidx]
		else:
			stream=urllib2.urlopen(urllib2.Request(self.config['streamurl'],headers={'User-Agent':'DiStreamer'}), timeout=self.config['httptimeout'])
		self.logger.log("Connected to stream",'ShoutcastClient',3)
		self.store.setIcyHeaders(icyheaders)
		
		while not self.isclosing:
			fragment=stream.read(self.config['fragmentsize'])
			if len(fragment)!=self.config['fragmentsize']:
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
					while x<self.config['fragmentsize']:
						if icyread==self.store.getIcyInt():
							icylen=ord(fragment[x])*16+1
							icystart=x+1
							icytpos=x+icylen
							icytblock=idx
							while icytpos>=self.config['fragmentsize']:
								icytblock=icytblock+1
								icytpos=icytpos-self.config['fragmentsize']
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
			self.logger.log("Created fragment "+str(idx),'ShoutcastClient',3)
			while len(fragments)>self.config['fragmentsnumber']:
				todelete=min(fragments.keys())
				del fragments[todelete]
				if icylist.has_key(todelete):
					del icylist[todelete]
				self.logger.log("Deleted fragment "+str(todelete),'ShoutcastClient',3)
			
			self.store.setFragments(fragments)
			self.store.setIcyList(icylist)
		self.logger.log('ShoutcastClient terminated normally','ShoutcastClient',2)
		
	def close(self):
		self.isclosing=True
