from tkFileDialog import askdirectory      
try:
    import json
except:
    import simplejson as json
from Tkinter import * 
import copy
import os
import time
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

class AutoScrollbar(Scrollbar):
    # a scrollbar that hides itself if it's not needed.  only
    # works if you use the grid geometry manager.
    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            # grid_remove is currently missing from Tkinter!
            self.tk.call("grid", "remove", self)
        else:
            self.grid()
        Scrollbar.set(self, lo, hi)
    def pack(self, **kw):
        raise TclError, "cannot use pack with this widget"
    def place(self, **kw):
        raise TclError, "cannot use place with this widget"

class Application():
    def __init__(self, master):

        frame = Frame(master)
        frame.pack(fill=BOTH,padx=2,pady=2)

        self.f1 = tkFont.Font(family="arial", size = "14", weight = "bold")
        self.titleLabel = Label(frame, width=38, padx = '3', pady = '3', font = self.f1, text = (VERSION),anchor=W)
        self.titleLabel.pack()

        self.report = ScrolledText(frame)

        menu = Menu(frame)
        root.config(menu=menu)

        filemenu = Menu(menu)
        menu.add_cascade(label="File", menu=filemenu)
        filemenu.add_command(label="Open...", command=self.get_data_file)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=root.quit)

        self.clear_button = Button(frame, text="Clear",command=self.clear)
        self.clear_button.pack(side=RIGHT)

        self.iterations = 1

        filemenu = Menu(menu)
        menu.add_cascade(label="Iterations", menu=filemenu)
        filemenu.add_command(label="1", command=lambda: self.set_iterations(1))
        filemenu.add_command(label="10", command=lambda: self.set_iterations(10))
        filemenu.add_command(label="100", command=lambda: self.set_iterations(100))
        filemenu.add_command(label="1000", command=lambda: self.set_iterations(1000))
        filemenu.add_command(label="5000", command=lambda: self.set_iterations(5000))

        self.write("use the \"File\" menu to open a data file")

        self.frame = frame

    def write(self,text,delete_text=False):
        if delete_text:
            self.report.settext(text)
        else:
            self.report.addtext(text)

    def clear(self):
        self.report.settext('')

    def set_iterations(self,num):
        self.iterations = num 
        if self.run_button:
            self.run_button.pack_forget()
        self.run_button = Button(self.frame, text="Run Tally with "+str(num)+" iterations",command=self.run_tally)
        self.run_button.pack(side=LEFT)
    
    def get_data_file(self):
        self.clear()
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
