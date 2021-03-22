import pandas as pd
import random
import math
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry.polygon import LinearRing, Polygon, Point
from maxrect import get_intersection, get_maximal_rectangle, rect2poly
from vertical_adhesion import *


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


def adhesion_structure_horizontal(file_name):
    gcode = open(file_name)

    lines = gcode.readlines()

    # get inner wall
    extruder = 0
    layer = 0
    is_inner_wall = 0
    inner_walls = []
    layer_count = 0
    all_layers = []

    set = ""

    for l in lines:
        if "T0" in l:
            extruder = 0
        elif "T1" in l:
            extruder = 1
        elif ";LAYER:" in l:
            layer = int(l.split(":")[1].strip())

        if ";TYPE:WALL-INNER" in l:
            is_inner_wall = 1
        elif is_inner_wall == 1 and ";TYPE:" in l:
            is_inner_wall = 0

        if is_inner_wall == 1:
            if len(inner_walls) == 0:
                set += l
                inner_walls.append([layer, extruder, set])
            else:
                if inner_walls[-1][0] == layer and inner_walls[-1][1] == extruder:
                    set += l
                    inner_walls[-1][2] = set
                else:
                    set = l
                    inner_walls.append([layer, extruder, set])

            # inner_walls.append([layer, extruder, l])
            all_layers.append([layer, extruder])

        if ";LAYER_COUNT:" in l:
            layer_count = int(l.split(":")[-1].strip())

    # get multimaterial layers
    layers_drop_dups = []

    for i in all_layers:
        if i not in layers_drop_dups:
            layers_drop_dups.append(i)

    layer_df = pd.DataFrame(layers_drop_dups, columns=['layer', 'extruder'])

    layer_df = layer_df.groupby(['layer']).size().reset_index(name='count')

    multi_layers_number = []

    for i in range(len(layer_df)):
        if layer_df.iloc[i]['count'] > 1:
            multi_layers_number.append(layer_df.iloc[i]['layer'])

    first_or_last = []
    excluded_layers = [0, 1, 2, 3, 4,
                       layer_count - 1, layer_count - 2, layer_count - 3, layer_count - 4, layer_count - 5]

    for i in excluded_layers:
        multi_layers_number.remove(i)

    # get inner walls of multimaterial layers
    multi_inner_walls = []

    for i in range(len(inner_walls)):
        if inner_walls[i][0] in multi_layers_number:  # if the layer contains two materials
            multi_inner_walls.append(inner_walls[i])

    flag = 0
    points_0 = []
    points_1 = []

    # for i in range(len(infills)):
    #   points_0 = []
    #  points_1 = []
    #       print(infills)

    # get outer wall
    is_outer_wall = 0
    extruder = 0
    layer = 0
    set = ""

    outer_walls = []

    for l in lines:
        if "T0" in l:
            extruder = 0
        elif "T1" in l:
            extruder = 1
        elif ";LAYER:" in l:
            layer = int(l.split(":")[1].strip())

        if layer in multi_layers_number:
            if ";TYPE:WALL-OUTER" in l:
                is_outer_wall = 1
            elif is_outer_wall == 1 and ";" in l:
                is_outer_wall = 0

            if is_outer_wall == 1:
                # outer_walls.append([layer, extruder, l])
                if len(outer_walls) == 0:
                    set += l
                    outer_walls.append([layer, extruder, set])
                else:
                    if outer_walls[-1][0] == layer and outer_walls[-1][1] == extruder:
                        set += l
                        outer_walls[-1][2] = set
                    else:
                        set = l
                        outer_walls.append([layer, extruder, set])
                        set = ""

    # plt.plot(x_values, y_values, 'ro')
    # plt.plot(a_x, a_y, 'bo')
    # plt.plot(b_x, b_y, 'go')
    # plt.show()
    inner_walls_df = pd.DataFrame(multi_inner_walls, columns=['layer', 'extruder', 'commands'])
    outer_walls_df = pd.DataFrame(outer_walls, columns=['layer', 'extruder', 'commands'])

    # for i in range(len(outer_walls_df)):
    #    print(outer_walls_df.iloc[i]['commands'])

    # polygons_x_list = []
    # polygons_y_list = []
    polygons_list = []

    for i in range(len(outer_walls)):
        commands = outer_walls[i][2].split("\n")
        extruder = outer_walls[i][1]

        polygons_list.append(get_polygons_of_wall(commands))

    outer_walls_df['polygons'] = polygons_list

    polygons_list = []

    for i in range(len(multi_inner_walls)):
        commands = multi_inner_walls[i][2].split("\n")
        extruder = multi_inner_walls[i][1]

        polygons_list.append(get_polygons_of_wall(commands))

    inner_walls_df['polygons'] = polygons_list

    stitches_per_layer = []

    dist = 0.4  # nozzle diameter, the maximum gap to find adjacent points

    #----------------------------------------------
    i = 10
    current_outer_walls_df = outer_walls_df.loc[outer_walls_df['layer'] == i]
    current_inner_walls_df = inner_walls_df.loc[inner_walls_df['layer'] == i]

    adjacency_set = []

    # first material
    polygons_0 = current_outer_walls_df.iloc[0]['polygons']
    # second material
    polygons_1 = current_outer_walls_df.iloc[1]['polygons']

    # inner polygons
    inner_polygon_0 = current_inner_walls_df.iloc[0]['polygons']
    inner_polygon_1 = current_inner_walls_df.iloc[1]['polygons']

    pairs = []

    print(inner_polygon_0)
    print(inner_polygon_1)
    all_the_points = []

    for poly in inner_polygon_0:
        for point in poly:
            all_the_points.append(point)
    for poly in inner_polygon_1:
        for point in poly:
            all_the_points.append(point)

    print(all_the_points)

    inner_x = []
    inner_y = []

    #for point


    # find material 0 - material 1 pairs
    for j in range(len(polygons_0)):
        for k in range(len(polygons_1)):
            pairs.append([j, k])

    # print(pairs)

    adjacency = []

    for j in range(len(pairs)):
        p_0 = polygons_0[pairs[j][0]]
        p_1 = polygons_1[pairs[j][1]]

        for k in range(len(p_0)):
            for l in range(len(p_1)):
                if math.hypot(p_0[k][0] - p_1[l][0], p_0[k][1] - p_1[l][1]) <= dist:
                    # print(math.hypot(p_0[k][0] - p_1[l][0], p_0[k][1] - p_1[l][1]))
                    if p_0[k] not in adjacency:
                        adjacency.append(p_0[k])
                    if p_1[l] not in adjacency:
                        adjacency.append(p_1[l])

        if len(adjacency) != 0:
            adjacency_set.append(adjacency)
        adjacency = []

    # print(adjacency_set)

    '''
    for i in multi_layers_number:

        current_outer_walls_df = outer_walls_df.loc[outer_walls_df['layer'] == i]
        current_inner_walls_df = inner_walls_df.loc[inner_walls_df['layer'] == i]

        adjacency_set = []

        # first material
        polygons_0 = current_outer_walls_df.iloc[0]['polygons']
        # second material
        polygons_1 = current_outer_walls_df.iloc[1]['polygons']

        # inner polygons
        inner_polygon_0 = current_inner_walls_df.iloc[0]['polygons']
        inner_polygon_1 = current_inner_walls_df.iloc[1]['polygons']

        pairs = []

        print(polygons_0)
        print(polygons_1)
        # find material 0 - material 1 pairs
        for j in range(len(polygons_0)):
            for k in range(len(polygons_1)):
                pairs.append([j, k])

        # print(pairs)

        adjacency = []

        for j in range(len(pairs)):
            p_0 = polygons_0[pairs[j][0]]
            p_1 = polygons_1[pairs[j][1]]

            for k in range(len(p_0)):
                for l in range(len(p_1)):
                    if math.hypot(p_0[k][0] - p_1[l][0], p_0[k][1] - p_1[l][1]) <= dist:
                        # print(math.hypot(p_0[k][0] - p_1[l][0], p_0[k][1] - p_1[l][1]))
                        if p_0[k] not in adjacency:
                            adjacency.append(p_0[k])
                        if p_1[l] not in adjacency:
                            adjacency.append(p_1[l])

            if len(adjacency) != 0:
                adjacency_set.append(adjacency)
            adjacency = []

        # print(adjacency_set)

        stitches = ";TYPE:STITCH\n"

        for j in range(len(adjacency_set)):
            adj_points = adjacency_set[j]

            x_min = 0
            y_min = 0
            x_max = 0
            y_max = 0

            x_values = []
            y_values = []
            # print(adj_points)
            for k in range(len(adj_points)):
                x_values.append(adj_points[k][0])
                y_values.append(adj_points[k][1])

            x_min, x_max = get_min_max(x_values)
            y_min, y_max = get_min_max(y_values)

            fair_dist = 3
            fair_dist_to_outer = 1.2

            # direction = 0  # 0: horizontal, 1: vertical

            if x_max - x_min < y_max - y_min:
                direction = 0
            else:
                direction = 1

            if direction == 0:  # horizontal alignment
                x_min -= fair_dist
                x_max += fair_dist
                y_min += fair_dist_to_outer
                y_max -= fair_dist_to_outer

            elif direction == 1:  # vertical alignment
                x_min += fair_dist_to_outer
                x_max -= fair_dist_to_outer
                y_min -= fair_dist
                y_max += fair_dist

            stitch_x, stitch_y = generate_adjacent_stitch(x_min, x_max, y_min, y_max, direction)

            stitch = generate_full_infill_for_horizontal_stitch(stitch_x, stitch_y, direction)
            stitches += stitch

        stitches_per_layer.append([i, stitches])

    stitch_df = pd.DataFrame(stitches_per_layer, columns=['layer', 'stitch'])

    # print(len(stitch_df))

    # get final gcode
    final = ""
    stitch = ""

    for l in lines:

        if ";LAYER:" in l:
            layer = int(l.split(":")[1].strip())

        if ";MESH:NONMESH" in l and layer in multi_layers_number:
            stitch = stitch_df.loc[stitch_df['layer'] == int(layer)].iloc[0][1]
            final += stitch

        final += l

    with open(file_name.split(".gcode")[0] + "_stitched.gcode", "w") as f:
        f.write(final)
        
    '''


