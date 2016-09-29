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
		while not self.isclosing:
			if self.config['password']!='':
				result=urllib2.urlopen(urllib2.Request(self.config['serverurl']+'/list/'+self.config['password'],headers={'User-Agent':'DiStreamer'}), timeout=self.config['httptimeout'])
			else:
				result=urllib2.urlopen(urllib2.Request(self.config['serverurl']+'/list',headers={'User-Agent':'DiStreamer'}), timeout=self.config['httptimeout'])
			exclen=result.headers['Content-Length']
			cslist=result.read()
			if len(cslist)!=int(exclen):
				self.logger.log("Incomplete read of list",'DiStreamerRevClient',2)
				return False
			infolist=json.loads(cslist)
			remotelist=infolist['fragmentslist']
			fragments=self.store.getFragments()
			for fragn in fragments.keys():
				if self.isclosing:
					break
				if not fragn in remotelist:
					if self.config['password']:
						result=urllib2.urlopen(urllib2.Request(self.config['serverurl']+'/'+str(fragn)+'/'+self.config['password'],fragments[fragn],headers={'User-Agent':'DiStreamer'}), timeout=self.config['httptimeout'])
					else:
						result=urllib2.urlopen(urllib2.Request(self.config['serverurl']+'/'+str(fragn),fragments[fragn],headers={'User-Agent':'DiStreamer'}), timeout=self.config['httptimeout'])
					res=result.read()
					if res!='OK':
						self.logger.log('Failed to send block '+str(fragn),'DiStreamerRevClient',2)
						return False
					self.logger.log('Sent fragment '+str(fragn),'DiStreamerRevClient',3)
			if not self.isclosing:
				flist=self.store.getFragments().keys()
				flist.sort()
				tosend=json.dumps({
					'fragmentslist': flist,
					'icyint': self.store.getIcyInt(),
					'icylist': self.store.getIcyList(),
					'icyheaders': self.store.getIcyHeaders(),
					'icytitle': self.store.getIcyTitle(),
					'sourcegen': self.store.getSourceGen()
				})
				if self.config['password']!='':
					result=urllib2.urlopen(urllib2.Request(self.config['serverurl']+'/list/'+self.config['password'],tosend,headers={'User-Agent':'DiStreamer'}), timeout=self.config['httptimeout'])
				else:
					result=urllib2.urlopen(urllib2.Request(self.config['serverurl']+'/list',tosend,headers={'User-Agent':'DiStreamer'}), timeout=self.config['httptimeout'])
			time.sleep(self.config['httpinterval'])
		self.logger.log('DiStreamerRevClient terminated normally','DiStreamerRevClient',2)

	def close(self):
		self.isclosing=True
		self.logger.log('DiStreamerRevClient is terminating, this could need some time','ShoutcastClient',3)
