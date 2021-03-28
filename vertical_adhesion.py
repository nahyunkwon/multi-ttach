import pandas as pd
import random
import math
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry.polygon import LinearRing, Polygon, Point
from maxrect import get_intersection, get_maximal_rectangle, rect2poly
from horizontal_adhesion import *


def heating_top_layer(file_name, layer_no):
    """
    after changing the filament,
    moves nozzle without extrusion to heat the previous layer.
    :param layer_no: target layer number
    :return: null
    """
    gcode = open(file_name, "r")
    pause = open("pause_code.txt","r")
    pauselines = pause.readlines()
    pausecode =""
    lines = gcode.readlines()
    layer_count = 0
    flag = "no"

    i = 0
    head = ""
    after_half_layer = ""
    half_layer = ""
    replaced = ""
    layer_flag = "no"
    goback = ""
    goback2 = ""

    # Get pausecode
    for p in pauselines:
        pausecode += p

    # Get total layer count
    for i in range(len(lines)):

        if ";LAYER_COUNT:" in lines[i]:
            countline = lines[i].split(":")
            layer_count = int(countline[1])
    # Get header part of code
    for l in lines:

        if ";LAYER:" + str(int(layer_no)) + "\n" in l:
            break
        else:
            head += l

    # Get layer to be repeated and remove the E commands
    for i in range(len(lines)):
        if ";LAYER:"+str(int(layer_no)) + "\n" in lines[i]:
            flag = "yes"

        elif ";LAYER:" in lines[i]:
            flag = "no"


        if flag == "yes":
            half_layer += lines[i]
            # Get co-ordinates of where the extruder paused and Z height
            if "Z" in lines[i]:
                split_goback = lines[i].split(" ")

                for j in range(len(split_goback)):
                    if "F" in split_goback[j]:
                        split_goback[j] = "F6000"
                    goback2 += split_goback[j] + " "
                    if "Z" in split_goback[j]:
                        current_z = float(split_goback[j].split("Z")[1])
                        new_z = current_z - 0.2
                        split_goback[j] = "Z"+str(new_z)
                    goback += split_goback[j] + " "

            split_layer = lines[i].split(" ")

            for k in range(len(split_layer)):
                if "E" in split_layer[k]:
                    split_layer[k]="\n"

            for j in range(len(split_layer)):
                replaced += split_layer[j] + " "



    #Get rest of the code
    for i in range(len(lines)):
        if ";LAYER:"+str(int(layer_no)+1) in lines[i]:
            layer_flag = "yes"
        if layer_flag == "yes":
            after_half_layer += lines[i]


    #print(layer_no)
    newcode = open(file_name.split(".gcode")[0] +"_heating.gcode", "wt")
    #withoutheat = open("dogbonewithoutheat.gcode", "wt")
    n = newcode.write(head + half_layer + pausecode + "\n" + goback + "\n" + "\n;REPEAT LAYER\n"+ replaced + after_half_layer)
    #m = withoutheat.write(head + half_layer + pausecode + "\n" + goback2 + "\n" + after_half_layer)
    #withoutheat.close()
    #newcode.close()


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


def get_all_polygons(x_values, y_values):
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
                #areas.append(Polygon(polygon_coords).area)
                all_polygons.append([polygon_coords, Polygon(polygon_coords).area])
                polygon_coords = []
        else:
            coord = [x_values[i], y_values[i]]
            if len(coord) != 0:
                polygon_coords.append(coord)

    polygons_df = pd.DataFrame(all_polygons, columns=['polygon', 'area'])

    polygons_df = polygons_df.sort_values(by=['area'], ascending=False)
    '''
    for i in range(len(polygons_df)):
        print(polygons_df.iloc[i]['polygon'])

    outer_poly = Polygon(polygons_df.iloc[0])
    for i in polygons_df.iloc[1]['polygon']:
        if not outer_poly.contains(i[0], i[1]):
            print(i)

 
    max_area = areas[0]
    max_index = 0

    for i in range(len(areas)):
        if areas[i] > max_area:
            max_area = areas[i]
            max_index = i
    '''
    #all_polygons_final = []
    #all_polygon_areas = []

    #for i in range(len(all_polygons)):
    #   if len(all_polygons[i]) != 0:
    #        all_polygons_final.append(all_polygons[i])
    #for i in range(len(polygons_df)):
    #    plt.fill(polygons_df.iloc[i]['polygon'])
    #plt.show()
    #return
    return polygons_df


