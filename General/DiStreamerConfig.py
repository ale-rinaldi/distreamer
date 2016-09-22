from ConfigParser import ConfigParser

''' TODO: check configuration options and stop if something is missing or invalid '''
class DiStreamerConfig(self):
	def __init__(self):
		try:
			config = ConfigParser()
			if len(sys.argv)>1:
				configfile=sys.argv[1]
			else:
				configfile='distreamer.conf'
			config.read([configfile])
		except:
			raise ValueError('Unable to read configuration file '+configfile)
		self.config=config

	def getGeneralConfig(self):
		genconfig=dict(self.config.items('GENERAL'))
		genconfig['inputmode']=self.config.get('INPUT','MODE')
		genconfig['outputmode']=self.config.get('OUTPUT','MODE')
		return genconfig
		
	def getInputConfig(self,defaults):
		inconfig=dict(self.config.items('INPUT'))
		del inconfig['MODE']
		for key in defaults:
			if inconfig.has_key(key):
				defaults[key]=inconfig[key]
		return defaults

	def getOutputConfig(self,defaults):
		outconfig=dict(self.config.items('OUTPUT'))
		del outconfig['MODE']
		for key in defaults:
			if outconfig.has_key(key):
				defaults[key]=inconfig[key]
		return defaults
