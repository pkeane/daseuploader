from xml.dom import minidom
import fnmatch
import httplib
import md5
import mimetypes
import os
import urllib 
import wx
import base64
import string

DASE_HOST = 'daseupload.laits.utexas.edu'
DASE_BASE = '/'
PROTOCOL = 'https'


class UploaderPanel(wx.Panel):
    def __init__(self, parent, *args, **kwargs):
        """Create the UploaderPanel."""
        wx.Panel.__init__(self, parent, *args, **kwargs)

        self.parent = parent 
        atom_ns = "http://www.w3.org/2005/Atom"
        d = minidom.parse(urllib.urlopen(PROTOCOL+'://'+DASE_HOST+DASE_BASE.rstrip('/')+'/collections.atom?get_all=1'))
        entries = d.getElementsByTagNameNS(atom_ns,'entry')
        self.coll_dict = {}
        self.colls = []
        for entry in entries:
            title = entry.getElementsByTagNameNS(atom_ns,'title')[0].firstChild.nodeValue
            self.colls.append(title)
            self.coll_dict[title] = entry.getElementsByTagNameNS(atom_ns,'id')[0].firstChild.nodeValue.split('/').pop()
    
        self.chooser = wx.Choice(self, -1, (85, 18), choices=self.colls)
        self.chooser.Bind(wx.EVT_CHOICE,self.choose_coll)
        dirButton = wx.Button(self, label='Select Directory')
        dirButton.Bind(wx.EVT_BUTTON, self.picker)
        uploadButton = wx.Button(self, label='Upload')
        uploadButton.Bind(wx.EVT_BUTTON, self.upload_file)
        closeButton = wx.Button(self, label='Close')
        closeButton.Bind(wx.EVT_BUTTON, self.close)
        self.directory = wx.TextCtrl(self)
        self.username = wx.TextCtrl(self)
        self.password = wx.TextCtrl(self,-1,'',(0,0),(0,0),wx.TE_PASSWORD)
        username_label = wx.StaticText(self, -1,"Username: ",wx.Point(0,0),wx.Size(80,-1),wx.ALIGN_RIGHT)
        password_label = wx.StaticText(self, -1,"Password: ",wx.Point(0,0),wx.Size(80,-1),wx.ALIGN_RIGHT)
        self.contents = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.HSCROLL)
        hbox = wx.BoxSizer()
        hbox.Add(self.chooser, proportion=1)
        hbox.Add(self.directory, proportion=1, flag=wx.EXPAND)
        hbox.Add(dirButton, proportion=0, flag=wx.LEFT, border=5)
        hbox2 = wx.BoxSizer()
        hbox2.Add(username_label)
        hbox2.Add(self.username, proportion=1, flag=wx.EXPAND)
        hbox2.Add(password_label)
        hbox2.Add(self.password, proportion=1, flag=wx.EXPAND)
        hbox2.Add(uploadButton, proportion=1)
        hbox3 = wx.BoxSizer()
        hbox3.Add(closeButton, proportion=0, flag=wx.LEFT, border=5)
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(hbox, proportion=0, flag=wx.EXPAND | wx.ALL, border=5)
        vbox.Add(hbox2, proportion=0, flag=wx.EXPAND | wx.ALL, border=5)
        vbox.Add(self.contents, proportion=1, flag=wx.EXPAND | wx.LEFT | wx.BOTTOM | wx.RIGHT, border=5)
        vbox.Add(hbox3, proportion=0, flag=wx.EXPAND | wx.ALL, border=5)
        self.SetSizer(vbox)

    def picker(self,event):
        dialog = wx.DirDialog(None, "Choose a Directory", style=wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON)
        if dialog.ShowModal() == wx.ID_OK:
            dirname = dialog.GetPath()
            self.directory.SetValue(dirname)
#           self.write('uploading files from '+dirname+' into '+self.coll)
            dialog.Destroy

    def upload_file(self,event):
        u = self.username.GetValue()
        p = self.password.GetValue()
        if not hasattr(self,'coll'):
            self.write('Please select a Collection!')
            return
        if not self.coll:
            self.write('Please select a Collection!')
            return
        if '401' == str(self.checkAuth(DASE_HOST,self.coll,u,p)):
            self.write('unauthorized')
            return
        path = self.directory.GetValue()+'/'
        for f in os.listdir(path):
            if not fnmatch.fnmatch(f,'.*'):
                (mime_type,enc) = mimetypes.guess_type(path+f)
                self.write("uploading "+f)
                status = self.postFile(path,f,DASE_HOST,self.coll,mime_type,u,p)
                if (201 == status):
                    self.write("server says... "+str(status)+" OK!!\n")
                else:
                    self.write("problem with "+f+"("+str(status)+")\n")
        self.write("operations completed")

    def write(self,txt):
        orig = self.contents.GetValue()
        if orig:
            self.contents.SetValue(orig+"\n"+txt)
        else:
            self.contents.SetValue(txt)
        wx.YieldIfNeeded()

    def postFile(self,path,filename,DASE_HOST,coll,mime_type,u,p):
        auth = 'Basic ' + string.strip(base64.encodestring(u + ':' + p))
        f = file(path+filename, "rb")
        self.body = f.read()                                                                     
        h = self.getHTTP()
        headers = {
            "Content-Type":mime_type,
            "Content-Length":str(len(self.body)),
            "Authorization":auth,
            "Slug":filename,
        };

        md5sum = md5.new(self.body).hexdigest()
        if not self.checkMd5(coll,md5sum):
            h.request("POST",DASE_BASE.rstrip('/')+'/media/'+coll,self.body,headers)
            r = h.getresponse()
            return (r.status)

    def getHTTP(self):
        if ('https' == PROTOCOL):
            h = httplib.HTTPSConnection(DASE_HOST,443)
        else:
            h = httplib.HTTPConnection(DASE_HOST,80)
        return h


    def checkAuth(self,DASE_HOST,coll,u,p):
        auth = 'Basic ' + string.strip(base64.encodestring(u + ':' + p))
        headers = {
            "Authorization":auth,
        };
        h = self.getHTTP()
        h.request("POST",DASE_BASE.rstrip('/')+'/media/'+coll,None,headers)
        r = h.getresponse()
        return (r.status)

    def choose_coll(self,event):
        self.coll = self.coll_dict[self.colls[self.chooser.GetSelection()]]

    def close(self,event):
        frame.Destroy()

    def checkMd5(self,coll,md5):
        h = self.getHTTP() 
        h.request("GET",DASE_BASE.rstrip('/')+'/collection/'+coll+'/items/by/md5/'+md5+'.txt')  
        r = h.getresponse()
        if 200 == r.status:
            self.write(r.read())
            return True
        else:
            return False

class UploaderFrame(wx.Frame):
    """ Main Frame holding the Panel. """
    def __init__(self, *args, **kwargs):
        wx.Frame.__init__(self, *args, **kwargs)

        # Add the Panel
        self.Panel = UploaderPanel(self)

    def OnQuit(self, event=None):
        """Exit application."""
        self.Close()

if __name__=='__main__':
    app = wx.App()
    frame = UploaderFrame(None, title="DASe Uploader", size=(755, 535))
    frame.Show()
    app.MainLoop()

