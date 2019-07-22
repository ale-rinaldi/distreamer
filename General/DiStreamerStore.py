import time

class DiStreamerStore:
    def __init__(self):
        self.sourcegen = 0
        self.fragments = {}
        self.icylist = {}
        self.icyheaders = {}
        self.icyint =- 1
        self.icytitle = ''
        self.lastupdate = int(time.time())

    def reset(self):
        self.fragments.clear()
        self.icylist.clear()
        self.icyheaders.clear()
        self.icyint =- 1
        self.icytitle = ''
        self.lastupdate = int(time.time())
        
    def clearFragmentsList(self):
        self.fragments.clear()
        self.lastupdate = int(time.time())

    def getFragments(self):
        return self.fragments

    def setFragments(self,fragments):
        temp = {}
        temp.update(fragments)
        self.fragments.clear()
        self.fragments.update(temp)
        self.lastupdate = int(time.time())

    def getIcyList(self):
        return self.icylist

    def setIcyList(self, icylist):
        temp = {}
        temp.update(icylist)
        self.icylist.clear()
        self.icylist.update(temp)
        self.lastupdate = int(time.time())

    def getIcyHeaders(self):
        return self.icyheaders

    def setIcyHeaders(self,icyheaders):
        temp = {}
        temp.update(icyheaders)
        self.icyheaders.clear()
        self.icyheaders.update(temp)
        self.lastupdate = int(time.time())

    def getIcyInt(self):
        return self.icyint

    def setIcyInt(self, icyint):
        self.icyint = icyint
        self.lastupdate = int(time.time())

    def getIcyTitle(self):
        return self.icytitle

    def setIcyTitle(self, icytitle):
        self.icytitle = icytitle
        self.lastupdate = int(time.time())
        
    def getSourceGen(self):
        return self.sourcegen

    def setSourceGen(self, sourcegen):
        self.sourcegen = sourcegen
        self.lastupdate = int(time.time())

    def incrementSourceGen(self):
        self.sourcegen += 1
        self.lastupdate = int(time.time())

    def getLastUpdate(self):
        return self.lastupdate
