#! /usr/bin/python3

import json
import gzip
import time
import sys
import re
import timeit
'''
Extract events from LEIDOS archived json file and format into a CSV file, 1 event per line in the format
DATE OBJECT USER EVENT_TYPE
'''

INPUT_DIR = '../../leidos_data/Events'
DATE_START_YYYYMMDD = '20170817'
DATE_END_YYYYMMDD = '20170831'
OUTPUT_FILE = 'gt-time-events-' + DATE_START_YYYYMMDD + '-' + DATE_END_YYYYMMDD + '.csv'

def extractEvent(record):

    if "login_h" in record["actor"]:
        userId = record["actor"]["login_h"]
    else:
        userId = "None"

    if "name_h" in record["repo"]:
        objectId = record["repo"]["name_h"]
    else:
        objectId = "None"
    eventTime = record["created_at"].replace('Z', ' ').replace('T', ' ')
    eventType = record["type"]
    return str(eventTime) + "," + str(eventType) + "," + str(userId) + "," + str(objectId) + "\n"

def readJson(filename):
    eventList = []
    with gzip.open(filename, 'rb') as f:
        for line in f:
            event = extractEvent(json.loads(line))
            eventList.append(event)
    return eventList

def extract_date(input_date):
    '''
    Extract year, month and day from given string in format YYYYMMDD
    '''
    y = m = d = 0
    matched = re.match('(\d{4})(\d{2})(\d{2})', input_date)
    if matched and len(matched.groups()) == 3:
        y = matched.group(1)
        m  = matched.group(2)
        d  = matched.group(3)
    return int(y), int(m), int(d)
    
def extract_events():
    '''
    Core processing function extracting events within the given dates and writing to output file
    '''
#     monthlyDay = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    y1, m1, d1 = extract_date(DATE_START_YYYYMMDD)
    y2, m2, d2 = extract_date(DATE_END_YYYYMMDD)
    if None in (y1, m1, d1, y2, m2, d2):
        print ('ERROR> Misformatted date(s): ' + DATE_START_YYYYMMDD + ',' + DATE_END_YYYYMMDD)
        sys.exit(0)
    print ('Extracting events from ' + DATE_START_YYYYMMDD + ' to ' + DATE_END_YYYYMMDD + '...')
    with open(OUTPUT_FILE, "w") as output:
        for year in range(y1, y2+1):
            for month in range(m1, m2+1):
                for day in range(d1, d2+1):#monthlyDay[month-1] + 1):
                    for hour in range(24):
                        fileName = INPUT_DIR + "/Anon/" + str(year) + str(month).zfill(2) + "/" + str(year) + \
                                   str(month).zfill(2) + str(day).zfill(2) \
                                   + "/an_" + str(year) + "-" + str(month).zfill(2) + "-" + \
                                   str(day).zfill(2) + "-" + str(hour) + ".json.gz"
                        print ('Processing ' + fileName + '...')
                        eventList = readJson(fileName)
                        for event in eventList:
                            output.write(event)
    print ('Done. Events saved into ' + OUTPUT_FILE)
    
if __name__ == '__main__':

    elapsed = timeit.timeit(extract_events, number=1)
    print ('Computation took ' + str(elapsed) + ' secs.')