def is_far_from_inner_wall(x, y, x_values, y_values, threshold):
    """
    determine if the point is fairly distant from points on polygon
    :param x: point_x
    :param y: point_y
    :param x_values: x coordinates of polygon
    :param y_values: y coordinates of polygon
    :param threshold: maximum distance
    :return: true or false
    """

    for k in range(len(x_values)):
        if math.hypot(x - x_values[k], y - y_values[k]) < threshold:
            return False

    return True


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


def get_zig_zag_for_lines_for_y(x, y):

    final = []
    line = []

    line.append([x[0], y[0]])

    for i in range(len(y) - 1):
        if y[i + 1] == y[i]:  # at the same line
            line.append([x[i + 1], y[i + 1]])
        elif y[i + 1] > y[i]:  # next line
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


def get_grid_points_for_target_layer(file, target_layer, gap):
    '''
    get grid points inside infill on the target layer
    :param file: gcode file location
    :param target_layer: target layer number
    :param gap: gap between grid points (mm)
    :return: lists of x coordinates and y coordinates of a-structure and b-structure
    '''

    gcode = open(file)

    lines = gcode.readlines()

    is_target = 0
    is_inner_wall = 0

    target_lines = ""

    for l in lines:
        if is_target == 1 and is_inner_wall == 1 and ";TYPE:" in l:
            is_inner_wall = 0
        if ";LAYER:" + str(target_layer)+"\n" in l:  # target layer
            is_target = 1
            target_lines += l
        if ";LAYER:" + str(target_layer+1)+"\n" in l:  # next layer
            break
        if is_target == 1 and ";TYPE:WALL-INNER" in l:
            is_inner_wall = 1
        if is_target == 1 and is_inner_wall == 1:
            target_lines += l

    x_values = []
    y_values = []
    #print(target_lines)

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

    # all polygons
    all_polygons_coords = get_all_polygons(x_values, y_values)

    set_a_x = []
    set_a_y = []
    set_b_x = []
    set_b_y = []

    #print(Polygon(all_polygons_coords.iloc[1]['polygon']).area)

    inner_polygons_index = []
    print(all_polygons_coords)

    for index in range(len(all_polygons_coords)):
        if index in inner_polygons_index:
            print("inner-polygon", index)
            pass
        else:
            polygon = all_polygons_coords.iloc[index]['polygon']
            inner_polygons = []

            for a in range(index + 1, len(all_polygons_coords)):
                smaller_polygon = all_polygons_coords.iloc[a]['polygon']

                is_in = True
                for b in range(len(smaller_polygon)):
                    if not Polygon(polygon).contains(Point([smaller_polygon[b][0], smaller_polygon[b][1]])):
                        is_in = False
                        print(smaller_polygon[b])

                if is_in:
                    inner_polygons.append(smaller_polygon)
                    inner_polygons_index.append(a)

            polygon.append(polygon[0])

            # print(polygon_coords)

            x_values = []
            y_values = []

            for i in range(len(polygon)):
                x_values.append(polygon[i][0])
                y_values.append(polygon[i][1])

            # print(polygon.area)

            x_min, x_max = get_min_max(x_values)
            y_min, y_max = get_min_max(y_values)

            grid_x = []
            grid_y = []

            current_x = x_min + gap / 2.2
            current_y = y_min + gap / 2.2
            # print(x_min)
            # print(y_min)

            grid_x.append(current_x)
            grid_y.append(current_y)

            while current_x <= x_max:
                current_x += gap
                grid_x.append(current_x)
            while current_y <= y_max:
                current_y += gap
                grid_y.append(current_y)

            # print(grid_x)
            # print(grid_y)

            # a structure
            a_x = []
            a_y = []

            polygon = Polygon(polygon)

            for i in range(len(grid_x)):
                for j in range(len(grid_y)):
                    current_point = Point(grid_x[i], grid_y[j])

                    if polygon.contains(current_point):

                        if is_far_from_inner_wall(current_point.x, current_point.y, x_values, y_values, threshold=1):
                            if len(inner_polygons) > 0:  # has inner polygons
                                for inner_poly in inner_polygons:
                                    if not Polygon(inner_poly).contains(Point(current_point.x, current_point.y)):
                                        a_x.append(current_point.x)
                                        a_y.append(current_point.y)

                            else:  # no inner polygon
                                a_x.append(current_point.x)
                                a_y.append(current_point.y)

            a_coords = []  # coordinates of a structure

            for i in range(len(a_x)):
                a_coords.append([a_x[i], a_y[i]])

            # print(a_coords)

            # print(sorted(a_coords, key=lambda x: x[1]))

            # x and y values for b structure
            b_x = []
            b_y = []

            # check if the unit square is included in the polygon
            for i in range(len(a_coords)):
                if unit_square_is_included(a_coords[i], gap, a_coords):
                    b_x.append(a_coords[i][0] + gap / 2)
                    b_y.append(a_coords[i][1] + gap / 2)

            # plt.plot(x_values, y_values, linewidth=0.2)
            plt.plot(a_x, a_y, 'bo', markersize=0.1)
            plt.plot(b_x, b_y, 'go')
            plt.show()

            set_a_x.append(a_x)
            set_a_y.append(a_y)
            set_b_x.append(b_x)
            set_b_y.append(b_y)

        #return a_x, a_y, b_x, b_y

    #print(len(set_a_x), len(set_a_y), len(set_b_x), len(set_b_y))


    #plt.plot(set_a_x, set_a_y, 'bo', markersize=0.1)
    #plt.plot(set_b_x, set_b_y, 'go')
    #plt.show()

    #for i in range(len(set_a_x)):
    #    plt.plot(set_a_x[i], set_a_y[i], 'bo')
    #for i in range(len(set_b_x)):
    #    plt.plot(set_b_x[i], set_b_y[i], 'ro')

    #plt.show()

    return set_a_x, set_a_y, set_b_x, set_b_y


