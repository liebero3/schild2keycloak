from ctypes import alignment
from mmap import PAGESIZE
from turtle import color
import xml.etree.ElementTree as ET
import re
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.units import cm
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
# from reportlab.pdfgen.canvas import Canvas
import qrcode


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
            # print(given, name)
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
        courseslist.append(groupname)
    return courseslist


def returnUsername(given, last, typ):
    if typ == "vorname.nachname":
        username = given.translate(mappingusername).split(" ")[0] + "." + \
            last.translate(mappingusername).replace(" ", "").replace("-", "")
    if typ == "kurzform":
        username = given.translate(mappingusername).split(" ")[0][:4] + \
            last.translate(mappingusername).replace(
                " ", "").replace("-", "")[:4]
    return username.lower()


mappinguntis = {
    # ord(u"Ä"): u"Ae",
    # ord(u"ä"): u"ae",
    ord(u"Ë"): u"E",
    ord(u"ë"): u"e",
    ord(u"Ï"): u"I",
    ord(u"ï"): u"i",
    # ord(u"Ö"): u"Oe",
    # ord(u"ö"): u"oe",
    # ord(u"Ü"): u"Ue",
    # ord(u"ü"): u"ue",
    ord(u"Ÿ"): u"Y",
    ord(u"ÿ"): u"y",
    # ord(u"ß"): u"ss",
    ord(u"À"): u"A",
    ord(u"Á"): u"A",
    ord(u"Â"): u"A",
    ord(u"Ã"): u"A",
    ord(u"Å"): u"A",
    ord(u"Æ"): u"Ae",
    ord(u"Ç"): u"C",
    # ord(u"È"): u"E",
    # ord(u"É"): u"E",
    # ord(u"Ê"): u"E",
    ord(u"Ì"): u"I",
    ord(u"Í"): u"I",
    ord(u"Î"): u"I",
    ord(u"Ð"): u"D",
    ord(u"Ñ"): u"N",
    ord(u"Ò"): u"O",
    ord(u"Ó"): u"O",
    # ord(u"Ô"): u"O",
    ord(u"Õ"): u"O",
    ord(u"Ø"): u"Oe",
    ord(u"Œ"): u"Oe",
    ord(u"Ù"): u"U",
    ord(u"Ú"): u"U",
    ord(u"Û"): u"U",
    ord(u"Ý"): u"Y",
    ord(u"Þ"): u"Th",
    ord(u"à"): u"a",
    ord(u"á"): u"a",
    ord(u"â"): u"a",
    ord(u"ã"): u"a",
    ord(u"å"): u"a",
    ord(u"æ"): u"ae",
    ord(u"ç"): u"c",
    # ord(u"è"): u"e",
    # ord(u"é"): u"e",
    # ord(u"ê"): u"e",
    ord(u"ì"): u"i",
    ord(u"í"): u"i",
    ord(u"î"): u"i",
    ord(u"ð"): u"d",
    ord(u"ñ"): u"n",
    ord(u"ò"): u"o",
    ord(u"ó"): u"o",
    # ord(u"ô"): u"o",
    ord(u"õ"): u"o",
    ord(u"ø"): u"oe",
    ord(u"œ"): u"oe",
    ord(u"ù"): u"u",
    ord(u"ú"): u"u",
    ord(u"û"): u"u",
    ord(u"ý"): u"y",
    ord(u"þ"): u"Th",
    ord(u"Š"): u"S",
    ord(u"Ş"): u"S",
    ord(u"š"): u"s",
    ord(u"Č"): u"C",
    ord(u"ă"): u"a",
    ord(u"č"): u"c"
}
mappingusername = {
    ord(u"Ä"): u"Ae",
    ord(u"ä"): u"ae",
    ord(u"Ë"): u"E",
    ord(u"ë"): u"e",
    ord(u"Ï"): u"I",
    ord(u"ï"): u"i",
    ord(u"Ö"): u"Oe",
    ord(u"ö"): u"oe",
    ord(u"Ü"): u"Ue",
    ord(u"ü"): u"ue",
    ord(u"Ÿ"): u"Y",
    ord(u"ÿ"): u"y",
    ord(u"ß"): u"ss",
    ord(u"À"): u"A",
    ord(u"Á"): u"A",
    ord(u"Â"): u"A",
    ord(u"Ã"): u"A",
    ord(u"Å"): u"A",
    ord(u"Æ"): u"Ae",
    ord(u"Ç"): u"C",
    ord(u"È"): u"E",
    ord(u"É"): u"E",
    ord(u"Ê"): u"E",
    ord(u"Ì"): u"I",
    ord(u"Í"): u"I",
    ord(u"Î"): u"I",
    ord(u"Ð"): u"D",
    ord(u"Ñ"): u"N",
    ord(u"Ò"): u"O",
    ord(u"Ó"): u"O",
    ord(u"Ô"): u"O",
    ord(u"Õ"): u"O",
    ord(u"Ø"): u"Oe",
    ord(u"Œ"): u"Oe",
    ord(u"Ù"): u"U",
    ord(u"Ú"): u"U",
    ord(u"Û"): u"U",
    ord(u"Ý"): u"Y",
    ord(u"Þ"): u"Th",
    ord(u"à"): u"a",
    ord(u"á"): u"a",
    ord(u"â"): u"a",
    ord(u"ã"): u"a",
    ord(u"å"): u"a",
    ord(u"æ"): u"ae",
    ord(u"ç"): u"c",
    ord(u"è"): u"e",
    ord(u"é"): u"e",
    ord(u"ê"): u"e",
    ord(u"ì"): u"i",
    ord(u"í"): u"i",
    ord(u"î"): u"i",
    ord(u"ð"): u"d",
    ord(u"ñ"): u"n",
    ord(u"ò"): u"o",
    ord(u"ó"): u"o",
    ord(u"ô"): u"o",
    ord(u"õ"): u"o",
    ord(u"ø"): u"oe",
    ord(u"œ"): u"oe",
    ord(u"ù"): u"u",
    ord(u"ú"): u"u",
    ord(u"û"): u"u",
    ord(u"ý"): u"y",
    ord(u"þ"): u"Th",
    ord(u"Š"): u"S",
    ord(u"Ş"): u"S",
    ord(u"š"): u"s",
    ord(u"Č"): u"C",
    ord(u"ă"): u"a",
    ord(u"č"): u"c"
}

