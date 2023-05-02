#!/usr/bin/python3

import datetime
import os
import re
import signal
import subprocess
import sys
import threading
import time

import OpenEXR
import Imath
import numpy as np
from PIL import Image

import PySimpleGUI as sg

hcg_theme = {
    'BACKGROUND': '#3a3a3a',
    'TEXT': '#d6d6d6',
    'INPUT': '#131313',
    'TEXT_INPUT': '#ffffff',
    'SCROLL': '#474747',
    'BUTTON': ('#ffffff', '#555555'),
    'PROGRESS': ('#222222', '#D0D0D0'),
    'BORDER': 0,
    'SLIDER_DEPTH': 0,
    'PROGRESS_DEPTH': 0
}
sg.theme_add_new('HCGTheme', hcg_theme)
sg.theme('HCGTheme')

sg.SetOptions(
    font=('SYSTEM_DEFAULT', 10, 'normal'),
    margins=(0, 0),
    element_padding=(0, 0),
    sbar_relief=sg.RELIEF_FLAT,
)

default_folder = '/mnt/Data/active_jobs/'
default_outnode = '/out/Redshift_ROP1'
default_log = default_folder + 'output.txt'
versionNum = 'v1.0'

dir_path = os.path.dirname(os.path.realpath(__file__))
os.chdir(dir_path)

if os.path.exists('houdini_cli_temp.py'):
    os.remove('houdini_cli_temp.py')
else:
    pass

tempPY = open('houdini_cli_temp.py', 'w')
tempPY.write('''
from optparse import OptionParser

def initRender(out, sframe, eframe, userange):
    rnode = hou.node(out)

    def dataHelper(rop_node, render_event_type, frame):
        if render_event_type == hou.ropRenderEventType.PostFrame:
            output_file = rnode.evalParm("RS_outputFileNamePrefix")
            print(f"hgui_outputfile: {output_file}")

    rnode.addRenderEventCallback(dataHelper)

    if "merge" in str(rnode.type()).lower():
        rnode.render()
        if (userange == "True"):
            print(f"hgui_note: Out Path leads to a merge node, but you have selected to override the frame range. Defaulting to the frame range that was set from within Houdini for each ROP.")
    else:
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

    initRender(options.outnode, int(options.startframe), int(options.endframe), options.userange)
''')
tempPY.close()

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


def output(default_text, text_color, reroute_stdout=True, reroute_stderr=True, visible=True, key='term1'):
    return sg.Multiline(
        default_text=default_text,
        size=(50, 30),
        expand_x=True,
        expand_y=True,
        font='Courier 8',
        text_color=text_color,
        auto_refresh=True,
        reroute_stdout=reroute_stdout,
        reroute_stderr=reroute_stderr,
        autoscroll=True,
        autoscroll_only_at_bottom=True,
        #  sbar_width=4,
        #  sbar_arrow_width=4,
        sbar_trough_color="#323232",
        sbar_relief='flat',
        sbar_background_color='#3b3b3b',
        sbar_arrow_color=None,
        sbar_width=None,
        sbar_arrow_width=None,
        key=key,
        disabled=True,
        visible=visible,
        pad=(0)
    )


overrides_layout = [
    [
        sg.Checkbox('Frame Range: ', default=sg.user_settings_get_entry(
            '-last userange-', False), key='userange', enable_events=True, pad=((0, 0), (0, 10))),
        sg.Combo(sg.user_settings_get_entry('-sframe-', []),
                 default_value=sg.user_settings_get_entry('-last start-', 0),
                 size=(10, 1), enable_events=True, key='sframe', disabled=(not sg.user_settings_get_entry('-last userange-')), pad=((0, 0), (0, 10))),
        sg.Text(" to ", pad=((0, 0), (0, 10))),
        sg.Combo(sg.user_settings_get_entry('-eframe-', []),
                 default_value=sg.user_settings_get_entry('-last end-', 100),
                 size=(10, 1), enable_events=True, key='eframe', disabled=(not sg.user_settings_get_entry('-last userange-')), pad=((0, 0), (0, 10)))
    ],
    [sg.Text('res')],
    [sg.Text('quality')],
    [sg.Text('method')],
    [sg.Text('ignore_bypass_flags')],
    [sg.Text('verbose')],
]

