


def get_infill_area():

    gcode = open("cuberelative.gcode")

    lines = gcode.readlines()

    is_target = 0
    is_infill = 0
    layer_count = 0
    target_infill = ""
    new_z = 0

    target_z = "no"
    z_flag = 0

    # Get total layer count

    for i in range(len(lines)):

        if ";LAYER_COUNT:" in lines[i]:
            countline = lines[i].split(":")
            layer_count = int(countline[1])

    #print(layer_count)


    for l in lines:
        if ";LAYER:10\n" in l:  # target layer
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

    x_min = float(x_values[0].split(".")[0])
    x_max = float(x_values[-1].split(".")[0])
    y_min = float(y_values[0].split(".")[0])
    y_max = float(y_values[-1].split(".")[0])

    #print(x_min)

    grid_x = []
    grid_y = []
    full_x = []

    second_x = []
    second_y = []

    current_x = x_min

    current_y = y_min

    # get coordinates for grid lines
    while current_x <= x_max:
        grid_x.append(current_x)
        current_x += 1.5

    while current_y <= y_max:
        grid_y.append(current_y)
        current_y += 1.5

    #get coordinates for full horizontal infill
    current_x = x_min
    while current_x <= x_max:
        full_x.append(current_x)
        current_x += 0.4 #because 0.4 is nozzle diameter

    print(grid_y)
    print(grid_x)
    print(full_x)
    reverse_y = []
    rev_full_x = []
    for i in range(len(grid_y)):
        reverse_y.append(grid_y[len(grid_y)-i-1])

    for i in range(len(grid_y)):
        rev_full_x.append(full_x[len(full_x) - i - 1])

    print(rev_full_x)


    #get Z value

    for i in range(len(lines)):
        if ";LAYER:10\n" in lines[i]:  # target layer
            target_z = "yes"
        elif ";LAYER" in lines[i]:
            target_z = "no"

        if target_z == "yes":
            #print(lines[i])
            if "Z" in lines[i]:
                print(lines[i])
                splitline = lines[i].split(" ")
                for j in range(len(splitline)):
                    if "Z" in splitline[j]:
                        if splitline[j].split("Z")[1] == '':
                            break
                        else:
                            current_z = float(splitline[j].split("Z")[1])
                            current_z -= 0.2
                            new_z = current_z + 0.4




    # a-structure

    g0 = "G0 F9500 "
    g1 = "G1 F9500 "

    result = ""

    for x in range(1, len(grid_x)):

        if x % 2 == 0:
            i = 0
            j = 0

            for i in range(1, len(grid_y)-1):


                if i%2 == 0:

                        j=i+1
                        result += g1 + "X" + str(grid_x[x]) + " Y" + str(grid_y[i]) + " E0.5" + "\n"
                        result += g0 + "X" + str(grid_x[x]) + " Y" + str(grid_y[i]) + " Z" + str(new_z) +"\n"
                        result += g0 + "X" + str(grid_x[x]) + " Y" + str(grid_y[j]) + " Z" + str(current_z) +"\n"



            result += g1 + "X" + str(grid_x[x]) + " Y" + str(grid_y[-1]) + " E0.5" + "\n"
            result += g0 + "X" + str(grid_x[x]) + " Y" + str(grid_y[-1]) + " Z" + str(new_z) + "\n"
        else:

            i = 0
            j = 0
            for i in range(len(reverse_y) - 1):


                # print(i)
                if i % 2 == 0:
                        j = i+1
                        result += g1 + "X" + str(grid_x[x]) + " Y" + str(reverse_y[i]) + " E0.5" + "\n"
                        result += g0 + "X" + str(grid_x[x]) + " Y" + str(reverse_y[i]) + " Z" + str(new_z) + "\n"
                        result += g0 + "X" + str(grid_x[x]) + " Y" + str(reverse_y[j]) + " Z" + str(current_z) + "\n"



    for i in range(1, len(grid_y) - 1):
        if i % 2 != 0:
            second_x.append(grid_y[i])
    second_x.append(grid_y[-1])
    print(second_x)



    result += "\n"


    print(result)

    # b-structure

    result = ""
    k=0
    for i in range(1, len(grid_y)-1):
        if i%2 !=0:
            for k in range(len(grid_x) - 1):
                result += g1 + "X" + str(grid_x[k]) + " Y" + str(grid_y[i]) + " E0.5" + "\n"
                result += g0 + "X" + str(grid_x[k]) + " Y" + str(grid_y[i]) + " Z" + str(new_z) + "\n"
                result += g0 + "X" + str(grid_x[k+1]) + " Y" + str(grid_y[i]) + " Z" + str(current_z) + "\n"
            result += g1 + "X" + str(grid_x[-1]) + " Y" + str(grid_y[i]) + " E0.5" + "\n"
            result += g0 + "X" + str(grid_x[-1]) + " Y" + str(grid_y[i]) + " Z" + str(new_z) + "\n"


    result += "\n"


    print("---------------b-------------")
    print(result)

    #full infill-structure

    result = ""
    for i in range(1,len(full_x)):

        if i%2==0:

            result += g1 + "X" + str(full_x[i]) + " Y" + str(full_x[0]) + " E0.2" + "\n"
            result += g1 + "X" + str(full_x[i]) + " Y" + str(full_x[-1]) + "\n"
        else:

            result += g1 + "X" + str(full_x[i]) + " Y" + str(full_x[-1]) + " E0.2" + "\n"
            result += g1 + "X" + str(full_x[i]) + " Y" + str(full_x[0]) + "\n"
 #how to calculate the E value for other shapes since 0.2 is arbitrary?
    result += "\n"

    print("---------------infill-------------")
    print(result)


if __name__ == "__main__":
    get_infill_area()
