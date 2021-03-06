import re
import json

file1 = open('amazon-meta-sample.txt', 'r')
Lines = file1.readlines()

maxJsonObjCount = 0
maxJsonObj = 1000000

jsonFile = open('data/amazon-meta-sample.json', 'w')

structureStarted = False
structureEnded = False

jsonContent = ''
jsonContentList = []

jsonObjectString = ''
jsonObjectDictionary = {}

count = 0

totalLines = len(Lines)

# jsonFile.writelines('[\n') # Used for a true syntax JSON file, one that SparkSQL does not like

categoriesCollectionStarted = False
reviewsCollectionStarted = False

# Strips the newline character
for line in Lines:

    if maxJsonObj == maxJsonObjCount and maxJsonObj > 0:
        break

    count += 1

    if count < 3:
        continue

    print('Processing Line ' + str(count) + ': ' + line.strip())

    emptyLine = True if line.strip() == '' else False

    # JSON Object open
    if emptyLine and not(structureStarted):
        structureStarted = True
        reviewsCollectionStarted = False
        maxJsonObjCount += 1

    if not(emptyLine):

        leadingSpaces = len(line) - len(line.lstrip())

        regexKeySearch = re.findall(r"(.*?)\:", line.lstrip())
        if len(regexKeySearch) > 0 and not(reviewsCollectionStarted): # Key:value pair found
            regexValueSearch = re.findall(r"\: (.*)", line.lstrip())

            if regexKeySearch[0] == 'similar':
                similarAsinList = regexValueSearch[0].strip().split("  ")
                del similarAsinList[0] # Remove the count of similar items
                jsonObjectDictionary[regexKeySearch[0]] = similarAsinList

            elif regexKeySearch[0] == 'categories':
                jsonObjectDictionary[regexKeySearch[0]] = []
                categoriesCollectionStarted = True
            elif regexKeySearch[0] == 'reviews':
                reviewsDistionary = {}

                for keyValue in regexValueSearch[0].strip().split("  "):
                    key = re.findall(r"(.*?)\:", keyValue.lstrip())
                    value = re.findall(r"\: (.*)", keyValue.lstrip())
                    reviewsDistionary[key[0].replace(" ", "_")] = value[0]

                jsonObjectDictionary['reviews_summary'] = reviewsDistionary
                jsonObjectDictionary['reviews'] = []

                categoriesCollectionStarted = False
                reviewsCollectionStarted = True

            else:
                jsonObjectDictionary[regexKeySearch[0]] = regexValueSearch[0].strip() if len(regexValueSearch) > 0 else 'unknown'
        else:
            if categoriesCollectionStarted:

                categoryList = jsonObjectDictionary['categories'] if jsonObjectDictionary['categories'] else []

                for category in line.split("|"):
                    if(category.strip() == ''):
                        continue
                    else:
                        if category.strip() not in categoryList:

                            name = re.findall(r"(.*?)\[", category.strip())
                            id = re.findall(r"\[(.*?)\]", category.strip())
                            jsonObjectDictionary['categories'].append({'name': name[0], 'id': id[0]})

            elif reviewsCollectionStarted:
                reviewList = line.replace("   ", " ").replace("  ", " ").strip().split(" ")
                reviewDisctionary = {
                    'date': reviewList[0],
                    'cutomer': reviewList[2],
                    'rating': reviewList[4],
                    'votes': reviewList[6],
                    'helpful': reviewList[8]
                }
                jsonObjectDictionary['reviews'].append(reviewDisctionary)

    # JSON Object close
    if emptyLine and structureStarted and not(structureEnded):
        structureEnded = True

    # JSON Object write to file
    if structureStarted and structureEnded:
        if jsonObjectDictionary:

            # Handle jsonObjectDictionary that do not have all of the properties as we would expect
            if 'Id' not in jsonObjectDictionary:
                jsonObjectDictionary['Id'] = None

            if 'ASIN' not in jsonObjectDictionary:
                jsonObjectDictionary['ASIN'] = None

            if 'title' not in jsonObjectDictionary:
                jsonObjectDictionary['title'] = None

            if 'group' not in jsonObjectDictionary:
                jsonObjectDictionary['group'] = None

            if 'salesrank' not in jsonObjectDictionary:
                jsonObjectDictionary['salesrank'] = None

            if 'similar' not in jsonObjectDictionary:
                jsonObjectDictionary['similar'] = []

            if 'categories' not in jsonObjectDictionary:
                jsonObjectDictionary['categories'] = []

            if 'reviews' not in jsonObjectDictionary:
                jsonObjectDictionary['reviews_summary'] = {}
                jsonObjectDictionary['reviews'] = []

            if (count < totalLines and maxJsonObjCount < maxJsonObj and maxJsonObj > 0):
            #     jsonFile.writelines(json.dumps(jsonObjectDictionary) + ',\n')  # Used for a true syntax JSON file, one that SparkSQL does not like
                jsonFile.writelines(json.dumps(jsonObjectDictionary) + '\n')
            else:
                jsonFile.writelines(json.dumps(jsonObjectDictionary))

            jsonContentList.append(jsonObjectDictionary)

        # Resets the Booleans in prep for the next object
        structureStarted = False
        structureEnded = False

        # Reset the string in order to keep RAM usage down
        jsonObjectString = ''
        jsonObjectDictionary = {}

# jsonFile.writelines(']')  # Used for a true syntax JSON file, one that SparkSQL does not like

jsonFile.writelines(jsonContent)
jsonFile.close()