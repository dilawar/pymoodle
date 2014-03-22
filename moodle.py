#!/usr/bin/env python 

"""
    moodle.py
    Author : Dilawar Singh
    Institute : IIT Bombay
    Email : dilawar@ee.iitb.ac.in
    Log : Created on Feb 16, 2012

        Saturday 22 March 2014 08:02:49 PM IST
        Changed to work with http://moodle.lyceejeanbart.fr/

    ABOUT : This module fetch assignements from moodle course page as specified
    in its configuration file .moodlerc which must be located in user home
    folder. See this file for options.

                                       
"""

import os
import re
import mechanize
import urllib2
import sys
import shutil
import subprocess
import urlparse
import glob
import tarfile
import zipfile
from collections import defaultdict
import errno

assignments = defaultdict(list)

def extract_asssignments(dirs):
  for dir in dirs:
      print("+ Extracting a submission into {}".format(dir.encode('utf-8')))
      path = dir
      os.chdir(path)
      listing = glob.glob(path+'/*gz')
      for file in listing:
          print(" |- Extracting archive ...{0}".format(file))
          subprocess.call(["tar", "xzvf", file], stdout=subprocess.PIPE)

      listing = glob.glob(path+'/*bz')
      for file in listing:
          print(" |- Extracting archive ...{0}".format(file))
          subprocess.call(["tar", "xjvf", file], stdout=subprocess.PIPE)

      listing = glob.glob(path+'/*zip')
      for file in listing:
          print(" |- Extracting archive ...{0}".format(file))
          subprocess.call(["unzip", "-o", file], stdout=subprocess.PIPE)

      listing = glob.glob(path+'/*rar')
      for file in listing:
          print(" |- Extracting archive ...{0}".format(file))
          subprocess.call(["unrar", "x", "-o+", file], stdout=subprocess.PIPE)

      listing = glob.glob(path+'/*tar')
      for file in listing:
          print(" |- Extracting archive ...{0}".format(file))
          subprocess.call(["tar", "xvf", file], stdout=subprocess.PIPE)


def unzipAssignemnetFile(inputFile, curDir):
    ''' Unzip the large file downloaded from moodle'''
    with zipfile.ZipFile(inputFile, "r") as myzip:
        listobj = myzip.infolist()
        filesToExtract = list()
        for obj in listobj:
            zippedFile = obj.filename
            filename = zippedFile.split("_")
            studentName = filename[0].strip()
            file = filename[1]
            assignments[studentName].append(file)
            path = os.path.join(curDir, studentName)
            try:
                os.makedirs(path)
            except OSError as exception:
                if exception.errno != errno.EEXIST:
                    raise  exception
            myzip.extract(zippedFile, path)
            pathToExtract= os.path.join(curDir, studentName, zippedFile)
            filesToExtract.append(path)
        extract_asssignments(filesToExtract)
        

