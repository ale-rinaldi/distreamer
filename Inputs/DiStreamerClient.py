import urllib2,time

class DiStreamerClient():
	def __init__(self,store,logger):
		self.store=store
		self.logger=logger
		self.config_set=False
		self.isclosing=False
		

	def getDefaultConfig(self):
		return {
			'serverurl': '',
			'getmetadata': True,
			'httptimeout': 5,
			'httpinterval': 3,
		}
	
	def setConfig(self,config):
		self.config=config
		self.config_set=True

	def run(self):
		while not self.isclosing:
			result=urllib2.urlopen(urllib2.Request(self.config['serverurl']+'/list',headers={'User-Agent':'DiStreamer'}), timeout=self.config['httptimeout'])
			exclen=result.headers['Content-Length']
			cslist=result.read()
			if len(cslist)!=int(exclen):
				self.logger.log("Incomplete read of list",'DiStreamerClient',2)
				return False
			infolist=cslist.split('|')
			icyint=int(infolist[1])
			self.store.setIcyInt(icyint)
			if icyint>0:
				icylist=self.store.getIcyList()
				sicylist=infolist[2].split(',')
				for icyfrag in sicylist:
					aicylist=icyfrag.split(':')
					if aicylist[0]!='':
						icyidx=int(aicylist[0])
						icylist[icyidx]=map(int,aicylist[1].split('-'))
				self.store.setIcyList(icylist)
			aicyheaders=infolist[3].split(',')
			tmplist={}
			for header in aicyheaders:
				seppos=header.find(':')
				key=header[:seppos]
				val=header[seppos+1:]
				if key!='':
					tmplist[key]=val
			self.store.setIcyHeaders(tmplist)
			self.store.setSourceGen(int(infolist[4]))
			self.store.setIcyTitle(infolist[5])
			cslist=infolist[0]
			slist=cslist.split(',')
			list=map(int,slist)
			fragments=self.store.getFragments()
			for fragn in list:
				if self.isclosing:
					break
				if (not(fragments.has_key(fragn)) or fragments[fragn]==''):
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
		self.logger.log('DiStreamerClient terminated normally','ShoutcastClient',2)

	def close(self):
		self.isclosing=True
		self.logger.log('DiStreamerClient is terminating, this could need some time','ShoutcastClient',3)
