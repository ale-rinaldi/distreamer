class DiStreamerStore:
    def __init__(self):
        self.sourcegen=0
        self.fragments={}
        self.icylist={}
        self.icyheaders={}
        self.icyint=-1
        self.icytitle=''

    def reset(self):
        self.fragments.clear()
        self.icylist.clear()
        self.icyheaders.clear()
        self.icyint=-1
        self.icytitle=''
        
    def clearFragmentsList(self):
        self.fragments.clear()

    def getFragments(self):
        return self.fragments

    def setFragments(self,fragments):
        temp={}
        temp.update(fragments)
        self.fragments.clear()
        self.fragments.update(temp)

    def getIcyList(self):
        return self.icylist

    def setIcyList(self,icylist):
        temp={}
        temp.update(icylist)
        self.icylist.clear()
        self.icylist.update(temp)

    def getIcyHeaders(self):
        return self.icyheaders

    def setIcyHeaders(self,icyheaders):
        temp={}
        temp.update(icyheaders)
        self.icyheaders.clear()
        self.icyheaders.update(temp)

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