class Moodle():

    """ A python application to access moodle and download data from it.
    """
    def __init__(self):
        print("Initializing moodle ... ")
        self.br = mechanize.Browser( factory=mechanize.RobustFactory())
        self.br.set_handle_equiv(False)
        self.br.set_handle_robots(False)
        self.br.set_handle_referer(False)
        self.br.set_handle_redirect(True)
        self.br.set_debug_redirects(True)
        self.br.set_debug_responses(False)
        self.br.set_debug_http(False)
        self.br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=2)
        self.br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux 1686; en-US;\
            rv:1.9.0.1) Gecko/201171615 Ubuntu/11.10-1 Firefox/3.0.1')]
    
    def set_proxy(self, proxy=None):
        if not proxy:
            self.br.set_proxies({})
        else:
            self.br.set_proxies({"http": os.environ['http_proxy']
                , "ftp": os.environ['ftp_proxy']
                , "https" : os.environ['https_proxy']}
                )

    def read_configuration(self):
        """ This function reads a config file and set the values needed for
        making a successfull connection to Moodle.
        """
        print("Reading configuration file ...")
        self.url = ''
        self.username = ""
        self.password = ""
        self.course_key = ""
        self.activity_name = ""
        self.activities = []
        self.num_assignment = 0;
        self.root_dir = "./Moodle";
        self.proxy = "false"
        self.extract = 'true'
        self.language = 'vhdl'
        self.regex = ''
        self.compile = 'false'
        self.compare = 'false'
        self.download = 'true'
        self.autotest = 'false'
        self.cxx = ''
        home = os.environ['HOME']
        path = home+"/.moodlerc"
        if os.path.isfile(path) :
            f = open(path, 'r')
        else :
            print "File .moodlerc does not exists in your home folder. \
            Existing..."
            sys.exit(0)

        for line in f :
            if line[0] == '#' :
                pass

            elif line.split() == "" :
                pass
            
            else :
                (key, val) = line.split("=")

                if key.split()[0] == 'url' :
                    self.url = val.split()[0]
                
                elif key.split()[0] == 'username' :
                    self.username = val.split()[0]
                

                elif key.split()[0] == 'password' :
                    self.password = ' '.join(val.split())
                    if self.password == '':
                        self.password=getpass.getpass()

                elif key.split()[0] == 'course' :
                    val = ' '.join(val.split())
                    self.course_key = val

                elif key.split()[0] == 'autotest' :
                    val = ' '.join(val.split())
                    self.autotest = val

                elif key.split()[0] == 'activities' :
                    val = ' '.join(val.split())
                    self.activity_name = val

                elif key.split()[0] == 'activity' :
                   val = ' '.join(val.split())
                   self.activities.append(val)
               
                elif key.split()[0] == 'download' :
                   self.download = val.split()[0] 
                
                elif key.split()[0] == 'downloaddir' :
                   self.root_dir = val.split()[0]
                
                elif key.split()[0] == 'extract' :
                   self.extract = val.split()[0]
                
                elif key.split()[0] == 'proxy' :
                   self.proxy = val.split()[0]

                elif key.split()[0] == 'language' :
                   self.language = val.split()[0]

                elif key.split()[0] == 'regex' :
                   self.regex = val.split()[0]

                elif key.split()[0] == 'compare' :
                   self.compare = val.split()[0]

                elif key.split()[0] == 'compile' :
                   self.compile = val.split()[0]

                elif key.split()[0] == 'cxx' :
                   self.cxx = val.split()[0]

                else :
                     print("Unknow configuration variable {0}.".format(
                         key.split()[0])
                         )
    
    def printAvailableLinks(self):
        ''' Print all available links on the page'''
        print("+ Available links are ")
        for l in self.br.links():
            print("|- {}".format(l.url))

    def make_connection(self):
        if self.proxy != "false" :
            print("Using proxy variables from environment ...")
        else :
            print("Ignoring proxy variables...")
            self.set_proxy()

        print("Logging into Moodle ..")
        res = self.br.open(self.url)
        # select the form and login
        assert self.br.viewing_html()

        form_id = 0;
        for i in self.br.forms():
            id = i.attrs.get('id') 
            id = id.lower()
            if id.find("login") == 0 :
                #select form 1 which is used for login.
                assert self.username.strip()
                assert self.password.strip()
                self.br.select_form(nr = form_id)
                self.br.form['username'] = self.username.strip()
                self.br.form['password'] = self.password.strip()
                res = self.br.submit()
                res = self.br.response()
            else:
                form_id = form_id + 1;


    def reachCoursePage(self):
        print("|- Figuring out the page where courses are listed for user")
        try:
            self.br.follow_link(text_regex='My courses')
        except Exception as e:
            print("|- Looks like course page is not at usual place. Guessing")

    def followLink(self, text_regex=None, url_regex=None):
        res = None
        if text_regex:
            try:
                res = self.br.follow_link(text_regex=text_regex)
            except Exception as e:
                print("ERROR: Failed to find link {}".format(text_regex))
                self.printAvailableLinks()
                sys.exit()
        elif url_regex:
            try: 
               res = self.br.follow_link(url_regex=url_regex)
            except Exception as e:
                print("ERROR: Failed to find link {}".format(url_regex))
                self.printAvailableLinks()
                sys.exit(0)
        assert(res is not None)
        print("\t...Success. Currently on:: '{}'".format(self.br.title()))
        return res

    def get_course_page(self):

        # We can handle both course name and id.
        print("|- Acquiring course page for {}".format(self.course_key))
        if self.course_key.isdigit() == False :
            self.course = self.followLink(text_regex=self.course_key)
            course_url = self.course.geturl()
            [url, id ] = course_url.split('id=')
            self.course_id = id
        else :
            self.course = self.br.follow_link(url_regex=r"course.*"+self.course_key)
            course_url = self.course.geturl()
            self.course_id = self.course_key 

    def goto_main_activity(self): 
        self.activity_id = []
        print ("|- Acquiring page of activity: {}".format(self.activity_name))
        activity_res = self.followLink(text_regex=self.activity_name)
        assert self.br.viewing_html()
        for l in self.br.links():
            if l.text == "Download all submissions":
                print("|- Downloading all submission in single zip file")
                fileName = os.path.join(self.root_dir
                        , self.activity_name+".zip")
                loc = self.br.retrieve(l.url, fileName)
                if os.path.isfile(fileName):
                    print("\t...Successfully downloaded {}".format(fileName))
                    return fileName
                else:
                    print("FATAL: Can't download data-file")
                    sys.exit()
    
    def download_data(self) :
        self.dir = "./Moodle"
        zipFile = self.goto_main_activity()
        if self.extract == "true":
            print("|- Extracting submissions")
            unzipAssignemnetFile(zipFile, self.root_dir)
        else:
            print("Not extracting the zip file {}".format(zipFile))

        
if __name__ == "__main__":

    moodle = Moodle()
    moodle.read_configuration()

    if moodle.download == "true" :
        moodle.make_connection()
        moodle.reachCoursePage()
        moodle.get_course_page()
        moodle.download_data()
        print("All done")
    else : pass