mappingklassen = {
    "05B-Schueler": "5b",
    "05A-Schueler": "5a",
    "05C-Schueler": "5c",
    "06A-Schueler": "6a",
    "06B-Schueler": "6b",
    "06C-Schueler": "6c",
    "07A-Schueler": "7a",
    "07B-Schueler": "7b",
    "07C-Schueler": "7c",
    "08A-Schueler": "8a",
    "08B-Schueler": "8b",
    "08C-Schueler": "8c",
    "09A-Schueler": "9a",
    "09B-Schueler": "9b",
    "09C-Schueler": "9c",
    "EF-Schueler": "EF",
    "Q1-Schueler": "Q1",
    "Q2-Schueler": "Q2"
}


def returnKlasseOfUser(user):
    klassen = returnCoursesOfStudent(user.lehrerid)
    for item in mappingklassen:
        if item in klassen:
            return mappingklassen[item]


def returnUntisName(user):
    bday = user.birthday.split(".")
    try:
        untisname = f"{user.name.translate(mappinguntis)}_{user.given.translate(mappinguntis)}_{bday[2]}{bday[1]}{bday[0]}"
    except:
        untisname = returnUsername(user.given, user.name, "vorname.nachname")
    return untisname


def readFile(users, groups, memberships):
    readUsers(users)
    readGroups(groups)
    readMemberships(memberships)


