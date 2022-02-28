import xml.etree.ElementTree as ET
import re
from reportlab.lib.units import mm
from reportlab.pdfgen.canvas import Canvas
from reportlab_qrcode import QRCodeImage
import qrcode


class User:
    def __init__(self, lehrerid, name, given, institutionrole, email, birthday):
        self.lehrerid = lehrerid
        self.name = name
        self.given = given
        self.institutionrole = institutionrole
        self.email = email
        self.birthday = birthday

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
        for child in elem.findall(
                ".//{http://www.metaventis.com/ns/cockpit/sync/1.0}bday"):
            birthday = child.text
        users.append(
            User(
                lehrerid, name, given, institutionrole, email,
                birthday))


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


def returnUsername(studentid):
    last = [user.name for user in users if user.lehrerid == studentid][0]
    given = [user.given for user in users if user.lehrerid == studentid][0]
    username = given.split(" ")[0] + "." + last
    return username.lower().replace(
        "ü", "ue").replace(
        "ä", "ae").replace(
        "ö", "oe").replace(
        "á", "a").replace(
        "à", "a").replace(
        "é", "e").replace(
        "è", "e").replace(
        "ó", "o").replace(
        "ò", "o").replace(
        "â", "a").replace(
        "ê", "e").replace(
        "û", "u").replace(
        "ë", "e").replace(
        " ", "").replace(
        "ß", "ss").replace(
        "ï", "i").replace(
        "ÿ", "y").replace(
        "ã", "a").replace(
        "å", "a").replace(
        "æ", "ae").replace(
        "ç", "c").replace(
        "ì", "i").replace(
        "í", "i").replace(
        "î", "i").replace(
        "ð", "d").replace(
        "ñ", "n").replace(
        "ô", "o").replace(
        "õ", "o").replace(
        "ø", "oe").replace(
        "œ", "oe").replace(
        "ù", "u").replace(
        "ú", "u").replace(
        "ý", "y").replace(
        "š", "s").replace(
        "č", "c")


def readFile(users, groups, memberships):
    readUsers(users)
    readGroups(groups)
    readMemberships(memberships)


def createKeyCloakCSV(nameOfOutputCsv: str):
    with open(nameOfOutputCsv, "w", encoding="utf-8") as f:
        f.write(
            "id; nachname; vorname; benutzername; geburtstag; ncQuota; initialpasswort; gruppen\n")
        for user in users:
            courses = returnCoursesOfStudent(user.lehrerid)
            f.write(
                f'{returnUsername(user.lehrerid) if "X" in user.lehrerid else user.lehrerid[10:]};{user.name}; {user.given};{returnUsername(user.lehrerid)}; {user.birthday}; {20000 if "X" in user.lehrerid else 1000}; {f"{user.lehrerid[-3:]}{returnUsername(user.lehrerid)[-2:]}{stripHyphensFromBirthday(user.birthday)[-3:]}{returnUsername(user.lehrerid)[:2]}"}; {"##".join(courses)}\n')


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
    last = [user.name for user in users if user.lehrerid == studentid][0]
    given = [user.given for user in users if user.lehrerid == studentid][0]
    return {"id": studentid, "given": given, "last": last, "username": returnUsername(studentid)}


def returnGroupId(groupname: str):
    return [group.groupid for group in groups if group.name == groupname][0]


if __name__ == "__main__":
    users = []
    groups = []
    memberships = []
    tree = ET.parse("schild4.xml")
    root = tree.getroot()
    readFile(users, groups, memberships)

    for group in groups:
        if "Klasse" in group.name:
            group.name = group.name[7:].replace(" ", "")
        if "(" in group.name:
            start = group.name.rfind("(")
            ende = group.name.rfind(")")
            m = re.search(r"\d", group.name)
            digitfound = m.group(0)
            templist = group.name[start+1:ende].replace(" ", "").split(",")
            group.name = f"2122-{templist[0]}{templist[1] if templist[1] == 'GK' or templist[1] == 'LK' else ''}{digitfound if templist[1] == 'GK' or templist[1] == 'LK' else ''}-{templist[2]}-{templist[3]}"
        if "Alle - Schueler" in group.name:
            group.name = "Alle-Schueler"

    createKeyCloakCSV("testexport.csv")

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
