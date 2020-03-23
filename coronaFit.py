import numpy as np
import urllib.request as ur
import matplotlib.pyplot as plt
import os
import datetime as dt
from matplotlib.artist import setp
import matplotlib.dates as mdates

def FindCountryIndex(country, fileContent):

    # Find the index for the column in the CSV file relevant for the considered country
    fcZero = fileContent[0].split(',')
    countryIndex = -1
    for i in range(len(fcZero)):
        if fcZero[i] == country:
            countryIndex = i
            break
    assert countryIndex >= 0, 'Country {} not found'.format(country)
    return countryIndex

def GetData(index, fileContent, startDate):

    # Read the whole CSV file, split it, and make a mapping of dates to case numbers for the country in consideration, as indicated by the index. Ignore dates before 'startDate'.
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
        if dayContent == '':
            dayContent = dataMap[day - dt.timedelta(days = 1)]
        dataMap[day] = int(dayContent)
    return dataMap

def Model(day, fit):

    # Simple exponential model, taking as arguments the slope and ordinate of the log-value distribution
    return np.exp(fit[0] * day + fit[1])

def CreatePredArray(fit, xVals, futureDays):

    #Create arrays for the dates and predictions in the considered timespan
    xValsExtended = xVals[:]
    for i in range(futureDays):
        xValsExtended.append(xValsExtended[-1] + dt.timedelta(days = 1))
    arr = np.array([])
    for d in xValsExtended:
        arr = np.append(arr, Model((d - xValsExtended[0]).days, fit))
    return [arr, xValsExtended]

def MakePlot(data, fit, country, futureDays = 0, nPeople = 1, modeledQuantity = 'cases', percent = False):

    # Normalize observed data to population size
    xVals = list(data.keys())
    yVals = np.array(list(data.values()))
    yVals2 = yVals.copy()
    yVals = yVals/nPeople
    if percent:
        yVals *= 100

    # Setup directory for plotting output
    plotPath = './plots'
    if not os.path.exists(plotPath):
        os.mkdir(plotPath)

    # Create model for best-fit exponential increase
    model, xValsExtended = CreatePredArray(fit, xVals, futureDays)
    # Normalize modeled case numbers to population size
    model2 = model.copy()
    model = model/nPeople
    if percent:
        model *= 100

    # Actual plotting
    fig, ax = plt.subplots()
    ax2 = ax.twinx()
    ax.plot(xVals, yVals, 'ro', label='Observed')
    ax.plot(xValsExtended, model, 'b', label='Model')
    ax2.plot(xVals, yVals2, 'ro', label='Observed')
    ax2.plot(xValsExtended, model2, 'b', label='Model')
    ax.set_yscale('log')
    ax2.set_yscale('log')
    percString = " [%]" if percent else ""
    if modeledQuantity == 'cases':
        yLabel = 'Diagnosed cases / population' + percString
        yLabel2 = 'Diagnosed cases'
    elif modeledQuantity == 'deaths':
        yLabel = ' Deaths / population' + percString
        yLabel2 = 'Deaths'
    else:
        'No valid quantity chosen'
        return
    fig.subplots_adjust(bottom=0.15)
    degrees = 20
    plt.setp( ax.xaxis.get_majorticklabels(), rotation=degrees )
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b-%d"))
    ax.set_xlabel('Date')
    ax.set_ylabel(yLabel)
    ax2.set_ylabel(yLabel2)
    ax2.tick_params(labelbottom=False, bottom = False)
    plt.title("{0} in {1}".format(modeledQuantity.capitalize(), country))
    leg = ax2.legend()

    plotFileName = 'plots/total_{1}_{0}.png'.format(country, modeledQuantity)
    fig.savefig(plotFileName)
    print('Saved plot for {0}: {1}\n'.format(country, plotFileName))

def MakeDayArray(n):
    # Used to create a dummy day array for the fit

    arr = np.array([])
    for i in range(n):
        arr = np.append(arr, i)
    return arr

def GetCSVFile(filename):

    # Retrieve CSV file from internet and save it to directory
    dataPath = './data'
    if not os.path.exists(dataPath):
        os.mkdir(dataPath)

    filePath = './data/{}'.format(filename)
    url = 'https://covid.ourworldindata.org/data/ecdc/{}'.format(filename)
    ur.urlretrieve(url, filePath)

# Choose whether diagnosed cases or deaths should be considered
modeledQuantities = ['cases', 'deaths']

for modeledQuantity in modeledQuantities:
    filename = 'total_{}.csv'.format(modeledQuantity)
    
    # Download data from the European Centre for Disease Prevention and Control (ECDC)
    try:
        GetCSVFile(filename)
    except:
        print('No valid CSV file URL')
        quit()
    else:
        print('Got CSV file')
    
    # Read whole downloaded input file
    with open('data/{}'.format(filename), 'r') as infile:
        fileCont = infile.readlines()
    
    # Which countries should be analyzed? If another country is added, an initial date and the population size for that country must be added as well below
    #countryList = ['Germany']
    countryList = ['Germany', 'United States', 'Switzerland', 'Italy', 'South Africa']
    
    # How many days should the model be extrapolated into the future?
    extrapolatedDays = 14
    showPercentage = False
    
    # Starting dates for the fit. Case number growth can change significantly, and by giving a more recent date, the current infection situation can be better modeled. To get an idea what to set for the date, choose an early value and look at the resulting plot.
    startDayMap = dict()
    startDayMap['cases']  = {
            #'Germany' : dt.date(2020, 3, 10), 
            'Germany' : dt.date(2020, 3, 2), 
            'United States' : dt.date(2020, 3, 3), 
            'Switzerland' : dt.date(2020, 3, 7),
            'Italy' : dt.date(2020, 3, 10),
            'South Africa' : dt.date(2020, 3, 10),
            }
    startDayMap['deaths']  = {
            'Germany' : dt.date(2020, 3, 10), 
            'United States' : dt.date(2020, 3, 3), 
            'Switzerland' : dt.date(2020, 3, 7),
            'Italy' : dt.date(2020, 3, 13),
            'South Africa' : dt.date(2020, 3, 10),
            }
    
    
    # Population size; necessary for the normalization of case numbers to a rate
    nPeopleMap  = {
            'Germany' : 8e7, 
            'United States' : 3.25e8, 
            'Switzerland' : 8.5e6,
            'Italy' : 6e7,
            'South Africa' : 6e7,
            }
    
    # Loop over countries
    for country in countryList:
    
        print("Run fit and plotting for {0}".format(country))
    
        # Get the index in the CSV file for the country in question
        countryIndex = FindCountryIndex(country, fileCont)
    
        # Get a mapping from date to number of cases/deaths, starting at a given date
        data = GetData(countryIndex, fileCont, startDayMap[modeledQuantity][country])
    
        # Make dummy array for the x-axis in the fit
        nConsideredDays = len(data)
        dayArray = MakeDayArray(nConsideredDays)
        # The actual fit of the log-values of the case numbers
        if np.count_nonzero(np.array(list(data.values()))) == 0:
            print('No {0} for country {1}; skipping'.format(modeledQuantity, country))
            continue
        fit = np.polyfit(dayArray, np.log(np.array(list(data.values()))), deg = 1) 
    
        # Make a plot of the data and the modeled data. Can be extended in the future by choosing a 'futureDays' larger than 0
        MakePlot(data, fit, country, extrapolatedDays, nPeopleMap[country], modeledQuantity, showPercentage)

print('All done!')    
