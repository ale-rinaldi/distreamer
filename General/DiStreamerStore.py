class DiStreamerStore:
	def __init__(self):
		self.sourcegen=0
		self.reset()

	def reset(self):
		self.fragments={}
		self.icylist={}
		self.icyheaders={}
		self.icyint=0
		self.icytitle=''

	def getFragments(self):
		return self.fragments

	def setFragments(self,fragments):
		self.fragments=fragments

	def getIcyList(self):
		return self.icylist

	def setIcyList(self,icylist):
		self.icylist=icylist

	def getIcyHeaders(self):
		return self.icyheaders

	def setIcyHeaders(self,icyheaders):
		self.icyheaders=icyheaders

	def getIcyInt(self):
		return self.icyint

	def setIcyInt(self,icyint):
		self.icyint=icyint

	def getIcyTitle(self):
		return self.icytitle

	def setIcyTitle(self,icytitle):
		self.icytitle=icytitle
		
	def getSourceGen(self):
		return self.sourcegen

	def setSourceGen(self,sourcegen):
		self.sourcegen=sourcegen

	def incrementSourceGen(self):
		self.sourcegen+=1