def generate_grid_infill(a_x, a_y, b_x, b_y, gap):

    arbitrary = 0.08  # arbitrary number to optimize extrusion amount

    # a-structure

    g0 = "G0 F5000 "
    g1 = "G1 F500 "

    a_structure = ""

    layer_height = 0.2
    nozzle_dia = 0.4
    length = gap
    fa = ((1.75/2) ** 2) / math.pi

    extrusion = (layer_height * nozzle_dia * length * arbitrary) / fa

    try:
        a_structure += g0 + "X" + str(a_x[0]) + " Y" + str(a_y[0]) + "\n"
    except IndexError:
        return "", ""

    a_final = get_zig_zag_for_lines(a_x, a_y)

    for i in range(len(a_x)):
        if i + 1 < len(a_x):
            if a_final[i + 1][0] == a_final[i][0]:  # at the same line (y-axis)
                if abs(a_final[i + 1][1] - a_final[i][1]) <= gap+0.1:
                    a_structure += g1 + "X" + str(a_final[i + 1][0]) + " Y" + str(a_final[i + 1][1]) + " E" + str(extrusion) + "\n"
                else:
                    a_structure += g0 + "X" + str(a_final[i + 1][0]) + " Y" + str(a_final[i + 1][1]) + "\n"
            elif a_final[i + 1][0] > a_final[i][0]:  # next line
                a_structure += g0 + "X" + str(a_final[i + 1][0]) + " Y" + str(a_final[i + 1][1]) + "\n"

    a_structure += g0 + "X" + str(a_final[0][0]) + " Y" + str(a_final[0][1]) + "\n"

    a_coords = []  # coordinates of a structure

    for i in range(len(a_x)):
        a_coords.append([a_x[i], a_y[i]])

    y_sorted = sorted(a_coords, key=lambda k: k[1])

    a_structure += g0 + "X" + str(a_x[0]) + " Y" + str(a_y[0]) + "\n"

    #print(y_sorted)

    v_x = []
    v_y = []

    for i in range(len(y_sorted)):
        v_x.append(y_sorted[i][0])
        v_y.append(y_sorted[i][1])

    v_final = get_zig_zag_for_lines_for_y(v_x, v_y)

    for i in range(len(v_final)):
        if i + 1 < len(v_final):
            if v_final[i + 1][1] == v_final[i][1]:  # at the same line (x-axis)
                if v_final[i + 1][0] - v_final[i][0] == gap:
                    a_structure += g1 + "X" + str(v_final[i + 1][0]) + " Y" + str(v_final[i + 1][1]) + " E" + str(extrusion) + "\n"
                else:
                    a_structure += g0 + "X" + str(v_final[i + 1][0]) + " Y" + str(v_final[i + 1][1]) + "\n"
            elif a_x[i + 1] > a_x[i]:  # next line
                a_structure += g0 + "X" + str(v_final[i + 1][0]) + " Y" + str(v_final[i + 1][1]) + "\n"

    # b-structure
    b_structure = ""

    filling = 0.9  # optimized amount (by experiments) of extrusion for filling empty spaces of grid

    g0 = "G0 F5000 "
    g1 = "G1 F50 "

    count = 0

    for i in range(len(b_x)):
        count += 1
        b_structure += g0 + "X" + str(b_x[i]) + " Y" + str(b_y[i]) + "\n"
        b_structure += g1 + "X" + str(b_x[i]) + " Y" + str(b_y[i]) + " E" + str(filling) + "\n"

    return a_structure, b_structure


