'''
This is the UI part of the LAAFU program
Author: Robert ZHAO Ziqi
'''

import sys
from os import getcwd, path, listdir
from PyQt5.QtCore import Qt,QObject,QThread,pyqtSignal
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QTextCursor,QColor, QIcon
from main import construct_fp_database, detect, detect_original
from heatmap_plotter import *

class DBThread(QThread):

    def __init__(self, root_path="", paths_file="", parent=None):
        super(DBThread, self).__init__(parent)
        self.root_path = root_path
        self.paths_file = paths_file

    def run(self):
        pre_target = path.splitext(path.basename(self.paths_file))[0]
        construct_fp_database(self.root_path,pre_target)

class DetectThread(QThread):
    def __init__(self,target_file="",root_path="", parent=None):
        super(DetectThread, self).__init__(parent)
        self.root_path = root_path
        self.target_file = target_file

    def run(self):
        # detect(self.target_file,self.root_path)
        detect_original(self.target_file,self.root_path)

class LAAFU_Main(QWidget):

    def __init__(self, root_path = "", paths_file="", target_file=""):
        super().__init__()
        self.title = 'LAAFU System'
        self.width = 800
        self.height = 10
        self.paths_file = paths_file
        self.root_path = root_path
        self.target_file = target_file

        self.initUI()
        
    def initUI(self):
        # 0.0 window settings
        self.setWindowTitle(self.title)
        self.setMinimumSize(self.width, self.height)
        self.setWindowIcon(QIcon("icon.png"))

        # 0.1 main title
        self.main_title = QLabel("Welcome to LAAFU System!")
        self.main_title.setAlignment(Qt.AlignCenter)

        # 1.1 dir location
        self.dir = QLabel("Data folder: {}".format(self.root_path))
        self.dir_loc = QPushButton("Choose folder")
        self.dir_loc.setFixedWidth(160)
        def choose_path():
            self.root_path = QFileDialog.getExistingDirectory(self,"Choose a folder", path.dirname(getcwd()))
            self.dir.setText("Data folder: {}".format(self.root_path))
        self.dir_loc.clicked.connect(choose_path)

        # 1.2 hbox to contain them
        hbox1 = QHBoxLayout()
        hbox1.addWidget(self.dir)
        hbox1.addWidget(self.dir_loc)

        # 2.1 Paths file
        self.paths = QLabel("Paths File: {}".format(self.paths_file))
        self.paths_loc = QPushButton("Choose paths file")
        self.paths_loc.setFixedWidth(160)
        def choose_paths_file():
            if not self.root_path:
                QMessageBox.warning(self,"Error", "Please choose worksapce directory!")
                return
            file,filetype = QFileDialog.getOpenFileName(self,"Choose a file", self.root_path)
            if file != "":
                self.paths_file = file
            self.paths.setText("Paths File: {}".format(self.paths_file))
        self.paths_loc.clicked.connect(choose_paths_file)

        # 2.2 hbox to contain them
        hbox2 = QHBoxLayout()
        hbox2.addWidget(self.paths)
        hbox2.addWidget(self.paths_loc)

        # 3.1 target file location
        self.target = QLabel("Target File: {}".format(self.target_file))
        self.target_loc = QPushButton("Choose target file")
        self.target_loc.setFixedWidth(160)
        def choose_target_file():
            if not self.root_path:
                QMessageBox.warning(self,"Error", "Please choose worksapce directory!")
                return
            file,filetype = QFileDialog.getOpenFileName(self,"Choose a file", self.root_path)
            if file != "":
                self.target_file = file
            self.target.setText("Target File: {}".format(self.target_file))
        self.target_loc.clicked.connect(choose_target_file)

        # 3.2 hbox to contain them
        hbox3 = QHBoxLayout()
        hbox3.addWidget(self.target)
        hbox3.addWidget(self.target_loc)
        
        # 4 Progress Bar
        self.pb = QProgressBar(self)
        self.pb.setOrientation(Qt.Horizontal)
        self.pb.setAlignment(Qt.AlignCenter)

        # 5 Construct Fingerprint Database
        self.db_button = QPushButton("Construct Fingerprint Database")
        def construct_fp_db_end():
            QMessageBox.information(self,"Information","Construction complete!",QMessageBox.Yes)
            self.pb.setMaximum(100)
            self.db_button.setDisabled(False)
        db_thread = DBThread()
        db_thread.finished.connect(construct_fp_db_end)
        def constrct_fp_db():
            if not self.root_path:
                QMessageBox.warning(self,"Error", "Please choose worksapce directory!")
                return
            reply = QMessageBox.information(self,"Confirmation","Are you sure to do this?",QMessageBox.Yes | QMessageBox.No)
            if (reply==QMessageBox.Yes):
                try:
                    self.pb.setMinimum(0)
                    self.pb.setMaximum(0)
                    self.db_button.setDisabled(True)

                    db_thread.root_path = self.root_path
                    db_thread.paths_file = self.paths_file
                    db_thread.start()
                    
                except BaseException as e:
                    QMessageBox.warning(self,"Error", "Error occurred! {}".format(str(e)))   
        self.db_button.clicked.connect(constrct_fp_db)

        # 6 View APs' information
        self.ap_button = QPushButton("View APs' Information")
        def view_aps():
            if not self.root_path:
                QMessageBox.warning(self,"Error", "Please choose worksapce directory!")
                return
            try:
                self.hide()
                self.new_window = show_paths_ui(self.root_path, self.paths_file, self.target_file)
                self.new_window.show()
            except BaseException as e:
                QMessageBox.warning(self,"Error", "Error occurred! {}".format(str(e)))
                self.show()        
        self.ap_button.clicked.connect(view_aps)

        # 7 Detect Altered APs
        self.detect_button = QPushButton("Detect target files")
        def detect_ap_end():
            QMessageBox.information(self,"Information","Detection complete!",QMessageBox.Yes)
            self.pb.setMaximum(100)
            self.detect_button.setDisabled(False)
        detect_thread = DetectThread()
        detect_thread.finished.connect(detect_ap_end)
        def detect_ap():
            if not self.root_path:
                QMessageBox.warning(self,"Error", "Please choose worksapce directory!")
                return
            reply = QMessageBox.information(self,"Confirmation","Are you sure to do this?",QMessageBox.Yes | QMessageBox.No)
            if (reply==QMessageBox.Yes):
                try:
                    self.pb.setMinimum(0)
                    self.pb.setMaximum(0)
                    self.detect_button.setDisabled(True)

                    detect_thread.root_path = self.root_path
                    detect_thread.target_file = self.target_file
                    detect_thread.start()
                except BaseException as e:
                    QMessageBox.warning(self,"Error", "Error occurred! {}".format(str(e)))
        self.detect_button.clicked.connect(detect_ap)

        # 8 Show Alternaton Level
        self.target_button = QPushButton("Show Alternation Level")
        def view_target_aps():
            if not self.target_file:
                QMessageBox.warning(self,"Error", "Please choose target file!")
                return
            try:
                self.hide()
                self.new_window = show_target_ui(self.root_path, self.paths_file, self.target_file)
                self.new_window.show()
            except BaseException as e:
                QMessageBox.warning(self,"Error", "Error occurred! {}".format(str(e)))
        self.target_button.clicked.connect(view_target_aps)

        # 9 Exit
        self.ex_button = QPushButton("Quit")
        self.ex_button.clicked.connect(self.close)

        # 10 Adding all widgets and layouts to the window
        vbox = QVBoxLayout()
        vbox.addWidget(self.main_title)
        vbox.addLayout(hbox1)
        vbox.addLayout(hbox2)
        vbox.addLayout(hbox3)
        vbox.addWidget(self.pb)
        vbox.addWidget(self.db_button)
        vbox.addWidget(self.ap_button)
        vbox.addWidget(self.detect_button)
        vbox.addWidget(self.target_button)
        vbox.addWidget(self.ex_button)
        
        # Set the layout to the window
        self.setLayout(vbox)

