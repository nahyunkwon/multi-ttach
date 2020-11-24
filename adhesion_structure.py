import pandas as pd
import random
import math
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry.polygon import LinearRing, Polygon, Point
from maxrect import get_intersection, get_maximal_rectangle, rect2poly


def get_min_max(input_list):
    '''
    get minimum and maximum value in the list
    :param input_list: list of numbers
    :return: min, max
    '''

    min_value = input_list[0]
    max_value = input_list[0]

    for i in input_list:
        if i > max_value:
            max_value = i
        elif i < min_value:
            min_value = i

    return min_value, max_value


def get_largest_polygon(x_values, y_values):
    '''
    Get the largest polygon among multiple polygons (if exist)
    :param x_values: a list of all x coordinates in infill
    :param y_values: a list of all y coordinates in infill
    :return: the list of x-y coordinates of the largest polygon
    '''

    areas = []
    polygon_coords = []

    all_polygons = []

    for i in range(len(x_values)):
        if x_values[i] == "G0":  # next polygon
            if len(polygon_coords) != 0:
                areas.append(Polygon(polygon_coords).area)
                all_polygons.append(polygon_coords)
                polygon_coords = []
        else:
            polygon_coords.append([x_values[i], y_values[i]])

    max_area = areas[0]
    max_index = 0

    print(areas)

    for i in range(len(areas)):
        if areas[i] > max_area:
            max_area = areas[i]
            max_index = i

    return all_polygons[max_index]


def is_far_from_inner_wall(x, y, x_values, y_values, threshold=1):
    """

    :param x:
    :param y:
    :param x_values:
    :param y_values:
    :param threshold:
    :return:
    """

    for k in range(len(x_values)):
        if math.hypot(x - x_values[k], y - y_values[k]) < threshold:
            return False

    return True


