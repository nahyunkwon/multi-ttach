import pandas as pd
import random


def modifying_gcode():
    gcode = open("vase.txt", "r")

    lines = gcode.readlines()

    flag = "no"

    result = ""

    for l in lines:
        #result = result+l
        if ";TYPE:WALL-OUTER" in l:
            flag = "yes"
        elif ";TYPE:" in l:
            flag = "no"

        if flag == "yes" and ";TYPE:WALL-OUTER" not in l:
            #print(l)

            splited = l.split(" ")

            old_x = ""
            old_y = ""
            new_x = ""
            new_y = ""

            for i in range(len(splited)):
                if "X" in splited[i]:
                    old_x = splited[i].split("X")[1]
                    new_x = str(float(splited[i].split("X")[1]) * random.randint(100, 120) / 100)
                    break
            for j in range(len(splited)):
                if "Y" in splited[j]:
                    old_y = splited[j].split("Y")[1]
                    new_y = str(float(splited[j].split("Y")[1]) * random.randint(100, 120) / 100)
                    break


            replaced = ""
            for k in range(len(splited)):
                if k == i:
                    replaced += new_x + " "
                elif k == j:
                    replaced += new_y + " "
                else:
                    replaced += splited[k] + " "

            print(l)
            l = replaced
            print(l)

        result = result + l

    text_file = open("randomized_vase_20.txt", "wt")
    n = text_file.write(result)
    text_file.close()




if __name__ == "__main__":
    modifying_gcode()
