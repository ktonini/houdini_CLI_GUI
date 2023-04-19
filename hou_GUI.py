#!/usr/bin/python3

import threading
import re
import sys
import time
import datetime
import subprocess
import os
import signal
import PySimpleGUI as sg

# sg.theme('dark grey 9')

hcg_theme = {'BACKGROUND': '#3b3b3b',
             'TEXT': '#d6d6d6',
             'INPUT': '#323232',
             'TEXT_INPUT': '#ffffff',
             'SCROLL': '#474747',
             'BUTTON': ('#212121', '#6e6e6e'),
             'PROGRESS': ('#222222', '#D0D0D0'),
             'BORDER': 0,
             'SLIDER_DEPTH': 0,
             'PROGRESS_DEPTH': 0}
sg.theme_add_new('HCGTheme', hcg_theme)
sg.theme('HCGTheme')

sg.SetOptions(
    font=('Calibri', 8, 'bold'),
    margins=(20, 20),
    element_padding=(20, 20),
)

default_folder = '/mnt/Data/active_jobs/'
default_outnode = '/out/Redshift_ROP1'
default_log = default_folder + 'output.txt'
versionNum = 'v0.02'

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
        rnode.render(output_progress=True)
    elif (userange == "True"):
        rnode.render(frame_range=(sframe, eframe), output_progress=True)
    else:
        rnode.render(frame_range=(rnode.parm("f1").eval(), rnode.parm("f2").eval()), output_progress=True)

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

hipSize = (100, 1)
outSize = (114, 1)
logSize = (98, 1)
buttonSize = (10, 1)
disabledTextColor = "#ff4c00"


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