def get_grid_points_for_target_layer(file, target_layer, gap):
    '''

    :param file:
    :param target_layer:
    :param gap: (mm)
    :return:
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

    x_values = []
    y_values = []

    for l in target_lines.split("\n"):
        if "G1" in l:
            elems = l.split(" ")

            for e in elems:
                if ";" not in e:
                    if "X" in e:
                        x_values.append(float(e.split("X")[1]))
                    if "Y" in e:
                        y_values.append(float(e.split("Y")[1]))

        elif "G0" in l:  # flag that indicates the next polygon
            x_values.append("G0")
            y_values.append("G0")

    polygon_coords = get_largest_polygon(x_values, y_values)

    polygon_coords.append(polygon_coords[0])

    #print(polygon_coords)

    x_values = []
    y_values = []

    for i in range(len(polygon_coords)):
        x_values.append(polygon_coords[i][0])
        y_values.append(polygon_coords[i][1])

    #print(polygon.area)

    x_min, x_max = get_min_max(x_values)
    y_min, y_max = get_min_max(y_values)

    grid_x = []
    grid_y = []

    current_x = x_min + 1
    current_y = y_min + 1

    #print(x_min)
    #print(y_min)

    while current_x <= x_max:
        grid_x.append(current_x)
        current_x += gap
    while current_y <= y_max:
        grid_y.append(current_y)
        current_y += gap

    #print(grid_x)
    #print(grid_y)

    # a structure
    a_x = []
    a_y = []

    polygon = Polygon(polygon_coords)

    for i in range(len(grid_x)):
        for j in range(len(grid_y)):
            current_point = Point(grid_x[i], grid_y[j])

            if polygon.contains(current_point):

                if is_far_from_inner_wall(current_point.x, current_point.y, x_values, y_values):
                    a_x.append(current_point.x)
                    a_y.append(current_point.y)

    a_coords = []  # coordinates of a structure

    for i in range(len(a_x)):
        a_coords.append([a_x[i], a_y[i]])

    print(a_coords)

    print(sorted(a_coords, key=lambda x: x[1]))

    # x and y values for b structure
    b_x = []
    b_y = []

    # check if the unit square is included in the polygon
    for i in range(len(a_coords)):
        if unit_square_is_included(a_coords[i], gap, a_coords):
            b_x.append(a_coords[i][0] + gap/2)
            b_y.append(a_coords[i][1] + gap/2)

    '''
    plt.plot(x_values, y_values, 'ro')
    plt.plot(a_x, a_y, 'bo')
    plt.plot(b_x, b_y, 'go')
    plt.show()
    '''
    return a_x, a_y, b_x, b_y


def generate_grid_infill(a_x, a_y, b_x, b_y, gap):

    arbitrary = 0.1  # arbitrary number to optimize extrusion amount

    # a-structure

    g0 = "G0 F9500 "
    g1 = "G1 F2000 "

    a_structure = ""

    layer_height = 0.2
    nozzle_dia = 0.4
    length = gap
    fa = ((1.75/2) ** 2) / math.pi

    extrusion = (layer_height * nozzle_dia * length * arbitrary) / fa

    a_structure += g0 + "X" + str(a_x[0]) + " Y" + str(a_y[0]) + "\n"

    for i in range(len(a_x)):
        if i+1 < len(a_x):
            if a_x[i+1] == a_x[i]:  # at the same line (y-axis)
                a_structure += g1 + "X" + str(a_x[i+1]) + " Y" + str(a_y[i+1]) + " E" + str(extrusion) + "\n"
            elif a_x[i+1] > a_x[i]:  # next line
                a_structure += g0 + "X" + str(a_x[i+1]) + " Y" + str(a_y[i+1]) + "\n"

    a_structure += g0 + "X" + str(a_x[0]) + " Y" + str(a_y[0]) + "\n"

    a_coords = []  # coordinates of a structure

    for i in range(len(a_x)):
        a_coords.append([a_x[i], a_y[i]])

    y_sorted = sorted(a_coords, key=lambda k: k[1])

    a_structure += g0 + "X" + str(a_x[0]) + " Y" + str(a_y[0]) + "\n"

    for i in range(len(y_sorted)):
        if i+1 < len(y_sorted):
            if y_sorted[i+1][1] == y_sorted[i][1]:  # at the same line (x-axis)
                a_structure += g1 + "X" + str(y_sorted[i+1][0]) + " Y" + str(y_sorted[i+1][1]) + " E" + str(extrusion) + "\n"
            elif a_x[i + 1] > a_x[i]:  # next line
                a_structure += g0 + "X" + str(y_sorted[i+1][0]) + " Y" + str(y_sorted[i+1][1]) + "\n"

    # b-structure
    b_structure = ""

    filling = 0.3  # optimized amount (by experiments) of extrusion for filling empty spaces of grid

    g0 = "G0 F9500 "
    g1 = "G1 F50 "

    count = 0

    for i in range(len(b_x)):
        count += 1
        b_structure += g0 + "X" + str(b_x[i]) + " Y" + str(b_y[i]) + "\n"
        b_structure += g1 + "X" + str(b_x[i]) + " Y" + str(b_y[i]) + " E" + str(filling) + "\n"

    return a_structure, b_structure


def get_zig_zag_for_lines(x, y):

    final = []
    line = []

    line.append([x[0], y[0]])

    for i in range(len(x) - 1):
        if x[i + 1] == x[i]:  # at the same line
            line.append([x[i + 1], y[i + 1]])
        elif x[i + 1] > x[i]:  # next line
            if len(final) % 2 == 0:
                final.append(line)
                line = []
            else:
                line.reverse()
                final.append(line)
                line = []
            line.append([x[i+1], y[i+1]])

    line.append([x[-1], y[-1]])
    if len(final) % 2 == 0:
        final.append(line)
    else:
        line.reverse()
        final.append(line)

    result = []

    for f in final:
        for i in f:
            result.append(i)

    return result


def generate_blob_infill(a_x, a_y, b_x, b_y, gap, file_name, target_layer):

    gcode = open(file_name)

    lines = gcode.readlines()

    current_z = 0
    new_z = 0

    target_z = "no"

    # get Z value
    for i in range(len(lines)):
        if ";LAYER:" + str(target_layer) + "\n" in lines[i]:  # target layer
            target_z = "yes"
        elif ";LAYER" in lines[i]:
            target_z = "no"

        if target_z == "yes":
            # print(lines[i])
            if "Z" in lines[i]:
                #print(lines[i])
                splitline = lines[i].split(" ")
                for j in range(len(splitline)):
                    if "Z" in splitline[j]:
                        if splitline[j].split("Z")[1] == '':
                            break
                        else:
                            current_z = float(splitline[j].split("Z")[1])
                            current_z -= 0.2
                            new_z = current_z + 0.4

    a_final = get_zig_zag_for_lines(a_x, a_y)

    b_final = get_zig_zag_for_lines(b_x, b_y)

    print(a_final)
    print(b_final)
    
    # a-structure
    g0 = "G0 F9500 "
    g1 = "G1 F9500 "

    a_structure = ""
    b_structure = ""

    for i in range(len(a_final)):
        if i+1 < len(a_final):
            a_structure += g1 + "X" + str(a_final[i][0]) + " Y" + str(a_final[i][1]) + " E0.5" + "\n"
            a_structure += g0 + "X" + str(a_final[i][0]) + " Y" + str(a_final[i][1]) + " Z" + str(new_z) + "\n"
            a_structure += g0 + "X" + str(a_final[i][0]) + " Y" + str(a_final[i+1][1]) + " Z" + str(current_z) + "\n"

    a_structure += g1 + "X" + str(a_final[-1][0]) + " Y" + str(a_final[-1][1]) + " E0.5" + "\n"
    a_structure += g0 + "X" + str(a_final[-1][0]) + " Y" + str(a_final[-1][1]) + " Z" + str(new_z) + "\n"

    for i in range(len(b_final)):
        if i+1 < len(b_final):
            b_structure += g1 + "X" + str(b_final[i][0]) + " Y" + str(b_final[i][1]) + " E0.5" + "\n"
            b_structure += g0 + "X" + str(b_final[i][0]) + " Y" + str(b_final[i][1]) + " Z" + str(new_z) + "\n"
            b_structure += g0 + "X" + str(b_final[i+1][0]) + " Y" + str(b_final[i][1]) + " Z" + str(current_z) + "\n"

    b_structure += g1 + "X" + str(b_final[-1][0]) + " Y" + str(b_final[-1][1]) + " E0.5" + "\n"
    b_structure += g0 + "X" + str(b_final[-1][0]) + " Y" + str(b_final[-1][1]) + " Z" + str(new_z) + "\n"

    return a_structure, b_structure


def replace_infill_to_adhesion_structure(file_name, target_layer, type):

    gcode = open(file_name)

    if type == "grid":
        gap = 2
        a_x, a_y, b_x, b_y = get_grid_points_for_target_layer(file_name, target_layer, gap)
        a_structure, b_structure = generate_grid_infill(a_x, a_y, b_x, b_y, gap)
    elif type == "blob":
        gap = 1.5
        a_x, a_y, b_x, b_y = get_grid_points_for_target_layer(file_name, target_layer, gap)
        a_structure, b_structure = generate_blob_infill(a_x, a_y, b_x, b_y, gap, file_name, target_layer)

    lines = gcode.readlines()

    is_target = 0
    is_infill = 0

    modified = ""

    is_b = 0

    if type == "grid":
        for l in lines:
            if ";LAYER:" + str(target_layer - 2)+ "\n" in l \
                    or ";LAYER:" + str(target_layer - 1) + "\n" in l \
                    or ";LAYER:" + str(target_layer) + "\n" in l \
                    or ";LAYER:" + str(target_layer + 1) + "\n" in l:  # target layer
                is_target = 1
                if ";LAYER:" + str(target_layer + 1) + "\n" in l:
                    is_b = 1
            if is_target == 1 and ";TYPE:FILL" in l:
                modified += l
                is_infill = 1

            if ";MESH:NONMESH" in l and is_target == 1 and is_infill == 1:
                is_target = 0
                is_infill = 0
                if is_b == 0:
                    modified += a_structure
                else:
                    modified += b_structure
                    is_b = 0
                modified += ";MESH:NONMESH\n"
            elif is_target == 1 and is_infill == 1:
                pass
            else:
                modified += l

        with open(file_name.split(".gcode")[0] + "_grid.gcode", "w") as f:
            f.write(modified)

    elif type == "blob":
        for l in lines:
            if ";LAYER:" + str(target_layer) + "\n" in l\
                    or ";LAYER:" + str(target_layer + 1) + "\n" in l:  # target layer
                is_target = 1
                if ";LAYER:" + str(target_layer + 1) + "\n" in l:
                    is_b = 1
            if is_target == 1 and ";TYPE:FILL" in l:
                modified += l
                is_infill = 1

            if ";MESH:NONMESH" in l and is_target == 1 and is_infill == 1:
                is_target = 0
                is_infill = 0
                if is_b == 0:
                    modified += a_structure
                else:
                    modified += b_structure
                    is_b = 0
                modified += ";MESH:NONMESH\n"
            elif is_target == 1 and is_infill == 1:
                pass
            elif ";LAYER:" + str(target_layer + 2) + "\n" in l:
                modified += "G0 X0 Y0"
                modified += "M0\n"

                modified += l
            else:
                modified += l

        with open(file_name.split(".gcode")[0] + "_blob.gcode", "w") as f:
            f.write(modified)


def unit_square_is_included(p, gap, coords):
    if [p[0] + gap, p[1]] not in coords:
        return False
    if [p[0], p[1] + gap] not in coords:
        return False
    if [p[0] + gap, p[1] + gap] not in coords:
        return False

    return True


if __name__ == "__main__":
    #file_name = "./cube.gcode"
    target_layer = 4

    #replace_infill_to_adhesion_structure(file_name, target_layer, "blob")

    replace_infill_to_adhesion_structure("./cube.gcode", 4, "blob")
    replace_infill_to_adhesion_structure("./cylinder.gcode", 6, "blob")

    replace_infill_to_adhesion_structure("./cube.gcode", 4, "grid")
    replace_infill_to_adhesion_structure("./cylinder.gcode", 6, "grid")

    #get_grid_points_for_target_layer("./cube.gcode", 10, 2)
    #get_grid_points_for_target_layer("./cylinder.gcode", 20, 0.4)
    #get_grid_points_for_target_layer("./bunny.gcode", 13, 2)
