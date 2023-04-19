
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
