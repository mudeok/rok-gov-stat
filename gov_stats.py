# -*- coding: utf-8 -*-
from datetime import datetime
from typing import List
from collections import namedtuple
import pyexcel as pe
import calendar
import csv
import cv2
import pytesseract
import numpy as np
import os


OCR_LOCATION = namedtuple("ORC_LOCATION", ["id", "bbox", "number"])
TESSERACT_ARGS_NUMBER = "--oem 3 --psm 7 digits -c tessedit_char_whitelist=0123456789"
TESSERACT_ARGS_TEXT = "--oem 3 --psm 7"


name_dead = [
    OCR_LOCATION("name", (1142, 675, 462, 95), False),
    OCR_LOCATION("power", (1701, 675, 325, 95), True),
    OCR_LOCATION("kills_points", (2216, 675, 258, 95), True),
    OCR_LOCATION("dead", (1789, 1088, 570, 65), True),
    OCR_LOCATION("ressource_gathered", (1789, 1313, 570, 65), True),
    OCR_LOCATION("ressource_assistance", (1789, 1394, 570, 65), True),
    OCR_LOCATION("alliance_help_times", (1789, 1475, 570, 65), True),
]

id_kills = [
    OCR_LOCATION("id", (1650, 822, 145, 41), True),
    OCR_LOCATION("kills_t3", (1763, 1404, 336, 52), True),
    OCR_LOCATION("kills_t4", (1763, 1464, 336, 52), True),
    OCR_LOCATION("kills_t5", (1763, 1523, 336, 52), True),
]


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


def save_data_into_file(filename, data):
    # Save data into an .xlsx file
    d_now = datetime.utcnow()
    date = d_now.strftime('%d_%m_%Y')
    ts = calendar.timegm(d_now.timetuple())
    filename = "%s-%s-%s" % (filename, date, ts)
    file_destination = os.path.abspath("./%s.xlsx" % (filename))
    pe.save_as(array=data, dest_file_name=file_destination)


def get_gov_stats(folder):
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


def parse_folder_alliance(folder):
    data = get_gov_stats(folder)
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
        "KILLS T4",
        "KILLS T5",
    ]
    export_content = []
    export_content.append(export_header)
    export_content += values
    save_data_into_file(f"rok_gov_stats_{folder}", export_content)
    return data


def import_old_data():
    history = dict()
    order_ids = []
    filename = "data/export.csv"
    path_filename = os.path.abspath(filename)
    if not os.path.exists(path_filename):
        return None, None
    with open(path_filename, "r") as f:
        reader = csv.reader(f)
        for row in reader:
            player_id = row[0]
            if player_id == "ID":
                continue
            else:
                player_id = int(player_id)
            order_ids += [player_id]
            history[player_id] = row[1:]
    return history, order_ids


history, order_ids = import_old_data()

folder = "alliance_gov_hs"
data = parse_folder_alliance(folder)

export_header = [
    "ID",
    "POWER",
    "KILLS POINTS",
    "DEAD",
    "RSS GATHERED",
    "RSS ASSISTANCE",
    "ALLIANCE HELP",
    "KILLS T3",
    "KILLS T4",
    "KILLS T5",
]
export_content = []
export_content.append(export_header)
for player_id in order_ids:
    player = data.get(player_id, None)
    if player is None:
        export_content += [[player_id] + [0] * 9]
    else:
        export_content += [[player_id] + player[2:]]
save_data_into_file(f"rok_gov_stats_{folder}_aggregated", export_content)