icon_browse = b'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'

form_layout = [
    [
        sg.Text("Hip Path", pad=((0, 10), (0, 10))),
        sg.Combo(
            sg.user_settings_get_entry('-hipnames-', []),
            default_value=sg.user_settings_get_entry('-last hipname-', ''),
            expand_x=True,
            key='hippath',
            pad=((0, 0), (0, 10))
        ),
        sg.Button(
            button_type=sg.BUTTON_TYPE_BROWSE_FILE,
            image_data=icon_browse,
            image_size=(30, 30),
            image_subsample=3,
            button_color="#3b3b3b",
            mouseover_colors="#6e6e6e",
            initial_folder=os.path.dirname(sg.user_settings_get_entry('-last hipname-', default_folder)),
            file_types=(("Hip Files", "*.hip*"), ("All Files", "*.*")),
            pad=((0, 0), (0, 10))),
    ],
    [
        sg.Text("Out Path", pad=((0, 10), (0, 10))),
        sg.Combo(
            sg.user_settings_get_entry('-outnames-', []),
            default_value=sg.user_settings_get_entry('-last outname-', ''),
            expand_x=True,
            key='outnode',
            pad=((0, 32), (0, 10))
        ),
    ],
    [
        sg.Text('Log Path', pad=((0, 0), (0, 0))),
        sg.Checkbox('', default=sg.user_settings_get_entry(
            '-last log-', False), key='log', enable_events=True, pad=((0, 0), (0, 0))),
        sg.Combo(
            sg.user_settings_get_entry('-lognames-', []),
            default_value=sg.user_settings_get_entry('-last logname-', ''),
            expand_x=True,
            key='logpath',
            disabled=not sg.user_settings_get_entry('-last log-'),
            pad=((0, 0), (0, 0))
        ),
        sg.Button(
            button_type=sg.BUTTON_TYPE_BROWSE_FILE,
            image_data=icon_browse,
            image_size=(30, 30),
            image_subsample=3,
            button_color="#3b3b3b",
            mouseover_colors="#6e6e6e",
            initial_folder=os.path.dirname(sg.user_settings_get_entry('-last logname-', default_log)),
            key='logbrowse',
            disabled=not sg.user_settings_get_entry('-last log-'),
            pad=((0, 0), (0, 0))),
    ],
    [
        sg.Frame(
            'Overrides',
            overrides_layout,
            pad=((0, 0), (0, 10)),
            expand_x=True,
            expand_y=False,
            border_width=1,
            title_location='n',
            relief='solid',
        )
    ],
    [
        sg.Button("Force Save",
                  pad=((0, 0), (0, 0)),
                  #   size=(10, 1)
                  ),
        sg.Button("Reset",
                  pad=((0, 0), (0, 0)),
                  #   size=(10, 1)
                  ),
        sg.Button("Clear History",
                  pad=((0, 0), (0, 0)),
                  #   size=(10, 1)
                  ),
        sg.Button("View Output",
                  pad=((0, 0), (0, 0)),
                  #   size=(10, 1),
                  key='switch',
                  ),
        sg.Stretch(),
        sg.Button("Cancel",
                  key='cancel',
                  pad=((0, 0), (0, 0)),
                  #   size=(10, 1),
                  button_color=("#ff4c00", "#323232"),
                  visible=False,
                  ),
        sg.Button("Render",
                  pad=((0, 0), (0, 0)),
                  #   size=(10, 1),
                  button_color=("#ff4c00", "#323232")
                  ),
    ],
]

