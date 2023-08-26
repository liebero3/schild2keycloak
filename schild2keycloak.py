import xml.etree.ElementTree as ET
import re
import mappings
# from turtle import color
from mmap import PAGESIZE
from ctypes import alignment
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.units import cm
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import csv
from difflib import SequenceMatcher
import pandas as pd


class User:
    def __init__(self, lehrerid, name, given, institutionrole, email, birthday, username, initialpassword):
        self.lehrerid = lehrerid
        self.name = name
        self.given = given
        self.institutionrole = institutionrole
        self.email = email
        self.birthday = birthday
        self.username = username
        self.initialpassword = initialpassword

    def __repr__(self):  # optional
        return f'User {self.name}'


class Group:

    def __init__(self, groupid, name, parent):
        self.groupid = groupid
        self.name = name
        self.parent = parent

    def __repr__(self):  # optional
        return f'Group {self.name}'


class Membership:

    def __init__(self, membershipid, groupid, nameid):
        self.membershipid = membershipid
        self.groupid = groupid
        self.nameid = nameid

    def __repr__(self):  # optional
        return f'Membership {self.groupid}'


def readUsers(users):
    for elem in root.findall(
            ".//{http://www.metaventis.com/ns/cockpit/sync/1.0}person"):
        for child in elem.findall(
                ".//{http://www.metaventis.com/ns/cockpit/sync/1.0}id"):
            lehrerid = child.text
        for child in elem.findall(
                ".//{http://www.metaventis.com/ns/cockpit/sync/1.0}family"):
            name = child.text
        for child in elem.findall(
                ".//{http://www.metaventis.com/ns/cockpit/sync/1.0}given"):
            given = child.text
        for child in elem.findall(".//{http://www.metaventis.com/ns/cockpit/sync/1.0}institutionrole"):
            institutionrole = child.get('institutionroletype')
        email = ""
        for child in elem.findall(
                ".//{http://www.metaventis.com/ns/cockpit/sync/1.0}email"):
            email = child.text
        if institutionrole == "Student":
            for child in elem.findall(
                    ".//{http://www.metaventis.com/ns/cockpit/sync/1.0}bday"):
                birthdaytemp = child.text.split("-")
                birthday = f"{birthdaytemp[2]}.{birthdaytemp[1]}.{birthdaytemp[0]}"
            tempusername = returnUsername(given, name, "kurzform")
        if institutionrole == "faculty" or institutionrole == "extern":
            tempusername = returnUsername(given, name, "vorname.nachname")
            birthday = ""
        for user in users:
            if tempusername == user.username:
                tempusername = tempusername + "1"

        initialPassword = f"{lehrerid[-3:]}{tempusername[-2:]}{stripHyphensFromBirthday(birthday)[:3]}{tempusername[:2]}"
        users.append(
            User(
                lehrerid, name, given, institutionrole, email,
                birthday, tempusername, initialPassword))


def readGroups(groups):
    parent = ''
    for elem in root.findall(
            ".//{http://www.metaventis.com/ns/cockpit/sync/1.0}group"):
        for child in elem.findall("{http://www.metaventis.com/ns/cockpit/sync/1.0}sourcedid/{http://www.metaventis.com/ns/cockpit/sync/1.0}id"):
            groupid = child.text
        # use short or long as course info
        for child in elem.findall("{http://www.metaventis.com/ns/cockpit/sync/1.0}description/{http://www.metaventis.com/ns/cockpit/sync/1.0}short"):
            name = child.text
            # print(name)
        for child in elem.findall("{http://www.metaventis.com/ns/cockpit/sync/1.0}relationship/{http://www.metaventis.com/ns/cockpit/sync/1.0}sourcedid/{http://www.metaventis.com/ns/cockpit/sync/1.0}id"):
            parent = child.text
        groups.append(Group(groupid, name, parent))


def readMemberships(memberships):
    i = 0
    for elem in root.findall(
            ".//{http://www.metaventis.com/ns/cockpit/sync/1.0}membership"):

        for child in elem.findall("{http://www.metaventis.com/ns/cockpit/sync/1.0}sourcedid/{http://www.metaventis.com/ns/cockpit/sync/1.0}id"):
            groupid = child.text
        for child in elem.findall("{http://www.metaventis.com/ns/cockpit/sync/1.0}member/{http://www.metaventis.com/ns/cockpit/sync/1.0}sourcedid/{http://www.metaventis.com/ns/cockpit/sync/1.0}id"):
            nameid = child.text
        memberships.append(Membership(i, groupid, nameid))
        i += 1


def returnCoursesOfStudent(studentid):
    courseslist = []
    for course in [
            membership.groupid for membership in memberships
            if membership.nameid == studentid]:
        groupname = [group.name for group in groups
                     if group.groupid == course][0]
        # print(groupname)
        if groupname != "":
            courseslist.append(groupname)
    return courseslist


def returnUsername(given, last, typ):
    if typ == "vorname.nachname":
        username = given.translate(mappings.mappingusername).split(" ")[0] + "." + last.translate(mappings.mappingusername).replace(
            " ", "").replace("-", "")
        # print(f"{username}")
        if username in mappings.alternative_usernames:
            username = mappings.alt_usernames[username]
            # print(f"Habe alternativen username gespeichert: {username}")
    if typ == "kurzform":
        username = given.translate(mappings.mappingusername).split(" ")[0][:4] + last.translate(mappings.mappingusername).replace(
            " ", "").replace("-", "")[:4]
    return username.lower()


