# -*- coding: utf-8 -*-
from datetime import datetime
from operator import invert
from typing import List
from collections import namedtuple
import pyexcel as pe
import calendar
import cv2
import pytesseract
import numpy as np
import os


OCR_LOCATION = namedtuple("ORC_LOCATION", ["id", "bbox", "number"])
TESSERACT_ARGS_NUMBER = "--oem 3 --psm 7 digits -c tessedit_char_whitelist=0123456789"
TESSERACT_ARGS_TEXT = "--oem 3 --psm 7"

id_name_power_killpoints = [
    OCR_LOCATION("id", (1630, 774, 140, 33), True),
    OCR_LOCATION("name", (1449, 806, 634, 58), False),
    OCR_LOCATION("power", (1798, 940, 279, 43), True),
    OCR_LOCATION("kill_points", (2088, 939, 286, 40), True),
]

name_dead = [
    OCR_LOCATION("name", (1118, 628, 466, 85), False),
    OCR_LOCATION("power", (1676, 634, 326, 68), True),
    OCR_LOCATION("kills_points", (2194, 629, 262, 80), True),
    OCR_LOCATION("dead", (1732, 1050, 609, 45), True),
    OCR_LOCATION("ressource_gathered", (1776, 1263, 571, 58), True),
    OCR_LOCATION("ressource_assistance", (1776, 1341, 571, 58), True),
    OCR_LOCATION("alliance_help_times", (1776, 1424, 571, 58), True),
]

id_kills = [
    OCR_LOCATION("id", (1628, 770, 142, 37), True),
    OCR_LOCATION("kills_t3", (1739, 1353, 331, 49), True),
    OCR_LOCATION("kill_points_t3", (2121, 1356, 352, 45), True),
    OCR_LOCATION("kills_t4", (1739, 1415, 331, 49), True),
    OCR_LOCATION("kill_points_t4", (2121, 1417, 352, 45), True),
    OCR_LOCATION("kills_t5", (1739, 1474, 331, 49), True),
    OCR_LOCATION("kill_points_t5", (2121, 1477, 352, 45), True),
]

folder_id_name_power_killpoints = "rok_ss_step_1"
folder_name_dead = "rok_ss_step_2"
folder_id_kills = "rok_ss_step_3"


def get_grayscale(image):
    # Returns image in gray scale mode, easier to extract data
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def get_text(image, locations: List[OCR_LOCATION]) -> List[str]:
    """ For an image, locations refer to all possible data we want to extract.
    Return a list of values extracted from provided locations.
    """
    values = []

    for location in locations:
        # extract coordinates x, y, width and height of the desired area
        (x, y, w, h) = location.bbox

        # use coordinates above to select the desired area
        cropped_image = image[y:y + h, x:x + w]

        gray_image = get_grayscale(cropped_image)

        # if the data we want to extract is a number or a string
        data_type_number = location.number is True
        if data_type_number:
            config = TESSERACT_ARGS_NUMBER
        else:
            config = TESSERACT_ARGS_TEXT

        result = pytesseract.image_to_string(gray_image, config=config)

        # if the result is an empty value, we skip it
        text = result.strip().replace("\n", "")
        if text == "":
            continue

        # if data is a number, we cast the value to an integer
        if data_type_number:
            try:
                text = int(text)
            except Exception as e:
                print(e)

        values += [text]

    return values


def parse_folder(folder: str, locations: List[OCR_LOCATION]) -> List[List[str]]:
    """ Parse a folder to retrieve all screenshots inside that folder.
    Then iterate through all screenshot to extract data.
    Return a list of values extracted for each screenshots.
    """
    folder_path = os.path.abspath(folder)
    files = os.listdir(folder_path)
    files_values = []

    for a_file in files:
        filename, extension = os.path.splitext(a_file)

        # hack, we skip macos hidden file
        if filename == ".DS_Store":
            continue
        elif extension != ".png" \
                and extension != ".jpeg" and \
                extension != ".jpg":
            continue

        file_path = os.path.abspath(f"{folder}/{a_file}")
        # we treat the file only if it exists
        if os.path.exists(file_path):
            image = cv2.imread(file_path)
            values = get_text(image, locations)
            files_values += [values]

    return files_values


def save_data_into_file(filename, data):
    # Save data into an .xlsx file
    d_now = datetime.utcnow()
    date = d_now.strftime('%d_%m_%Y')
    ts = calendar.timegm(d_now.timetuple())
    filename = "%s-%s-%s" % (filename, date, ts)
    file_destination = os.path.abspath("./%s.xlsx" % (filename))
    pe.save_as(array=data, dest_file_name=file_destination)


