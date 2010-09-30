try:
    import json
except:
    import simplejson as json
from operator import itemgetter, attrgetter
from random import randint
from tkFileDialog import askdirectory      
from tkFileDialog import askopenfilename      
from Tkinter import * 
from tkSimpleDialog import askstring
import base64
import copy
import httplib
import md5
import mimetypes
import os
import string
import time
import tkFont 
import tkSimpleDialog
import urllib
import urllib2

VERSION = "DASe Uploader v.1.0"

MIMETYPES = [
        'application/msword',
        'application/ogg',
        'application/pdf',
        'application/xml',
        'application/xslt+xml',
        'audio/mpeg',
        'audio/mpg',
        'audio/ogg',
        'image/gif',
        'image/jpeg',
        'image/png',
        'image/tiff',
        'text/css',
        'text/html',
        'text/plain',
        'text/xml',
        'video/mp4',
        'video/ogg',
        'video/quicktime',
        ];


ABOUT_TEXT = """
about text and licensing here.
"""
HELP_TEXT = """
DASe Uploader Help text here
"""

DASE_HOST = 'daseupload.laits.utexas.edu'
DASE_BASE = '/'
PROTOCOL = 'https'

def rfc3339():
    """ Format a date the way Atom likes it (RFC3339)
    """
    return time.strftime('%Y-%m-%dT%H:%M:%S%z')

class ScrolledText(Frame):
    """ from O'Reilly Programming Python 3rd ed.
    """
    def __init__(self, parent=None, text='', file=None):
        Frame.__init__(self, parent)
        self.pack(expand=YES, fill=BOTH)                 # make me expandable
        self.makewidgets()
        self.settext(text, file)
    def makewidgets(self):
        sbar = Scrollbar(self)
        text = Text(self, relief=SUNKEN,height=18)
        sbar.config(command=text.yview)                  # xlink sbar and text
        text.config(yscrollcommand=sbar.set)             # move one moves other
        sbar.pack(side=RIGHT, fill=Y)                    # pack first=clip last
        text.pack(side=LEFT, expand=YES, fill=BOTH)      # text clipped first
        self.text = text
    def addtext(self,text):
        self.text.insert(END,text+"\n")
        self.text.focus()                                # save user a click
        self.text.yview_pickplace("end")
    def settext(self, text='', file=None):
        if file: 
            text = open(file, 'r').read()
        self.text.delete('1.0', END)                     # delete current text
        self.text.insert('1.0', text)                    # add at line 1, col 0
        self.text.mark_set(INSERT, '1.0')                # set insert cursor
        self.text.focus()                                # save user a click
    def gettext(self):                                   # returns a string
        return self.text.get('1.0', END+'-1c')           # first through last

