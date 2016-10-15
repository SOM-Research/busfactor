__author__ = 'atlanmod'

from bus_factor_metric import Metrics
from Tkinter import *
from tkFileDialog import *
import ttk
import os
import tkMessageBox
import shutil
import logging
import getopt
import threading
import re
import traceback
from PIL import ImageTk, Image

class BusFactor(Tk):

    LOG_FILENAME = "bus_factor_log"
    NOTIFICATION = "bus_factor_notification"

    def __init__(self, notify):
        Tk.__init__(self)
        self.mypath = os.path.dirname(os.path.abspath(__file__)) + "/"

        self.logger = logging.getLogger('bus_factor')
        fileHandler = logging.FileHandler(BusFactor.LOG_FILENAME, mode='w')
        formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s", "%Y-%m-%d %H:%M:%S")
        fileHandler.setFormatter(formatter)

        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(fileHandler)

        self.NOTIFY = notify

        self.JSON_PATH = ""
        self.initialize_gui()
        self.title("Bus Factor Calculator")
        self.mainloop()

    def search_for_resource(self):
        f = askopenfilename(parent=self, title='Choose a file',
                            filetypes=[("JSON files", "*.json")])
        self.JSONPathVariable.set(f)

    def initialize_gui(self):

        img = Image.open(self.mypath + "bus_img.png")
        img = img.resize((250, 250), Image.ANTIALIAS)
        img = ImageTk.PhotoImage(img)

        labelImg = Label(image=img)
        labelImg.image = img
        labelImg.grid(row=0, columnspan=2, rowspan=2, sticky='WE')

        ##########################
        #select repo
        labelJSONPath = Label(self, text=u"JSON Path", anchor="w")
        labelJSONPath.grid(column=0, row=3, sticky='W')

        self.JSONPathVariable = StringVar()
        self.entryJSONPath = Entry(self, textvariable=self.JSONPathVariable, width=40)
        self.entryJSONPath.grid(column=1, row=3, sticky='W')

        buttonSearchJSON = Button(self, text=u"search", command=self.search_for_resource)
        buttonSearchJSON.grid(column=2, row=3, sticky="E")

        ##########################
        #empty label
        emptyLabel = Label(self, anchor="w")
        emptyLabel.grid(column=0, row=4, sticky='WE')

        ##########################
        #Tuning label
        labelTuning = Label(self, text=u"Tuning:", anchor="w")
        labelTuning.grid(column=0, row=5, sticky='WE')

        #Primary expert knowledge
        labelPrimaryExpertKnowledge = Label(self, text=u"Primary Dev. Knowl.", anchor="w")
        labelPrimaryExpertKnowledge.grid(column=0, row=6, sticky='W')

        self.labelPrimaryExpertKnowledgeVariable = StringVar()
        entryLabelPrimaryExpertKnowledge = Entry(self, textvariable=self.labelPrimaryExpertKnowledgeVariable)
        self.labelPrimaryExpertKnowledgeVariable.set("1/D")
        entryLabelPrimaryExpertKnowledge.grid(column=1, row=6, sticky='W')

        #Secondary Expert knowledge proportion
        labelSecondaryExpertProportion = Label(self, text=u"Secondary Dev. Knowl. Prop.", anchor="w")
        labelSecondaryExpertProportion.grid(column=0, row=7, sticky='W')

        self.labelSecondaryExpertProportionVariable = StringVar()
        entryLabelSecondaryExpertProportion = Entry(self, textvariable=self.labelSecondaryExpertProportionVariable)
        self.labelSecondaryExpertProportionVariable.set("0.5")
        entryLabelSecondaryExpertProportion.grid(column=1, row=7, sticky='W')

        #detail level
        self.detailLevelVariable = StringVar()
        labelDetailLevel = Label(self, text=u"Detail Level", anchor="w")
        labelDetailLevel.grid(column=0, row=8, sticky='W')

        self.detailLevelComboBox = ttk.Combobox(self, textvariable=self.detailLevelVariable)
        self.detailLevelComboBox['values'] = ('line', 'file')
        self.detailLevelComboBox.current(0)
        self.detailLevelComboBox.grid(column=1, row=8, sticky='W')


        #metric
        labelMetric = Label(self, text=u"Metric", anchor="w")
        labelMetric.grid(column=0, row=9, sticky='W')

        self.metricComboBoxVariable = StringVar()
        self.metricComboBox = ttk.Combobox(self, textvariable=self.metricComboBoxVariable)
        self.metricComboBox['values'] = ('last change', 'multiple changes', 'distinct changes', 'weighted distinct changes')
        self.metricComboBox.current(0)
        self.metricComboBox.grid(column=1, row=9, sticky='W')

        #Finish button
        self.buttonFinish = Button(self, text=u"Execute", command=self.launch_thread_execute)
        self.buttonFinish.grid(column=1, row=10, sticky="E")

        #Abort interrupt
        self.buttonAbort = Button(self, text=u"Abort", command=self.launch_thread_interrupt)
        self.buttonAbort.grid(column=2, row=10, sticky="E")
        self.buttonAbort.config(state=DISABLED)

        self.info_execution = StringVar()
        labelExecuting = Label(self, textvariable=self.info_execution, anchor="w")
        labelExecuting.grid(column=0, row=10, sticky='EW')

        self.resizable(True, False)
        
        # TKinker is not thread safe!
        # See http://stackoverflow.com/questions/22541693/tkinter-and-thread-out-of-stack-space-infinite-loop
        self.resetButtons = False
        self.importingFailureMsg = ""
        def do_every_50_ms(self):
            if self.resetButtons:
                self.buttonFinish.config(state=NORMAL)
                self.buttonAbort.config(state=DISABLED)
                self.resetButtons = False
            if self.importingFailureMsg:
                tkMessageBox.showerror("Execution failed:", 
                                       self.importingFailureMsg)
                self.importingFailureMsg = ""
            self.after(50, do_every_50_ms, self)
        do_every_50_ms(self)

    def search_for_directory(self):
        dir = askdirectory(parent=self, title='Choose a directory')
        self.repoPathVariable.set(dir)
        try:
            repoName = dir.split('/')[-1]
            self.repoNameVariable.set(re.sub(r'\W', '', repoName).lower())
        except:
            try:
                repoName = dir.split('\\')[-1]
                self.repoNameVariable.set(re.sub(r'\W', '', repoName).lower())
            except:
                repoName = ''

    def search_for_resource(self):
        f = askopenfilename(parent=self, title='Choose a file',
                            filetypes=[("Forbidden-resource files", "*.json")])
        self.JSONPathVariable.set(f)

    def check_path_existance(self, string):
        flag = True
        if not os.path.exists(string):
            flag = False
        return flag

    def launch_thread_interrupt(self):
        self.buttonFinish.config(state=DISABLED)
        self.buttonAbort.config(state=NORMAL)
        self.thread_interrupt = threading.Thread(target=self.interrupt)
        self.thread_interrupt.daemon = True
        self.thread_interrupt.start()
        self.thread_interrupt.join()

    def launch_thread_execute(self):
        self.info_execution.set("Executing...")
        self.buttonFinish.config(state=DISABLED)
        self.buttonAbort.config(state=NORMAL)
        self.thread_execute = threading.Thread(target=self.validator)
        self.thread_execute.daemon = True
        self.thread_execute.start()

    def interrupt(self):
        self.info_execution.set("Aborting...")
        sys.exc_clear()
        sys.exc_traceback = sys.last_traceback = None
        os._exit(-1)

    def validator(self):
        flag = True
        if self.JSONPathVariable.get() == "":
            self.JSONPathVariable.set("path cannot be empty!")
            flag = False
        else:
            if not self.check_path_existance(self.JSONPathVariable.get()):
                self.repoPathVariable.set("not valid path!")
                flag = False

        if self.labelPrimaryExpertKnowledgeVariable.get() == "":
            self.labelPrimaryExpertKnowledgeVariable.set("cannot be empty!")
            flag = False
        else:
            if self.labelPrimaryExpertKnowledgeVariable.get() != "1/D":
                try:
                    value = float(self.labelPrimaryExpertKnowledgeVariable.get())
                    if value < 0 or value >= 1:
                        self.labelPrimaryExpertKnowledgeVariable.set("(0,1] || 1/D")
                        flag = False
                except:
                    self.labelPrimaryExpertKnowledgeVariable.set("(0,1] || 1/D")
                    flag = False


        if self.labelSecondaryExpertProportionVariable.get() == "":
            self.labelSecondaryExpertProportionVariable.set("cannot be empty!")
            flag = False
        else:
            try:
                value = float(self.labelSecondaryExpertProportionVariable.get())
                if value < 0 or value >= 1:
                    self.labelSecondaryExpertProportionVariable.set("(0,1]")
                    flag = False
            except:
                flag = False
                self.labelSecondaryExpertProportionVariable.set("(0,1]")

        if flag:
            try:
                self.execute_process()
            except:
                print traceback.format_exc()
                self.info_execution.set("Failed")
                #self.buttonFinish.config(state=NORMAL)
                #self.buttonAbort.config(state=DISABLED)
                self.importingFailureMsg = traceback.format_exc(limit=1)
            self.resetButtons = True

    def execute_process(self):
        self.init_process()
        self.start_process()
        self.notify()
        self.info_execution.set("Finished")
        #self.buttonFinish.config(state=NORMAL)
        #self.buttonAbort.config(state=DISABLED)
        self.resetButtons = True

    def notify(self):
        if self.NOTIFY:
            notified = open(self.NOTIFICATION, "w")
            notified.close()
        sys.exc_clear()
        sys.exc_traceback = sys.last_traceback = None
        return

    def start_process(self):
        input_json = self.JSONPathVariable.get()

        output_json = self.OUTPUT_DIRECTORY_VISUALIATION
        metrics = Metrics(input_json, output_json,
                          self.DEVELOPER_KNOWLEDGE_STRATEGY,
                          self.PRIMARY_EXPERT_KNOWLEDGE,
                          self.SECONDARY_EXPERT_KNOWLEDGE_PROPORTION, self.logger)
        metrics.export_bus_factor_information()

    def init_process(self):
        self.OUTPUT_DIR = './output/'
        self.OUTPUT_DIRECTORY_VISUALIATION = self.OUTPUT_DIR + "data/"
        self.JSON_PATH = self.JSONPathVariable.get()

        if self.detailLevelVariable.get() == "line":
             self.LINE_DETAILS = True
        else:
            self.LINE_DETAILS = False

        if self.labelPrimaryExpertKnowledgeVariable.get() == "1/D":
            self.PRIMARY_EXPERT_KNOWLEDGE = "default"
        else:
            self.PRIMARY_EXPERT_KNOWLEDGE = self.labelPrimaryExpertKnowledgeVariable.get()

        if self.labelSecondaryExpertProportionVariable.get() == "0.5":
            self.SECONDARY_EXPERT_KNOWLEDGE_PROPORTION = "default"
        else:
            self.SECONDARY_EXPERT_KNOWLEDGE_PROPORTION = self.labelSecondaryExpertProportionVariable.get()

        self.DEVELOPER_KNOWLEDGE_STRATEGY = self.metricComboBoxVariable.get().replace(' ', '_')

        #create output directories
        if not os.path.exists(self.OUTPUT_DIRECTORY_VISUALIATION):
            os.makedirs(self.OUTPUT_DIRECTORY_VISUALIATION)
        shutil.copy(self.mypath + "index.html", self.OUTPUT_DIR)
        shutil.copytree(self.mypath + "css", self.OUTPUT_DIR + 'css')
        shutil.copytree(self.mypath + "js", self.OUTPUT_DIR + 'js')


def main(argv):
    notify = False
    try:
        opts, args = getopt.getopt(argv, "hn", ["notify="])
    except getopt.GetoptError:
        print 'bus_factor_gui.py -n <notify>'
        sys.exit(2)
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            print 'bus_factor_gui.py -n <notify:True|False>'
            sys.exit()
        elif opt in ("-n", "--notify"):
            notify = bool(args[0])
    #if notify is true, a file is generate after the bus factor calculation to notify tool.py
    BusFactor(notify)

if __name__ == "__main__":
    main(sys.argv[1:])