layout = [
    [
        sg.Frame(
            '',
            form_layout,
            pad=((10, 10), (10, 10)),
            expand_x=True,
            expand_y=False,
            relief='flat',
        )
    ],
    [
        sg.Text("-", key='ropnode', font=('SYSTEM_DEFAULT', 15, 'bold'), text_color='#ff4c00', pad=((10, 0), (0, 10))),
        sg.Stretch(),
        sg.Text("-", key="eta", font=('SYSTEM_DEFAULT', 15, 'bold'), text_color='#ff4c00', pad=((0, 0), (0, 10))),
        sg.Stretch(),
        sg.Text("-", key="remaining", font=('SYSTEM_DEFAULT', 15, 'bold'), text_color='#ff4c00', pad=((0, 10), (0, 10))),
    ],
    [
        sg.ProgressBar(100,
                       orientation='h',
                       size=(81, 10),
                       expand_x=True,
                       key='progressTotal',
                       pad=(0),
                       bar_color=('#ff4c00', '#323232'),
                       )
    ],
    [
        output('''TIPS:
    For batch rendering -
        Point the 'Out Path' field to a merge node with multiple ROPs connected to it.
        The 'Frame Range' override will be ignored, instead using the range set up in Houdini.
        Each ROP should have -
            'Non-blocking Current Frame Rendering' unchecked.
            'Valid Frame Range' set to 'Render Frame Range Only (Strict)' if the ROPs have different ranges.''',
               '#ff804a',
               False,
               False,
               True,
               'term1'
               ),
        output('''
Full output...
''',
               '#cccccc',
               True,
               True,
               False,
               'term2'
               ),

    ],
    # [sg.HorizontalSeparator()],
    [
        sg.ProgressBar(100,
                       orientation='h',
                       size=(81, 10),
                       expand_x=True,
                       key='progressFrame',
                       pad=(0),
                       bar_color=('#22adf2', '#323232')
                       )
    ],
    [
        sg.Stretch(),
        sg.Text("Frames: ", pad=((0, 0), (10, 10))),
        sg.Text("-", pad=((0, 0), (10, 10)), key="fc", text_color='#ff4c00'),
        sg.Text("/", pad=((0, 0), (10, 10)), text_color='#ff4c00'),
        sg.Text("-", pad=((0, 0), (10, 10)), key="tfc", text_color='#ff4c00'),
        sg.Stretch(),
        sg.Text("Average: ", pad=((0, 0), (10, 10))),
        sg.Text("-", pad=((0, 0), (10, 10)), key="average", text_color='#ff4c00'),
        sg.Stretch(),
        sg.Text("Elapsed: ", pad=((0, 0), (10, 10))),
        sg.Text("-", pad=((0, 0), (10, 10)), key="elapsed", text_color='#ff4c00'),
        sg.Stretch(),
        sg.Text("Est. Total: ", pad=((0, 0), (10, 10))),
        sg.Text("-", pad=((0, 0), (10, 10)), key="total", text_color='#ff4c00'),
        sg.Stretch(),
    ],
]


class CountTask:
    def __init__(self, stop_flag):
        self.stop_flag = stop_flag
        self.seconds_current = 0

    def terminate(self):
        self.stop_flag.set()

    def run(self, seconds, window):
        self.seconds_current = 0
        self.stop_flag.clear()
        window["progressFrame"].update(max=seconds)
        while self.seconds_current < seconds and not self.stop_flag.is_set():
            time.sleep(1)
            self.seconds_current += 1
            window["progressFrame"].update(current_count=self.seconds_current, max=seconds)


