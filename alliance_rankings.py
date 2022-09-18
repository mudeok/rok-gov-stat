# -*- coding: utf-8 -*-
from datetime import datetime
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

# actually a list of 6 players by screenshot
ocr_locations = [
    [
        OCR_LOCATION("name", (790, 740, 695, 63), False),
        OCR_LOCATION("points", (1724, 741, 458, 96), True),
    ],
    [
        OCR_LOCATION("name", (790, 872, 695, 63), False),
        OCR_LOCATION("points", (1724, 872, 458, 96), True),
    ],
    [
        OCR_LOCATION("name", (790, 1004, 695, 63), False),
        OCR_LOCATION("points", (1724, 1004, 458, 96), True),
    ],
    [
        OCR_LOCATION("name", (790, 1137, 695, 63), False),
        OCR_LOCATION("points", (1724, 1137, 458, 96), True),
    ],
    [
        OCR_LOCATION("name", (790, 1270, 695, 63), False),
        OCR_LOCATION("points", (1724, 1270, 458, 96), True),
    ],
    [
        OCR_LOCATION("name", (790, 1401, 695, 63), False),
        OCR_LOCATION("points", (1724, 1401, 458, 96), True),
    ],
]

folder_scientist = "alliance_rankings_scientist"
folder_builder = "alliance_rankings_builder"
folder_help = "alliance_rankings_help"


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


def get_rankings(folder: str, locations: List[List[OCR_LOCATION]], db, save=False):
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
            for location in locations:
                values = get_text(image, location)
                if len(values) != 2:
                    continue
                name = values[0]
                if name not in db.keys():
                    db[name] = dict()
                db[name][folder] = values[1]
                files_values += [values]

    if save is True:
        # this is for debugging just in case
        save_data_into_file(folder, files_values)

    return db

# hash map of players
rankings = dict()
rankings = get_rankings(folder_scientist, ocr_locations, rankings)
rankings = get_rankings(folder_builder, ocr_locations, rankings)
rankings = get_rankings(folder_help, ocr_locations, rankings)

export_header = [
    "NAME",
    "SCIENTIST PTS",
    "BUILDER PTS",
    "HELP PTS",
]
export_content = []
export_content.append(export_header)

for k in rankings:
    # colum name
    name = k
    a_player = [name]
    points = rankings[k]

    # column scientist pts
    if folder_scientist in points:
        a_player += [points[folder_scientist]]
    else:
        a_player += [0]

    # column builder pts
    if folder_builder in points:
        a_player += [points[folder_builder]]
    else:
        a_player += [0]

    # column help pts
    if folder_help in points:
        a_player += [points[folder_help]]
    else:
        a_player += [0]

    export_content += [a_player]

# we save the final data, need to clean manually for weird name
save_data_into_file("rok_gov_alliance_rankings", export_content)