def returnKlasseOfUser(user):
    klassen = returnCoursesOfStudent(user.lehrerid)
    # print(klassen)
    mappingklassen = mappings.mappingklassen
    # print(mappingklassen)
    for item in mappingklassen:
        if item+f"{schuljahr}" in klassen:
            return mappingklassen[item]


def returnUntisName(user):
    bday = user.birthday.split(".")
    if "X" in user.lehrerid:
        return returnUsername(user.given, user.name, "kurzform")
    else:
        try:
            untisname = f"{user.name.translate(mappings.mappinguntis)}_{user.given.translate(mappings.mappinguntis)}_{bday[2]}{bday[1]}{bday[0]}"
        except:
            print(f"Fehler bei {user}, konnte kein Untisname erstellt werden.")
    return untisname


def readFile(users, groups, memberships):
    readUsers(users)
    readGroups(groups)
    readMemberships(memberships)


def webuntisUid(user):
    return returnUsername(user.given, user.name, "kurzform") if "X" in user.lehrerid else user.lehrerid[10:]


def userNameUntiscleaned(user):
    return user.name.translate(mappings.mappinguntis)


def userGivenUntiscleaned(user):
    return user.given.translate(mappings.mappinguntis)


def userEmailIfTeacher(user):
    return user.email if (user.institutionrole == "faculty" or user.institutionrole == "extern") else f"{user.username}@luisengym.de"


def returnUsernameCSV(user):
    return user.username


def returnUsernameNC(user):
    return f'{user.username}-sso' if "X" in user.lehrerid else user.lehrerid[10:]


def returnBirthday(user):
    return user.birthday


def returnQuota(user):
    return 20000 if "X" in user.lehrerid else 1000


def returnInitialPassword(user):
    return f'{user.lehrerid[-3:]}{user.username[-2:]}{stripHyphensFromBirthday(user.birthday)[:3]}{user.username[:2]}'


def returnCoursesAsString(courses):
    return f'{"##".join(courses)}'


def returnWebuntisRole(user):
    return "Teacher" if "X" in user.lehrerid else "Student"


def createKeyCloakCSV(nameOfOutputCsv: str):
    with open(nameOfOutputCsv, "w", encoding="utf-8") as f:
        mappingSpaltentitelCSV = mappings.mappingSpaltentitelCSV
        f.write(
            f'{mappingSpaltentitelCSV[0]};{mappingSpaltentitelCSV[1]};{mappingSpaltentitelCSV[2]};{mappingSpaltentitelCSV[3]};{mappingSpaltentitelCSV[4]};{mappingSpaltentitelCSV[5]};{mappingSpaltentitelCSV[6]};{mappingSpaltentitelCSV[7]};{mappingSpaltentitelCSV[8]};{mappingSpaltentitelCSV[9]};{mappingSpaltentitelCSV[10]};{mappingSpaltentitelCSV[11]};{mappingSpaltentitelCSV[12]};{mappingSpaltentitelCSV[13]}\n')
        for user in users:
            courses = returnCoursesOfStudent(user.lehrerid)
            mappingSpaltenschleife = {
                0: 'luisengymnasium-duesseldorf',
                1: f'{returnUntisName(user)}',
                2: f'{webuntisUid(user)}',
                3: f'{userNameUntiscleaned(user)}',
                4: f'{userGivenUntiscleaned(user)}',
                5: f'{returnKlasseOfUser(user)}',
                6: f'{userEmailIfTeacher(user)}',
                7: f'{returnUsernameCSV(user)}',
                8: f'{returnBirthday(user)}',
                9: f'{returnQuota(user)}',
                10: f'{returnInitialPassword(user)}',
                11: f'{returnCoursesAsString(courses)}',
                12: f'{returnUsernameNC(user)}',
                13: f'{returnWebuntisRole(user)}'
            }
            f.write(
                f'{mappingSpaltenschleife[0]};{mappingSpaltenschleife[1]};{mappingSpaltenschleife[2]};{mappingSpaltenschleife[3]};{mappingSpaltenschleife[4]};{mappingSpaltenschleife[5]};{mappingSpaltenschleife[6]};{mappingSpaltenschleife[7]};{mappingSpaltenschleife[8]};{mappingSpaltenschleife[9]};{mappingSpaltenschleife[10]};{mappingSpaltenschleife[11]};{mappingSpaltenschleife[12]};{mappingSpaltenschleife[13]}\n')


