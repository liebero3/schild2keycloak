import xml.etree.ElementTree as ET
import re
import mappings
from turtle import color
from mmap import PAGESIZE
from ctypes import alignment
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.units import cm
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors


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
        if groupname != "":
            courseslist.append(groupname)
    return courseslist


def returnUsername(given, last, typ):
    if typ == "vorname.nachname":
        username = given.translate(mappings.mappingusername).split(" ")[0] + "." + \
            last.translate(mappings.mappingusername).replace(
                " ", "").replace("-", "")
    if typ == "kurzform":
        username = given.translate(mappings.mappingusername).split(" ")[0][:4] + \
            last.translate(mappings.mappingusername).replace(
                " ", "").replace("-", "")[:4]
    return username.lower()


def returnKlasseOfUser(user):
    klassen = returnCoursesOfStudent(user.lehrerid)
    mappingklassen = mappings.mappingklassen
    for item in mappingklassen:
        if item in klassen:
            return mappingklassen[item]


def returnUntisName(user):
    bday = user.birthday.split(".")
    if "X" in user.lehrerid:
        return returnUsername(user.given, user.name, "kurzform")
    else:
        try:
            untisname = f"{user.name.translate(mappings.mappinguntis)}_{user.given.translate(mappings.mappinguntis)}_{bday[2]}{bday[1]}{bday[0]}"
        except:
            print(f"Fehler bei {user}, konnte keinen Untisnamen erstellen")
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
    return user.email if user.institutionrole == "faculty" else ""


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
            group.name = group.name[7:].replace(" ", "").replace(
                "Schueler", "S").replace("Lehrer", "L").replace("--", "-").replace(")", "")
            # print(group.name)
        if "(" in group.name:
            start = group.name.rfind("(")
            ende = group.name.rfind(")")
            try:
                m = re.search(r"\d", group.name)
                digitfound = m.group(0)
            except:
                digitfound = ''
            templist = group.name[start+1:ende].replace(" ", "").split(",")
            group.name = f"2122-{templist[0]}-{templist[1] if templist[1] == 'GK' or templist[1] == 'LK' else ''}{digitfound if templist[1] == 'GK' or templist[1] == 'LK' else ''}-{templist[2]}-{templist[3]}".replace(
                "Schueler", "S").replace("Lehrer", "L").replace("--", "-").replace(")", "")
        if "Alle - Schueler" in group.name:
            group.name = "Alle-Schueler".replace(
                "Schueler", "S").replace("Lehrer", "L").replace(")", "")
        if "Alle - Lehrer" in group.name:
            group.name = "Alle-Lehrer".replace("Schueler",
                                               "S").replace("Lehrer", "L").replace(")", "")
        if "Fach" in group.name:
            group.name = mappings.mappinggroups[group.name].replace(
                "Schueler", "S").replace("Lehrer", "L").replace("--", "-").replace(")", "")


def printUserCredentials(filename, importurl):
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
        for user in users:
            kurse = returnCoursesOfStudent(user.lehrerid)
            if klasse in kurse:
                addTitle(document, 36, colors.blue, "Benutzername:")
                addTitle(document, 20, colors.black, f"{user.username}")
                addTitle(document, 36, colors.blue, "Passwort:")
                addTitle(document, 20, colors.black, f"{user.initialpassword}")
                addTitle(document, 36, colors.blue, "URL:")
                addTitle(document, 20, colors.black, importurl)
                addTitle(document, 36, colors.blue, "QR-Code:")
                document.append(Image("qr-code.png", 8*cm, 8*cm))
        SimpleDocTemplate(
            f"./exports/{klasse}.pdf",
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
            addTitle(document, 36, colors.blue, "URL:")
            addTitle(document, 20, colors.black, importurl)
            addTitle(document, 36, colors.blue, "QR-Code:")
            document.append(Image("qr-code.png", 8*cm, 8*cm))
    SimpleDocTemplate(
        f"./exports/lehrer.pdf",
        pagesize=A4,
        rightMargin=12,
        leftMargin=12,
        topMargin=12,
        bottomMargin=6
    ).build(document)
    document = []

    for user in users:
        addTitle(document, 36, colors.blue, "Benutzername:")
        addTitle(document, 20, colors.black, f"{user.username}")
        addTitle(document, 36, colors.blue, "Passwort:")
        addTitle(document, 20, colors.black, f"{user.initialpassword}")
        addTitle(document, 36, colors.blue, "URL:")
        addTitle(document, 20, colors.black, importurl)
        addTitle(document, 36, colors.blue, "QR-Code:")
        document.append(Image("qr-code.png", 8*cm, 8*cm))
    SimpleDocTemplate(
        f"./exports/{filename}",
        pagesize=A4,
        rightMargin=12,
        leftMargin=12,
        topMargin=12,
        bottomMargin=6
    ).build(document)
    document = []


if __name__ == "__main__":
    users = []
    groups = []
    memberships = []
    tree = ET.parse("SchILD20220624.xml")
    root = tree.getroot()
    readFile(users, groups, memberships)
    renameGroups()
    createKeyCloakCSV("Export20220624.csv")
    checkForDuplicates()
    # printUserCredentials("usernames20220624.pdf", "https://ajax.webuntis.com")
    for user in users:
        if user.name == "Salzwedel":
            print(user.lehrerid)
    print(returnCoursesOfStudent("ID-2309553-0102X"))
    # for user in users:
    #     kurse = returnCoursesOfStudent(user.lehrerid)
    #     if "06C-S" in kurse:
    #         print(f"{user.name}, {user.given}")

    # print(returnCoursesOfStudent("ID-blub-blub"))

    # print(returnCoursesOfStudent('1139685'))
    # for user in users:
    #     print(user.lehrerid)
    # allgroups = []
    # for user in users:
    #     allgroups += returnCoursesOfStudent(user.lehrerid)
    # print(list(set(allgroups)))
    # with open("Export20220301v12.csv","r") as f:
    #     n = 0
    #     for line in f.readlines():
    #         if "Alle-S##Q2-S" in line:
    #             n += 1
    #     print(701-n)
