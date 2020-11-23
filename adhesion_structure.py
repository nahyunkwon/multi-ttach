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

    plt.plot(x_values, y_values, 'ro')
    plt.plot(a_x, a_y, 'bo')
    plt.plot(b_x, b_y, 'go')
    plt.show()

    return a_x, a_y, b_x, b_y


def generate_grid_infill(a_x, a_y, b_x, b_y, gap, file_name, target_layer):

    gcode = open(file_name)

    lines = gcode.readlines()

    '''

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
        
    '''

    arbitrary = 0.1

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
                a_structure += g1 + "X" + str(a_x[i+1]) + " Y" + str(a_y[i+1]) + " E" + str(extrusion)  + "\n"
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

    print(a_structure)

    # b-structure
    b_structure = ""

    filling = 0.3

    g0 = "G0 F9500 "
    g1 = "G1 F50 "

    count = 0

    for i in range(len(b_x)):
        count += 1
        b_structure += g0 + "X" + str(b_x[i]) + " Y" + str(b_y[i]) + "\n"
        b_structure += g1 + "X" + str(b_x[i]) + " Y" + str(b_y[i]) + " E" + str(filling) + "\n"

    print("--------")

    print(b_structure)

    print(len(b_x))
    print(count)

    return a_structure, b_structure


def unit_square_is_included(p, gap, coords):
    if [p[0] + gap, p[1]] not in coords:
        return False
    if [p[0], p[1] + gap] not in coords:
        return False
    if [p[0] + gap, p[1] + gap] not in coords:
        return False

    return True


if __name__ == "__main__":
    file_name = "./CE3_cube.gcode"
    target_layer = 10
    gap = 2
    a_x, a_y, b_x, b_y = get_grid_points_for_target_layer(file_name, target_layer, gap)

    generate_grid_infill(a_x, a_y, b_x, b_y, gap, file_name, target_layer)
    #get_grid_points_for_target_layer("./cylinder.gcode", 20, 2)
    #get_grid_points_for_target_layer("./bunny.gcode", 13, 2)