def createKeyCloakCSVTeacher(nameOfOutputCsv: str):
    with open(nameOfOutputCsv + "_teachers.csv", "w", encoding="utf-8") as f:
        mappingSpaltentitelCSV = mappings.mappingSpaltentitelCSV
        f.write(
            f'{mappingSpaltentitelCSV[0]};{mappingSpaltentitelCSV[1]};{mappingSpaltentitelCSV[2]};{mappingSpaltentitelCSV[3]};{mappingSpaltentitelCSV[4]};{mappingSpaltentitelCSV[5]};{mappingSpaltentitelCSV[6]};{mappingSpaltentitelCSV[7]};{mappingSpaltentitelCSV[8]};{mappingSpaltentitelCSV[9]};{mappingSpaltentitelCSV[10]};{mappingSpaltentitelCSV[11]};{mappingSpaltentitelCSV[12]};{mappingSpaltentitelCSV[13]}\n')
        for user in users:
            if user.institutionrole == 'faculty':  # Filter for teachers
                courses = returnCoursesOfStudent(user.lehrerid)
                mappingSpaltenschleife = {
                    0: 'luisengymnasium-duesseldorf',
                    1: f'{returnUntisName(user)}',
                    2: f'{webuntisUid(user)}',
                    3: f'{userNameUntiscleaned(user)}',
                    4: f'{userGivenUntiscleaned(user)}',
                    5: f'{returnKlasseOfUser(user)}',
                    6: f'{userEmailIfTeacher(user)}',
                    7: f'{returnUsernameCSV(user)}',
                    8: f'{returnBirthday(user)}',
                    9: f'{returnQuota(user)}',
                    10: f'{returnInitialPassword(user)}',
                    11: f'{returnCoursesAsString(courses)}',
                    12: f'{returnUsernameNC(user)}',
                    13: f'{returnWebuntisRole(user)}'
                }
                f.write(
                    f'{mappingSpaltenschleife[0]};{mappingSpaltenschleife[1]};{mappingSpaltenschleife[2]};{mappingSpaltenschleife[3]};{mappingSpaltenschleife[4]};{mappingSpaltenschleife[5]};{mappingSpaltenschleife[6]};{mappingSpaltenschleife[7]};{mappingSpaltenschleife[8]};{mappingSpaltenschleife[9]};{mappingSpaltenschleife[10]};{mappingSpaltenschleife[11]};{mappingSpaltenschleife[12]};{mappingSpaltenschleife[13]}\n')


def createKeyCloakCSVStudent(nameOfOutputCsv: str):
    with open(nameOfOutputCsv + "_students.csv", "w", encoding="utf-8") as f:
        mappingSpaltentitelCSV = mappings.mappingSpaltentitelCSV
        f.write(
            f'{mappingSpaltentitelCSV[0]};{mappingSpaltentitelCSV[1]};{mappingSpaltentitelCSV[2]};{mappingSpaltentitelCSV[3]};{mappingSpaltentitelCSV[4]};{mappingSpaltentitelCSV[5]};{mappingSpaltentitelCSV[6]};{mappingSpaltentitelCSV[7]};{mappingSpaltentitelCSV[8]};{mappingSpaltentitelCSV[9]};{mappingSpaltentitelCSV[10]};{mappingSpaltentitelCSV[11]};{mappingSpaltentitelCSV[12]};{mappingSpaltentitelCSV[13]}\n')
        for user in users:
            if user.institutionrole == 'Student':  # Filter for students
                courses = returnCoursesOfStudent(user.lehrerid)
                mappingSpaltenschleife = {
                    0: 'luisengymnasium-duesseldorf',
                    1: f'{returnUntisName(user)}',
                    2: f'{webuntisUid(user)}',
                    3: f'{userNameUntiscleaned(user)}',
                    4: f'{userGivenUntiscleaned(user)}',
                    5: f'{returnKlasseOfUser(user)}',
                    6: f'{userEmailIfTeacher(user)}',
                    7: f'{returnUsernameCSV(user)}',
                    8: f'{returnBirthday(user)}',
                    9: f'{returnQuota(user)}',
                    10: f'{returnInitialPassword(user)}',
                    11: f'{returnCoursesAsString(courses)}',
                    12: f'{returnUsernameNC(user)}',
                    13: f'{returnWebuntisRole(user)}'
                }
                f.write(
                    f'{mappingSpaltenschleife[0]};{mappingSpaltenschleife[1]};{mappingSpaltenschleife[2]};{mappingSpaltenschleife[3]};{mappingSpaltenschleife[4]};{mappingSpaltenschleife[5]};{mappingSpaltenschleife[6]};{mappingSpaltenschleife[7]};{mappingSpaltenschleife[8]};{mappingSpaltenschleife[9]};{mappingSpaltenschleife[10]};{mappingSpaltenschleife[11]};{mappingSpaltenschleife[12]};{mappingSpaltenschleife[13]}\n')


def createKeyCloakCSVNoPW(nameOfOutputCsv: str):
    with open(nameOfOutputCsv, "w", encoding="utf-8") as f:
        mappingSpaltentitelCSV = mappings.mappingSpaltentitelCSV
        f.write(
            f'{mappingSpaltentitelCSV[0]};{mappingSpaltentitelCSV[1]};{mappingSpaltentitelCSV[2]};{mappingSpaltentitelCSV[3]};{mappingSpaltentitelCSV[4]};{mappingSpaltentitelCSV[6]};{mappingSpaltentitelCSV[7]};{mappingSpaltentitelCSV[8]};{mappingSpaltentitelCSV[9]};{mappingSpaltentitelCSV[11]};{mappingSpaltentitelCSV[12]};{mappingSpaltentitelCSV[13]}\n')
        for user in users:
            courses = returnCoursesOfStudent(user.lehrerid)
            mappingSpaltenschleife = {
                0: 'luisengymnasium-duesseldorf',
                1: f'{returnUntisName(user)}',
                2: f'{webuntisUid(user)}',
                3: f'{userNameUntiscleaned(user)}',
                4: f'{userGivenUntiscleaned(user)}',
                6: f'{userEmailIfTeacher(user)}',
                7: f'{returnUsernameCSV(user)}',
                8: f'{returnBirthday(user)}',
                9: f'{returnQuota(user)}',
                11: f'{returnCoursesAsString(courses)}',
                12: f'{returnUsernameNC(user)}',
                13: f'{returnWebuntisRole(user)}'
            }
            f.write(
                f'{mappingSpaltenschleife[0]};{mappingSpaltenschleife[1]};{mappingSpaltenschleife[2]};{mappingSpaltenschleife[3]};{mappingSpaltenschleife[4]};{mappingSpaltenschleife[6]};{mappingSpaltenschleife[7]};{mappingSpaltenschleife[8]};{mappingSpaltenschleife[9]};{mappingSpaltenschleife[11]};{mappingSpaltenschleife[12]};{mappingSpaltenschleife[13]}\n')