def generate_full_infill_for_horizontal_stitch(a_x, a_y, direction, gap=0.2):

    arbitrary = 0.4  # arbitrary number to optimize extrusion amount

    # a-structure

    g0 = "G0 F9500 "
    g1 = "G1 F2000 "

    stitch_structure = ""

    layer_height = 0.2
    nozzle_dia = 0.4
    length = gap
    fa = ((1.75 / 2) ** 2) / math.pi

    extrusion = (layer_height * nozzle_dia * length * arbitrary) / fa

    if direction == 1:
        stitch_structure += g0 + "X" + str(a_x[0]) + " Y" + str(a_y[0]) + "\n"

        for i in range(len(a_x)):
            if i + 1 < len(a_x):
                if a_x[i + 1] == a_x[i]:  # at the same line (y-axis)
                    stitch_structure += g1 + "X" + str(a_x[i + 1]) + " Y" + str(a_y[i + 1]) + " E" + str(extrusion) + "\n"
                elif a_x[i + 1] > a_x[i]:  # next line
                    stitch_structure += g0 + "X" + str(a_x[i + 1]) + " Y" + str(a_y[i + 1]) + "\n"

        # a_structure += g0 + "X" + str(a_x[0]) + " Y" + str(a_y[0]) + "\n"

    elif direction == 0:
        stitch_structure += g0 + "X" + str(a_x[0]) + " Y" + str(a_y[0]) + "\n"

        for i in range(len(a_y)):
            if i + 1 < len(a_y):
                if a_y[i + 1] == a_y[i]:  # at the same line (x-axis)
                    stitch_structure += g1 + "X" + str(a_x[i + 1]) + " Y" + str(a_y[i + 1]) + " E" + str(extrusion) + "\n"
                elif a_y[i + 1] > a_y[i]:  # next line
                    stitch_structure += g0 + "X" + str(a_x[i + 1]) + " Y" + str(a_y[i + 1]) + "\n"

        # a_structure += g0 + "X" + str(a_x[0]) + " Y" + str(a_y[0]) + "\n"

    return stitch_structure


