import pandas as pd
import random
import math
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry.polygon import LinearRing, Polygon


def get_infill_area():

    gcode = open("./CE3_cube.gcode")

    lines = gcode.readlines()

    is_target = 0
    is_infill = 0

    target_infill = ""

    for l in lines:
        if ";LAYER:4" in l:  # target layer
            is_target = 1
        if is_target == 1 and ";TYPE:FILL" in l:
            is_infill = 1
        if is_target == 1 and is_infill == 1:
            target_infill += l
        if ";MESH:NONMESH" in l and is_target == 1 and is_infill == 1:
            #is_target = 0
            #is_infill = 0
            break

    x_values = []
    y_values = []

    #print(target_infill)

    # calculating the area of infill
    for l in target_infill.split("\n"):
        if "X" in l:
            elems = l.split(" ")

            for e in elems:
                if "X" in e:
                    x_values.append(e.split("X")[1])
                if "Y" in e:
                    y_values.append(e.split("Y")[1])

    x_values.sort()
    y_values.sort()

    x_min = int(x_values[0].split(".")[0]) + 1
    x_max = int(x_values[-1].split(".")[0])
    y_min = int(y_values[0].split(".")[0]) + 1
    y_max = int(y_values[-1].split(".")[0])

    #print(x_min)

    grid_x = []
    grid_y = []

    current_x = x_min
    current_y = y_min

    # get coordinates for grid lines
    while current_x <= x_max:
        grid_x.append(current_x)
        current_x += 2

    while current_y <= y_max:
        grid_y.append(current_y)
        current_y += 2

    # a-structure

    g0 = "G0 F9500 "
    g1 = "G1 F2000 "

    result = ""

    layer_height = 0.2
    nozzle_dia = 0.4
    length = 0.2
    fa = ((1.75/2) ** 2) / math.pi

    extrusion = (layer_height * nozzle_dia * length) / fa

    for x in grid_x:
        result += g0 + "X" + str(x) + " Y" + str(grid_y[0]) + "\n"
        for i in range(1, len(grid_y)):
            result += g1 + "X" + str(x) + " Y" + str(grid_y[i]) + " E" + str(extrusion) + "\n"
    result += "\n"
    for y in grid_y:
        result += g0 + "X" + str(grid_x[0]) + " Y" + str(y) + "\n"
        for i in range(1, len(grid_x)):
            result += g1 + "X" + str(grid_x[i]) + " Y" + str(y) + " E" + str(extrusion) + "\n"

    print(result)

    # b-structure

    result = ""

    current_x = x_min + 1
    current_y = y_min + 1

    g0 = "G0 F9500 "
    g1 = "G1 F50 "

    grid_x.clear()
    grid_y.clear()

    while current_x <= x_max:
        grid_x.append(current_x)
        current_x += 2

    while current_y <= y_max:
        grid_y.append(current_y)
        current_y += 2

    for x in grid_x:
        #result += g0 + "X" + str(x) + " Y" + str(grid_y[0]) + "\n"
        for y in grid_y:
            result += g0 + "X" + str(x) + " Y" + str(y) + "\n"
            result += g1 + "X" + str(x) + " Y" + str(y) + " E0.3" + "\n"

    result += "\n"
    '''
    for y in grid_y:
        for x in grid_x:
            result += g0 + "X" + str(x) + " Y" + str(y) + "\n"
            # result += g0 + "X" + str(grid_x[0]) + " Y" + str(y) + "\n"
            result += g1 + "X" + str(x) + " Y" + str(y) + " E0.3" + "\n"
            '''

    print("---------------b-------------")
    print(result)


def get_largest_rect(file, target_layer):
    '''
    get the largest rectangle that fits inner-wall
    :return: x_min, y_min, x_max, y_max
    '''

    gcode = open(file)

    lines = gcode.readlines()

    is_target = 0
    is_inner_wall = 0

    target_lines = ""

    for l in lines:
        if is_target == 1 and is_inner_wall == 1 and ";TYPE:WALL-OUTER" in l:
            break
        if ";LAYER:" + str(target_layer)+"\n" in l:  # target layer
            is_target = 1
            target_lines += l
        if is_target == 1 and ";TYPE:WALL-INNER" in l:
            is_inner_wall = 1
        if is_target == 1 and is_inner_wall == 1:
            target_lines += l

    print(target_lines)

    x = []
    y = []

    for l in target_lines.split("\n"):
        if "G1" in l:
            elems = l.split(" ")

            for e in elems:
                if ";" not in e:
                    if "X" in e:
                        x.append(e.split("X")[1])
                    if "Y" in e:
                        y.append(e.split("Y")[1])

    print(x)
    print(y)

    #plt.scatter(np.array(x), np.array(y))

    #plt.show()

    polygon_coords = []

    '''

    for i in range(len(x)):
        polygon_coords.append((float(x[i]), float(y[i])))

    polygon_coords.append((float(x[0]), float(y[0])))

    print(polygon_coords)

    polygon = Polygon(polygon_coords)
    '''

    x.append(x[0])
    y.append(y[0])

    fig, ax = plt.subplots()

    ax.plot(x, y, color='#6699cc', alpha=0.7,
            linewidth=3, solid_capstyle='round', zorder=2)
    ax.set_title('Polygon')
    plt.show()


if __name__ == "__main__":
    #get_largest_rect("./CE3_cube.gcode", 4)
    get_largest_rect("./cylinder.gcode", 22)