def createKeyCloakCSVNoPW2(nameOfOutputCsv: str):
    mappingSpaltentitelCSV = mappings.mappingSpaltentitelCSV
    header = f'{mappingSpaltentitelCSV[0]};{mappingSpaltentitelCSV[1]};{mappingSpaltentitelCSV[2]};{mappingSpaltentitelCSV[3]};{mappingSpaltentitelCSV[4]};{mappingSpaltentitelCSV[6]};{mappingSpaltentitelCSV[7]};{mappingSpaltentitelCSV[8]};{mappingSpaltentitelCSV[9]};{mappingSpaltentitelCSV[11]};{mappingSpaltentitelCSV[12]};{mappingSpaltentitelCSV[13]}\n'
    fileCount = 1
    entryCount = 0

    f = open(nameOfOutputCsv + str(fileCount) + '.csv', "w", encoding="utf-8")
    f.write(header)

    for user in users:
        if entryCount == 200:
            f.close()
            fileCount += 1
            entryCount = 0
            f = open(nameOfOutputCsv + str(fileCount) +
                     '.csv', "w", encoding="utf-8")
            f.write(header)

        courses = returnCoursesOfStudent(user.lehrerid)
        mappingSpaltenschleife = {
            0: 'luisengymnasium-duesseldorf',
            1: f'{returnUntisName(user)}',
            2: f'{webuntisUid(user)}',
            3: f'{userNameUntiscleaned(user)}',
            4: f'{userGivenUntiscleaned(user)}',
            6: f'{userEmailIfTeacher(user)}',
            7: f'{returnUsernameCSV(user)}',
            8: f'{returnBirthday(user)}',
            9: f'{returnQuota(user)}',
            11: f'{returnCoursesAsString(courses)}',
            12: f'{returnUsernameNC(user)}',
            13: f'{returnWebuntisRole(user)}'
        }
        f.write(
            f'{mappingSpaltenschleife[0]};{mappingSpaltenschleife[1]};{mappingSpaltenschleife[2]};{mappingSpaltenschleife[3]};{mappingSpaltenschleife[4]};{mappingSpaltenschleife[6]};{mappingSpaltenschleife[7]};{mappingSpaltenschleife[8]};{mappingSpaltenschleife[9]};{mappingSpaltenschleife[11]};{mappingSpaltenschleife[12]};{mappingSpaltenschleife[13]}\n')

        entryCount += 1
    f.close()


def stripHyphensFromBirthday(birthday: str):
    return birthday.replace("-", "")


def returnUsersOfCourse(groupid):
    users = []
    for user in [
            membership.nameid for membership in memberships
            if membership.groupid == groupid]:
        users.append(returnUserGivenAndName(user))
    return users


def returnUserGivenAndName(studentid):
    last = [user.name for user in users if studentid in user.lehrerid][0]
    given = [user.given for user in users if studentid in user.lehrerid][0]
    username = [user.username for user in users if studentid in user.lehrerid][0]
    return {"id": studentid, "given": given, "last": last, "username": username}


def returnGroupId(groupname: str):
    return [group.groupid for group in groups if group.name == groupname][0]


def checkForDuplicates():
    usernames = [user.username for user in users]
    seen = set()
    dups = []
    for username in usernames:
        if username in seen:
            dups.append(username)

        else:
            seen.add(username)
    if len(dups) == 0:
        print("Keine Duplikate.")
    if len(dups) > 0:
        print(dups)