def generate_full_infill(a_x, a_y, gap=0.6):

    arbitrary = 0.2  # arbitrary number to optimize extrusion amount

    # a-structure

    g0 = "G0 F2000 "
    g1 = "G1 F500 "

    a_structure = ""

    layer_height = 0.2
    nozzle_dia = 0.4
    length = gap
    fa = ((1.75 / 2) ** 2) / math.pi

    extrusion = (layer_height * nozzle_dia * length * arbitrary) / fa

    #a_structure += g0 + "X" + str(a_x[0]) + " Y" + str(a_y[0]) + "\n"
    try:
        a_structure += g0 + "X" + str(a_x[0]) + " Y" + str(a_y[0]) + "\n"
    except IndexError:
        return ""

    for i in range(len(a_x)):
        if i + 1 < len(a_x):
            if a_x[i + 1] == a_x[i]:  # at the same line (y-axis)
                #a_structure += g1 + "X" + str(a_x[i + 1]) + " Y" + str(a_y[i + 1]) + " E" + str(extrusion) + "\n"
                print(abs(a_y[i + 1] - a_y[i]))
                if abs(a_y[i + 1] - a_y[i]) <= gap+0.2:
                    a_structure += g1 + "X" + str(a_x[i + 1]) + " Y" + str(a_y[i + 1]) + " E" + str(extrusion) + "\n"
                else:
                    a_structure += g0 + "X" + str(a_x[i + 1]) + " Y" + str(a_y[i + 1]) + "\n"
            elif a_x[i + 1] > a_x[i]:  # next line
                a_structure += g0 + "X" + str(a_x[i + 1]) + " Y" + str(a_y[i + 1]) + "\n"

    a_structure += g0 + "X" + str(a_x[0]) + " Y" + str(a_y[0]) + "\n"

    return a_structure


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

    #print(a_final)
    #print(b_final)

    # a-structure
    g0 = "G0 F1000 "
    g1 = "G1 F50 "

    a_structure = ""
    b_structure = ""

    extrusion = 0.7  # extrusion amount optimized by experiment

    for i in range(len(a_final)):
        if i + 1 < len(a_final):
            a_structure += g1 + "X" + str(a_final[i][0]) + " Y" + str(a_final[i][1]) + " E" + str(extrusion) + "\n"
            a_structure += g0 + "X" + str(a_final[i][0]) + " Y" + str(a_final[i][1]) + " Z" + str(new_z) + "\n"
            a_structure += g0 + "X" + str(a_final[i][0]) + " Y" + str(a_final[i + 1][1]) + " Z" + str(current_z) + "\n"

    a_structure += g1 + "X" + str(a_final[-1][0]) + " Y" + str(a_final[-1][1]) + " E" + str(extrusion) + "\n"
    a_structure += g0 + "X" + str(a_final[-1][0]) + " Y" + str(a_final[-1][1]) + " Z" + str(new_z) + "\n"

    for i in range(len(b_final)):
        if i + 1 < len(b_final):
            b_structure += g1 + "X" + str(b_final[i][0]) + " Y" + str(b_final[i][1]) + " E" + str(extrusion) + "\n"
            b_structure += g0 + "X" + str(b_final[i][0]) + " Y" + str(b_final[i][1]) + " Z" + str(new_z) + "\n"
            b_structure += g0 + "X" + str(b_final[i + 1][0]) + " Y" + str(b_final[i][1]) + " Z" + str(current_z) + "\n"

    b_structure += g1 + "X" + str(b_final[-1][0]) + " Y" + str(b_final[-1][1]) + " E" + str(extrusion) + "\n"
    b_structure += g0 + "X" + str(b_final[-1][0]) + " Y" + str(b_final[-1][1]) + " Z" + str(new_z) + "\n"

    return a_structure, b_structure


