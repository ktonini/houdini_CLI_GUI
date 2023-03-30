#!/usr/bin/python3

import subprocess
from subprocess import PIPE
import os
import PySimpleGUI as sg

sg.theme('dark grey 9')
default_folder = '/mnt/Data/active_jobs/'
default_outnode = '/out/Redshift_ROP1'
versionNum = 'v0.01'

dir_path = os.path.dirname(os.path.realpath(__file__))
os.chdir(dir_path)

if os.path.exists('houdini_cli_temp.py'):
    os.remove('houdini_cli_temp.py')
else:
    pass

tempPY = open('houdini_cli_temp.py', 'w')
tempPY.write('''
from optparse import OptionParser

def do_the_thing(out, sframe, eframe, userange):
    rnode = hou.node(out)
    if (userange == "True"):
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


    (options, args) = parser.parse_args()

    hou.hipFile.load(options.hipfile)

    do_the_thing(options.outnode, int(options.startframe), int(options.endframe), options.userange)
''')
tempPY.close()

layout = [
    [
        sg.Text("Hip Path"),
        sg.Combo(sg.user_settings_get_entry('-hipnames-', []),
                 default_value=sg.user_settings_get_entry('-last hipname-', ''), size=(100, 1), key='hippath'),
        sg.FileBrowse(initial_folder=os.path.dirname(
            sg.user_settings_get_entry('-last hipname-', default_folder))),
    ],
    [
        sg.Text("Out Path"),
        sg.Combo(sg.user_settings_get_entry('-outnames-', []),
                 default_value=sg.user_settings_get_entry('-last outname-', ''), size=(100, 1), key='outnode'),
    ],
    [
        sg.Text('_' * 120)
    ],
    [
        sg.Checkbox('Use Frame Range', default=sg.user_settings_get_entry(
            '-last userange-', False), key='userange')
    ],
    [
        sg.Text("Frame Range from"),
        sg.In(sg.user_settings_get_entry('-last start-', 0),
              size=(10, 1), enable_events=True, key='sframe'),
        sg.Text("to"),
        sg.In(sg.user_settings_get_entry('-last end-', 100),
              size=(10, 1), enable_events=True, key='eframe')
    ],
    [
        sg.Button("Render"),
        sg.Cancel(),
        sg.Button("Clear History")
    ]
]

window = sg.Window(f"Houdini CLI Render {versionNum}", icon="houdini_logo.png", enable_close_attempted_event=True,
                   location=sg.user_settings_get_entry('-location-', (None, None))).Layout(layout)

while True:
    event, values = window.read()

    if event == "Clear History":
        sg.user_settings_set_entry('-hipnames-', [])
        sg.user_settings_set_entry('-outnames-', [])
        sg.user_settings_set_entry('-last hipname-', default_folder)
        sg.user_settings_set_entry('-last outname-', default_outnode)
        sg.user_settings_set_entry('-last userange-', False)
        sg.user_settings_set_entry('-last start-', 0)
        sg.user_settings_set_entry('-last end-', 100)
        window['hippath'].update(values=[], value=default_folder)
        window['outnode'].update(values=[], value=default_outnode)

    if event == "Render":
        out = values['outnode']
        hip = values['hippath']
        sframe = values['sframe']
        eframe = values['eframe']
        userange = str(values['userange'])

        # cp = subprocess.run(['konsole', '-e', 'hython', 'houdini_cli_temp.py',
        # cp = subprocess.run(['gnome-terminal', '--', 'hython', 'houdini_cli_temp.py',
        cp = subprocess.run(['cool-retro-term', '-e', 'hython', 'houdini_cli_temp.py',
                             '-i', hip, '-o', out, '-s', sframe, '-e', eframe, '-u',
                             userange, '| tee /mnt/Data/active_jobs/output.txt'],
                            universal_newlines=True, stdout=PIPE, stderr=PIPE)
        print(cp.args)
        print(cp.returncode)
        print(cp.stdout)
        print(cp.stderr)

        sg.user_settings_set_entry(
            '-hipnames-', list(set(sg.user_settings_get_entry('-hipnames-', []) + [hip, ])))
        sg.user_settings_set_entry(
            '-outnames-', list(set(sg.user_settings_get_entry('-outnames-', []) + [out, ])))
        sg.user_settings_set_entry('-last hipname-', hip)
        sg.user_settings_set_entry('-last outname-', out)
        sg.user_settings_set_entry('-last userange-', userange)
        sg.user_settings_set_entry('-last start-', sframe)
        sg.user_settings_set_entry('-last end-', eframe)

    elif event == "Cancel" or event == sg.WINDOW_CLOSE_ATTEMPTED_EVENT:
        sg.user_settings_set_entry('-location-', window.current_location())
        break
