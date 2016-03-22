import csv
from collections import defaultdict
import time

def mapCategories(mapFile):
    f = open(mapFile, 'rU')
    reader = csv.DictReader(f)
    mapDict = {}
    for row in reader:
        mapDict[int(row['TU1CODE'].encode('utf-8'))] = row['TU1DESC'].encode('utf-8')
    return mapDict


def aggregatePeople(data):
    #person-> entries
    people = defaultdict(list)
    for val in data:
        people[val['id']].append(val)
    return people

def parseHoursActivities(file):
    f = open(file, 'rU') 
    activity_reader = csv.DictReader(f)
    labels = set()
    data = []
    for row in activity_reader:
        rowdata = {}
        labels.add(row['activity'])
        rowdata['activity'] = row['activity']
        rowdata['start'] = row['start']
        rowdata['end'] = row['end']
        data.append(rowdata)

    f.close()
    return (data, labels)


def parseActivities(activity_file):
    f = open(activity_file, 'rU') 
    activity_reader = csv.DictReader(f)
    data = []
    for row in activity_reader:
        if int(row['TUTIER1CODE']) > 18:
            continue
        rowdata = {}
        rowdata['activity'] = int(row['TUTIER1CODE'])
        rowdata['start'] = row['TUSTARTTIM']
        rowdata['end'] = row['TUSTOPTIME']
        rowdata['id'] = row['TUCASEID']
        data.append(rowdata)

    f.close()
    return data

def parseDemographics(filepath):
    f = open(demographicsfile) 
    demographics_reader = csv.DictReader(demographics_file)
    data = {}
    for row in demographics_reader:
        rowdata = {}
        rowdata['race'] = row['RACE']
        rowdata['age'] = row['AGE']
        rowdata['GENDER'] = row['GENDER']
        data[row['CASEID']] = rowdata

    f.close()
    return data
    
 
def validateTime(start, end):
    if start.tm_hour > end.tm_hour or (start.tm_hour == end.tm_hour and start.tm_min >= end.tm_min):
        return False
    return True

def parseTime(timestamp):
    t= timestamp.split(":")
    return time.strptime(timestamp, "%H:%M:%S")

def getMinutePercentages(data):
    totals = defaultdict(int)

    for hour, m in data.iteritems():
        for activity, mins in m.iteritems():
            totals[hour] += mins

    percents = {}
    for hour, m in data.iteritems():
        breakdown = {}
        for activity, mins in m.iteritems():
            breakdown[activity] = float(mins)/float(totals[hour])
        percents[hour] = breakdown
    return percents

def getMinuteDistributions(data):
    # map hour-> (map activity-> # of minutes)
    timeMap = defaultdict(lambda: defaultdict(int))
    for val in data:
        start_time = parseTime(val['start'])
        end_time = parseTime(val['end'])
        activity = val['activity']
        if not validateTime(start_time, end_time):
            continue
        
        if start_time.tm_hour == end_time.tm_hour:
            minutes = end_time.tm_min - start_time.tm_min
            timeMap[start_time.tm_hour][activity] += minutes
            continue

        for i in range(start_time.tm_hour, end_time.tm_hour + 1):
            breakdown = timeMap[i]
            if i == start_time.tm_hour:
                breakdown[activity] += 60 - start_time.tm_min
            elif i == end_time.tm_hour:
               breakdown[activity] += end_time.tm_min
            else:
               breakdown[activity] += 60
            timeMap[i] = breakdown

    return timeMap

def writePersonalDistributions(data, categories):
    f = open("personal.csv", 'w')
    print data[0].keys()
    writer = csv.DictWriter(f, fieldnames=['hour']+ categories)
    writer.writeheader()

    for hour, m in data.iteritems():
        rowdata = defaultdict(int)
        rowdata['hour'] = hour
        for category in categories:
            rowdata[category] = m[category]
        writer.writerow(rowdata)
    f.close()

def writeMinuteDistributions(data, categories):
    f = open("minutesFile.csv", 'w')
    writer = csv.DictWriter(f, fieldnames=['hour']+ categories.values())
    writer.writeheader()

    for hour, m in data.iteritems():
        rowdata = {'hour': hour}
        for activity, mins in m.iteritems():
            rowdata[categories[activity]] = mins
        writer.writerow(rowdata)
    f.close()

def getTransitionDistributions(data):
    people = aggregatePeople(data)
    #map hour -> (from activity -> (map to activity -> # of people))
    transitionMap = defaultdict(lambda:defaultdict(lambda: defaultdict(int)))
    for person, entries in people.iteritems(): 
        # sort the entries by time
        s = sorted(entries, key=lambda x: x['start'])
        hour = 0
        schedule = {}
        for activity in s:
            start = parseTime(activity['start'])
            end = parseTime(activity['end'])
            if start.tm_hour > hour:
                hour = start.tm_hour
            if start.tm_hour == hour:
                schedule[hour] = activity['activity']
                hour += 1
            elif end.tm_hour == hour:
                schedule[hour] = activity['activity']
                hour += 1

        previous = None
        previous_hour = -2
        for hour in range(24):
            if hour not in schedule:
                continue
            activity = schedule[hour]
            if not (previous_hour == hour -1):
                previous = activity
                previous_hour = hour
                continue
            if previous == None:
                print "ugh"
            transitionMap[previous_hour][previous][activity] += 1
            previous = activity
            previous_hour = hour
    return transitionMap

def writeTransitions(data):
    f = open("transitionFile.csv", 'w')
    writer = csv.DictWriter(f, fieldnames=['hour', 'from', 'to', 'number of people'])
    writer.writeheader()
    for hour, transition in data.iteritems():
        for frm, m, in transition.iteritems():
            for to, p in m.iteritems():
                row = {'hour': hour, 'from': frm, 'to':to, 'number of people':p } 
                writer.writerow(row)
    f.close()

def main():
    categories = mapCategories('mappings.csv')
    activities = parseActivities('activity.csv')
    hour_dist = getMinuteDistributions(activities)
    writeMinuteDistributions(hour_dist, categories)
    (personal, labels) = parseHoursActivities('hours.csv')
    personal_dist = getMinuteDistributions(personal)
    writePersonalDistributions(personal_dist, list(labels))

if __name__ == '__main__':
    main()
