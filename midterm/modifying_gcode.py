import pandas as pd


def modifying_gcode():
    gcode = open("vase.txt", "r")

    lines = gcode.readlines()

    layers = ""

    # if it contains 'layer'
    # # of total layer = 100

    #flag = "remove"

    # get head/tail lines
    head = ""
    tail = ""
    '''
    for l in lines:
        if ";LAYER:0" in l:
            break
        else:
            head += l

    for l in lines:
        if ";TIME_ELAPSED:905.713563" in l:
            flag = "keep"
        elif flag == "keep":
            tail += l
    '''

    flag = "yes"

    for l in lines:
        if ";TYPE:SKIN" in l:
            flag = "no"
        if ";TYPE:WALL-OUTER":
            flag = "yes"

        if flag == "yes" and ";TYPE:WALL-OUTER" not in l and ";" not in l:
            print(l)
            '''
            splited = l.split(" ")
            print(splited)

            for i in splited:
                if "X" in i:
                    print(i)
                    '''




        '''
        if ";LAYER:" in l and int(l.split(":")[1]) % 2 == 0:
            flag = "keep"
            layers += l
        elif ";LAYER:" in l and int(l.split(":")[1]) % 2 == 1:
            flag = "remove"
        elif flag == "keep":
            layers += l
        '''

    #print(head+layers+tail)





if __name__ == "__main__":
    modifying_gcode()
