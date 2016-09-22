class DiStreamerStore():
	def __init__(self):
		self.sourcegen=0
		self.reset()

	def reset():
		self.fragments={}
		self.icylist={}
		self.icyheaders={}
		self.icyint=0
		self.icytitle=''

	def getFragments():
		return self.fragments

	def setFragments(fragments):
		self.fragments=fragments

	def getIcyList():
		return self.icylist

	def setIcyList(icylist):
		self.icylist=icylist

	def getIcyHeaders():
		return self.icyheaders

	def setIcyHeaders(icyheaders):
		self.icyheaders=icyheaders

	def getIcyInt():
		return self.icyint

	def setIcyInt(icyint):
		self.icyint=icyint

	def incrementSourceGen():
		self.sourcegen+=1
