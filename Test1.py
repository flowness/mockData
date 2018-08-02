import boto3
import os
import csv
import random

# Global parameters
Details = ''

class WaterUserFlow:
    def __init__(self, second=0, flowRate=0):
        self.second = second
        self.flowRate = flowRate
    def __repr__(self):
        return ("{}('{},{}')".format(self.__class__.__name__, self.second, self.flowRate))

class WaterUsageProbabilityByHour:

    def __init__(self, _hour=0, _percentage=0):
        self.hour = _hour
        self.percentage = _percentage

    #def __repr__(self):
    #    return ("{}('{},{}')".format(self.__class__.__name__, self.hour, self.percentage))


class HumanProfileByWaterUserAndByHour:

    UsageActive = False
    usageCurrentSecond = 0
    profile = []
    waterUserProfile = []
    maximumUsageInHour = 0
    maximumUsageInDay = 0
    hourUsageCounter = 0
    dayUsageCounter = 0

    def __init__(self, waterUserType, WaterUsageFileName, WaterUsageColumnName, WaterUserFileName, humanName):
        self.WaterUsageFileName = WaterUsageFileName
        self.WaterUsageColumnName = WaterUsageColumnName
        self.WaterUserFileName = WaterUserFileName
        self.waterUserType = waterUserType
        self.humanName = humanName
        self.GetProfile()

    def read_waterUse_profile(self):
        with open(self.WaterUserFileName, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                #W = WaterUserFlow(int(row['second']), int(row['flowRate']))
                #print(W)
                self.waterUserProfile.append(WaterUserFlow(int(row['second']), int(row['flowRate'])))

    def getGeneralUsageProfile(self):
        with open('Profiles/Humans/General.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row['General'] == 'Max Usage per hour':
                    self.maximumUsageInHour = int(row[self.WaterUsageColumnName])
                if row['General'] == 'Max Usage per day':
                    self.maximumUsageInDay = int(row[self.WaterUsageColumnName])


    def GetProfile (self):
        with open(self.WaterUsageFileName, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                W = WaterUsageProbabilityByHour(int(row['hour']), int(row[self.WaterUsageColumnName]))
                #print(vars(W)['hour'])
                #W.print_params()
                self.profile.append(W)
        self.getGeneralUsageProfile()
        self.read_waterUse_profile()

    def generateFlowwhenActive(self):
        flowRate = -1
        global Details
        #print('Length == ' + str(len(self.waterUserProfile)))
        for x in self.waterUserProfile:
            #print('WaterUserProfile: FlowRate == ' + str(x.flowRate) + ', ProfileSecond == ' + str(x.second) + ', usageCurrentSecond == ' + str(self.usageCurrentSecond))
            if x.second == self.usageCurrentSecond:
                flowRate = x.flowRate
                #print('FlowRate == ' + str(x.flowRate))
                break
        if flowRate == -1:
            self.UsageActive = False
            Details += ', ' + self.humanName + ' -> ' + ' Finished ' + self.waterUserType
            return 0
        else:
            self.usageCurrentSecond += 1
            Details += ', ' + self.humanName + ' -> ' + self.waterUserType + ' used ' + str(flowRate)
            return flowRate

    def generateUsage(self, secondInDay, activeHuman):
        global Details

        if secondInDay%3600 == 0:
            self.hourUsageCounter = 0

        if self.UsageActive:
            #print('Active Toilet1')
            return(self.generateFlowwhenActive())

        if activeHuman:
            return 0

        if self.dayUsageCounter < self.maximumUsageInDay and self.hourUsageCounter < self.maximumUsageInHour:
            R = random.randrange(360000) #100% * 60 * 60 -> as the csv refer to chance of usage in 1 hour
            percentageOfUsage = 0
            hourOfDay = int(secondInDay/3600) + 1
            #print('Hour == ' + str(hourOfDay))
            for x in self.profile:
                if x.hour == hourOfDay:
                    percentageOfUsage = x.percentage
                    break

            if  R <= percentageOfUsage:
                self.UsageActive = True
                self.usageCurrentSecond = 1
                self.hourUsageCounter+=1
                self.dayUsageCounter+=1
                return (self.generateFlowwhenActive())
            else:
                return 0
        else:
            if self.dayUsageCounter >= self.maximumUsageInDay:
                Details += ', ' + self.humanName + ' -> ' + self.waterUserType + ' reached Daily quata'
            else:
                if self.hourUsageCounter >= self.maximumUsageInHour:
                    Details += ', ' + self.humanName + ' -> ' + self.waterUserType + ' reached Hourly quata'

            #print('Out of daily or hourly quota')
            return 0

class Human:

    fileName = ''
    profile = None

    ActiveUsage = False
    secondCounter = 1
    WaterFlowRate = 0

    waterUsers = []



    def __init__(self, fileName, humanName, profileName):
        self.fileName = fileName
        self.profile = None
        self.humanName= humanName
        self.profileName = profileName

        print('Human, filName =' + self.fileName)

        self.waterUsers.append(HumanProfileByWaterUserAndByHour('Toilet 1', fileName, 'Toilet1', 'Profiles/WaterUsers/Toilet1.csv', self.humanName))
        self.waterUsers.append(HumanProfileByWaterUserAndByHour('Toilet 2', fileName, 'Toilet2', 'Profiles/WaterUsers/Toilet2.csv', self.humanName))
        self.waterUsers.append(HumanProfileByWaterUserAndByHour('Shower', fileName, 'Shower', 'Profiles/WaterUsers/Shower.csv', self.humanName))

    def generateWaterUsage(self, secondCounter):

        currentFlow = 0
        counter = 1
        for waterUser in self.waterUsers:
            print(str(secondCounter) + ',counter = ' + str(counter) + ', ' + self.humanName + ', ' + str(waterUser.waterUserType))
            counter += 1
            currentFlow += waterUser.generateUsage(secondCounter, self.ActiveUsage)

        #currentFlow += self.Toilet1Profile.generateUsage(secondCounter, self.ActiveUsage)
        #currentFlow += self.Toilet2Profile.generateUsage(secondCounter, self.ActiveUsage)
        #currentFlow += self.ShowerProfile.generateUsage(secondCounter,self.ActiveUsage)
        
        self.WaterFlowRate += currentFlow

        return (currentFlow)

class house:

    humanList = []
    numOfSecondsInDay = 86400
    WaterUsageCSVObject = None
    CSVwriter = None
    totalWaterVolume = 0

    def __init__(self, fileName):
        self.fileName = fileName

        self.WaterUsageCSVObject = open('waterUsage.csv', 'w', newline='')
        self.CSVwriter = csv.writer(self.WaterUsageCSVObject)
        fieldnames = ['hour', 'second', 'currentFlow', 'totalFlow', 'details']
        self.CSVwriter = csv.DictWriter(self.WaterUsageCSVObject, fieldnames=fieldnames)
        self.CSVwriter.writeheader()

        self.getPropertyProfile()

    def getPropertyProfile(self):
        with open(self.fileName, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                H = Human(str(row['ProfilePath']), str(row['name']), str(row['profileName']))
                print(H.humanName)
                print(H.fileName)
                self.humanList.append(H)


    def generate24hWaterUsageProfile(self):
        waterFlow = 0
        secondCounter = 1
        for secondCounter in range(1, self.numOfSecondsInDay):  # No. of seconds in a day
            waterFlow = 0
            global Details
            Details = ''
            for cur_human in self.humanList:
                waterFlow += cur_human.generateWaterUsage(secondCounter)
            self.totalWaterVolume += waterFlow

            self.writeWaterUsageToCSV(secondCounter, waterFlow)

        self.WaterUsageCSVObject.close()

    def writeWaterUsageToCSV (self, secondCounter, currentFlow):
        global Details
        self.CSVwriter.writerow({'hour' : str(int(secondCounter/3600)+1), 'second' : str(secondCounter), 'currentFlow' : str(currentFlow), 'totalFlow' : str(self.totalWaterVolume), 'details' : Details})


# main


print('Start')

myHome = house('Profiles/Properties/Appartment_1.csv')
myHome.generate24hWaterUsageProfile()

print('End')
