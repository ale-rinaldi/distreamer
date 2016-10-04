import urllib2,time,json

class DiStreamerRevClient():
	def __init__(self,store,logger):
		self.store=store
		self.logger=logger
		self.config_set=False
		self.isclosing=False
		

	def getDefaultConfig(self):
		return {
			'serverurl': '',
			'httptimeout': 5,
			'httpinterval': 3,
			'password': ''
		}
	
	def setConfig(self,config):
		self.config=config
		self.config_set=True

	def run(self):
		if not self.config_set:
			self.logger.log('Config not set','DiStreamerRevClient',1)
			return None
		if self.config['serverurl']=='':
			self.logger.log('Server URL not defined','DiStreamerRevClient',1)
			return None
		while not self.isclosing:
			fragments=self.store.getFragments()
			if self.config['password']!='':
				result=urllib2.urlopen(urllib2.Request(self.config['serverurl']+'/list/'+self.config['password'],headers={'User-Agent':'DiStreamer'}), timeout=self.config['httptimeout'])
			else:
				result=urllib2.urlopen(urllib2.Request(self.config['serverurl']+'/list',headers={'User-Agent':'DiStreamer'}), timeout=self.config['httptimeout'])
			exclen=result.headers['Content-Length']
			cslist=result.read()
			if len(cslist)!=int(exclen):
				self.logger.log("Incomplete read of list",'DiStreamerRevClient',2)
				return None
			infolist=json.loads(cslist)
			remotelist=infolist['fragmentslist']
			fkeys=fragments.keys()
			fkeys.sort()
			tosend=json.dumps({
					'fragmentslist': fkeys,
					'icyint': self.store.getIcyInt(),
					'icylist': self.store.getIcyList(),
					'icyheaders': self.store.getIcyHeaders(),
					'icytitle': self.store.getIcyTitle().encode('base64'),
					'sourcegen': self.store.getSourceGen()
				})
			if len(remotelist)>0:
				expfirst=min(remotelist)+1
			else:
				expfirst=1
			if expfirst!=1 and not expfirst in fkeys:
				if self.config['password']!='':
					result=urllib2.urlopen(urllib2.Request(self.config['serverurl']+'/list/'+self.config['password'],tosend,headers={'User-Agent':'DiStreamer'}), timeout=self.config['httptimeout'])
				else:
					result=urllib2.urlopen(urllib2.Request(self.config['serverurl']+'/list',tosend,headers={'User-Agent':'DiStreamer'}), timeout=self.config['httptimeout'])
			localfrags={}
			for fragn in fkeys:
				if self.isclosing:
					break
				if not fragn in remotelist:
					localfrags[fragn]=fragments[fragn]
			locfkeys=localfrags.keys()
			locfkeys.sort()
			for fragn in locfkeys:
				if self.config['password']:
					result=urllib2.urlopen(urllib2.Request(self.config['serverurl']+'/'+str(fragn)+'/'+self.config['password'],localfrags[fragn],headers={'User-Agent':'DiStreamer'}), timeout=self.config['httptimeout'])
				else:
					result=urllib2.urlopen(urllib2.Request(self.config['serverurl']+'/'+str(fragn),localfrags[fragn],headers={'User-Agent':'DiStreamer'}), timeout=self.config['httptimeout'])
				res=result.read()
				if res!='OK':
					self.logger.log('Failed to send block '+str(fragn),'DiStreamerRevClient',2)
					return None
				self.logger.log('Sent fragment '+str(fragn),'DiStreamerRevClient',3)
			if not self.isclosing:
				if self.config['password']!='':
					result=urllib2.urlopen(urllib2.Request(self.config['serverurl']+'/list/'+self.config['password'],tosend,headers={'User-Agent':'DiStreamer'}), timeout=self.config['httptimeout'])
				else:
					result=urllib2.urlopen(urllib2.Request(self.config['serverurl']+'/list',tosend,headers={'User-Agent':'DiStreamer'}), timeout=self.config['httptimeout'])
			time.sleep(self.config['httpinterval'])
		self.logger.log('DiStreamerRevClient terminated normally','DiStreamerRevClient',2)

	def close(self):
		self.isclosing=True
		self.logger.log('DiStreamerRevClient is terminating, this could need some time','ShoutcastClient',2)
