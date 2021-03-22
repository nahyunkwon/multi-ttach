from horizontal_adhesion import *
from vertical_adhesion import *


def calculate_extrusion_amount(filename):

    gcode = open(filename, "r")

    lines = gcode.readlines()

    total_extrusion = 0

    for l in lines:
        if "G1" in l:
            parts = l.split(" ")

            for p in parts:
                if "E" in p:
                    total_extrusion += float(p.split("E")[1])

    print(total_extrusion)


if __name__ == "__main__":

    #adhesion_structure("./gcode/CE3_sandal.gcode", [15, 24], "blob")
    #adhesion_structure("./gcode/CE3_sandal.gcode", [15, 24], "grid")
    #adhesion_structure("./gcode/CE3_d2095_samesidehole.gcode", [190], "blob")
    #adhesion_structure("./gcode/CE3_d2095_samesidehole.gcode", [190], "grid")
    #adhesion_structure("./gcode/CE3_d2095_small_11.7.gcode", [125], "blob")
    #adhesion_structure("./gcode/CE3_final.gcode", [127], "grid")
    #adhesion_structure("./gcode/CE3_cylinder.gcode", [10], "grid")
    #adhesion_structure_vertical("./example/another_gripper.gcode", [7], "grid")

    adhesion_structure_horizontal("./gcode_dual/FCPRO_final.gcode")

    #calculate_extrusion_amount("./gcode/CE3_final_grid.gcode")