def renameGroups():
    for group in groups:
        # print(group.name)
        if "Klasse" in group.name:
            group.name = f'{group.name[7:].replace(" ", "").replace("Schueler", "S").replace("Lehrer", "L").replace("--", "").replace("-", "").replace(")", "").replace("UNESCO","U")}'+f"{schuljahr}"
            # group.name = f'{group.name[7:].replace(" ", "").replace("Schueler", "S").replace("Lehrer", "L").replace("--", "-").replace(")", "").replace("UNESCO","U")}'+f"{schuljahr}"
            # print(group.name)
        if "BI8" in group.name:
            start = group.name.rfind("(")
            ende = group.name.rfind(")")
            try:
                m = re.search(r"\d", group.name)
                digitfound = m.group(0)
            except:
                digitfound = ''
            templist = group.name[start -
                                  3:ende].replace(" ", "").replace("(9", "").split(",")
            group.name = f"{templist[0]}{templist[1] if templist[1] == 'GK' or templist[1] == 'LK' else ''}{digitfound if templist[1] == 'GK' or templist[1] == 'LK' else ''}{templist[2]}{templist[3]}".replace(
                "Schueler", "S").replace("Lehrer", "L").replace("--", "-").replace(")", "")+f"{schuljahr}"
            # group.name = f"{templist[0]}-{templist[1] if templist[1] == 'GK' or templist[1] == 'LK' else ''}{digitfound if templist[1] == 'GK' or templist[1] == 'LK' else ''}-{templist[2]}-{templist[3]}".replace(
            #     "Schueler", "S").replace("Lehrer", "L").replace("--", "-").replace(")", "")+f"-{schuljahr}"
        elif "(" in group.name:
            start = group.name.rfind("(")
            ende = group.name.rfind(")")
            try:
                m = re.search(r"\d", group.name)
                digitfound = m.group(0)
            except:
                digitfound = ''
            templist = group.name[start+1:ende].replace(
                " ", "").replace("UNESCO", "U").split(",")
            group.name = f"{templist[0]}{templist[1] if templist[1] == 'GK' or templist[1] == 'LK' else ''}{digitfound if templist[1] == 'GK' or templist[1] == 'LK' else ''}{templist[2]}{templist[3]}".replace(
                "Schueler", "S").replace("Lehrer", "L").replace("--", "-").replace(")", "")+f"{schuljahr}"
            # group.name = f"{templist[0]}-{templist[1] if templist[1] == 'GK' or templist[1] == 'LK' else ''}{digitfound if templist[1] == 'GK' or templist[1] == 'LK' else ''}-{templist[2]}-{templist[3]}".replace(
            #     "Schueler", "S").replace("Lehrer", "L").replace("--", "-").replace(")", "")+f"-{schuljahr}"
        if "Alle - Schueler" in group.name:
            group.name = "Alle-Schueler".replace(
                "Schueler", "S").replace("Lehrer", "L").replace(")", "").replace("-", "")
        if "Alle - Lehrer" in group.name:
            group.name = "Alle-Lehrer".replace("Schueler",
                                               "S").replace("Lehrer", "L").replace(")", "").replace("-", "")
        if "Fach" in group.name:
            group.name = mappings.mappinggroups[group.name]
            # print(group.name)
        if "Bereich" in group.name:
            group.name = mappings.mappinggroups[group.name]
            # print(group.name)


def printUserCredentials(exportdate, importurl):
    document = []

    def addTitle(doc, fontSize, color, text):
        doc.append(Spacer(1, 20))
        doc.append(
            Paragraph(text,
                      ParagraphStyle(
                          name="Name",
                          fontName="Courier",
                          fontSize=fontSize,
                          color=color,
                          alignment=TA_CENTER
                      )))
        doc.append(Spacer(1, 50))
        return doc

    def addParagraphs(doc):
        pass

    def addTable(doc, data):
        table = Table(data, rowHeights=65)
        table.setStyle(TableStyle([
            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.green),
            ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
            ('BACKGROUND', (0, 0), (-1, 2), colors.lightgrey)
        ]))
        doc.append(table)
        return doc

    for klasse in mappings.klassenliste:
        # print(klasse)
        for user in users:
            kurse = returnCoursesOfStudent(user.lehrerid)
            # print(klasse)
            # print(kurse)
            if klasse in kurse:
                # print(klasse)
                addTitle(document, 36, colors.blue, "Benutzername:")
                addTitle(document, 20, colors.black, f"{user.username}")
                addTitle(document, 36, colors.blue, "Passwort:")
                addTitle(document, 20, colors.black, f"{user.initialpassword}")
                addTitle(document, 36, colors.blue, "Anleitung:")
                addTitle(document, 20, colors.black, importurl)
                document.append(Image("qr-code.png", 8*cm, 8*cm))
                document.append(PageBreak())
        SimpleDocTemplate(
            f"./exports/{exportdate}_{klasse}.pdf",
            pagesize=A4,
            rightMargin=12,
            leftMargin=12,
            topMargin=12,
            bottomMargin=6
        ).build(document)
        document = []

    for user in users:
        if user.institutionrole != "Student":
            addTitle(document, 36, colors.blue, "Benutzername:")
            addTitle(document, 20, colors.black, f"{user.username}")
            addTitle(document, 36, colors.blue, "Passwort:")
            addTitle(document, 20, colors.black, f"{user.initialpassword}")
            addTitle(document, 36, colors.blue, "Anleitung:")
            addTitle(document, 20, colors.black, importurl)
            addTitle(document, 36, colors.blue, "QR-Code zur Anleitung:")
            document.append(Image("qr-code.png", 8*cm, 8*cm))
            document.append(PageBreak())
    SimpleDocTemplate(
        f"./exports/{exportdate}_lehrer.pdf",
        pagesize=A4,
        rightMargin=12,
        leftMargin=12,
        topMargin=12,
        bottomMargin=6
    ).build(document)
    document = []


def searchSchuljahr(xmlfile):
    for i in range(10):
        for j in range(10):
            with open(xmlfile) as f:
                if f"20{i}{j}/{i}{j+1}" in f.read():
                    print(f"{i}{j}/{i}{j+1}")
                    # return f"{i}{j}/{i}{j+1}"
                    return f"{i}{j}"
                if f"20{i}{j}/{i+1}0" in f.read():
                    print(f"{i}{j}/{i+1}0")
                    # return f"{i}{j}/{i+1}0"
                    return f"{i}{j}"