def replace_infill_to_adhesion_structure(file_name, target_layer, type, temp, no_extruder, flag):
    """

    :param file_name:
    :param target_layer:
    :param type:
    :param temp:
    :param no_extruder:
    :param flag:
    :return:
    """
    gcode = open(file_name)

    if no_extruder == 1:  # single extruder
        pause_code_lines = open("./pause_code.txt").readlines()

        pause_code = ""

        for p in pause_code_lines:
            pause_code += p
            if ";temp change" in p and str(temp) != "-1":  # if temp == -1, no need to add temp change code
                pause_code += "M104 S" + str(temp) + "\nM105\nM109 S" + str(temp) + "\n"

    elif no_extruder == 2:  # dual extruder
        pause_code = ""

    lines = gcode.readlines()

    gap = 2  # gap for a and b structure
    set_a_x, set_a_y, set_b_x, set_b_y = get_grid_points_for_target_layer(file_name, target_layer, gap)
    set_f_x, set_f_y, unused1, unused1 = get_grid_points_for_target_layer(file_name, target_layer, gap=0.6)

    a_structure = ""
    b_structure = ""
    full_structure = ""

    for i in range(len(set_a_x)):
        a_x = set_a_x[i]
        a_y = set_a_y[i]
        b_x = set_b_x[i]
        b_y = set_b_y[i]
        if type == "grid":
            single_a_structure, single_b_structure = generate_grid_infill(a_x, a_y, b_x, b_y, gap)
        if type == "blob":
            single_a_structure, single_b_structure = generate_blob_infill(a_x, a_y, b_x, b_y, gap, file_name, target_layer)
        a_structure += single_a_structure
        b_structure += single_b_structure
    for i in range(len(set_f_x)):
        f_x = set_f_x[i]
        f_y = set_f_y[i]
        single_full_structure = generate_full_infill(f_x, f_y)
        full_structure += single_full_structure

    is_target = 0
    is_mesh = 0

    mesh = ""

    pop_list = []
    index = 0
    # get mesh code of the target layer
    for l in lines:
        if ";LAYER:" + str(target_layer) + "\n" in l:
            is_target = 1
        if ";MESH:NONMESH" in l and is_target == 1:
            is_mesh = 1

        if is_target == 1 and is_mesh == 1:
            if ";TIME_ELAPSED:" in l:
                break
            mesh += l
            pop_list.append(index)

        index += 1

    lines_a = lines
    lines = []
    for i in range(len(lines_a)):
        if i not in pop_list:
            lines.append(lines_a[i])

    mesh_f_replaced = ""

    for m in mesh.split("\n"):
        if "F300" in m:
            m = m.replace("F300", "F9500")
        if "Z" in m and type == "blob":
            z = m.split("Z")[1]
            new_z = float(z) - 0.2
            m = m.replace("Z" + str(z), "Z" + str(round(new_z, 2)))
        mesh_f_replaced += m + "\n"

    is_target = 0
    is_infill = 0

    modified = ""

    is_b = 0

    mesh_each = ""
    is_mesh = 0
    start = 0

    final = ""

    # grid structure
    if type == "grid":
        # target layers that need to remove infill commands
        target_layers = [target_layer - 3, target_layer - 2, target_layer - 1, target_layer, target_layer + 1, target_layer + 2]
        a_structure_layers = [target_layer - 2, target_layer - 1, target_layer]
        layer = 0

        for l in lines:
            if ";LAYER:" in l:
                layer = int(l.split(":")[1].strip())
                is_infill = 0
            if layer in target_layers:
                is_target = 1
            else:
                is_target = 0

            #if layer == target_layer + 1:  # b-structure
            #    is_b = 1

            if is_target == 1:
                if ";TYPE:FILL" in l or ";TYPE:SKIN" in l:
                    #if infill_start == 0:
                    is_infill = 1
                        #infill_start = 1  # start of infill

            if is_infill == 1 and ";" in l:
                if ";TYPE:FILL" in l or ";TYPE:SKIN" in l:
                    pass
                else:
                    is_infill = 0

            if is_infill == 1:
                pass
            elif ";LAYER:" + str(target_layer + 1) + "\n" in l:  # b-structure
                final += mesh
                final += "\n;PAUSE-CODE\n" + pause_code + "\n"
                final += mesh_f_replaced
                final += l
                final += ";TYPE:GRID-B-STRUCTURE\n" + b_structure
                final += ";TYPE:GRID-FULL-IN-B-STRUCTURE\n" + full_structure  # full infill for b-structure
            elif layer in a_structure_layers and ";LAYER:" in l:  # a-structure
                final += l
                final += ";TYPE:GRID-A-STRUCTURE\n" + a_structure
            elif ";LAYER:" + str(target_layer - 3) + "\n" in l or ";LAYER:" + str(target_layer + 2) + "\n" in l:  # full infill
                final += l
                final += ";TYPE:FULL-STRUCTURE\n" + full_structure
            else:
                final += l

        if flag == 0:  # only one interface
            with open(file_name.split(".gcode")[0] + "_grid.gcode", "w") as f:
                f.write(final)
        elif flag == 1:  # multiple interfaces
            with open(file_name, "w") as f:
                f.write(final)

    # blob structure
    elif type == "blob":
        target_layers = [target_layer - 1, target_layer, target_layer + 1,
                         target_layer + 2]
        a_structure_layers = [target_layer]
        layer = 0

        for l in lines:
            if ";LAYER:" in l:
                layer = int(l.split(":")[1].strip())
                is_infill = 0
            if layer in target_layers:
                is_target = 1
            else:
                is_target = 0

            # if layer == target_layer + 1:  # b-structure
            #    is_b = 1

            if is_target == 1:
                if ";TYPE:FILL" in l or ";TYPE:SKIN" in l:
                    # if infill_start == 0:
                    is_infill = 1
                    # infill_start = 1  # start of infill

            if is_infill == 1 and ";" in l:
                if ";TYPE:FILL" in l or ";TYPE:SKIN" in l:
                    pass
                else:
                    is_infill = 0

            if is_infill == 1:
                pass
            elif ";LAYER:" + str(target_layer + 1) + "\n" in l:  # b-structure
                final += mesh
                final += "\n;PAUSE-CODE\n" + pause_code + "\n"
                final += mesh_f_replaced
                final += l
                final += ";TYPE:BLOB-B-STRUCTURE\n" + b_structure
            elif layer in a_structure_layers and ";LAYER:" in l:  # a-structure
                final += l
                final += ";TYPE:BLOB-A-STRUCTURE\n" + a_structure
            elif ";LAYER:" + str(target_layer - 1) + "\n" in l or ";LAYER:" + str(target_layer + 2) + "\n" in l:  # full infill
                final += l
                final += ";TYPE:FULL-STRUCTURE\n" + full_structure
            else:
                final += l

        if flag == 0:
            with open(file_name.split(".gcode")[0] + "_blob.gcode", "w") as f:
                f.write(final)
        elif flag == 1:
            with open(file_name, "w") as f:
                f.write(final)


