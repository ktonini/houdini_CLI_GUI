import subprocess
from subprocess import PIPE
import os
import PySimpleGUI as sg


if os.path.exists("temp.py"):
    os.remove("temp.py")
else:
    pass

tempPY = open('temp.py', 'w')
tempPY.write('''
from optparse import OptionParser

def do_the_thing(out, sframe, eframe, userange):
    rnode = hou.node(out)
    if bool(userange):
        rnode.render(frame_range=(sframe, eframe))
    else:
        rnode.render()

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
        sg.In("/path/to/hipFile", size=(45, 1), enable_events=True, key='hippath'),
        sg.FileBrowse(initial_folder='/home/vsamusenko/Documents/projects'),

    ],
    [
        sg.Text("Out Path"),
        sg.InputText("/path/to/outNode", enable_events=True, key='outnode')
    ],
    [
        sg.Text('_'*30)
    ],
    [
        sg.Checkbox('Use Frame Range', default=False, key='userange')
    ],
    [
        sg.Text("Frame Range from"),
        sg.In("0",size=(5,1), enable_events=True, key='sframe'),
        sg.Text("to"),
        sg.In("100",size=(5,1), enable_events=True, key='eframe')
    ],
    [
        sg.Button("Render"),
        sg.Cancel(),
        sg.Button("TEST")
    ]
]

window = sg.Window("Redshift Houdini CLI Render", icon="houdini_logo.png").Layout(layout)

while True:
    event, values = window.read()

    if event == "TEST":
        print(values['outnode'])
        print(values['hippath'])
        print(values['sframe'])
        print(values['eframe'])
        print(values['userange'])

    if event == "Render":
        out = values['outnode']
        hip = values['hippath']
        sframe = values['sframe']
        eframe = values['eframe']
        userange = str(values['userange'])

        cp = subprocess.run(['konsole', '-e', 'hython', 'temp.py',
                         '-i', hip, '-o', out, '-s', sframe, '-e', eframe, '-u',
                             userange, '| tee /home/vsamusenko/Documents/output.txt'],
                        universal_newlines=True, stdout=PIPE, stderr=PIPE)
        print(cp.args)
        print(cp.returncode)
        print(cp.stdout)
        print(cp.stderr)

    elif event == "Cancel" or event == sg.WIN_CLOSED:
        break





