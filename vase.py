import pandas as pd
import random
import math


def get_center_point():
    gcode = open("vase.txt", "r")

    lines = gcode.readlines()

    flag = "no"

    first_layer = ""

    for l in lines:
        if ";TYPE:WALL-OUTER" in l:
            flag = "yes"
        elif ";TYPE:SKIN" in l:
            flag = "skin"

        if flag == "yes":
            first_layer = first_layer + l
        elif flag == "skin":
            break

    lines = first_layer.split("\n")
    # first point
    first_x = float(lines[1].split(" ")[2].split("X")[1])  # x coordinate
    first_y = float(lines[1].split(" ")[3].split("Y")[1])  # y coordinate

    max_dist = 0

    farthest_point = []

    for i in range(2, len(lines)):
        l = lines[i]
        if "X" in l and "Y" in l:

            x = float(l.split("X")[1].split(" ")[0])  # x coordinate
            y = float(l.split("Y")[1].split(" ")[0])  # y coordinate

            dist = math.sqrt((first_x - x) ** 2 + (first_y - y) ** 2)

            if dist > max_dist:
                max_dist = dist
                farthest_point.clear()
                farthest_point.append(x)
                farthest_point.append(y)
        else:
            pass

    #print(max_dist)
    #print(farthest_point)

    midpoint_x = (first_x + farthest_point[0]) / 2
    midpoint_y = (first_y + farthest_point[1]) / 2

    return [midpoint_x, midpoint_y]


def modifying_gcode():

    gcode = open("vase.txt", "r")

    lines = gcode.readlines()

    center_point = get_center_point()

    flag = "no"

    result = ""
    '''
    for l in lines:
        #result = result+l
        if ";TYPE:WALL-OUTER" in l:
            flag = "yes"
        elif ";TYPE:" in l:
            flag = "no"

        if flag == "yes" and ";TYPE:WALL-OUTER" not in l:
            #print(l)

            splited = l.split(" ")

            #old_x = ""
            #old_y = ""
            new_x = ""
            new_y = ""

            for i in range(len(splited)):
                if "X" in splited[i]:
                    current_x = float(splited[i].split("X")[1])
                    direction_vector_x = current_x - center_point[0]
                    new_x = str(current_x + (direction_vector_x * random.randint(100, 130) / 100))
                    break
            for j in range(len(splited)):
                if "Y" in splited[j]:
                    current_y = float(splited[j].split("Y")[1])
                    direction_vector_y = current_y - center_point[0]
                    new_y = str(current_y + (direction_vector_y * random.randint(100, 130) / 100))
                    break

            replaced = ""

            for k in range(len(splited)):
                if k == i:
                    replaced += new_x + " "
                elif k == j:
                    replaced += new_y + " "
                else:
                    replaced += splited[k] + " "

            l = replaced

        result = result +"\n" + l

    text_file = open("randomized_vase_20_center.txt", "wt")
    text_file.write(result)
    text_file.close()
    '''


if __name__ == "__main__":
    modifying_gcode()
