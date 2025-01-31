#!/usr/bin/python3

import datetime
import os
import re
import signal
import subprocess
import sys
import threading
import time
import base64
import io
import json

# TEMP
import traceback

import PIL.Image
import OpenEXR
import OpenImageIO as oiio
import numpy as np

from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *

try:
    import hou  # Only needed if running inside Houdini
    RUNNING_IN_HOUDINI = True
except ImportError:
    RUNNING_IN_HOUDINI = False

DEFAULT_FOLDER = '/mnt/Data/active_jobs/'
DEFAULT_OUTNODE = '/out/Redshift_ROP1'
DEFAULT_LOG = DEFAULT_FOLDER + 'output.txt'
VERSION_NUM = 'v1.0'
disabledTextColor = "#ff4c00"
icon_browse = b'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'
checkerboard = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00@\x00\x00\x00@\x08\x02\x00\x00\x00\x15\x0bg\x00\x00\x00\x04sBIT\x08\x08\x08\xdb\xe5O\xe7\x00\x00\x00\xaeIDATx\x9c\xed\x9d;\x0e\xc20\x10\xbd\xf7\xbf\xd9\xff\x1e\xc5\xa2j\xf9"\x17\x15\x8d\x81L\r\xd9\x9a\x1aP\x00\x00\x00\x00IEND\xaeB`\x82'
renderedImage = None

dir_path = os.path.dirname(os.path.realpath(__file__))
os.chdir(dir_path)

if os.path.exists('houdini_cli_temp.py'):
    os.remove('houdini_cli_temp.py')
else:
    pass

def create_temp_python_file():
    """Create the temporary Python file for Houdini"""
    dir_path = os.path.dirname(os.path.realpath(__file__))
    temp_file = os.path.join(dir_path, 'houdini_cli_temp.py')
    
    if os.path.exists(temp_file):
        os.remove(temp_file)
        
    with open(temp_file, 'w') as f:
        f.write('''#!/usr/bin/env python3

import os
import stat
from optparse import OptionParser

def initRender(out, sframe, eframe, userange, useskip):
    import hou
    rnode = hou.node(out)

    def dataHelper(rop_node, render_event_type, frame):
        if render_event_type == hou.ropRenderEventType.PostFrame:
            output_file = rnode.evalParm("RS_outputFileNamePrefix")
            print(f"hgui_outputfile: {output_file}")

    rnode.addRenderEventCallback(dataHelper)

    parm_skip = rnode.parm("RS_outputSkipRendered")
    if parm_skip is not None:
        if useskip:
            parm_skip.set(1)
        else:
            parm_skip.set(0)

    if "merge" in str(rnode.type()).lower():
        rnode.render()
        if userange == "True":
            print("hgui_note: Out Path leads to a merge node, but you have selected to override the frame range. "
                  "Defaulting to the frame range that was set from within Houdini for each ROP.")
    else:
        if userange == "True":
            rnode.render(frame_range=(sframe, eframe))
        else:
            rnode.render(frame_range=(rnode.parm("f1").eval(), rnode.parm("f2").eval()))

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-i", "--hip", dest="hipfile", help="path to .hip file")
    parser.add_option("-o", "--out", dest="outnode", help="path to out node")
    parser.add_option("-s", "--sframe", dest="startframe", help="start frame to render")
    parser.add_option("-e", "--eframe", dest="endframe", help="end frame to render")
    parser.add_option("-u", "--userange", dest="userange", help="toggle to enable frame range")
    parser.add_option("-r", "--useskip", dest="useskip", help="toggle to skip rendering of already rendered frames")

    (options, args) = parser.parse_args()

    # Convert hip file path to absolute and verify it exists
    hip_file = os.path.abspath(options.hipfile.strip())  # Strip whitespace and newlines
    hip_dir = os.path.dirname(hip_file)
    
    print(f"Current working directory: {os.getcwd()}")
    print(f"Hip file path: {hip_file}")
    print(f"Hip directory: {hip_dir}")
    
    # Detailed file checks
    exists = os.path.exists(hip_file)
    print(f"File exists: {exists}")
    
    if exists:
        st = os.stat(hip_file)
        print(f"File mode: {stat.filemode(st.st_mode)}")
        print(f"File owner: {st.st_uid}")
        print(f"File group: {st.st_gid}")
        print(f"File size: {st.st_size}")
    else:
        print("Checking parent directory...")
        parent_dir = os.path.dirname(hip_file)
        if os.path.exists(parent_dir):
            print(f"Parent directory exists")
            try:
                files = os.listdir(parent_dir)
                print(f"Directory contents: {files}")
            except Exception as e:
                print(f"Error listing directory: {e}")
        else:
            print(f"Parent directory does not exist")
    
    print(f"File is readable: {os.access(hip_file, os.R_OK)}")
    print(f"Current user ID: {os.getuid()}")
    print(f"Current group ID: {os.getgid()}")
    
    try:
        with open(hip_file, 'rb') as f:
            print("Successfully opened file for reading")
            print(f"First few bytes: {f.read(10)}")
    except Exception as e:
        print(f"Error opening file: {e}")
    
    # Change to the hip file directory before loading
    os.chdir(hip_dir)
    
    import hou
    hou.hipFile.load(hip_file)
    
    initRender(options.outnode.strip(),  # Strip other arguments too
              int(options.startframe), 
              int(options.endframe), 
              options.userange, 
              options.useskip)
''')

