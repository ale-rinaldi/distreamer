import sys
from ConfigParser import ConfigParser

class DiStreamerConfig:
    def __init__(self):
        config = ConfigParser()
        if len(sys.argv)>1:
            configfile=sys.argv[1]
        else:
            configfile='distreamer.conf'
        config.read([configfile])
        self.config=config
        
    def str2bool(self,v):
        return v.lower() in ("yes", "true", "t", "1")

    def getGeneralConfig(self):
        defaults={
            'outputlevel': 2,
            'logfile': '',
            'loglevel': 2
        }
        genconfig=dict(self.config.items('GENERAL'))
        for key in defaults:
            if genconfig.has_key(key):
                if type(defaults[key]) is int:
                    newval=int(genconfig[key])
                elif type(defaults[key]) is bool:
                    newval=self.str2bool(genconfig[key])
                else:
                    newval=genconfig[key]
                defaults[key]=newval
        defaults['inputmode']=self.config.get('INPUT','MODE')
        defaults['outputmode']=self.config.get('OUTPUT','MODE')
        return defaults
    
    def getInputConfig(self,defaults):
        inconfig=dict(self.config.items('INPUT'))
        del inconfig['mode']
        for key in defaults:
            if inconfig.has_key(key):
                if type(defaults[key]) is int:
                    newval=int(inconfig[key])
                elif type(defaults[key]) is bool:
                    newval=self.str2bool(inconfig[key])
                else:
                    newval=inconfig[key]
                defaults[key]=newval
        return defaults

    def getOutputConfig(self,defaults):
        outconfig=dict(self.config.items('OUTPUT'))
        del outconfig['mode']
        for key in defaults:
            if outconfig.has_key(key):
                if type(defaults[key]) is int:
                    newval=int(outconfig[key])
                elif type(defaults[key]) is bool:
                    newval=self.str2bool(outconfig[key])
                else:
                    newval=outconfig[key]
                defaults[key]=newval
        return defaults