def unit_square_is_included(p, gap, coords):

    if [p[0] + gap, p[1]] not in coords:
        return False
    if [p[0], p[1] + gap] not in coords:
        return False
    if [p[0] + gap, p[1] + gap] not in coords:
        return False

    return True


def find_target_layers_for_dual_extruder(filename):
    target_l = []
    dualcode = open(filename)
    lines = dualcode.readlines()
    in_layers = 0
    right_tool = 0
    left_tool = 0
    tool_change = 0
    for l in lines:
        if "M135 T0" in l and in_layers == 0:
            right_tool = 1
            left_tool = 0
        if "M135 T1" in l and in_layers ==0:
            right_tool = 0
            left_tool = 1
        if ";LAYER:0" in l:
            in_layers = 1
            #print("layer 0")
        if "M135 T0" in l and left_tool == 0 and in_layers == 1:
            tool_change = 0
            right_tool = 1
            print("right tool")
        if "M135 T1" in l and right_tool == 0 and in_layers == 1:
            tool_change = 0
            left_tool = 1
            print("left tool")
        if "M135 T0" in l and left_tool == 1 and in_layers == 1:
            tool_change = 1
            right_tool = 1
            left_tool = 0
            print("tool-change right tool")
        if "M135 T1" in l and right_tool == 1 and in_layers == 1:
            tool_change = 1
            left_tool = 1
            right_tool = 0
            print("tool-change left tool")
        if tool_change == 1 and ";LAYER:" in l:
            target_no = int(l.split(":")[1])
            #print(target_no)
            tool_change = 0
            target_no -= 2
            target_l.append(target_no)
            print("target_no", target_no)
    return target_l