class PlotAPThread(QThread):
    def __init__(self, mode, scale, filename="", root_path="", parent=None):
        super(PlotAPThread, self).__init__(parent)
        self.filename = filename
        self.root_path = root_path
        self.scale = scale
        self.mode = mode

    def run(self):
        plot_ap_heatmap(self.filename, self.root_path, self.mode, self.scale)

class PlotAPLocThread(QThread):
    def __init__(self, root_path="", n=settings.separate_parts, parent=None):
        super(PlotAPLocThread, self).__init__(parent)
        self.root_path = root_path
        self.n = n

    def run(self):
        plot_ap_loc(self.root_path, self.n)

class show_paths_ui(QWidget):
    def __init__(self, root_path, paths_file, target_file):
        super().__init__()
        self.title = 'Paths AP visualization'
        self.width = 600
        self.height = 500
        self.root_path = root_path
        self.paths_file = paths_file
        self.target_file = target_file
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setMinimumSize(self.width, self.height)
        self.setWindowIcon(QIcon('icon.png'))

        # 1 create textbox
        self.textbox = QTextBrowser(self)
        self.textbox.resize(280, 300)
        self.find_all_aps()

        # 2 Input label
        self.input_label = QLabel("Please copy the AP path from the left and choose one of the following options to visualize")
        self.input_label.width = 60
        self.input_label.setWordWrap(True)

        # 3 input box
        self.input = QLineEdit(self)

        # 4 Plot 2D Heatmap
        self.plot_2d_button = QPushButton("Plot 2D Heatmap")
        def plot_2d_end():
            self.plot_2d_button.setDisabled(False)
        plot_2d_thread = PlotAPThread(mode='2d', scale=False)
        plot_2d_thread.finished.connect(plot_2d_end)
        def plot_2d():
            filename = path.join(self.root_path,self.input.text())
            plot_2d_thread.filename = filename
            plot_2d_thread.root_path = self.root_path
            plot_2d_thread.start()
            self.plot_2d_button.setDisabled(True) 
        self.plot_2d_button.clicked.connect(plot_2d)

        # 5 Plot 3D Heatmap
        self.plot_3d_button = QPushButton("Plot 3D Heatmap")
        def plot_3d_end():
            self.plot_3d_button.setDisabled(False)
        plot_3d_thread = PlotAPThread(mode='3d', scale=False)
        plot_3d_thread.finished.connect(plot_3d_end)
        def plot_3d():
            filename = path.join(self.root_path,self.input.text())
            plot_3d_thread.filename = filename
            plot_3d_thread.root_path = self.root_path
            plot_3d_thread.start()
            self.plot_3d_button.setDisabled(True) 
        self.plot_3d_button.clicked.connect(plot_3d)

        # 6 Plot APs' locations
        self.plot_loc_button = QPushButton("Plot AP location map")
        def plot_loc_end():
            self.plot_loc_button.setDisabled(False)
        plot_loc_thread = PlotAPLocThread()
        plot_loc_thread.finished.connect(plot_loc_end)
        def plot_loc():
            plot_loc_thread.root_path = self.root_path
            plot_loc_thread.start()
            self.plot_loc_button.setDisabled(True) 
        self.plot_loc_button.clicked.connect(plot_loc)

        # 7 Back to main window
        self.back_button = QPushButton("Back")
        def back():
            self.hide()
            self.new_window = LAAFU_Main(self.root_path, self.paths_file, self.target_file)
            self.new_window.show()
        self.back_button.clicked.connect(back)

        # Adding all widgets and layouts to the window
        vbox = QVBoxLayout()
        vbox.addWidget(self.input_label)
        vbox.addWidget(self.input)
        vbox.addWidget(self.plot_2d_button)
        vbox.addWidget(self.plot_3d_button)
        vbox.addWidget(self.plot_loc_button)
        vbox.addWidget(self.back_button)
        hbox = QHBoxLayout()
        hbox.addWidget(self.textbox)
        hbox.addLayout(vbox)

        # Set the loyout to the window
        self.setLayout(hbox)

    def find_all_aps(self):
        ap_list = ""
        for idx in range(4):
            folder_name = "res{}".format(idx)
            for ap_file in listdir(path.join(self.root_path,folder_name)):
                ap_list += path.join(folder_name,ap_file) + "\n"
        self.textbox.setText(ap_list)