def returnGoerresUsernames(csvfile, outputfile, klasse):
    with open(csvfile) as f:
        reader = csv.reader(f)
        data = list(reader)

    data2 = []
    if ";" in data[1][0]:
        for line in data:
            data2.append(line[0].split(";"))
    else:
        data2 = data

    with open(outputfile, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["REALM", "AT_webuntisKurzname", "AT_webuntisUid", "US_lastName", "US_firstName", "webuntisKlasse", "US_email",
                        "US_username", "AT_birthday", "AT_ncQuota", "CR_password", "AT_nc.memberOf", "AT_colloxUid", "AT_webuntisRole"])

        for line in data2:
            vorname = line[0].strip()
            nachname = line[1].strip()
            username = returnUsername(vorname, nachname, 'kurzform')
            row = [f"luisengymnasium-duesseldorf", f"ZZ-{username}", f"GG-{username}", nachname, vorname, klasse, f"{username}@luisengym.de",
                   username, "", "1000", f"{username}@luisengym.de", f"Alle-S##{klasse}S23##Sek2-S", username, "Student"]
            writer.writerow(row)


def returnGeorresUsers(csvAlleGoerres, csvBeimLuisen):
    alleGoerres = []
    beimLuisen = []

    with open(csvAlleGoerres) as f:
        reader = csv.reader(f)
        alleGoerres = list(reader)

    with open(csvBeimLuisen) as f:
        reader = csv.reader(f)
        beimLuisen = list(reader)

    for item in alleGoerres:
        for user in beimLuisen:
            if SequenceMatcher(None, item[1], user[3]).ratio() > 0.8 and SequenceMatcher(None, item[7], user[4]).ratio() > 0.8:
                print(item)
                # if not SequenceMatcher(None, item[7], user[4]).ratio() > 0.8:
                #     print(item[1], item[7], user[3], user[4])
            # if item[1] == user[3]:
            #     print(item)
    # print(alleGoerres[5][1])
    # print(beimLuisen[5][3])
    # for user in alleGoerres:
    #     print(user)


def create_goerres_neu(keycloak, dat, output):
    # Einlesen der keycloak-Datei
    keycloak_df = pd.read_csv(keycloak, sep=";", usecols=[
                              'US_lastName', 'US_firstName'])

    # Einlesen der dat-Datei
    dat_df = pd.read_csv(dat, sep="|", usecols=['Nachname', 'Vorname'])

    # Listen für die neuen Nutzer
    new_users_firstname = []
    new_users_lastname = []

    # Überprüfen Sie jeden Nutzer aus der 'dat'-Datei
    for index, row in dat_df.iterrows():
        lastname = row['Nachname']
        firstname = row['Vorname']

        # Überprüfen Sie, ob der Nachname bereits existiert
        if lastname in keycloak_df['US_lastName'].values:
            # Wenn ja, überprüfen Sie, ob der Vorname unter den passenden Nachnamen existiert
            matching_users = keycloak_df[keycloak_df['US_lastName'] == lastname]
            if firstname not in matching_users['US_firstName'].values:
                new_users_firstname.append(firstname)
                new_users_lastname.append(lastname)
        else:
            new_users_firstname.append(firstname)
            new_users_lastname.append(lastname)

    # Erstellen Sie eine neue DataFrame mit den neuen Nutzern
    goerres_neu_df = pd.DataFrame(list(
        zip(new_users_firstname, new_users_lastname)), columns=['vorname', 'nachname'])

    # Speichern Sie die neue DataFrame in einer CSV-Datei
    goerres_neu_df.to_csv(output, sep=';', index=False)


def rueckgabeSchuelerAusKlasse(klasse):
    for user in users:
        kurse = returnCoursesOfStudent(user.lehrerid)
        # print(klasse)
        # print(kurse)
        if klasse in kurse:
            print(f"{user.given} {user.name}")


def csv_neue_user(filealt, fileneu, output):
    with open(filealt, 'r') as f1, open(fileneu, 'r') as f2:
        old_data = csv.reader(f1, delimiter=';')
        new_data = csv.reader(f2, delimiter=';')
        old_uids = {row[2] for row in old_data}
        new_rows = [row for row in new_data if row[2] not in old_uids]
        if len(new_rows) != 0:
            print("Es gibt neue Schüler!")

    with open(output, 'w', newline='') as f:
        writer = csv.writer(f, delimiter=';')
        header = ["REALM", "AT_webuntisKurzname", "AT_webuntisUid", "US_lastName", "US_firstName", "webuntisKlasse", "US_email",
                  "US_username", "AT_birthday", "AT_ncQuota", "CR_password", "AT_nc.memberOf", "AT_colloxUid", "AT_webuntisRole"]
        writer.writerow(header)
        writer.writerows(new_rows)


