from tkFileDialog import askdirectory      
from tkSimpleDialog import askstring
try:
    import json
except:
    import simplejson as json
from Tkinter import * 
import copy
import os
import time
import urllib
import urllib2
import httplib
import mimetypes
import tkFont 
from operator import itemgetter, attrgetter
from random import randint

VERSION = "DASe Uploader v.1.0"

MIMETYPES = ['image/jpeg','image/tiff','image/gif']

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
    def settext(self, text='', file=None):
        if file: 
            text = open(file, 'r').read()
        self.text.delete('1.0', END)                     # delete current text
        self.text.insert('1.0', text)                    # add at line 1, col 0
#        self.text.mark_set(INSERT, '1.0')                # set insert cursor
        self.text.focus()                                # save user a click
    def gettext(self):                                   # returns a string
        return self.text.get('1.0', END+'-1c')           # first through last

class Application():
    def __init__(self, master):

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
        filemenu.add_command(label="Open...", command=self.get_data_file)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=root.quit)

        self.clear_button = Button(frame, text="Clear",command=self.clear)
        self.clear_button.pack(side=RIGHT)

        self.login_button = Button(frame, text="Login",command=self.login_user)
        self.login_button.pack(side=LEFT)

        #self.write("use the \"File\" menu to select a directory")
        self.write("Please login (see \"Login\" button below)")
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
                
    def set_collection(self,ascii_id):
        self.collection = ascii_id
        self.write("Use the \"Open...\" command in the \"File\" menu \nto select a directory of files to upload to \nthe  * "+self.coll_lookup[ascii_id]+" *  Collection\n",True)

    def write(self,text,delete_text=False):
        if delete_text:
            self.report.settext(text)
        else:
            self.report.addtext(text)

    def clear(self):
        self.report.settext('')

    def get_data_file(self):
        self.clear()
        if not self.user:
            self.write('ERROR: please Login\n',True)
            return
        if not self.collection:
            self.write('ERROR: please select a collection\n',True)
            return
        self.write('processing file...')
        dirpath = askdirectory(title="Select A Folder")
        for f in os.listdir(dirpath):
            if not os.path.isfile(f):
                (mime_type,enc) = mimetypes.guess_type(dirpath+f)
                if mime_type and mime_type in MIMETYPES:
                    self.write(mime_type)
                    self.write("uploading "+f)
                #status = self.postFile(path,f,DASE_HOST,self.coll,mime_type,u,p)
#                if (201 == status):
#                    self.write("server says... "+str(status)+" OK!!\n")
#                else:
#                    self.write("problem with "+f+"("+str(status)+")\n")

if __name__ == "__main__":
    root = Tk()
    root.title(VERSION)
    root.geometry('+25+25')
    app = Application(root)
    root.mainloop() 
