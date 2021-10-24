import datetime
import json
import time
from random import Random

from flask import session

from api.utils import Utils
from config import CONST
from config.CONST import *

__author__ = "Xiejiadong"
__site__ = "xiejiadong.com"

checkFirstWeekDate = 0
checkReminder = 1

YES = 0
NO = 1

DONE_firstWeekDate: time.struct_time
DONE_reminder = ""
DONE_EventUID = ""
DONE_UnitUID = ""
DONE_CreatedTime = ""
DONE_ALARMUID = ""

classTimeList = []
classInfoList = []
# reminderList = ["-PT10M", "-PT15M", "-PT20M", "-PT30M", "-PT1H", "-P1D"]

request_id = "0"
obtainedClass = []


def get_class_csv(semester, reminder):
    obtainedClass.clear()
    global request_id
    request_id = session.get("requestid")
    set_reminder(reminder)
    set_first_week_date(CONST.FIRST_WEEK_DATE[semester])
    set_class_info()
    set_class_time()
    unite_setting()
    class_info_handle()
    ics_create_and_save()
    print("课程表已保存至脚本目录下的 class.ics 中，你现在可以导入了：）")
    result = {
        "link": "/output/class_" + request_id + ".ics",
        "obtained_class": obtainedClass,
        "reminder": reminder,
    }
    with open(DEPLOY_PATH + "log/success.log", "a+", encoding="utf-8") as f:
        f.write(
            Utils.getCurrentDateTime()
            + ","
            + request_id
            + ","
            + session.get("realname")
            + ","
            + reminder
            + ","
            + str(obtainedClass)
            + "\n"
        )
        f.close()
    return result


def save(string):
    f = open(DEPLOY_PATH + "static/output/class_" + request_id + ".ics", "wb+")
    f.write(string.encode("utf-8"))
    f.close()


def ics_create_and_save():
    ics_string = (
        "BEGIN:VCALENDAR\nMETHOD:PUBLISH\nVERSION:2.0\nX-WR-CALNAME:课程表\nPRODID:-//Apple Inc.//Mac OS X "
        "10.12//EN\nX-APPLE-CALENDAR-COLOR:#FC4208\nX-WR-TIMEZONE:Asia/Shanghai\nCALSCALE:GREGORIAN\nBEGIN"
        ":VTIMEZONE\nTZID:Asia/Shanghai\nBEGIN:STANDARD\nTZOFFSETFROM:+0900\nRRULE:FREQ=YEARLY;UNTIL"
        "=19910914T150000Z;BYMONTH=9;BYDAY=3SU\nDTSTART:19890917T000000\nTZNAME:GMT+8\nTZOFFSETTO:+0800\nEND"
        ":STANDARD\nBEGIN:DAYLIGHT\nTZOFFSETFROM:+0800\nDTSTART:19910414T000000\nTZNAME:GMT+8\nTZOFFSETTO"
        ":+0900\nRDATE:19910414T000000\nEND:DAYLIGHT\nEND:VTIMEZONE\n "
    )
    global classTimeList, DONE_ALARMUID, DONE_UnitUID
    event_string = ""
    for classInfo in classInfoList:
        i = int(classInfo["classTime"] - 1)
        # class_name = classInfo["class_name"]+"|"+classTimeList[i]["name"]+"|"+classInfo["classroom"]
        class_name = classInfo["class_name"]
        obtainedClass.append(class_name)
        end_time = classTimeList[i]["end_time"]
        start_time = classTimeList[i]["start_time"]
        index = 0
        for date in classInfo["date"]:
            event_string = (
                event_string + "BEGIN:VEVENT\nCREATED:" + classInfo["CREATED"]
            )
            event_string = event_string + "\nUID:" + classInfo["UID"][index]
            event_string = (
                event_string + "\nDTEND;TZID=Asia/Shanghai:" + date + "T" + end_time
            )
            event_string = (
                event_string + "00\nTRANSP:OPAQUE\n"
                "X-APPLE-TRAVEL-ADVISORY-BEHAVIOR:AUTOMATIC\n"
                "SUMMARY:" + class_name
            )
            event_string = (
                event_string
                + "\nDTSTART;TZID=Asia/Shanghai:"
                + date
                + "T"
                + start_time
                + "00"
            )
            event_string = event_string + "\nDTSTAMP:" + DONE_CreatedTime
            event_string = event_string + "\nLOCATION:" + classInfo["classroom"]
            event_string = (
                event_string
                + "\nSEQUENCE:0\nBEGIN:VALARM\nX-WR-ALARMUID:"
                + DONE_ALARMUID
            )
            event_string = event_string + "\nUID:" + DONE_UnitUID
            event_string = event_string + "\nTRIGGER:" + DONE_reminder
            event_string = (
                event_string
                + "\nDESCRIPTION:事件提醒\nACTION:DISPLAY\nEND:VALARM\nEND:VEVENT\n"
            )
            index += 1
    ics_string = ics_string + event_string + "END:VCALENDAR"
    save(ics_string)
    print("Now running: icsCreateAndSave()")