def createKeyCloakCSV(nameOfOutputCsv: str):
    with open(nameOfOutputCsv, "w", encoding="utf-8") as f:
        f.write(
            "webuntisKurzname;webuntisSchluessel(extern);Nachname;Vorname;webuntisKlasse;Email;Benutzername;Geburtstag;NCQuota;Initialpasswort;Gruppen\n")
        for user in users:
            courses = returnCoursesOfStudent(user.lehrerid)
            f.write(
                f'{returnUntisName(user)};{user.username if "X" in user.lehrerid else user.lehrerid[10:]};{user.name.translate(mappinguntis)};{user.given.translate(mappinguntis)};{returnKlasseOfUser(user)};{user.email if user.institutionrole == "faculty" else ""};{user.username};{user.birthday};{20000 if "X" in user.lehrerid else 1000};{f"{user.lehrerid[-3:]}{user.username[-2:]}{stripHyphensFromBirthday(user.birthday)[:3]}{user.username[:2]}"};{"##".join(courses)}\n')


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
        if "Klasse" in group.name:
            group.name = group.name[7:].replace(" ", "")
        if "(" in group.name:
            start = group.name.rfind("(")
            ende = group.name.rfind(")")
            try:
                m = re.search(r"\d", group.name)
                digitfound = m.group(0)
            except:
                digitfound = ''
            templist = group.name[start+1:ende].replace(" ", "").split(",")
            group.name = f"2122-{templist[0]}-{templist[1] if templist[1] == 'GK' or templist[1] == 'LK' else ''}{digitfound if templist[1] == 'GK' or templist[1] == 'LK' else ''}-{templist[2]}-{templist[3]}"
        if "Alle - Schueler" in group.name:
            group.name = "Alle-Schueler"
        if "Alle - Lehrer" in group.name:
            group.name = "Alle-Lehrer"


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

    for klasse in klassenliste:
        for user in users:
            kurse = returnCoursesOfStudent(user.lehrerid)
            if klasse in kurse:
                addTitle(document, 36, colors.blue, "Benutzername:")
                addTitle(document, 20, colors.black,
                         f"{user.given} {user.name}")
                addTitle(document, 36, colors.blue, "Passwort:")
                addTitle(document, 20, colors.black, f"{user.initialpassword}")
                addTitle(document, 36, colors.blue, "URL:")
                addTitle(document, 20, colors.black, importurl)
                addTitle(document, 36, colors.blue, "QR-Code:")
                document.append(Image("some_file.png", 8*cm, 8*cm))
        SimpleDocTemplate(
            f"./exports/{klasse}.pdf",
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
    tree = ET.parse("SchILD20220301.xml")
    root = tree.getroot()
    readFile(users, groups, memberships)
    renameGroups()
    # createKeyCloakCSV("Export20220301v6.csv")
    checkForDuplicates()
    printUserCredentials("usernames.pdf", "some_url")
    # for user in users:
    #     print(user.username, user.given, user.name)

    # for user in users:
    #     username = user.username
    #     for user in users:
    #         if user.username == username:
    #             user.username == user.username + "1"

    # for group in groups:
    #     print(group.name)

    # for user in users:
    #     if "EF-Schueler" in returnCoursesOfStudent(user.lehrerid):
    #         print(returnUntisName(user))
    # for user in users:
    #     if "Q1-Schueler" in returnCoursesOfStudent(user.lehrerid):
    #         print(returnUntisName(user))
    # for user in users:
    #     if "Q2-Schueler" in returnCoursesOfStudent(user.lehrerid):
    #         print(returnUntisName(user))
    # for user in users:
    #     print(returnKlasseOfUser(user))

    # print(returnUserGivenAndName("1082954"))
    # doc = Canvas('advanced.pdf')
    # qr = QRCodeImage(
    #     size=25 * mm,
    #     fill_color='blue',
    #     back_color='white',
    #     border=4,
    #     version=2,
    #     error_correction=qrcode.constants.ERROR_CORRECT_H,
    # )
    # qr.add_data('url')
    # qr.drawOn(doc, 30 * mm, 50 * mm)
    # doc.showPage()
    # doc.save()