def format_time(seconds):

    timedelta = datetime.timedelta(seconds=seconds)
    days = timedelta.days
    hours, remainder = divmod(timedelta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if seconds or not any((days, hours, minutes)):
        parts.append(f"{seconds}s")
    return "".join(parts)


class Settings:
    """Wrapper for QSettings to handle lists and other data types"""
    def __init__(self):
        self.settings = QSettings('HoudiniCLI', 'RenderUtility')
        
    def get(self, key, default=None):
        """Get a value from settings"""
        value = self.settings.value(key, default)
        
        # Convert string booleans back to bool
        if isinstance(value, str):
            if value.lower() == 'true':
                return True
            elif value.lower() == 'false':
                return False
                
        return value if value is not None else default
        
    def set(self, key, value):
        """Save a value to settings"""
        self.settings.setValue(key, value)
        
    def get_list(self, key, default=None):
        """Get a list from settings"""
        value = self.settings.value(key, default or [])
        if isinstance(value, str):
            # Handle single string value
            return [value] if value else []
        return value if isinstance(value, list) else []

class HoudiniRenderGUI(QMainWindow):
    # Define signals for thread-safe UI updates
    output_signal = Signal(str)
    raw_output_signal = Signal(str)
    progress_signal = Signal(int, int)
    image_update_signal = Signal(str)
    render_finished_signal = Signal()
    time_labels_signal = Signal(float, float, float, float, QDateTime, bool)
    
    def __init__(self):
        super().__init__()
        
        # First create all widgets
        self.setWindowTitle("Houdini Render GUI")
        self.setStyleSheet("""
            QMainWindow {
                background-color: #3a3a3a;
                color: #d6d6d6;
            }
            QLabel {
                color: #d6d6d6;
            }
            QLineEdit {
                background-color: #131313;
                color: #ffffff;
                border: 1px solid #555555;
                padding: 2px;
            }
            QComboBox {
                background-color: #131313;
                color: #ffffff;
                border: 1px solid #555555;
                padding: 2px;
            }
            QCheckBox {
                color: #d6d6d6;
            }
            QPushButton {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #555555;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #555555;
                color: #ffffff;
            }
            QProgressBar {
                background-color: #222222;
                border: 1px solid #555555;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #D0D0D0;
            }
            QTextEdit {
                background-color: #131313;
                color: #ffffff;
                border: 1px solid #555555;
                padding: 2px;
            }
        """)

        self.settings = Settings()

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)

        self.form_layout = QFormLayout()
        self.layout.addLayout(self.form_layout)

        self.hip_input = QComboBox()
        self.hip_input.setEditable(True)
        self.hip_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.hip_input.setMinimumWidth(300)
        self.hip_input.setMaxVisibleItems(10)
        self.hip_input.setInsertPolicy(QComboBox.InsertAtTop)
        self.hip_input.setDuplicatesEnabled(False)
        self.hip_input.setPlaceholderText("Enter HIP file path")
        self.form_layout.addRow("Hip Path:", self.hip_input)

        self.out_input = QComboBox()
        self.out_input.setEditable(True)
        self.out_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.out_input.setMinimumWidth(300)
        self.out_input.setMaxVisibleItems(10)
        self.out_input.setInsertPolicy(QComboBox.InsertAtTop)
        self.out_input.setDuplicatesEnabled(False)
        self.out_input.setPlaceholderText("Enter out node path")
        self.form_layout.addRow("Out Path:", self.out_input)

        self.log_check = QCheckBox("Log Path:")
        self.log_check.setChecked(False)
        self.log_check.stateChanged.connect(self.toggle_log_inputs)
        self.form_layout.addRow(self.log_check)

        self.log_input = QComboBox()
        self.log_input.setEditable(True)
        self.log_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.log_input.setMinimumWidth(300)
        self.log_input.setMaxVisibleItems(10)
        self.log_input.setInsertPolicy(QComboBox.InsertAtTop)
        self.log_input.setDuplicatesEnabled(False)
        self.log_input.setPlaceholderText("Enter log file path")
        self.log_input.setEnabled(False)
        self.form_layout.addRow("", self.log_input)

        self.overrides_frame = QFrame()
        self.overrides_frame.setFrameShape(QFrame.StyledPanel)
        self.overrides_frame.setLineWidth(1)
        self.overrides_layout = QFormLayout(self.overrides_frame)
        self.layout.addWidget(self.overrides_frame)

        self.range_check = QCheckBox("Frame Range:")
        self.range_check.setChecked(False)
        self.range_check.stateChanged.connect(self.toggle_frame_range)
        self.overrides_layout.addRow(self.range_check)

        self.start_frame = QComboBox()
        self.start_frame.setEditable(True)
        self.start_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.start_frame.setMinimumWidth(100)
        self.start_frame.setMaxVisibleItems(10)
        self.start_frame.setInsertPolicy(QComboBox.InsertAtTop)
        self.start_frame.setDuplicatesEnabled(False)
        self.start_frame.setPlaceholderText("Start frame")
        self.start_frame.setEnabled(False)
        self.overrides_layout.addRow("", self.start_frame)

        self.end_frame = QComboBox()
        self.end_frame.setEditable(True)
        self.end_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.end_frame.setMinimumWidth(100)
        self.end_frame.setMaxVisibleItems(10)
        self.end_frame.setInsertPolicy(QComboBox.InsertAtTop)
        self.end_frame.setDuplicatesEnabled(False)
        self.end_frame.setPlaceholderText("End frame")
        self.end_frame.setEnabled(False)
        self.overrides_layout.addRow("", self.end_frame)

        self.skip_check = QCheckBox("Skip Rendered Frames:")
        self.skip_check.setChecked(False)
        self.overrides_layout.addRow(self.skip_check)

        self.buttons_layout = QHBoxLayout()
        self.layout.addLayout(self.buttons_layout)

        self.force_save_btn = QPushButton("Force Save")
        self.buttons_layout.addWidget(self.force_save_btn)
        self.force_save_btn.clicked.connect(self.force_save)

        self.reset_btn = QPushButton("Reset")
        self.buttons_layout.addWidget(self.reset_btn)
        self.reset_btn.clicked.connect(self.reset_settings)

        self.clear_history_btn = QPushButton("Clear History")
        self.buttons_layout.addWidget(self.clear_history_btn)
        self.clear_history_btn.clicked.connect(self.clear_history)

        self.switch_btn = QPushButton("View Output")
        self.buttons_layout.addWidget(self.switch_btn)
        self.switch_btn.clicked.connect(self.switch_output)

        self.open_folder_btn = QPushButton("Open Output Location")
        self.buttons_layout.addWidget(self.open_folder_btn)
        self.open_folder_btn.clicked.connect(self.open_folder)
        self.open_folder_btn.setEnabled(False)

        self.cancel_btn = QPushButton("Cancel")
        self.buttons_layout.addWidget(self.cancel_btn)
        self.cancel_btn.clicked.connect(self.cancel_render)
        self.cancel_btn.setStyleSheet("background-color: #ff4c00; color: #000000;")
        self.cancel_btn.hide()

        self.render_btn = QPushButton("Render")
        self.buttons_layout.addWidget(self.render_btn)
        self.render_btn.clicked.connect(self.start_render)
        self.render_btn.setStyleSheet("background-color: #ff4c00; color: #000000;")

        # Create text widgets with splitter
        self.text_splitter = QSplitter(Qt.Horizontal)  # Vertical split
        self.text_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #212121;  # Match the background color
                width: 2px;
                margin: 2px;
            }
            QSplitter::handle:hover {
                background-color: #ff4c00;  # Keep the orange highlight
            }
            QSplitter::handle:pressed {
                background-color: #ff6b2b;  # Keep the pressed state
            }
        """)
        
        # Set handle width explicitly
        self.text_splitter.setHandleWidth(8)  # Make handle wider for easier grabbing
        
        # Create text widgets
        self.summary_text = QTextEdit()
        self.summary_text.setStyleSheet("""
            QTextEdit {
                background-color: #212121;
                color: #cccccc;
                border: none;
                padding: 10px;
            }
            QScrollBar:vertical {
                width: 8px;
                background: #323232;
            }
            QScrollBar::handle:vertical {
                background: #3b3b3b;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical {
                height: 8px;
                background: #323232;
                subcontrol-position: bottom;
            }
            QScrollBar::sub-line:vertical {
                height: 8px;
                background: #323232;
                subcontrol-position: top;
            }
            QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {
                width: 8px;
                height: 8px;
                background: #555555;
            }
        """)
        self.summary_text.setReadOnly(True)
        self.summary_text.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.summary_text.setAlignment(Qt.AlignLeft)
        self.summary_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        self.raw_text = QTextEdit()
        self.raw_text.setStyleSheet("""
            QTextEdit {
                background-color: #212121;
                color: #cccccc;
                border: none;
                padding: 10px;
            }
            QScrollBar:vertical {
                width: 8px;
                background: #323232;
            }
            QScrollBar::handle:vertical {
                background: #3b3b3b;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical {
                height: 8px;
                background: #323232;
                subcontrol-position: bottom;
            }
            QScrollBar::sub-line:vertical {
                height: 8px;
                background: #323232;
                subcontrol-position: top;
            }
            QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {
                width: 8px;
                height: 8px;
                background: #555555;
            }
        """)
        self.raw_text.setReadOnly(True)
        self.raw_text.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.raw_text.setAlignment(Qt.AlignLeft)
        self.raw_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.raw_text.hide()  # Hide raw text by default
        
        # Add text widgets to splitter
        self.text_splitter.addWidget(self.summary_text)
        self.text_splitter.addWidget(self.raw_text)
        
        # Set initial sizes for the splitter (50-50 split)
        self.text_splitter.setSizes([500, 500])
        
        # Add splitter to main layout and make it expand
        self.layout.addWidget(self.text_splitter, 1)  # Add stretch factor

        self.progress_frame = QProgressBar()
        self.progress_frame.setOrientation(Qt.Horizontal)
        self.progress_frame.setRange(0, 100)
        self.progress_frame.setValue(0)
        self.progress_frame.setStyleSheet("background-color: #222222; border: 1px solid #555555; text-align: center;")
        self.layout.addWidget(self.progress_frame)

        self.stats_layout = QHBoxLayout()
        self.layout.addLayout(self.stats_layout)

        self.fc_label = QLabel("Frames:")
        self.stats_layout.addWidget(self.fc_label)

        self.fc_value = QLabel("-")
        self.fc_value.setStyleSheet("color: #ff4c00;")
        self.stats_layout.addWidget(self.fc_value)

        self.tfc_label = QLabel("/")
        self.stats_layout.addWidget(self.tfc_label)

        self.tfc_value = QLabel("-")
        self.tfc_value.setStyleSheet("color: #ff4c00;")
        self.stats_layout.addWidget(self.tfc_value)

        self.average_label = QLabel("Average:")
        self.stats_layout.addWidget(self.average_label)

        self.average_value = QLabel("-")
        self.average_value.setStyleSheet("color: #ff4c00;")
        self.stats_layout.addWidget(self.average_value)

        self.elapsed_label = QLabel("Elapsed:")
        self.stats_layout.addWidget(self.elapsed_label)

        self.elapsed_value = QLabel("-")
        self.elapsed_value.setStyleSheet("color: #ff4c00;")
        self.stats_layout.addWidget(self.elapsed_value)

        self.total_label = QLabel("Est. Total:")
        self.stats_layout.addWidget(self.total_label)

        self.total_value = QLabel("-")
        self.total_value.setStyleSheet("color: #ff4c00;")
        self.stats_layout.addWidget(self.total_value)

        # Add the missing labels
        self.eta_label = QLabel("ETA: --:--:-- --")
        self.eta_label.setStyleSheet("color: #ff4c00;")
        self.stats_layout.addWidget(self.eta_label)

        self.remaining_label = QLabel("Remaining: --")
        self.remaining_label.setStyleSheet("color: #ff4c00;")
        self.stats_layout.addWidget(self.remaining_label)

        self.image_frame = QFrame()
        self.image_frame.setFrameShape(QFrame.StyledPanel)
        self.image_frame.setLineWidth(1)
        self.image_layout = QHBoxLayout(self.image_frame)  # Change to horizontal layout
        self.image_layout.setSpacing(1)  # Small gap between images
        self.image_layout.setContentsMargins(1, 1, 1, 1)  # Small margins
        self.layout.addWidget(self.image_frame)
        self.image_frame.hide()

        self.image_widgets = []
        for i in range(20):
            # Create a container widget for each image+label pair
            container = QWidget()
            container_layout = QVBoxLayout(container)
            container_layout.setSpacing(0)
            container_layout.setContentsMargins(0, 0, 0, 0)
            
            # Create image label
            image_label = QLabel()
            image_label.setAlignment(Qt.AlignCenter)
            image_label.setStyleSheet("background-color: #212121;")
            image_label.setMinimumSize(100, 100)  # Smaller minimum size
            image_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)  # Allow shrinking
            
            # Create name label
            name_label = QLabel()
            name_label.setAlignment(Qt.AlignCenter)
            name_label.setStyleSheet("""
                QLabel {
                    background-color: #212121;
                    color: #ffffff;
                    padding: 2px;
                    border-top: 1px solid #555555;
                    min-height: 14px;
                    max-height: 14px;
                    font-size: 10px;
                }
            """)
            
            # Add both labels to container
            container_layout.addWidget(image_label)
            container_layout.addWidget(name_label)
            
            # Add container to horizontal layout
            self.image_layout.addWidget(container)
            container.hide()  # Hide initially
            self.image_widgets.append((image_label, name_label))

        # After creating all widgets, connect the signals
        self.output_signal.connect(self.append_output_safe)
        self.raw_output_signal.connect(self.raw_text.append)
        self.progress_signal.connect(self.update_progress_safe)
        self.image_update_signal.connect(self.update_image_preview_safe)
        self.render_finished_signal.connect(self.render_finished)
        self.time_labels_signal.connect(self.update_time_labels_safe)
        
        # Load settings last
        self.load_settings()

        # Set initial minimum window size
        self.setMinimumWidth(800)  # Or whatever minimum width you prefer

        # Store original image data and dimensions
        self.original_images = [None] * 20  # Will store tuples of (bytes, width, height)

    def toggle_log_inputs(self, state=None):
        """Enable/disable log inputs"""
        if state is None:
            state = self.log_check.isChecked()
        self.log_input.setEnabled(state)

    def toggle_frame_range(self, state=None):
        """Enable/disable frame range inputs"""
        if state is None:
            state = self.range_check.isChecked()
        self.start_frame.setEnabled(state)
        self.end_frame.setEnabled(state)

    def load_settings(self):
        """Load saved settings into UI elements"""
        self.hip_input.addItems(self.settings.get_list('hipnames', []))
        self.hip_input.setEditText(self.settings.get('last_hipname', DEFAULT_FOLDER))
        
        self.out_input.addItems(self.settings.get_list('outnames', []))
        self.out_input.setEditText(self.settings.get('last_outname', DEFAULT_OUTNODE))
        
        self.log_check.setChecked(self.settings.get('last_log', False))
        self.log_input.addItems(self.settings.get_list('lognames', []))
        self.log_input.setEditText(self.settings.get('last_logname', DEFAULT_LOG))
        self.toggle_log_inputs()
        
        self.range_check.setChecked(self.settings.get('last_userange', False))
        self.start_frame.addItems(map(str, self.settings.get_list('sframe', [])))
        self.start_frame.setEditText(str(self.settings.get('last_start', 0)))
        self.end_frame.addItems(map(str, self.settings.get_list('eframe', [])))
        self.end_frame.setEditText(str(self.settings.get('last_end', 100)))
        self.toggle_frame_range()
        
        self.skip_check.setChecked(self.settings.get('last_useskip', False))

    def save_settings(self):
        """Save current UI state to settings"""
        self.settings.set('hipnames', self._get_unique_items(self.hip_input))
        self.settings.set('last_hipname', self.hip_input.currentText())
        
        self.settings.set('outnames', self._get_unique_items(self.out_input))
        self.settings.set('last_outname', self.out_input.currentText())
        
        self.settings.set('last_log', self.log_check.isChecked())
        self.settings.set('lognames', self._get_unique_items(self.log_input))
        self.settings.set('last_logname', self.log_input.currentText())
        
        self.settings.set('last_userange', self.range_check.isChecked())
        self.settings.set('sframe', self._get_unique_items(self.start_frame))
        self.settings.set('last_start', self.start_frame.currentText())
        self.settings.set('eframe', self._get_unique_items(self.end_frame))
        self.settings.set('last_end', self.end_frame.currentText())
        
        self.settings.set('last_useskip', self.skip_check.isChecked())

    def _get_unique_items(self, combo):
        """Helper to get unique items from QComboBox"""
        return list(set(combo.itemText(i) for i in range(combo.count())))

    def force_save(self):
        """Force save current settings"""
        self.save_settings()
        self.append_output_safe('\n\n Form Values Saved To History \n\n', 
                          color='#7abfff', 
                          bold=True, 
                          center=True)

    def reset_settings(self):
        """Reset settings to defaults"""
        self.hip_input.setEditText(DEFAULT_FOLDER)
        self.out_input.setEditText(DEFAULT_OUTNODE)
        self.log_check.setChecked(False)
        self.log_input.setEditText(DEFAULT_LOG)
        self.range_check.setChecked(False)
        self.start_frame.setEditText('0')
        self.end_frame.setEditText('100')
        self.skip_check.setChecked(False)
        self.save_settings()
        self.append_output_safe(' Form Reset To Default ', 
                          color='#fffd7a', 
                          bold=True, 
                          center=True)

    def clear_history(self):
        """Clear combo box histories"""
        for combo in [self.hip_input, self.out_input, self.log_input, 
                     self.start_frame, self.end_frame]:
            combo.clear()
        self.save_settings()
        self.append_output_safe(' Form History Cleared ', 
                          color='#fffd7a', 
                          bold=True, 
                          center=True)

    def append_output_safe(self, text, color=None, bold=False, center=False):
        """Append text to output safely (called in main thread)"""
        cursor = self.summary_text.textCursor()
        format = QTextCharFormat()
        if color:
            format.setForeground(QColor(color))
        if bold:
            format.setFontWeight(QFont.Bold)
        if center:
            cursor.insertBlock()
            blockFormat = QTextBlockFormat()
            blockFormat.setAlignment(Qt.AlignCenter)
            cursor.setBlockFormat(blockFormat)
        cursor.insertText(text, format)
        cursor.setBlockFormat(QTextBlockFormat())  # Reset block format to default (left-aligned)
        self.summary_text.setTextCursor(cursor)

    def start_render(self):
        """Start the render process"""
        self.render_btn.hide()
        self.cancel_btn.show()
        self.canceling = False
        
        # Clear previous image previews
        for label, name_label in self.image_widgets:
            label.clear()
            name_label.clear()
            label.parent().hide()
            
        # Create the temp Python file
        create_temp_python_file()
        
        # Build command list without quotes
        cmd_parts = [
            'hython',
            os.path.join(dir_path, 'houdini_cli_temp.py'),
            '-i', self.hip_input.currentText(),
            '-o', self.out_input.currentText(),
            '-s', self.start_frame.currentText(),
            '-e', self.end_frame.currentText(),
            '-u', str(self.range_check.isChecked()),
            '-r', str(self.skip_check.isChecked())
        ]
        
        # Handle log file
        if self.log_check.isChecked():
            log_file = self.log_input.currentText()
            # Create a shell script to handle the pipe
            script_path = os.path.join(dir_path, 'temp_render.sh')
            with open(script_path, 'w') as f:
                f.write('#!/bin/bash\n')
                f.write(' '.join(cmd_parts) + f' | tee "{log_file}"\n')
            os.chmod(script_path, 0o755)
            
            # Use the shell script
            cmd = ['/bin/bash', script_path]
        else:
            cmd = cmd_parts
            
        # Start process
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            start_new_session=True
        )

        # Start monitoring thread
        self.render_thread = threading.Thread(
            target=self.monitor_render,
            daemon=True
        )
        self.render_thread.start()
        
        # Log command
        self.append_output_safe(
            '\n\n RENDER STARTED AT ' + 
            time.strftime('%l:%M%p %Z on %b %d, %Y ') + 
            '\n\n',
            color='#22adf2',
            bold=True,
            center=True
        )
        self.append_output_safe(' '.join(cmd) + '\n', color='#c0c0c0')
        self.append_output_safe('Loading scene...\n', color='#c0c0c0')
        
        # Save settings
        self.save_settings()

    def __del__(self):
        """Cleanup temporary files"""
        script_path = os.path.join(dir_path, 'temp_render.sh')
        if os.path.exists(script_path):
            try:
                os.remove(script_path)
            except:
                pass

    def cancel_render(self):
        """Cancel the render process"""
        if not self.canceling:
            self.canceling = True
            self.cancel_btn.setText('Kill')
            os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            self.append_output_safe(
                '\n Canceling after current frame... \n\n',
                color='#ff7a7a',
                bold=True,
                center=True
            )
        else:
            self.append_output_safe(
                '\n Killing the render... \n\n',
                color='#ff7a7a',
                bold=True,
                center=True
            )
            os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
            self.process.wait()
            self.append_output_safe(
                '\n Render Killed \n\n',
                color='#ff7a7a',
                bold=True,
                center=True
            )
            self.render_btn.show()
            self.cancel_btn.hide()
            self.cancel_btn.setText('Cancel')

    def monitor_render(self):
        """Monitor the render process and update UI"""
        try:
            frame_times = []
            frame_total = 0
            frame_count = 0
            average = 0
            recent_average = 0
            start_time = None
            current_frame_start = None
            
            for line in iter(self.process.stdout.readline, b''):
                line = line.decode(errors='backslashreplace').rstrip()
                line = line.replace('[Redshift] ', '').replace('[Redshift]', '')
                
                # Update raw output
                self.raw_output_signal.emit(line)
                
                if 'render started for' in line:
                    frame_count = 0
                    clean_line = line.split(' Time from')[0]
                    self.output_signal.emit('\n' + clean_line + '\n')
                    
                    # Update total frames
                    frame_total = int(re.findall(r'\d+', clean_line)[-1])
                    self.fc_value.setText("0")  # Reset frame counter
                    self.tfc_value.setText(str(frame_total))  # Set total frames
                    self.progress_signal.emit(frame_count, frame_total)
                    
                elif 'Rendering frame' in line:
                    # Extract current frame number
                    frame_match = re.search(r'frame (\d+)', line)
                    if frame_match:
                        current_frame = frame_match.group(1)
                        self.fc_value.setText(current_frame)  # Update current frame
                    
                    self.output_signal.emit(
                        line.replace('Rendering f', 'F') + '\n'
                    )
                    current_frame_start = datetime.datetime.now()
                    
                    if average != 0:
                                estimate = current_frame_start + datetime.timedelta(seconds=recent_average)
                                self.output_signal.emit(
                                    f"   Started  {current_frame_start.strftime('%I:%M:%S %p')}\n"
                                    f"  Estimate  {estimate.strftime('%I:%M:%S %p')} - {self.format_time(recent_average)}\n"
                                )
                    
                elif 'Skip rendering enabled. File already rendered' in line:
                    # Handle skipped frames
                    frame_count += 1
                    self.fc_value.setText(str(frame_count))  # Update frame counter
                    self.progress_signal.emit(frame_count, frame_total)
                    self.output_signal.emit("   Skipped - File already exists\n")
                    
                elif 'scene extraction time' in line:
                    if current_frame_start:
                        # Extract render time
                        match = re.search(r"total time (\d+\.\d+) sec", line)
                        if match:
                            render_time = float(match.group(1))
                            frame_times.append(render_time)
                            
                            # Update progress
                            frame_count += 1
                            self.fc_value.setText(str(frame_count))  # Update frame counter
                            self.progress_signal.emit(frame_count, frame_total)
                            
                            # Calculate averages
                            average = sum(frame_times) / len(frame_times)
                            if len(frame_times) >= 2:
                                recent_times = frame_times[-2:]
                                recent_average = (2 * recent_times[1]) - recent_times[0]
                            else:
                                recent_average = average
                                
                            # Update time estimates
                            end_time = datetime.datetime.now()
                            self.output_signal.emit(
                                f"     Ended  {end_time.strftime('%I:%M:%S %p')} - {self.format_time(render_time)}\n"
                            )
                            
                            # Calculate progress times
                            time_progress = sum(frame_times)
                            total_time = frame_total * average if average > 0 else 0
                            remaining_time = total_time - time_progress
                            
                            # Update time labels
                            self.time_labels_signal.emit(
                                average,
                                time_progress,
                                total_time,
                                remaining_time,
                                QDateTime(end_time),
                                frame_count == frame_total
                            )
                            
                elif 'hgui_outputfile' in line:
                    self.renderedImage = line.split(': ')[1]
                    print(f"Emitting image update signal for: {self.renderedImage}")  # Debug output
                    self.image_update_signal.emit(self.renderedImage)
            
            # Render finished
            self.process.wait()
            self.render_finished_signal.emit()
            
        except Exception as e:
            print(f"Error in monitor thread: {str(e)}\n{traceback.format_exc()}")

    def render_finished(self):
        """Handle render completion (called in main thread)"""
        self.output_signal.emit('\n Rendering Stopped \n\n')
        self.render_btn.show()
        self.cancel_btn.hide()
        self.cancel_btn.setText('Cancel')

    def update_progress_safe(self, current, total):
        """Update progress bars (called in main thread)"""
        self.progress_frame.setMaximum(total)
        self.progress_frame.setValue(current)

    def update_time_labels_safe(self, average, elapsed, total, remaining, current_time, is_finished):
        """Update time labels (called in main thread)"""
        self.average_value.setText(self.format_time(average))
        self.elapsed_value.setText(self.format_time(elapsed))
        self.total_value.setText(self.format_time(total))
        
        if is_finished:
            self.eta_label.setText(f'Finished: {current_time.toString("hh:mm:ss ap")}')
        else:  # Fix indentation here
            eta_time = current_time.addSecs(int(remaining))
            self.eta_label.setText(f'ETA: {eta_time.toString("hh:mm:ss ap")}')
        self.remaining_label.setText(f'Remaining: {self.format_time(remaining)}')

    def update_image_preview_safe(self, image_path):
        """Update image preview safely (called in main thread)"""
        try:
            print(f"Attempting to update preview with image: {image_path}")
            self.open_folder_btn.setEnabled(True)
            self.image_frame.show()  # Show the frame when we have images to display
            
            # Get frame number from path
            frame_num = re.search(r'\.(\d+)\.', image_path)
            
            if image_path.lower().endswith('.exr'):
                # Load image using OpenImageIO
                buf = oiio.ImageBuf(image_path)
                subCount = 0
                
                # Clear previous previews
                for label, name_label in self.image_widgets:
                    label.clear()
                    name_label.clear()
                    label.parent().hide()
                
                # Process each subimage/AOV
                while subCount < buf.nsubimages:
                    if subCount >= len(self.image_widgets):
                        break
                        
                    label, name_label = self.image_widgets[subCount]
                    label.parent().show()
                    
                    spec = buf.spec()
                    subimage = oiio.ImageBuf(image_path, subCount, 0)
                    
                    # Get channel names for this subimage
                    channelnames = subimage.spec().channelnames
                    layers = {}
                    for channelname in channelnames:
                        layername = ".".join(channelname.split(".")[:-1])
                        if layername not in layers:
                            layers[layername] = []
                        layers[layername].append(channelname)

                    # Create label text
                    for layername, channelnames in layers.items():
                        channels = [cn.split(".")[-1].lower() for cn in channelnames]
                        if len(channels) == 1:
                            channel_str = channels[0]
                        else:
                            channel_str = "".join(channels)
                        if layername == "":
                            layer_str = f"{channel_str}"
                        else:
                            layer_str = f"{layername}.{channel_str}"
                        
                        # Just set the layer string without frame number
                        name_label.setText(layer_str)
                    
                    # Convert to display format
                    display_buf = oiio.ImageBufAlgo.colorconvert(subimage, "linear", "srgb")
                    pixels = display_buf.get_pixels(oiio.FLOAT)
                    
                    # Handle different channel configurations
                    if len(pixels.shape) == 3:
                        if pixels.shape[2] == 1:  # Single channel
                            pixels = np.repeat(pixels, 3, axis=2)
                        elif pixels.shape[2] not in [3, 4]:  # Not RGB or RGBA
                            if pixels.shape[2] > 3:
                                pixels = pixels[:, :, :3]
                            else:
                                padding = np.zeros((*pixels.shape[:2], 3-pixels.shape[2]))
                                pixels = np.concatenate([pixels, padding], axis=2)
                    elif len(pixels.shape) == 2:  # Single channel
                        pixels = np.stack([pixels] * 3, axis=2)
                    
                    # Normalize the float data to 0-1 range
                    pixels = np.clip(pixels, 0, 1)

                    # Convert to 8-bit
                    pixels = (pixels * 255).astype(np.uint8)
                    
                    # Convert to QPixmap
                    img = PIL.Image.fromarray(pixels)
                    
                    # Store the original image data and dimensions
                    self.original_images[subCount] = (
                        img.tobytes("raw", "RGB"),
                        img.width,
                        img.height
                    )
                    
                    # Initial scaling will be handled by adjust_image_sizes
                    label.setPixmap(QPixmap.fromImage(QImage(
                        self.original_images[subCount][0],  # bytes
                        self.original_images[subCount][1],  # width
                        self.original_images[subCount][2],  # height
                        QImage.Format_RGB888
                    )))
                    label.setScaledContents(False)
                    label.setAlignment(Qt.AlignCenter)
                    
                    # Style the name label
                    name_label.setStyleSheet("""
                        QLabel {
                            background-color: #212121;
                            color: #ffffff;
                            padding: 2px;
                            border-top: 1px solid #555555;
                            min-height: 14px;
                            max-height: 14px;
                            font-size: 10px;
                        }
                    """)
                    
                    print(f"Successfully loaded AOV: {layer_str}")
                    subCount += 1
                    
            else:
                self._preview_single_image(image_path)
                
            # After showing/hiding containers, adjust sizes
            self.adjust_image_sizes()
            
        except Exception as e:
            print(f"Error updating image preview: {str(e)}\n{traceback.format_exc()}")

    def _preview_single_image(self, image_path):
        """Helper method to preview a single image"""
        for label, name_label in self.image_widgets:
            if label.pixmap() is None or label.pixmap().isNull():
                label.parent().show()
                
                frame_num = re.search(r'\.(\d+)\.', image_path)
                if frame_num:
                    name_label.setText(f"Frame {frame_num.group(1)}")
                
                # Style the name label
                name_label.setStyleSheet("""
                    QLabel {
                        background-color: #212121;
                        color: #ffffff;
                        padding: 2px;
                        border-top: 1px solid #555555;
                        min-height: 14px;
                        max-height: 14px;
                        font-size: 10px;
                    }
                """)
                
                pixmap = QPixmap(image_path)
                if not pixmap.isNull():
                    scaled = pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    label.setPixmap(scaled)
                break

    def format_time(self, seconds):
        """Format seconds into human readable time"""
        timedelta = datetime.timedelta(seconds=seconds)
        days = timedelta.days
        hours, remainder = divmod(timedelta.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        parts = []
        if days:
            parts.append(f"{days}d")
        if hours:
            parts.append(f"{hours}h")
        if minutes:
            parts.append(f"{minutes}m")
        if seconds or not any((days, hours, minutes)):
            parts.append(f"{seconds}s")
        return "".join(parts)

    def switch_output(self):
        """Switch between output views"""
        current_text = self.switch_btn.text()
        
        if current_text == "View Output":
            # Switch to raw output view
            self.summary_text.hide()
            self.raw_text.show()
            self.switch_btn.setText("View Output and Summary")
            
        elif current_text == "View Output and Summary":
            # Show both views
            self.summary_text.show()
            self.raw_text.show()
            self.switch_btn.setText("View Summary")
            
        else:  # "View Summary"
            # Show only summary
            self.summary_text.show()
            self.raw_text.hide()  # Hide raw text
            self.switch_btn.setText("View Output")

    def open_folder(self):
        """Open the output folder in file explorer"""
        if hasattr(self, 'renderedImage') and self.renderedImage:
            folder = os.path.dirname(self.renderedImage)
            if sys.platform == 'win32':
                os.startfile(folder)
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', folder])
            else:
                subprocess.Popen(['xdg-open', folder])

    def resizeEvent(self, event):
        """Handle window resize events"""
        super().resizeEvent(event)
        self.adjust_image_sizes()

    def adjust_image_sizes(self):
        """Adjust image sizes based on window width and number of visible images"""
        visible_count = sum(1 for label, _ in self.image_widgets if label.parent().isVisible())
        if visible_count == 0:
            return

        # Get available width (accounting for margins and spacing)
        available_width = self.image_frame.width() - (self.image_layout.spacing() * (visible_count - 1)) - 2
        
        # Calculate width for each container
        width = max(100, min(300, available_width // visible_count))
        
        # Track maximum height to adjust frame
        max_container_height = 0
        
        # Update size for all visible containers
        for i, (image_label, name_label) in enumerate(self.image_widgets):
            container = image_label.parent()
            if container.isVisible():
                # Set container width
                container.setFixedWidth(width)
                
                # Scale image from original if available
                if self.original_images[i] is not None:
                    image_data, img_width, img_height = self.original_images[i]
                    
                    # Calculate height maintaining aspect ratio
                    aspect_ratio = img_height / img_width
                    target_height = int(width * aspect_ratio)
                    
                    # Create QImage from original data
                    qimg = QImage(image_data, img_width, img_height, QImage.Format_RGB888)
                    pixmap = QPixmap.fromImage(qimg)
                    
                    # Scale the pixmap
                    scaled = pixmap.scaled(width, target_height, 
                                         Qt.KeepAspectRatio, 
                                         Qt.SmoothTransformation)
                    image_label.setPixmap(scaled)
                    
                    # Calculate total container height (image + label)
                    LABEL_HEIGHT = 14  # Fixed height for labels
                    container_height = target_height + LABEL_HEIGHT
                    container.setFixedHeight(container_height)
                    max_container_height = max(max_container_height, container_height)
                    
                    # Ensure image label has correct size
                    image_label.setFixedSize(width, target_height)
                
                # Update container layout
                container_layout = container.layout()
                container_layout.setSpacing(0)
                container_layout.setContentsMargins(0, 0, 0, 0)
        
        # Set frame height to match tallest container
        if max_container_height > 0:
            self.image_frame.setFixedHeight(max_container_height)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HoudiniRenderGUI()
    window.show()
    sys.exit(app.exec_())