def class_info_handle():
    global classInfoList
    global DONE_firstWeekDate

    for classInfo in classInfoList:
        # 具体日期计算出来

        start_week = json.dumps(classInfo["week"]["start_week"])
        end_week = json.dumps(classInfo["week"]["end_week"])
        weekday = float(json.dumps(classInfo["weekday"]))
        week = float(json.dumps(classInfo["weeks"]))
        date_length = float((int(start_week) - 1) * 7)
        start_date = datetime.datetime.fromtimestamp(
            int(time.mktime(DONE_firstWeekDate))
        ) + datetime.timedelta(days=date_length + weekday - 1)
        string = start_date.strftime("%Y%m%d")

        date_length = float((int(end_week) - 2) * 7)
        end_date = datetime.datetime.fromtimestamp(
            int(time.mktime(DONE_firstWeekDate))
        ) + datetime.timedelta(days=date_length + weekday - 1)

        date = start_date
        date_list = []
        if week == 3:
            date_list.append(string)
        if (week == 2) and (int(start_week) % 2 == 0):
            date_list.append(string)
        if (week == 1) and (int(start_week) % 2 == 1):
            date_list.append(string)
        i = NO
        w = int(start_week) + 1
        while i:
            date = date + datetime.timedelta(days=7.0)
            if date > end_date:
                i = YES
            if week == 3:
                string = date.strftime("%Y%m%d")
                date_list.append(string)
            if (week == 1) and (w % 2 == 1):
                string = date.strftime("%Y%m%d")
                date_list.append(string)
            if (week == 2) and (w % 2 == 0):
                string = date.strftime("%Y%m%d")
                date_list.append(string)
            w = w + 1
        classInfo["date"] = date_list
        # 设置 UID
        global DONE_CreatedTime, DONE_EventUID
        create_time()
        classInfo["CREATED"] = DONE_CreatedTime
        classInfo["DTSTAMP"] = DONE_CreatedTime
        uid_list = []
        for _ in date_list:
            uid_list.append(uid_create())
        classInfo["UID"] = uid_list
    print("Now running: classInfoHandle()")


def uid_create():
    return random_str(20) + "&xiejiadong.com"


def create_time():
    # 生成 CREATED
    global DONE_CreatedTime
    date = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
    DONE_CreatedTime = date + "Z"
    # 生成 UID
    # global DONE_EventUID
    # DONE_EventUID = random_str(20) + "&xiejiadong.com"

    print("Now running: CreateTime()")


def unite_setting():
    #
    global DONE_ALARMUID
    DONE_ALARMUID = random_str(30) + "&xiejiadong.com"
    #
    global DONE_UnitUID
    DONE_UnitUID = random_str(20) + "&xiejiadong.com"
    print("Now running: uniteSetting()")


def set_class_time():
    with open(DEPLOY_PATH + "config/conf_classTime.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    global classTimeList
    classTimeList = data["classTime"]
    print("Now running: setclassTime()")


def set_class_info():
    with open(
        DEPLOY_PATH + "static/temp/json/classInfo_" + request_id + ".json",
        "r",
        encoding="utf-8",
    ) as f:
        data = json.load(f)
    global classInfoList
    classInfoList = data["classInfo"]
    print("Now running: setClassInfo()")


def set_first_week_date(first_week_date):
    global DONE_firstWeekDate
    DONE_firstWeekDate = time.strptime(first_week_date, "%Y%m%d")
    print("Now running: setFirstWeekDate():", DONE_firstWeekDate)


def set_reminder(reminder):
    global DONE_reminder
    # global reminderList
    # DONE_reminder = reminderList[int(reminder) - 1]
    if reminder == "0":
        DONE_reminder = "NULL"
    else:
        DONE_reminder = "-PT" + reminder + "M"
    print("setReminder", reminder)


def random_str(randomlength):
    s = ""
    chars = "AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz0123456789"
    length = len(chars) - 1
    random = Random()
    for i in range(randomlength):
        s += chars[random.randint(0, length)]
    return s
