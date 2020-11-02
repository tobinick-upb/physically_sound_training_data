import random


def makeString(prefix, tag, angle):
    randomAngleArrayFor12Views = []
    tempStoreString = ""
    tempStr = []
    string = ""

    for i in range(1, 13):
        randomAngleArrayFor12Views.append(i)
    random.shuffle(randomAngleArrayFor12Views)
    for j in range(1, 13):
        if angle >= 100:
            string += prefix + "_0" + str(angle) + "_"
        elif angle >= 10:
            string += prefix + "_00" + str(angle) + "_"
        else:
            string += prefix + "_000" + str(angle) + "_"
        if (randomAngleArrayFor12Views[j-1] >= 10):
            string += "0" + str(randomAngleArrayFor12Views[j-1]) + ".png"
        else:
            string += "00" + str(randomAngleArrayFor12Views[j-1]) + ".png"
        string += " " + str(tag)
        string += '\n'

    tempStr.append(string)

    for k in range(0, tempStr.__len__()):
        tempStoreString += tempStr[k]

    # print(tempStoreString)
    return tempStoreString


base_path = "/base/path/"
data_set_name = "random30"

AMOUNT_OF_INSTANCES = 100

filePath = []
file1 = open('/path/to/random_30_classes.txt', 'r')
Lines = file1.readlines()
count = 0
# filePath contains the pathes to all classes
for line in Lines:
    filePath.append(base_path + "/" + data_set_name +
                    "/" + line.rstrip() + "/" + line.rstrip())


# angleArray contains the values from 1 to "amount_of_instances"
angleArray = []
for angle in range(1, AMOUNT_OF_INSTANCES + 1):
    angleArray.append(angle)


# dictionary containing the label of each class
labelMap = dict()
for i in range(0, filePath.__len__()):
    labelMap[filePath[i]] = i % Lines.__len__() + 1

randomAngleArrayFor12Views = []
random.shuffle(filePath)
random.shuffle(angleArray)
fileAndAngle = []

for file in range(0, filePath.__len__()):
    for angle in range(0, angleArray.__len__()):
        key = filePath[file]
        value = str(angleArray[angle])
        fileAndAngle.append((key, value))

random.shuffle(fileAndAngle)
print(fileAndAngle.__len__())

mainStringOutput = ""
for item in fileAndAngle:
    prefix = item[0]
    tag = labelMap[prefix]
    angle = int(item[1])
    mainStringOutput += makeString(prefix, tag-1, angle)

target_file = open("path/to/training/file/list.txt", "w")
target_file.write(mainStringOutput)
target_file.close()

print("OK")