class Application():
    def __init__(self, master):

        self.root = master
        frame = Frame(master)
        frame.pack(fill=BOTH,padx=2,pady=2)

        self.f1 = tkFont.Font(family="arial", size = "14", weight = "bold")
        self.titleLabel = Label(frame, width=66, padx = '3', pady = '3', font = self.f1, text = (VERSION),anchor=W)
        self.titleLabel.pack()

        self.report = ScrolledText(frame)

        menu = Menu(frame)
        self.menu = menu
        root.config(menu=menu)

        filemenu = Menu(menu)
        menu.add_cascade(label="File", menu=filemenu)
        filemenu.add_command(label="Login", command=self.login_user)
        filemenu.add_command(label="Select Directory...", command=self.get_directory)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=root.quit)

        self.clear_button = Button(frame, text="Clear",command=self.clear)
        self.clear_button.pack(side=RIGHT)

        #self.abort_button = Button(frame, text="Abort Upload",command=self.abort_upload)
        #self.abort_button.pack(side=LEFT)

        #self.write("use the \"File\" menu to select a directory")
        self.write("Please login\n")
        self.frame = frame
        self.collection = ''
        self.user = ''

    def login_user(self):
        eid = askstring('enter your EID','EID')
        password = askstring('enter your Web Service Key','Web Service Key')

        url = PROTOCOL+'://'+DASE_HOST+DASE_BASE.rstrip('/')+'/user/'+eid+'/collections.json?auth=service'

        # create a password manager
        password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
        
        # Add the username and password.
        # If we knew the realm, we could use it instead of ``None``.
        top_level_url = PROTOCOL+'://'+DASE_HOST+DASE_BASE.rstrip('/')
        password_mgr.add_password(None, top_level_url, eid, password)
        
        handler = urllib2.HTTPBasicAuthHandler(password_mgr)
        
        # create "opener" (OpenerDirector instance)
        opener = urllib2.build_opener(handler)
        
        # Now all calls to urllib2.urlopen use our opener.
        urllib2.install_opener(opener)

        response = urllib2.urlopen(url)

        json_colls = response.read()
        pycolls = json.loads(json_colls)

        colls = []
        self.coll_lookup = {}
        for c in pycolls:
            if 'admin' == pycolls[c]['auth_level']:
                tup = (c,pycolls[c]['collection_name'],pycolls[c]['collection_name'].lower())
                colls.append(tup)
                self.coll_lookup[c] = tup[1]
        colls.sort(key=itemgetter(2))
           
        filemenu = Menu(self.menu)
        self.menu.add_cascade(label="Collections", menu=filemenu)
        for coll in colls:
            filemenu.add_command(label=coll[1], command=lambda co=coll[0]: self.set_collection(co))
        self.write("Select a collection from the \"Collections\" menu above",True)
        self.user = eid
        self.password = password 
                
    def set_collection(self,ascii_id):
        self.collection = ascii_id
        self.write("Use the \"Select Directory...\" command in the \"File\" menu \nto select a directory of files to upload to \nthe  * "+self.coll_lookup[ascii_id]+" *  Collection\n",True)

    def write(self,text,delete_text=False):
        if delete_text:
            self.report.settext(text)
        else:
            self.report.addtext(text)

    def clear(self):
        self.report.settext('')

    def checkMd5(self,coll,md5):
        h = self.getHTTP() 
        h.request("GET",DASE_BASE.rstrip('/')+'/collection/'+coll+'/items/by/md5/'+md5+'.txt')  
        r = h.getresponse()
        if 200 == r.status:
            self.write(r.read())
            return True
        else:
            return False

    def postFile(self,path,filename,DASE_HOST,coll,mime_type,u,p):
        auth = 'Basic ' + string.strip(base64.encodestring(u + ':' + p))
        f = file(path.rstrip('/')+'/'+filename, "rb")
        self.body = f.read()                                                                     
        h = self.getHTTP()
        headers = {
            "Content-Type":mime_type,
            "Content-Length":str(len(self.body)),
            "Authorization":auth,
            "Title":filename,
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

    def abort_upload(self):
        self.root.destroy()

    def get_directory(self):
        self.clear()

        if not self.user:
            self.write('ERROR: please Login\n',True)
            return
        if not self.collection:
            self.write('ERROR: please select a collection\n',True)
            return
        self.write('processing file...')
        home = os.getenv('USERPROFILE') or os.getenv('HOME')
        dirpath = askdirectory(initialdir=home,title="Select A Folder")
        files = []
        for f in os.listdir(dirpath):
            (mime_type,enc) = mimetypes.guess_type(dirpath+f)
            if mime_type and mime_type in MIMETYPES:
                files.append(f)

        #work on confirmation
        #confirm = Toplevel()
        #button = Button(confirm, text="upload "+str(len(files))+" files",command=self.clear)
        #button.pack(padx=5,pady=5)

        for file in files:
            self.write("uploading "+file)
            self.frame.update_idletasks()
            status = self.postFile(dirpath,file,DASE_HOST,self.collection,mime_type,self.user,self.password)
            if (201 == status):
                self.write("server says... "+str(status)+" OK!!\n")
            else:
                self.write("problem with "+file+"("+str(status)+")\n")
            self.frame.update_idletasks()

if __name__ == "__main__":
    root = Tk()
    root.title(VERSION)
    root.geometry('+25+25')
    app = Application(root)
    root.mainloop() 
