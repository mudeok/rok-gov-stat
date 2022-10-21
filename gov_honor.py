# -*- coding: utf-8 -*-
from datetime import datetime
from typing import List
from collections import namedtuple
from thefuzz import fuzz
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

# actually a list of 5 players by screenshot
ocr_locations = [
    [
        OCR_LOCATION("name", (1749, 916, 259, 109), False),
        OCR_LOCATION("points", (2191, 916, 279, 109), True),
    ],
    [
        OCR_LOCATION("name", (1749, 1041, 259, 109), False),
        OCR_LOCATION("points", (2191, 1041, 279, 109), True),
    ],
    [
        OCR_LOCATION("name", (1749, 1176, 259, 109), False),
        OCR_LOCATION("points", (2191, 1176, 279, 109), True),
    ],
    [
        OCR_LOCATION("name", (1749, 1308, 259, 109), False),
        OCR_LOCATION("points", (2191, 1308, 279, 109), True),
    ],
    [
        OCR_LOCATION("name", (1749, 1436, 259, 109), False),
        OCR_LOCATION("points", (2191, 1436, 279, 109), True),
    ],
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


def save_data_into_file(filename, data) -> None:
    # Save data into an .xlsx file
    d_now = datetime.utcnow()
    date = d_now.strftime('%d_%m_%Y')
    ts = calendar.timegm(d_now.timetuple())
    filename = "%s-%s-%s" % (filename, date, ts)
    file_destination = os.path.abspath("./%s.xlsx" % (filename))
    pe.save_as(array=data, dest_file_name=file_destination)


def get_rankings(folder: str, locations: List[List[OCR_LOCATION]], db):
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
        if not os.path.exists(file_path):
            continue
        print(f"...processing {file_path}")
        image = cv2.imread(file_path)
        for location in locations:
            values = get_text(image, location)
            if len(values) != 2:
                continue
            name = values[0]
            if name not in db.keys():
                db[name] = dict()
            db[name][folder] = values[1]
            files_values += [values]

    return db

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

export_header = [
    "NAME",
    "ALLIANCE",
    "HONOR PTS",
]
export_content = []
export_content.append(export_header)

folders = [
    ("honor_hs", "HS"),
    ("honor_bw", "BW"),
    ("honor_hw", "HW"),
    ("honor_sa", "SA"),
]
all_govs = dict()

for folder in folders:
    f, a = folder
    rankings = dict()
    rankings = get_rankings(f, ocr_locations, rankings)
    for k in rankings:
        # colum name
        name = k
        a_player = [name, a]
        points = rankings[k]

        db = dict()
        db[name] = 0
        if f in points:
            a_player += [points[f]]
            db[name] = points[f]
        else:
            a_player += [0]
        all_govs = {**all_govs, **db}
        export_content += [a_player]

aggregated = []
aggregated.append([
    "ID",
    "LAST REGISTERED NAME",
    "HONOR PTS",
])
for player_id in order_ids:
    player = history[player_id]
    last_registerd_name = player[44]
    if last_registerd_name == "0" or last_registerd_name == 0:
        aggregated += [[player_id, last_registerd_name, 0]]
        continue
    all_names = all_govs.keys()
    find_player = False
    for name in all_names:
        if fuzz.partial_ratio(last_registerd_name, name) > 90:
            aggregated += [[player_id, last_registerd_name, all_govs[name]]]
            find_player = True
            break
    if find_player is False:
        aggregated += [[player_id, last_registerd_name, 0]]

# we save the final data, need to clean manually for weird name
save_data_into_file(f"rok_gov_honor_all", export_content)
save_data_into_file(f"rok_gov_honor_all_aggregated", aggregated)


