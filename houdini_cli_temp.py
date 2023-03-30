
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