def generate_adjacent_stitch(x_min, x_max, y_min, y_max, direction):
    grid_points = []

    gap = 0.6

    grid_x = []
    grid_y = []

    current_x = x_min
    current_y = y_min

    grid_x.append(current_x)
    grid_y.append(current_y)

    while current_x <= x_max:
        current_x += gap
        grid_x.append(current_x)
    while current_y <= y_max:
        current_y += gap
        grid_y.append(current_y)

    a_x = []
    a_y = []

    # print(x_min, x_max, y_min, y_max)

    if direction == 1:
        for i in range(len(grid_x)):
            for j in range(len(grid_y)):
                a_x.append(grid_x[i])
                a_y.append(grid_y[j])
    elif direction == 0:
        for i in range(len(grid_y)):
            for j in range(len(grid_x)):
                a_x.append(grid_x[j])
                a_y.append(grid_y[i])
    # print(a_x)
    # print(a_y)

    return a_x, a_y


def get_polygons_of_wall(commands):
    g1_x = []
    g1_y = []

    # g0_x = []
    # g0_y = []

    polygons_x = []
    polygons_y = []
    flag = 0

    for c in commands:
        if "G1" in c:
            flag = 0
            words = c.split(" ")
            for w in words:
                if "X" in w:
                    flag = 0
                    g1_x.append(float(w.split("X")[1]))
                elif "Y" in w:
                    g1_y.append(float(w.split("Y")[1]))
        elif "G0" in c and flag == 0:  # next polygon
            flag = 1
            polygons_x.append(g1_x)
            polygons_y.append(g1_y)

            g1_x = []
            g1_y = []
        elif "G0" in c and flag == 1:
            pass

    # print(polygons_x)
    # print(polygons_y)

    polygons = []
    poly = []

    for i in range(len(polygons_x)):

        for j in range(len(polygons_x[i])):
            poly.append([polygons_x[i][j], polygons_y[i][j]])

        polygons.append(poly)
        poly = []
    # print(polygons)
    # return polygons_x, polygons_y
    return polygons