layout = [
    [
        sg.Stretch(),
        sg.Text("Frames: ", pad=((0, 0), (0, 20))),
        sg.Text("-", pad=((0, 0), (0, 20)), key="fc", text_color='#ff4c00'),
        sg.Text("/", pad=((0, 0), (0, 20)), text_color='#ff4c00'),
        sg.Text("-", pad=((0, 0), (0, 20)), key="tfc", text_color='#ff4c00'),
        sg.Stretch(),
        sg.Text("Average: ", pad=((0, 0), (0, 20))),
        sg.Text("-", pad=((0, 0), (0, 20)), key="average", text_color='#ff4c00'),
        sg.Stretch(),
        sg.Text("Elapsed: ", pad=((0, 0), (0, 20))),
        sg.Text("-", pad=((0, 0), (0, 20)), key="elapsed", text_color='#ff4c00'),
        sg.Stretch(),
        sg.Text("Remaining: ", pad=((0, 0), (0, 20))),
        sg.Text("-", pad=((0, 0), (0, 20)), key="remaining", text_color='#ff4c00'),
        sg.Stretch(),
        sg.Text("Total: ", pad=((0, 0), (0, 20))),
        sg.Text("-", pad=((0, 0), (0, 20)), key="total", text_color='#ff4c00'),
        sg.Stretch(),
    ],
    [
        sg.ProgressBar(100,
                       orientation='h',
                       size=(81, 10),
                       key='-PROG-',
                       pad=((0, 0), (0, 10)),
                       bar_color=('#ff4c00', '#323232')
                       )
    ],
    [
        sg.Multiline(default_text="directions here...\n\n",
                     size=(140, 40),
                     font='Courier 8',
                     text_color='#ff4c00',
                     auto_refresh=True,
                     reroute_stdout=True,
                     reroute_stderr=True,
                     autoscroll=True,
                     autoscroll_only_at_bottom=True,
                     sbar_width=4,
                     sbar_arrow_width=4,
                     sbar_trough_color="#ff4c00",
                     sbar_relief="RELIEF_FLAT",
                     key='term',
                     pad=((0, 0), (0, 10))
                     )
    ],
    [
        sg.Text("Hip Path", pad=((0, 10), (0, 10))),
        sg.Combo(sg.user_settings_get_entry('-hipnames-', []),
                 default_value=sg.user_settings_get_entry('-last hipname-', ''), size=hipSize, key='hippath', pad=((0, 10), (0, 10))),
        sg.FileBrowse(initial_folder=os.path.dirname(
            sg.user_settings_get_entry('-last hipname-', default_folder)), size=buttonSize, pad=((0, 0), (0, 10))),
    ],
    [
        sg.Text("Out Path", pad=((0, 10), (0, 10))),
        sg.Combo(sg.user_settings_get_entry('-outnames-', []),
                 default_value=sg.user_settings_get_entry('-last outname-', ''), size=outSize, key='outnode', pad=((0, 0), (0, 10))),
    ],
    [
        sg.Checkbox('Out is a merge node', default=sg.user_settings_get_entry(
            '-last merge-', False), key='merge', enable_events=True, pad=((75, 0), (0, 10))),
    ],
    [
        sg.Checkbox('Override Frame Range: ', default=sg.user_settings_get_entry(
            '-last userange-', False), key='userange', enable_events=True, disabled=sg.user_settings_get_entry('-last merge-'), pad=((74, 10), (0, 10))),
        sg.Combo(sg.user_settings_get_entry('-sframe-', []),
                 default_value=sg.user_settings_get_entry('-last start-', 0),
                 size=(10, 1), enable_events=True, key='sframe', disabled=(not sg.user_settings_get_entry('-last userange-') or sg.user_settings_get_entry('-last merge-')), pad=((0, 0), (0, 10))),
        sg.Text(" to ", pad=((0, 0), (0, 10))),
        sg.Combo(sg.user_settings_get_entry('-eframe-', []),
                 default_value=sg.user_settings_get_entry('-last end-', 100),
                 size=(10, 1), enable_events=True, key='eframe', disabled=(not sg.user_settings_get_entry('-last userange-') or sg.user_settings_get_entry('-last merge-')), pad=((0, 0), (0, 10)))
    ],
    [
        sg.Text('Log File', pad=((0, 10), (0, 10))),
        sg.Checkbox('', default=sg.user_settings_get_entry(
            '-last log-', False), key='log', enable_events=True, pad=((0, 0), (0, 10))),
        sg.Combo(sg.user_settings_get_entry('-lognames-', []),
                 default_value=sg.user_settings_get_entry('-last logname-', ''), size=logSize, key='logpath', disabled=not sg.user_settings_get_entry('-last log-'), pad=((0, 10), (0, 10))),
        sg.FileBrowse(initial_folder=os.path.dirname(
            sg.user_settings_get_entry('-last logname-', default_log)), size=buttonSize, key='logbrowse', disabled=not sg.user_settings_get_entry('-last log-'), pad=((0, 10), (0, 10))),
    ],
    [
        sg.Button("Save To Form History", pad=(
            (0, 10), (10, 0)), size=(20, 2)),
        sg.Button("Reset Form to Defaults and Clear History",
                  pad=((0, 0), (10, 0)), size=(20, 2)),
        sg.Stretch(),
        sg.Button("Kill",
                  pad=((0, 10), (0, 0)),
                  size=(10, 2),
                  button_color=("#ff4c00", "#323232")
                  ),
        sg.Button("Render",
                  pad=((0, 0), (0, 0)),
                  size=(10, 2),
                  button_color=("#ff4c00", "#323232")
                  ),
    ]
]


