import numpy as np
import urllib.request as ur
import matplotlib.pyplot as plt
import os
import datetime as dt

def FindCountryIndex(country, fileContent):
    fcZero = fileContent[0].split(',')
    countryIndex = -1
    for i in range(len(fcZero)):
        if fcZero[i] == country:
            countryIndex = i
            break
    assert countryIndex >= 0, 'Country {} not found'.format(country)
    return countryIndex

def GetData(index, fileContent, startDate):

    dataMap = dict()
    for i in range(1, len(fileContent)):
        lineVec = fileContent[i].split(',')
        dayStrVec = lineVec[0].split('-')
        day = dt.date( 
                int(dayStrVec[0]), 
                int(dayStrVec[1]), 
                int(dayStrVec[2]))
        if day < startDate:
            continue
        dayContent = lineVec[index]
        print(day, dayContent)
        if dayContent == '':
            dayContent = dataMap[day - dt.timedelta(days = 1)]
        dataMap[day] = int(dayContent)
    return dataMap

def Model(day, fit):
    return np.exp(fit[0] * day + fit[1])

def Chi2(yObsArray, yPredArray, offset):
    chi2 = 0.
    for i in range(30, len(yObsArray)):
        chi2 += (yObsArray[i] - yPredArray[i])**2
    return chi2

def CreatePredArray(fit, xVals, futureDays):
    xValsExtended = xVals[:]
    for i in range(futureDays):
        xValsExtended.append(xValsExtended[-1] + dt.timedelta(days = 1))
    arr = np.array([])
    for d in xValsExtended:
        arr = np.append(arr, Model((d - xValsExtended[0]).days, fit))
    return [arr, xValsExtended]

def MakePlot(data, fit, country, futureDays = 0, nPeople = 1):
    xVals = list(data.keys())
    yVals = np.array(list(data.values()))
    yVals = yVals/nPeople
    plotPath = './plots'
    if not os.path.exists(plotPath):
        os.mkdir(plotPath)
    model, xValsExtended = CreatePredArray(fit, xVals, futureDays)
    model = model/nPeople
    fig, ax = plt.subplots()
    ax.plot(xVals, yVals, 'ro', label='Observed')
    ax.plot(xValsExtended, model, 'b', label='Model')
    ax.set_yscale('log')
    ax.set_xlabel('Date')
    ax.set_ylabel('Diagnosed cases / population')
    degrees = 20
    plt.xticks(rotation=degrees)
    ax.tick_params(labelright=True, right = True)
    leg = ax.legend()
    plt.title(country)
    fig.show()
    fig.savefig('plots/totalCases_{0}.png'.format(country))

def DaysUntilX(bestFitSlope, data, threshold):
    nData = len(data)
    dayUntilXIndex = -1
    index = 0
    while dayUntilXIndex < 0:
        nPred = Model(index + nData, bestFitSlope)
        if nPred > threshold:
            dayUntilXIndex = index
        index += 1
    return [dayUntilXIndex, Model(dayUntilXIndex + nData, bestFitSlope)]

def MakeDayArray(n):
    arr = np.array([])
    for i in range(n):
        arr = np.append(arr, i)
    return arr

countryList = ['Germany', 'United States', 'Switzerland', 'Italy', 'South Africa']
def GetCSVFile(filename):
    dataPath = './data'
    if not os.path.exists(dataPath):
        os.mkdir(dataPath)
    filePath = './data/{}'.format(filename)
    url = 'https://covid.ourworldindata.org/data/ecdc/{}'.format(filename)
    ur.urlretrieve(url, filePath)

filename = 'total_cases.csv'
GetCSVFile(filename)

file_total = open('data/{}'.format(filename), 'r')
fileCont_total = file_total.readlines()
file_total.close()

startDayMap  = {
        'Germany' : dt.date(2020, 3, 2), 
        'United States' : dt.date(2020, 3, 3), 
        'Switzerland' : dt.date(2020, 3, 7),
        'Italy' : dt.date(2020, 3, 1),
        'South Africa' : dt.date(2020, 3, 10),
        }
nPeopleMap  = {
        'Germany' : 8e7, 
        'United States' : 3.25e8, 
        'Switzerland' : 8.5e6,
        'Italy' : 6e7,
        'South Africa' : 6e7,
        }

for country in countryList:
    countryIndex = FindCountryIndex(country, fileCont_total)
    print(country, countryIndex)
    data = GetData(countryIndex, fileCont_total, startDayMap[country])
    nDays = len(data)
    fit = np.polyfit(MakeDayArray(len(data)), np.log(np.array(list(data.values()))), 1) 
    MakePlot(data, fit, country, futureDays = 7, nPeople = nPeopleMap[country])
    
#    print(country, DaysUntilX(bestFitSlope, data, 100000))
