import csv
from tkinter.ttk import Separator
infile = "testexport.csv"

klassenliste = [
    "05A-Schueler",
    "05B-Schueler",
    "05C-Schueler",
    "06A-Schueler",
    "06B-Schueler",
    "06C-Schueler",
    "07A-Schueler",
    "07B-Schueler",
    "07C-Schueler",
    "08A-Schueler",
    "08B-Schueler",
    "08C-Schueler",
    "09A-Schueler",
    "09B-Schueler",
    "09C-Schueler",
    "EF-Schueler",
    "Q1-Schueler",
    "Q2-Schueler"    
]

with open(infile, newline='') as csvfile:
    spamreader = csv.reader(csvfile, delimiter=';')
    data = list(spamreader)

print(data)
for klasse in klassenliste:
    print(klasse)
    for row in data:
        if klasse in row[7]:
            print(row[3], row[6])