def the_thread(window: sg.Window, p: subprocess.Popen):
    frameTimes = []
    frameTotal = 0
    frameCount = 0
    average = 0

    for line in p.stdout:
        line = line.decode(errors='replace' if (sys.version_info) < (
            3, 5) else 'backslashreplace').rstrip().replace('[Redshift] ', '').replace('[Redshift]', '')
        if 'File already rendered' in line:
            frameCount += 1
            window["fc"].update(frameCount)
            window["-PROG-"].update(current_count=frameCount, max=frameTotal)
        elif 'render started for' in line:
            frameCount = 0
            window["fc"].update(frameCount)
            window["-PROG-"].update(current_count=frameCount, max=frameTotal)
            cleanLine = line.split(' Time from')[0]
            print('\n' + cleanLine + '\n')
            frameTotal = int(re.findall(r'\d+', cleanLine)[-1])
            window["tfc"].update(frameTotal)
        elif 'Rendering frame' in line:
            print(line.replace('Rendering frame', 'Frame'))
            sTime = datetime.datetime.now()
            print("  Started  ", sTime.strftime("%I:%M:%S %p"))
            if average == 0:
                estimate = "N/A"
            else:
                estimate = f'{(sTime + datetime.timedelta(seconds=average)).strftime("%I:%M:%S %p")} - {format_time(average)}'
            # below: the average could be weighted here by getting the previous frame time, whole thing could even just be the average of the last few frames
            print('  Estimate ', estimate)
        elif 'Rendering time' in line:
            frameCount += 1
            window["fc"].update(frameCount)
            window["-PROG-"].update(current_count=frameCount, max=frameTotal)
            eTime = datetime.datetime.now()
            print("  Ended    ", eTime.strftime("%I:%M:%S %p"))
            rTime = eTime - sTime
            print("  Time     ", format_time(rTime.total_seconds()))
            frameTimes.append(rTime.total_seconds())
            average = sum(frameTimes) / len(frameTimes)

            timeProgress = sum(frameTimes) + \
                ((frameCount - len(frameTimes)) * average)

            total = frameTotal * average

            window["average"].update(format_time(average))
            window["elapsed"].update(format_time(timeProgress))
            window["remaining"].update(format_time((total - timeProgress)))
            window["total"].update(format_time(total))

        elif 'scene extraction time' in line:
            print('S' + line.split('\' s')[1] + '\n')
        # else:
        #     print(line)


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
    log = values['logpath']
    uselog = values['log']

    if event == sg.WINDOW_CLOSE_ATTEMPTED_EVENT:
        sg.user_settings_set_entry('-location-', window.current_location())
        break

    elif event == "merge":
        if merge == False:
            window['userange'].update(disabled=False)
            if values['userange'] != False:
                window['sframe'].update(disabled=False)
                window['eframe'].update(disabled=False)
        else:
            window['sframe'].update(disabled=True)
            window['eframe'].update(disabled=True)
            window['userange'].update(disabled=True)
            print('Out is a merge node: For batch rendering. Point the "Out Path" field to a merge node with multiple ROPs connected to it. Each ROP should have "Non-blocking Current Frame Rendering" unchecked, as well as "Valid Frame Range" set to "Render Frame Range Only (Strict)" if the ROPs have different ranges.\n')

    elif event == "userange":
        if userange == False:
            window['sframe'].update(disabled=True)
            window['eframe'].update(disabled=True)
        else:
            window['sframe'].update(disabled=False)
            window['eframe'].update(disabled=False)

    elif event == 'log':
        if uselog == False:
            window['logpath'].update(disabled=True)
            window['logbrowse'].update(disabled=True)
        else:
            window['logpath'].update(disabled=False)
            window['logbrowse'].update(disabled=False)

    elif event == "Save To Form History":

        sg.user_settings_set_entry(
            '-hipnames-', list(set(sg.user_settings_get_entry('-hipnames-', []) + [hip, ])))
        sg.user_settings_set_entry('-last hipname-', hip)

        sg.user_settings_set_entry(
            '-outnames-', list(set(sg.user_settings_get_entry('-outnames-', []) + [out, ])))
        sg.user_settings_set_entry('-last outname-', out)

        sg.user_settings_set_entry('-last userange-', userange)
        sg.user_settings_set_entry('-last merge-', merge)

        sg.user_settings_set_entry(
            '-sframe-', list(set(sg.user_settings_get_entry('-sframe-', []) + [sframe, ])))
        sg.user_settings_set_entry('-last hipname-', hip)
        sg.user_settings_set_entry('-last start-', sframe)

        sg.user_settings_set_entry(
            '-eframe-', list(set(sg.user_settings_get_entry('-eframe-', []) + [eframe, ])))
        sg.user_settings_set_entry('-last end-', eframe)

        sg.user_settings_set_entry('-last log-', uselog)
        sg.user_settings_set_entry(
            '-lognames-', list(set(sg.user_settings_get_entry('-lognames-', []) + [log, ])))
        sg.user_settings_set_entry('-last logname-', log)

        print("Saved.")

    elif event == "Reset Form to Defaults and Clear History":
        sg.user_settings_set_entry('-hipnames-', [])
        sg.user_settings_set_entry('-outnames-', [])
        sg.user_settings_set_entry('-last hipname-', default_folder)
        sg.user_settings_set_entry('-last outname-', default_outnode)
        sg.user_settings_set_entry('-last userange-', False)
        sg.user_settings_set_entry('-last merge-', False)
        sg.user_settings_set_entry('-sframe-', [])
        sg.user_settings_set_entry('-last start-', 0)
        sg.user_settings_set_entry('-eframe-', [])
        sg.user_settings_set_entry('-last end-', 100)
        sg.user_settings_set_entry('-lognames-', [])
        sg.user_settings_set_entry('-last log-', False)
        sg.user_settings_set_entry('-last logname-', default_log)
        window['hippath'].update(
            values=[], value=default_folder, size=hipSize)
        window['outnode'].update(
            values=[], value=default_outnode, size=outSize)
        window['logpath'].update(
            values=[], value=default_log, size=logSize)

        print("Reset.")

    elif event == "Render":
        # cp = subprocess.run(['konsole', '-e', 'hython', 'houdini_cli_temp.py',
        # cp = subprocess.run(['cool-retro-term', '-e', 'hython', 'houdini_cli_temp.py',

        # OG
        # cp = subprocess.run(['gnome-terminal', '--', 'hython', 'houdini_cli_temp.py',
        #                      '-i', hip, '-o', out, '-s', sframe, '-e', eframe, '-u',
        #                      str(userange), '-m', str(merge), (f' | tee {log}' if uselog == True else '')],
        #                     universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # p = sg.execute_command_subprocess('hython', f'houdini_cli_temp.py -i {hip} -o {out} -s {sframe} -e {eframe} -u {str(userange)} -m {str(merge)}',
        #                                   wait=False, pipe_output=True, merge_stderr_with_stdout=True, stdin=subprocess.PIPE)

        # OG
        # print(cp.args)
        # print(cp.returncode)
        # print(cp.stdout)
        # print(cp.stderr)

        window['term'].update((' RENDER STARTED AT' +
                               time.strftime('%l:%M%p %Z on %b %d, %Y ')).center(140, '-') + '\n\n', text_color_for_value='#c0c0c0', append=True)
        print('hython ' + dir_path + '/houdini_cli_temp.py \\')
        print('-i ' + hip + ' \\')
        print('-o ' + out + ' \\')
        print('-s ' + sframe + ' \\')
        print('-e ' + eframe + ' \\')
        print('-u ' + str(userange) + ' \\')
        print('-m ' + str(merge) + (' \\' if uselog == True else ''))
        print((f'| tee {log} \n' if uselog == True else ''))
        window['term'].update(('-').center(140, '-') + '\n\n',
                              text_color_for_value='#c0c0c0', append=True)

        p = subprocess.Popen(
            f'hython houdini_cli_temp.py -i {hip} -o {out} -s {sframe} -e {eframe} -u {str(userange)} -m {str(merge)}' + (
                f' | tee {log}' if uselog == True else ''),
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            preexec_fn=os.setsid
        )

        threading.Thread(target=the_thread, args=(window, p), daemon=True).start()

        window['term'].update(
            'Loading scene...\n\n', text_color_for_value='#c0c0c0', justification='left', append=True)

        sg.user_settings_set_entry(
            '-hipnames-', list(set(sg.user_settings_get_entry('-hipnames-', []) + [hip, ])))
        sg.user_settings_set_entry(
            '-outnames-', list(set(sg.user_settings_get_entry('-outnames-', []) + [out, ])))
        sg.user_settings_set_entry('-last hipname-', hip)
        sg.user_settings_set_entry('-last outname-', out)
        sg.user_settings_set_entry('-last userange-', userange)
        sg.user_settings_set_entry('-last merge-', merge)
        sg.user_settings_set_entry(
            '-sframe-', list(set(sg.user_settings_get_entry('-sframe-', []) + [sframe, ])))
        sg.user_settings_set_entry('-last start-', sframe)
        sg.user_settings_set_entry(
            '-eframe-', list(set(sg.user_settings_get_entry('-eframe-', []) + [eframe, ])))
        sg.user_settings_set_entry('-last end-', eframe)
        sg.user_settings_set_entry('-last log-', uselog)
        sg.user_settings_set_entry(
            '-lognames-', list(set(sg.user_settings_get_entry('-lognames-', []) + [log, ])))
        sg.user_settings_set_entry('-last logname-', log)

    elif event == 'Kill':
        os.killpg(os.getpgid(p.pid), signal.SIGTERM)
        time.sleep(2)
        if p.poll() is None:  # Force kill if process is still alive
            time.sleep(3)
            os.killpg(os.getpgid(p.pid), signal.SIGKILL)