def adhesion_structure_vertical(file_name, adhesion_type, target_layers, temps, no_extruder):
    """
    Generate adhesion structure for vertical adhesion
    :param file_name: source gcode file
    :param adhesion_type: "blob" or "grid"
    :param materials: material list in sequential order
    :param target_layers: interface layer numbers (the first element is always 0)
    :param temps: temperature list in sequential order
    :param no_extruder: the number of extruder. single(1) or dual(2)
    :return: none
    """

    #target_layers.sort()
    #target_layers = target_layers[1:]  # remove layer:0
    #temps = temps[1:]

    # only on interface
    replace_infill_to_adhesion_structure(file_name, target_layers[0], adhesion_type, temps[0], no_extruder, flag=0)

    if len(target_layers) > 1:  # muptiple interfaces
        for i in range(1, len(target_layers)):
            replace_infill_to_adhesion_structure(file_name.split(".gcode")[0] + "_" + adhesion_type + ".gcode",
                                                 target_layers[i], adhesion_type, temps[i], no_extruder, flag=1)


def adhesion_structure_vertical_for_dual_extruder(file_name, adhesion_type, no_extruder=2):
    """
    Generate adhesion structure for vertical adhesion
    :param file_name: source gcode file
    :param adhesion_type: "blob" or "grid"
    :param materials: material list in sequential order
    :param target_layers: interface layer numbers (the first element is always 0)
    :param temps: temperature list in sequential order
    :param no_extruder: the number of extruder. single(1) or dual(2)
    :return: none
    """

    target_layers_dual = find_target_layers_for_dual_extruder(file_name)
    target_layers = []
    for i in target_layers_dual:
        if adhesion_type == "grid":
            if i > 4:
                target_layers.append(i)
        elif adhesion_type == "blob":
            if i > 2:
                target_layers.append(i)
    #print(len(target_layers))
    #target_layers.sort()
    #target_layers = target_layers[1:]  # remove layer:0

    if len(target_layers) == 1:  # only one interface
        replace_infill_to_adhesion_structure(file_name, target_layers[0], adhesion_type, temp=-1, no_extruder=2, flag=0)

    if len(target_layers) > 1:  # muptiple interfaces
        for i in range(1, len(target_layers)):
            replace_infill_to_adhesion_structure(file_name.split(".gcode")[0] + "_" + adhesion_type + ".gcode",
                                                 target_layers[i], adhesion_type, temp=-1, no_extruder=2, flag=1)


if __name__ == "__main__":
    #adhesion_structure_vertical_for_dual_extruder("gcode_dual/FCPRO_gripper.gcode", "blob")

    #replace_infill_to_adhesion_structure("gcode_dual/FCPRO_gripper.gcode", 3, "blob", temp=-1, no_extruder=2, flag=0)
    #adhesion_structure_vertical("gcode/PLA-NYLON_3.gcode")

    adhesion_structure_vertical(file_name="gcode/PLA-NYLON_3.gcode", adhesion_type="blob", target_layers=[127], temps=[230], no_extruder=1)