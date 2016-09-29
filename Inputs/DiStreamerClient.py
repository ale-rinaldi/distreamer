import urllib2,time,json

class DiStreamerClient():
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
				self.logger.log("Incomplete read of list",'DiStreamerClient',2)
				return False
			infolist=json.loads(cslist)
			self.store.setIcyInt(infolist['icyint'])
			self.store.setIcyList(infolist['icylist'])
			self.store.setIcyHeaders(infolist['icyheaders'])
			self.store.setSourceGen(infolist['sourcegen'])
			self.store.setIcyTitle(infolist['icytitle'])
			list=infolist['fragmentslist']
			fragments=self.store.getFragments()
			for fragn in list:
				if self.isclosing:
					break
				if (not(fragments.has_key(fragn)) or fragments[fragn]==''):
					if self.config['password']:
						result=urllib2.urlopen(urllib2.Request(self.config['serverurl']+'/'+str(fragn)+'/'+self.config['password'],headers={'User-Agent':'DiStreamer'}), timeout=self.config['httptimeout'])
					else:
						result=urllib2.urlopen(urllib2.Request(self.config['serverurl']+'/'+str(fragn),headers={'User-Agent':'DiStreamer'}), timeout=self.config['httptimeout'])
					exclen=result.headers['Content-Length']
					fragment=result.read()
					if len(fragment)!=int(exclen):
						self.logger.log('Incomplete read of block','DiStreamerClient',2)
						return False
					fragments[fragn]=fragment
					self.store.setFragments(fragments)
					self.logger.log('Downloaded fragment '+str(fragn),'DiStreamerClient',3)
			locallist=fragments.keys()
			for localfragn in locallist:
				if self.isclosing:
					break
				if(localfragn not in list):
					del fragments[localfragn]
					self.store.setFragments(fragments)
					self.logger.log('Deleted fragment '+str(localfragn),'DiStreamerClient',3)
			time.sleep(self.config['httpinterval'])
		self.logger.log('DiStreamerClient terminated normally','DiStreamerClient',2)

	def close(self):
		self.isclosing=True
		self.logger.log('DiStreamerClient is terminating, this could need some time','ShoutcastClient',3)