def render_thread(window, p):
    frameTimes = []
    frameTotal = 0
    frameCount = 0
    average = 0
    recentAverage = 0
    timer = None
    c = None

    for line in p.stdout:
        line = line.decode(errors='replace' if (sys.version_info) < (
            3, 5) else 'backslashreplace').rstrip().replace('[Redshift] ', '').replace('[Redshift]', '')
        print(line)
        if 'File already rendered' in line:
            frameCount += 1
            window["fc"].update(frameCount)
            window["progressTotal"].update(current_count=frameCount, max=frameTotal)
        elif 'render started for' in line:
            frameCount = 0
            window["fc"].update(frameCount)
            window["progressTotal"].update(current_count=frameCount, max=frameTotal)
            cleanLine = line.split(' Time from')[0]
            window['term1'].update('\n' + cleanLine + '\n', append=True)
            frameTotal = int(re.findall(r'\d+', cleanLine)[-1])
            window["tfc"].update(frameTotal)
            rop_node = cleanLine.split("'")[3]
            window["ropnode"].update(rop_node)
        elif 'Rendering frame' in line:
            window['term1'].update(line.replace('Rendering f', 'F') + '\n', text_color_for_value='#22adf2', append=True, font_for_value=('Courier', 10, 'bold'))
            sTime = datetime.datetime.now()
            window['term1'].update("   Started  " + sTime.strftime("%I:%M:%S %p") + '\n', append=True)
            stop_flag = threading.Event()
            if average != 0:
                estimateString = f'{(sTime + datetime.timedelta(seconds=recentAverage)).strftime("%I:%M:%S %p")} - {format_time(recentAverage)}'
                window['term1'].update('  Estimate  ' + estimateString + '\n', append=True)
                c = CountTask(stop_flag)
                if timer != None:  # if this isnt the first time
                    stop_flag.set()
                    timer.join()
                timer = threading.Thread(target=c.run, args=(int(recentAverage), window), daemon=True)
                timer.start()

        elif 'scene extraction time' in line:
            splitLine = '  S' + line.split('\' s')[1]

            pattern = "total time (\d+\.\d+) sec"
            match = re.search(pattern, splitLine)
            if match:
                number = float(match.group(1))
            else:
                number = 0

            frameCount += 1
            window["fc"].update(frameCount)
            window["progressTotal"].update(current_count=frameCount, max=frameTotal)
            eTime = datetime.datetime.now()
            rTime = datetime.timedelta(seconds=number)
            endedString = f'{(eTime.strftime("%I:%M:%S %p"))} - {format_time(rTime.total_seconds())}'
            window['term1'].update("     Ended  " + endedString + '\n', append=True)

            frameTimes.append(rTime.total_seconds())
            average = sum(frameTimes) / len(frameTimes)

            # calculate the slope of the previous two renders to provide the estimated render time
            if len(frameTimes) >= 2:
                recentTimes = frameTimes[-2:]
                recentAverage = (2 * recentTimes[1]) - recentTimes[0]
            else:
                recentAverage = average

            # Calculate the progress as accurately as possibly given the log data in stdout
            # If run from the beginning will be exact
            # Else will use an (average-frame-time * alread-rendered-frames) + actual recent frame times as the render progresses
            timeProgress = sum(frameTimes) + \
                ((frameCount - len(frameTimes)) * average)

            total = frameTotal * average

            window["average"].update(format_time(average))
            window["elapsed"].update(format_time(timeProgress))
            window["total"].update(format_time(total))

            remaining = total - timeProgress

            if frameCount == frameTotal:
                window["eta"].update(f'Finished: {(eTime + datetime.timedelta(seconds=remaining)).strftime("%I:%M:%S %p")}')
            else:
                window["eta"].update(f'ETA: {(eTime + datetime.timedelta(seconds=remaining)).strftime("%I:%M:%S %p")}')
            window["remaining"].update(f'Remaining: {format_time(remaining)}')
        elif 'hgui_' in line:
            if 'note' in line:
                line = line.split(': ')[1]
                window['term1'].update('\n' + line + '\n', text_color_for_value='#22adf2', append=True, font_for_value=('Courier', 10, 'bold'))
            if 'outputfile' in line:
                renderedImage = line.split(': ')[1]
                # renderedImageType = os.path.splitext(renderedImage)[1]
                window['term1'].update(renderedImage + '\n', text_color_for_value='#22adf2', append=True, font_for_value=('Courier', 10, 'bold'))

    p.wait()
    window['term1'].update('\n' + (' Rendering Stopped ').center(10, '=') + '\n\n', text_color_for_value='#ff7a7a', append=True, font_for_value=('Courier', 12, 'bold'), justification='center')
    window['Render'].update(visible=True)
    window['cancel'].update(visible=False, disabled=False, text='Cancel')
    if c is not None:
        c.terminate