def csv_verlassene_user(filealt, fileneu, output):
    with open(filealt, 'r') as f1, open(fileneu, 'r') as f2:
        old_data = csv.reader(f1, delimiter=';')
        new_data = csv.reader(f2, delimiter=';')
        new_uids = {row[2] for row in new_data}
        old_rows = [row for row in old_data if row[2] not in new_uids]
        if len(old_rows) != 0:
            print("Schüler haben die Schule verlassen!")

    with open(output, 'w', newline='') as f:
        writer = csv.writer(f, delimiter=';')
        header = ["REALM", "AT_webuntisKurzname", "AT_webuntisUid", "US_lastName", "US_firstName", "webuntisKlasse", "US_email",
                  "US_username", "AT_birthday", "AT_ncQuota", "CR_password", "AT_nc.memberOf", "AT_colloxUid", "AT_webuntisRole"]
        writer.writerow(header)
        writer.writerows(old_rows)


def moodle_output(schildfile, output):
    # CSV-Datei lesen
    df = pd.read_csv(schildfile, delimiter=';')

    # Nur benötigte Spalten auswählen
    df = df[['US_email', 'AT_nc.memberOf']]

    # Spalten umbenennen
    df.columns = ['username', 'profile_field_Klasse']

    # Neue CSV-Datei schreiben
    df.to_csv(output, index=False, sep=';')


def createAntonCsv(schildfile, ANTONExport, output):
    # Lese die csv Dateien
    df_schild = pd.read_csv(schildfile, sep=';', index_col=False)
    df_ANTON = pd.read_csv(ANTONExport, sep=';', index_col=False)

    # Nur Zeilen behalten, in denen AT_webuntisRole 'Student' ist
    df_schild = df_schild[df_schild['AT_webuntisRole'] == 'Student']

    # Umbenennen der Spalten für die Vereinfachung
    df_schild = df_schild.rename(columns={
                                 'US_firstName': 'Vorname', 'US_lastName': 'Nachname', 'webuntisKlasse': 'Klasse'})
    df_ANTON = df_ANTON.rename(columns={'Vorname': 'Vorname', 'Nachname': 'Nachname',
                               'Klasse': 'Klasse', 'Referenz': 'Referenz', 'Anmelde-Code': 'Anmelde-Code'})

    # Zusammenführen der DataFrames
    df = pd.merge(df_ANTON, df_schild[['Vorname', 'Nachname', 'Klasse']], on=[
                  'Vorname', 'Nachname'], how='outer')

    # Den Klassenwert aus schildfile übernehmen, wenn der Nutzer in beiden Dateien vorhanden ist
    df.loc[df['Klasse_y'].notna(), 'Klasse_x'] = df['Klasse_y']

    # Den Klassenwert auf "delete" setzen, wenn der Nutzer nur in ANTONExport.csv vorhanden ist
    df.loc[df['Klasse_y'].isna(), 'Klasse_x'] = 'delete'

    # Referenz und Anmelde-Code auf NaN setzen, wenn der Nutzer nur in schildfile vorhanden ist
    df.loc[df['Klasse_x'].isna(), ['Referenz', 'Anmelde-Code']] = pd.NA

    # Unnötige Spalten entfernen und die Spalten umbenennen
    df = df.drop(columns=['Klasse_y'])
    df = df.rename(columns={'Klasse_x': 'Klasse'})

    # Speichern der Ergebnisse in der csv Datei
    df.to_csv(output, sep=';', index=False)


def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()


def returnElternUsernames(csvfile, outputfile):
    with open(csvfile) as f:
        reader = csv.reader(f)
        next(reader)  # Überspringt den Header
        data = list(reader)

    data2 = []
    if ";" in data[0][0]:
        for line in data:
            data2.append(line[0].split(";"))
    else:
        data2 = data

    seen = set()  # Set zum Speichern von bereits gesehenen Zeilen
    with open(outputfile, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["REALM", "AT_webuntisUid", "AT_webuntisKurzname", "US_lastName", "US_firstName", "US_email", "CR_password",
                        "US_username", "AT_webuntisRole"])

        for line in data2:
            vorname = line[0].strip()
            nachname = line[1].strip()
            username = returnUsername(vorname, nachname, 'kurzform')
            email = line[2]
            row = [f"luisengymnasium-duesseldorf", f"ZEltern-{username}", f"ZEltern-{username}", nachname, vorname, email, email,
                   returnUsername(vorname, nachname, "vorname.nachname"), "Parent"]

            # Wandelt die Liste in ein Tupel um, damit sie in einem Set gespeichert werden kann
            row_tup = tuple(row)
            if row_tup not in seen:  # Wenn die Zeile nicht bereits gesehen wurde, fügt sie hinzu und schreibt sie
                seen.add(row_tup)
                writer.writerow(row)


