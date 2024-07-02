import csv
import room_scheduler

with open('test_schedule_sp_22.csv', newline = '') as csvfile:
    spamreader = csv.reader(csvfile, delimiter=',', quotechar='|')
    for row in spamreader:
        print(row)