p = None
outputViewList = ['summary', 'raw', 'both']
outputView = outputViewList[0]
canceling = False

window = sg.Window(
    f'Houdini CLI Render {versionNum}',
    layout,
    icon="houdini_logo.png",
    enable_close_attempted_event=True,
    location=sg.user_settings_get_entry('-location-', (None, None)),
    resizable=True,
    no_titlebar=False,
    grab_anywhere=True,
    alpha_channel=1,
    finalize=True,
)
window.set_min_size(window.size)

while True:
    event, values = window.read()

    out = values['outnode']
    hip = values['hippath']
    sframe = values['sframe']
    eframe = values['eframe']
    userange = values['userange']
    log = values['logpath']
    uselog = values['log']

    if event == sg.WINDOW_CLOSE_ATTEMPTED_EVENT:
        sg.user_settings_set_entry('-location-', window.current_location())
        break

    elif event == 'switch':
        outputView = outputViewList[(outputViewList.index(outputView) + 1) % len(outputViewList)]
        if outputView == 'summary':
            window['term1'].update(visible=True)
            window['term2'].update(visible=False)
            window['switch'].update(text='View Output')
        elif outputView == 'raw':
            window['term1'].update(visible=False)
            window['term2'].update(visible=True)
            window['switch'].update(text='View Output and Summary')
        elif outputView == 'both':
            window['term1'].update(visible=True)
            window['term2'].update(visible=True)
            window['switch'].update(text='View Summary')

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

    elif event == "Force Save":

        sg.user_settings_set_entry(
            '-hipnames-', list(set(sg.user_settings_get_entry('-hipnames-', []) + [hip, ])))
        sg.user_settings_set_entry('-last hipname-', hip)

        sg.user_settings_set_entry(
            '-outnames-', list(set(sg.user_settings_get_entry('-outnames-', []) + [out, ])))
        sg.user_settings_set_entry('-last outname-', out)

        sg.user_settings_set_entry('-last userange-', userange)

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

        window['term1'].update(('\n\n Form Values Saved To History ').center(10, '=') + '\n\n', text_color_for_value='#7abfff',
                               append=True, font_for_value=('Courier', 12, 'bold'), justification='center')

    elif event == "Reset":
        sg.user_settings_set_entry('-last hipname-', default_folder)
        sg.user_settings_set_entry('-last outname-', default_outnode)
        sg.user_settings_set_entry('-last userange-', False)
        sg.user_settings_set_entry('-last start-', 0)
        sg.user_settings_set_entry('-last end-', 100)
        sg.user_settings_set_entry('-last log-', False)
        sg.user_settings_set_entry('-last logname-', default_log)
        window['hippath'].update(value=default_folder)
        window['outnode'].update(value=default_outnode)
        window['logpath'].update(value=default_log)
        window['term1'].update((' Form Reset To Default ').center(10, '=') + '\n\n', text_color_for_value='#fffd7a', append=True, font_for_value=('Courier', 12, 'bold'), justification='center')

    elif event == "Clear History":
        sg.user_settings_set_entry('-hipnames-', [
            sg.user_settings_get_entry('-hipnames-', [])[0]
        ])
        sg.user_settings_set_entry('-outnames-', [

        ])
        sg.user_settings_set_entry('-sframe-', [

        ])
        sg.user_settings_set_entry('-eframe-', [

        ])
        sg.user_settings_set_entry('-lognames-', [

        ])
        window['hippath'].update(values=[])
        window['outnode'].update(values=[])
        window['logpath'].update(values=[])
        window['term1'].update((' Form History Cleared ').center(10, '=') + '\n\n', text_color_for_value='#fffd7a', append=True, font_for_value=('Courier', 12, 'bold'), justification='center')

    elif event == "Render":
        window['Render'].update(visible=False)
        window['cancel'].update(visible=True)
        window['term1'].update(('\n\n RENDER STARTED AT ' + time.strftime('%l:%M%p %Z on %b %d, %Y ')).center(10, '=') +
                               '\n\n', text_color_for_value='#22adf2', font_for_value=('Courier', 12, 'bold'), justification='center', append=True)
        window['term1'].update('hython ' + dir_path + '/houdini_cli_temp.py \\\n', text_color_for_value='#c0c0c0', append=True)
        window['term1'].update('-i ' + hip + ' \\\n', text_color_for_value='#c0c0c0', append=True)
        window['term1'].update('-o ' + out + ' \\\n', text_color_for_value='#c0c0c0', append=True)
        window['term1'].update('-s ' + sframe + ' \\\n', text_color_for_value='#c0c0c0', append=True)
        window['term1'].update('-e ' + eframe + ' \\\n', text_color_for_value='#c0c0c0', append=True)
        window['term1'].update('-u ' + str(userange) + ' \\\n', text_color_for_value='#c0c0c0', append=True)
        window['term1'].update((f'| tee {log} \n' if uselog == True else '\n'), text_color_for_value='#c0c0c0', append=True)

        p = subprocess.Popen(
            f'hython houdini_cli_temp.py -i {hip} -o {out} -s {sframe} -e {eframe} -u {str(userange)}' + (
                f' | tee {log}' if uselog == True else ''),
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            start_new_session=True
        )

        threading.Thread(target=render_thread, args=(window, p), daemon=True).start()

        window['term1'].update(
            'Loading scene...\n', text_color_for_value='#c0c0c0', justification='left', append=True)

        sg.user_settings_set_entry(
            '-hipnames-', list(set(sg.user_settings_get_entry('-hipnames-', []) + [hip, ])))
        sg.user_settings_set_entry(
            '-outnames-', list(set(sg.user_settings_get_entry('-outnames-', []) + [out, ])))
        sg.user_settings_set_entry('-last hipname-', hip)
        sg.user_settings_set_entry('-last outname-', out)
        sg.user_settings_set_entry('-last userange-', userange)
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

    elif event == 'cancel':
        # window['cancel'].update(disabled=True, text='Canceling...')
        if canceling:
            window['term1'].update('\n' + (' Killing the render... ').center(10, '=') + '\n\n', text_color_for_value='#ff7a7a',
                                   append=True, font_for_value=('Courier', 12, 'bold'), justification='center')
            os.killpg(os.getpgid(p.pid), signal.SIGKILL)
            # if p.poll() is None:  # Force kill if process is still alive
            #     time.sleep(3)
            #     os.killpg(os.getpgid(p.pid), signal.SIGKILL)
            p.wait()
            window['term1'].update('\n' + (' Render Killed ').center(10, '=') + '\n\n', text_color_for_value='#ff7a7a', append=True, font_for_value=('Courier', 12, 'bold'), justification='center')
            window['Render'].update(visible=True)
            window['cancel'].update(visible=False, disabled=False, text='Cancel')
        else:
            canceling = True
            window['cancel'].update(text='Kill')
            os.killpg(os.getpgid(p.pid), signal.SIGTERM)
            time.sleep(2)
            if p.poll() is None:  # Force kill if process is still alive
                time.sleep(3)
                os.killpg(os.getpgid(p.pid), signal.SIGKILL)
            window['term1'].update('\n' + (' Canceling after current frame... ').center(10, '=') + '\n\n', text_color_for_value='#ff7a7a',
                                   append=True, font_for_value=('Courier', 12, 'bold'), justification='center')