class PlotAltThread(QThread): 
    def __init__(self, ap_file="", root_path="", parent=None):
        super(PlotAltThread, self).__init__(parent)
        self.ap_file = ap_file
        self.root_path = root_path

    def run(self):
        plot_alt_ap(self.ap_file, self.root_path)

class show_target_ui(QWidget):
    def __init__(self, root_path, paths_file, target_file):
        super().__init__()
        self.title = 'Target AP Alternation'
        self.width = 600
        self.height = 500
        self.root_path = root_path
        self.paths_file = paths_file
        self.target_file = target_file
        self.target = path.join(self.root_path, "output_{}".format(path.basename(path.splitext(self.target_file)[0])))
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setMinimumSize(self.width, self.height)
        self.setWindowIcon(QIcon('icon.png'))

        # 1 create textbox
        self.textbox = QTextBrowser(self)
        self.textbox.resize(280, 300)
        self.find_all_aps()

        # 2 Label
        self.input_label = QLabel("Please copy one AP Path from left to check its heatmap")
        self.input_label.width = 60
        self.input_label.setWordWrap(True)

        # 3 input box
        self.input = QLineEdit(self)

        # 4 input button
        self.input_button = QPushButton("Select")
        def plot_alt_end():
            self.input_button.setDisabled(False)
        plot_alt_thread = PlotAltThread()
        plot_alt_thread.finished.connect(plot_alt_end)
        def plot_alt(): #TODO:
            self.input_button.setDisabled(True)
            filename = path.join(self.target,self.input.text())

            plot_alt_thread.ap_file = filename
            plot_alt_thread.root_path = self.root_path
            plot_alt_thread.start()
        self.input_button.clicked.connect(plot_alt)

        # 5 back to main
        self.back_button = QPushButton("Back")
        def back():
            self.hide()
            self.new_window = LAAFU_Main(self.root_path, self.paths_file, self.target_file)
            self.new_window.show()
        self.back_button.clicked.connect(back)

        # adding all widgets and layouts to the window
        vbox = QVBoxLayout()
        vbox.addWidget(self.input_label)
        vbox.addWidget(self.input)
        vbox.addWidget(self.input_button)
        vbox.addWidget(self.back_button)
        hbox = QHBoxLayout()
        hbox.addWidget(self.textbox)
        hbox.addLayout(vbox)

        # apply the layout
        self.setLayout(hbox)

    def find_all_aps(self):
        ap_list = ""
        for ap_file in listdir(self.target):
            if path.getsize(path.join(self.target,ap_file)) != 0 and not ap_file.startswith("all_"):
                ap_list += ap_file + "\n"
        self.textbox.setText(ap_list)


if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        qb = LAAFU_Main()
        qb.show()
        sys.exit(app.exec_())
    except Exception as e:
        QMessageBox.warning(self,"Error", "Error occurred! \n{}".format(str(e)))