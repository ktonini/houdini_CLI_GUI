#!/usr/bin/python3

# import sys
import subprocess
import os
# import signal
import PySimpleGUI as sg

# sg.theme('dark grey 9')

hcg_theme = {'BACKGROUND': '#282828',
             'TEXT': 'gray',
             'INPUT': '#222222',
             'TEXT_INPUT': '#ffffff',
             'SCROLL': '#474747',
             'BUTTON': ('gray', '#424242'),
             'PROGRESS': ('#222222', '#D0D0D0'),
             'BORDER': 0,
             'SLIDER_DEPTH': 0,
             'PROGRESS_DEPTH': 0}

sg.theme_add_new('MyNewTheme', hcg_theme)

sg.theme('My New Theme')

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

def initRender(out, sframe, eframe, userange, merge):
    rnode = hou.node(out)
    if (merge == "True"):
        rnode.render()
    elif (userange == "True"):
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
    parser.add_option("-m", "--merge", dest="merge", help="toggle to enable executing a merge node for batch rendering ROPs")


    (options, args) = parser.parse_args()

    hou.hipFile.load(options.hipfile)

    initRender(options.outnode, int(options.startframe), int(options.endframe), options.userange, options.merge)
''')
tempPY.close()

layout = [
    [
        sg.Multiline(default_text="directions here...\n\n",
                     size=(108, 20),
                     font='Courier 10',
                     text_color='orange',
                     auto_refresh=True,
                     reroute_stdout=True,
                     reroute_stderr=True,
                     pad=((0, 0), (0, 20))
                     )
    ],
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
                 default_value=sg.user_settings_get_entry('-last outname-', ''), size=(110, 1), key='outnode'),
    ],
    [
        sg.Checkbox('Out is a merge node', default=sg.user_settings_get_entry(
            '-last merge-', False), key='merge', enable_events=True, pad=((75, 0), (0, 20))),
        sg.Stretch(),
        sg.Checkbox('Use Frame Range', default=sg.user_settings_get_entry(
            '-last userange-', False), key='userange', enable_events=True, disabled=sg.user_settings_get_entry('-last merge-'), pad=((0, 0), (0, 20))),
        sg.Text(" from ", pad=((0, 0), (0, 20))),
        sg.In(sg.user_settings_get_entry('-last start-', 0),
              size=(10, 1), enable_events=True, key='sframe', disabled=not sg.user_settings_get_entry('-last userange-'), pad=((0, 0), (0, 20))),
        sg.Text(" to ", pad=((0, 0), (0, 20))),
        sg.In(sg.user_settings_get_entry('-last end-', 100),
              size=(10, 1), enable_events=True, key='eframe', disabled=not sg.user_settings_get_entry('-last userange-'), pad=((0, 0), (0, 20)))
    ],
    [
        sg.Button("Save To Form History", pad=((75, 0), (0, 20))),
        sg.Button("Reset Form to Defaults and Clear History",
                  pad=((0, 0), (0, 20))),
        sg.Stretch(),
        sg.Button("Render", pad=((0, 0), (0, 20)))
    ]
]

window = sg.Window(f"Houdini CLI Render {versionNum}", icon="houdini_logo.png", enable_close_attempted_event=True,
                   location=sg.user_settings_get_entry('-location-', (None, None)), no_titlebar=False, grab_anywhere=True, alpha_channel=0.95).Layout(layout)

while True:
    event, values = window.read()

    out = values['outnode']
    hip = values['hippath']
    sframe = values['sframe']
    eframe = values['eframe']
    userange = values['userange']
    merge = values['merge']

    if event == "merge":
        if values['merge'] == False:
            window['userange'].update(disabled=False)
            if values['userange'] != False:
                window['sframe'].update(disabled=False)
                window['eframe'].update(disabled=False)
        else:
            window['sframe'].update(disabled=True)
            window['eframe'].update(disabled=True)
            window['userange'].update(disabled=True)
            print('Out is a merge node: For batch rendering. Point the "Out Path" field to a merge node with multiple ROPs connected to it. Each ROP should have "Non-blocking Current Frame Rendering" unchecked.\n')

    if event == "userange":
        if values['userange'] == False:
            window['sframe'].update(disabled=True)
            window['eframe'].update(disabled=True)
        else:
            window['sframe'].update(disabled=False)
            window['eframe'].update(disabled=False)

    if event == "Save To Form History":

        sg.user_settings_set_entry(
            '-hipnames-', list(set(sg.user_settings_get_entry('-hipnames-', []) + [hip, ])))
        sg.user_settings_set_entry(
            '-outnames-', list(set(sg.user_settings_get_entry('-outnames-', []) + [out, ])))
        sg.user_settings_set_entry('-last hipname-', hip)
        sg.user_settings_set_entry('-last outname-', out)
        sg.user_settings_set_entry('-last userange-', userange)
        sg.user_settings_set_entry('-last merge-', merge)
        sg.user_settings_set_entry('-last start-', sframe)
        sg.user_settings_set_entry('-last end-', eframe)

        print("Saved.")

    if event == "Reset Form to Defaults and Clear History":
        sg.user_settings_set_entry('-hipnames-', [])
        sg.user_settings_set_entry('-outnames-', [])
        sg.user_settings_set_entry('-last hipname-', default_folder)
        sg.user_settings_set_entry('-last outname-', default_outnode)
        sg.user_settings_set_entry('-last userange-', False)
        sg.user_settings_set_entry('-last merge-', False)
        sg.user_settings_set_entry('-last start-', 0)
        sg.user_settings_set_entry('-last end-', 100)
        window['hippath'].update(values=[], value=default_folder)
        window['outnode'].update(values=[], value=default_outnode)

        print("Reset.")

    if event == "Render":
        # cp = subprocess.run(['konsole', '-e', 'hython', 'houdini_cli_temp.py',
        # cp = subprocess.run(['cool-retro-term', '-e', 'hython', 'houdini_cli_temp.py',
        cp = subprocess.run(['gnome-terminal', '--', 'hython', 'houdini_cli_temp.py',
                             '-i', hip, '-o', out, '-s', sframe, '-e', eframe, '-u',
                             userange, '-m', merge, '| tee /mnt/Data/active_jobs/output.txt'],
                            universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # cp = sg.execute_command_subprocess('hython', f'houdini_cli_temp.py -i {hip} -o {out} -s {sframe} -e {eframe} -u {userange}',
        #                                    wait=False, pipe_output=True, stdin=PIPE)
        print(cp.args)
        print(cp.returncode)
        print(cp.stdout)
        print(cp.stderr)

        # p = subprocess.Popen(f'hython houdini_cli_temp.py -i {hip} -o {out} -s {sframe} -e {eframe} -u {userange}',
        #                      shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, preexec_fn=os.setsid)
        # output = ''
        # for line in p.stdout:
        #     line = line.decode(errors='replace' if (sys.version_info) < (
        #         3, 5) else 'backslashreplace').rstrip()
        #     output += line
        #     print(line)
        #     window.refresh() if window else None

        sg.user_settings_set_entry(
            '-hipnames-', list(set(sg.user_settings_get_entry('-hipnames-', []) + [hip, ])))
        sg.user_settings_set_entry(
            '-outnames-', list(set(sg.user_settings_get_entry('-outnames-', []) + [out, ])))
        sg.user_settings_set_entry('-last hipname-', hip)
        sg.user_settings_set_entry('-last outname-', out)
        sg.user_settings_set_entry('-last userange-', userange)
        sg.user_settings_set_entry('-last merge-', merge)
        sg.user_settings_set_entry('-last start-', sframe)
        sg.user_settings_set_entry('-last end-', eframe)

    if event == sg.WINDOW_CLOSE_ATTEMPTED_EVENT:
        sg.user_settings_set_entry('-location-', window.current_location())
        # os.killpg(os.getpgid(p.pid), signal.SIGTERM)
        break
