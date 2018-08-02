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

    def __init__(self, waterUserType, WaterUsageFileName, WaterUsageColumnName, WaterUserFileName):
        self.WaterUsageFileName = WaterUsageFileName
        self.WaterUsageColumnName = WaterUsageColumnName
        self.WaterUserFileName = WaterUserFileName
        self.waterUserType = waterUserType
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
        #print('Length == ' + str(len(self.waterUserProfile)))
        for x in self.waterUserProfile:
            #print('WaterUserProfile: FlowRate == ' + str(x.flowRate) + ', ProfileSecond == ' + str(x.second) + ', usageCurrentSecond == ' + str(self.usageCurrentSecond))
            if x.second == self.usageCurrentSecond:
                flowRate = x.flowRate
                #print('FlowRate == ' + str(x.flowRate))
                break
        if flowRate == -1:
            self.UsageActive = False
            return 0
        else:
            self.usageCurrentSecond += 1
            return flowRate

    def generateUsage(self, secondInDay):
        if secondInDay%3600 == 0:
            self.hourUsageCounter = 0

        if self.UsageActive:
            #print('Active Toilet1')
            return(self.generateFlowwhenActive())

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
                global Details
                Details += ', Daily quata reached'
            else:
                if self.hourUsageCounter >= self.maximumUsageInHour:
                    Details += ', Hourly quata reached'
            #print('Out of daily or hourly quota')
            return 0

class Human:

    fileName = ''
    profile = None

    ActiveUsage = False
    secondCounter = 1
    numOfSecondsInDay = 86400
    WaterFlowRate = 0

    Toilet1Profile = []
    Toilet2Profile = []
    ShowerProfile = []
    BathProfile = []
    BathTapProfile = []
    KitchenTapProfile = []

    WaterUsageCSVObject = None
    CSVwriter = None

    def __init__(self, fileName):
        self.fileName = fileName
        self.profile = None

        self.WaterUsageCSVObject = open('waterUsage.csv', 'w', newline='')
        self.CSVwriter = csv.writer(self.WaterUsageCSVObject)
        fieldnames = ['hour', 'second', 'currentFlow', 'totalFlow', 'details']
        self.CSVwriter = csv.DictWriter(self.WaterUsageCSVObject, fieldnames=fieldnames)
        self.CSVwriter.writeheader()

        print('Human, filName =' + self.fileName)
        self.Toilet1Profile = HumanProfileByWaterUserAndByHour('Toilet 1', fileName, 'Toilet1', 'Profiles/WaterUsers/Toilet1.csv')

    def generateWaterUsage(self, secondCounter):

        currentFlow = 0

        if not self.ActiveUsage:
            currentFlow += self.Toilet1Profile.generateUsage(secondCounter)
            #currentFlow += self.Toilet2Profile.generateUsage(secondCounter)
            #currentFlow += self.ShowerProfile.generateUsage(secondCounter)

            self.WaterFlowRate += currentFlow
        return (currentFlow)

    def generate24hWaterUsageProfile (self):
        for secondCounter in range (1,self.numOfSecondsInDay): # No. of seconds in a day
            global Details
            Details = ''
            currentFlow = self.generateWaterUsage(secondCounter)
            self.writeWaterUsageToCSV(secondCounter, currentFlow)

        self.WaterUsageCSVObject.close()

    def writeWaterUsageToCSV (self, secondCounter, currentFlow):
        global Details
        self.CSVwriter.writerow({'hour' : str(int(secondCounter/3600)+1), 'second' : str(secondCounter), 'currentFlow' : str(currentFlow), 'totalFlow' : str(self.WaterFlowRate), 'details' : Details})



class house:

    humanList = []
    numOfSecondsInDay = 86400

    def __init__(self, fileName):
        self.fileName = fileName
        self.profile = None
        self.getPropertyProfile()

    def getPropertyProfile(self):
        with open(self.fileName, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                H = Human(str(row['ProfilePath']))
                print(H.fileName)
                self.humanList.append(H)


    def generate24hWaterUsageProfile(self):
        for secondCounter in range(1, self.numOfSecondsInDay):  # No. of seconds in a day
            global Details
            Details = ''
            for cur_human in self.humanList
            currentFlow = self.generateWaterUsage(secondCounter)
            self.writeWaterUsageToCSV(secondCounter, currentFlow)


# main

myHome = house('Profiles/Properties/Appartment_1.csv')

print('Start')

person1 = Human('Profiles/Humans/Working_adult_profile.csv')
person1.generate24hWaterUsageProfile()

print('End')











Toilet1 = []
Toilet2 = []
Shower = []
KitchenTap = []
BathTap = []
Bath = []


def read_waterUse_profile (fileName, waterUser = [], *args):
    with open(fileName, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            #print(row['second'], row['flowRate'])
            waterUser.append(WaterUserFlow(row['second'], row['flowRate']))
        #for userFlow in waterUser:
            #print(userFlow)


def csv_read_test ():
    with open('names.csv', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            print(row['first_name'], row['last_name'])

def csv_write_test ():
    with open('names.csv', 'w', newline='') as csvfile:
        fieldnames = ['first_name', 'last_name']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerow({'first_name': 'Baked', 'last_name': 'Beans'})
        writer.writerow({'first_name': 'Lovely', 'last_name': 'Spam'})
        writer.writerow({'first_name': 'Wonderful', 'last_name': 'Spam'})

def s3_write_test ():
    BUCKET = 'hagaytest'
    KEY = os.urandom(32)
    s3 = boto3.client('s3')

    print("Uploading measurement")
    s3.put_object(Bucket=BUCKET,
                  Key='customer1',
                  Body=b'225',
                  Tagging=' customer=1')
    s3.put_object(Bucket=BUCKET,
                  Key='customer2',
                  Body=b'225')
    print('Done uploading measurement')
    return 0