def createElternaccounts(formsdatei, schildexport, kontrolloutput, outputfile):
    forms = pd.read_csv(formsdatei, delimiter=",", quotechar='"')
    schild = pd.read_csv(schildexport, delimiter=";", quotechar='"')

    outputtest = []
    output = []

    for idx, form_row in forms.iterrows():
        for i in range(1, 4):
            fname = form_row[f'Vorname des {i}. Kindes']
            lname = form_row[f'Nachname des {i}. Kindes']
            klasse = form_row[f'Klasse des {i}. Kindes']

            matching_schild = None
            second_matching_schild = None
            highest_similarity = 0
            second_highest_similarity = 0
            for _, schild_row in schild.iterrows():
                if schild_row['webuntisKlasse'] == klasse:
                    full_name_schild = f"{schild_row['US_firstName']} {schild_row['US_lastName']}"
                    full_name_forms = f"{fname} {lname}"
                    similarity = similar(full_name_schild, full_name_forms)
                    if similarity > highest_similarity:
                        second_highest_similarity = highest_similarity
                        highest_similarity = similarity
                        second_matching_schild = matching_schild
                        matching_schild = schild_row
                    elif similarity > second_highest_similarity:
                        second_highest_similarity = similarity
                        second_matching_schild = schild_row

            if matching_schild is not None:
                outputtest.append([form_row['Vorname des Elternteils'], form_row['Nachname des Elternteils'], fname, lname, matching_schild['US_firstName'],
                                  matching_schild['US_lastName'], matching_schild['AT_webuntisUid'], highest_similarity, second_highest_similarity])
                output.append([form_row['Vorname des Elternteils'], form_row['Nachname des Elternteils'],
                              form_row["Emailadresse des Elternteils"].lower(), matching_schild['AT_webuntisUid']])

    output_df = pd.DataFrame(outputtest, columns=['Eltern Vorname', 'Eltern Nachname', 'Kind Vorname (forms)', 'Kind Nachname (forms)',
                             'Kind Vorname (schild)', 'Kind Nachname (schild)', 'AT_webuntisUid', 'Best Similarity Score', 'Second Best Similarity Score'])
    output_df.to_csv(kontrolloutput, index=False, sep=';')
    output_df2 = pd.DataFrame(
        output, columns=['Eltern Vorname', 'Eltern Nachname', 'email', 'student-id'])
    print(output_df2)
    output_df2.to_csv(outputfile, index=False, sep=';')


if __name__ == "__main__":

    inputaktuell = "SchILD20230823.xml"
    inputalt = "SchILD20230822.xml"
    keycloakexport = 'keycloak20230125.csv'
    goerresdat = 'SchuelerLeistungsdatenQ1.dat'
    goerresstufe = "Q1"
    forms_eltern = "forms2.csv"
    exportdate = ''.join([i for i in inputaktuell if i.isdigit()])
    exportdate_alt = ''.join([i for i in inputalt if i.isdigit()])
    print(exportdate)
    users = []
    groups = []
    memberships = []
    tree = ET.parse(inputaktuell)
    schuljahr = searchSchuljahr(inputaktuell).replace("/", "")
    root = tree.getroot()
    readFile(users, groups, memberships)
    renameGroups()

    '''csv's erstellen'''
    createKeyCloakCSV(f"00-Export{exportdate}.csv")
    createKeyCloakCSVStudent(f"00-Export{exportdate}.csv")
    createKeyCloakCSVTeacher(f"00-Export{exportdate}.csv")
    createKeyCloakCSVNoPW2(f"01-Export{exportdate}noPW.csv")
    csv_neue_user(f"Export{exportdate_alt}.csv",
                  f"Export{exportdate}.csv", f"02-schild_neu{exportdate}.csv")
    csv_verlassene_user(f"Export{exportdate_alt}.csv",
                        f"Export{exportdate}.csv", f"03-schild_verlassen{exportdate}.csv")
    moodle_output(f"Export{exportdate}.csv", f"04-moodle{exportdate}.csv")
    createAntonCsv(f"Export{exportdate}.csv",
                   "ANTONExport.csv", f"05-anton_import{exportdate}.csv")

    '''Goerresuser'''
    create_goerres_neu(keycloakexport, goerresdat,
                       f"06-goerres_neu{goerresstufe}-{exportdate}.csv")
    returnGoerresUsernames(f"06-goerres_neu{goerresstufe}-{exportdate}.csv",
                           f"07-goerresimport-{goerresstufe}-{exportdate}.csv", "Q1")

    '''elternaccounts'''
    createElternaccounts(forms_eltern, f"00-Export{exportdate}.csv",
                         f"08-elternaccounts-control-{exportdate}.csv", f"08-elternaccounts-{exportdate}.csv")
    returnElternUsernames(
        f"08-elternaccounts-{exportdate}.csv", f"09-elternaccounts-kc-import-{exportdate}.csv")
    '''pdfs erstellen'''
    # printUserCredentials(exportdate, "docs.luisen-gymnasium.de")

    '''ID eines Users nach Namen ausgeben'''
    # for user in users:
    #     if user.name == "mustermann":
    #         print(user.lehrerid)

    '''Kurse eines Users nach ID ausgeben'''
    # print(returnCoursesOfStudent("ID-2309553-0102X"))

    '''Alle Kurse/Gruppen zurueckgeben'''
    # allgroups = []
    # for user in users:
    #     allgroups += returnCoursesOfStudent(user.lehrerid)
    # allgroups = list(set(allgroups))
    # for group in allgroups:
    #     if "Lie" in group:
    #         print(group)

    '''Alle Schüler einer Klasse zurückgeben'''
    # rueckgabeSchuelerAusKlasse("06BS22")
    # rueckgabeSchuelerAusKlasse("06AS22")
    # rueckgabeSchuelerAusKlasse("MGK1Q2Lie22")
    # rueckgabeSchuelerAusKlasse("PHGK1EFLie22")
    # rueckgabeSchuelerAusKlasse("IFGK1EFLie22")
    # rueckgabeSchuelerAusKlasse("IFGK1Q1Lie22")