def get_data(headers: List[str], filename: str, folder_name: str, locations: List[OCR_LOCATION], save=True):
    export_content = []
    export_content.append(headers)
    screenshots = parse_folder(folder_name, locations)
    export_content += [screenshot for screenshot in screenshots]
    if save is True:
        save_data_into_file(filename, export_content)
    return screenshots


def get_id_name_power_kill_points(folder_name: str, locations: List[OCR_LOCATION], save=True):
    export_header = ["ID", "NAME", "POWER", "KILL POINTS"]
    return get_data(
        export_header,
        "rok_gov_id_name_power_killpts",
        folder_name,
        locations,
        save=save
    )


def get_data_name_deads(folder_name: str, locations: List[OCR_LOCATION], save=True):
    export_header = ["NAME", "DEAD"]
    return get_data(
        export_header,
        "rok_gov_name_deads",
        folder_name,
        locations,
        save=save
    )


def get_data_id_kills(folder_name: str, locations: List[OCR_LOCATION], save=True):
    export_header = ["ID", "KILLS T3", "KILL POINTS T3", "KILLS T4", "KILL POINTS T4", "KILLS T5", "KILL POINTS T5"]
    return get_data(
        export_header,
        "rok_gov_name_deads",
        folder_name,
        locations,
        save=save
    )


def aggregate_data(data_1: List[List[str]], data_2: List[List[str]], data_3: List[List[str]]):
    export_header = [
        "ID",
        "NAME",
        "POWER",
        "KILL POINTS",
        "DEAD",
        "KILLS T3",
        "KILL POINTS T3",
        "KILLS T4",
        "KILL POINTS T4",
        "KILLS T5",
        "KILL POINTS T5",
    ]
    export_content = []
    export_content.append(export_header)

    memory_2 = {}
    for part in data_2:
        # part[0] refer to governor name
        # part[1] refer to governor number of dead
        memory_2[part[0]] = part[1]

    memory_3 = {}
    for part in data_3:
        # part[0] refer to governor id
        # part[1:] refer to governor kills stats
        memory_3[part[0]] = part[1:]

    for part in data_1:
        a_copy = part.copy()
        id_ = a_copy[0]
        name = a_copy[1]

        # match name with data_2
        # we add the column with governor dead
        if name in memory_2.keys():
            a_copy += [memory_2[name]]
        else:
            a_copy += []

        # match id with data_3
        # we add columns for kills stats (t3, t4, t5)
        kills_stats = memory_3.get(id_, [])
        if len(kills_stats) == 6:
            a_copy += [col for col in kills_stats]

        export_content += [a_copy]

    save_data_into_file("rok_gov_stats", export_content)


#p1 = get_id_name_power_kill_points(folder_id_name_power_killpoints, id_name_power_killpoints, save=False)
#p2 = get_data_name_deads(folder_name_dead, name_dead, save=False)
#p3 = get_data_id_kills(folder_id_kills, id_kills, save=False)
#aggregate_data(p1, p2, p3)


def get_gov_stats():
    folder = "rok_gov_ss"
    folder_path = os.path.abspath(folder)
    files = sorted(os.listdir(folder_path), reverse=True)

    hm_gov = dict()
    current_gov_id = None

    for i, a_file in enumerate(files):
        filename, extension = os.path.splitext(a_file)

        # hack, we skip macos hidden file
        if filename == ".DS_Store":
            continue
        # if not image, we skipp
        elif extension != ".png" \
                and extension != ".jpeg" and \
                extension != ".jpg":
            continue

        file_path = os.path.abspath(f"{folder}/{a_file}")
        # we treat the file only if it exists
        if not os.path.exists(file_path):
            continue
        print(f"...processing {file_path}")
        image = cv2.imread(file_path)
        # 2 following screenshot should belong to one governor
        if i % 2 == 0:
            # ID, NAME, KILLS
            values = get_text(image, id_kills)
            current_gov_id = values[0]
            hm_gov[current_gov_id] = values[1:]
        else:
            # NAME, DEADS
            values = get_text(image, name_dead)
            if current_gov_id is not None:
                _old = hm_gov[current_gov_id]
                hm_gov[current_gov_id] = [current_gov_id] + values + _old

    return hm_gov


data = get_gov_stats()
values = list(data.values())
export_header = [
    "ID",
    "NAME",
    "POWER",
    "KILLS POINTS",
    "DEAD",
    "RSS GATHERED",
    "RSS ASSISTANCE",
    "ALLIANCE HELP",
    "KILLS T3",
    "KILL POINTS T3",
    "KILLS T4",
    "KILL POINTS T4",
    "KILLS T5",
    "KILL POINTS T5",
]
export_content = []
export_content.append(export_header)
export_content += values
save_data_into_file("rok_gov_stats", export_content)
