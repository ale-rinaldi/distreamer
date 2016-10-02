import threading, time, importlib, sys
from General.DiStreamerConfig import DiStreamerConfig
from General.DiStreamerLogger import DiStreamerLogger
from General.DiStreamerStore import DiStreamerStore
from General.DiStreamerThread import DiStreamerThread

config=DiStreamerConfig()
logger=DiStreamerLogger(config.getGeneralConfig())
store=DiStreamerStore()

logger.log('DiStreamer started','Main',1)

def initInput():
	global config,inputthread,store,logger
	genconfig=config.getGeneralConfig()
	mode=genconfig['inputmode']
	mod=importlib.import_module('Inputs.'+mode)
	klass=getattr(mod,mode)
	input=klass(store,logger)
	inputconfig=config.getInputConfig(input.getDefaultConfig())
	input.setConfig(inputconfig)
	inputthread=DiStreamerThread(input)
	
def initOutput():
	global config,outputthread,store,logger
	genconfig=config.getGeneralConfig()
	mode=genconfig['outputmode']
	mod=importlib.import_module('Outputs.'+mode)
	klass=getattr(mod,mode)
	output=klass(store,logger)
	outputconfig=config.getOutputConfig(output.getDefaultConfig())
	output.setConfig(outputconfig)
	outputthread=DiStreamerThread(output)
	
def startInput():
	global inputthread
	inputthread.start()
	
def startOutput():
	global outputthread
	outputthread.start()

initInput()
initOutput()
startInput()
startOutput()
	
try:
	while True:
		if not inputthread.isAlive():
			logger.log('Input thread no longer running, restarting','Main',2)
			initInput()
			startInput()
		if not outputthread.isAlive():
			logger.log('Output thread no longer running, restarting','Main',2)
			initOutput()
			startOutput()
		time.sleep(1)
except KeyboardInterrupt:
	logger.log('Closing DiStreamer','Main',1)
	inputthread.close()
	outputthread.close()
	currtime=time.time()
	while (outputthread.isAlive() or inputthread.isAlive()):
		if time.time()>currtime+5:
			logger.log('One of the threads did not exit in 5 seconds. Killing it.','Main',2)
			break
		time.sleep(0.3)
	sys.exit(0)
except:
	logger.log('Unhandled error, DiStreamer must be closed. Sorry...','Main',1)
	inputthread.close()
	outputthread.close()
	currtime=time.time()
	while (outputthread.isAlive() or inputthread.isAlive()):
		if time.time()>currtime+5:
			logger.log('One of the threads did not exit in 5 seconds. Killing it.','Main',2)
			break
		time.sleep(0.3)
	sys.exit(0)