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
players_on_screenshot_scientist = [
    [
        # OCR_LOCATION("position", (818, 764, 87, 94), True),
        OCR_LOCATION("name", (790, 740, 695, 63), False),
        OCR_LOCATION("points", (1724, 741, 458, 96), True),
    ],
    [
        # OCR_LOCATION("position", (818, 902, 87, 94), True),
        OCR_LOCATION("name", (790, 872, 695, 63), False),
        OCR_LOCATION("points", (1724, 872, 458, 96), True),
    ],
    [
        # OCR_LOCATION("position", (818, 1036, 87, 94), True),
        OCR_LOCATION("name", (790, 1004, 695, 63), False),
        OCR_LOCATION("points", (1724, 1004, 458, 96), True),
    ],
    [
        # OCR_LOCATION("position", (818, 1169, 87, 94), True),
        OCR_LOCATION("name", (790, 1137, 695, 63), False),
        OCR_LOCATION("points", (1724, 1137, 458, 96), True),
    ],
    [
        # OCR_LOCATION("position", (818, 1304, 87, 94), True),
        OCR_LOCATION("name", (790, 1270, 695, 63), False),
        OCR_LOCATION("points", (1724, 1270, 458, 96), True),
    ],
    [
        # OCR_LOCATION("position", (818, 1435, 87, 94), True),
        OCR_LOCATION("name", (790, 1401, 695, 63), False),
        OCR_LOCATION("points", (1724, 1401, 458, 96), True),
    ],
]

players_on_screenshot_builder_help = [
    [
        # OCR_LOCATION("position", (818, 764, 87, 94), True),
        OCR_LOCATION("name", (790, 740, 695, 63), False),
        OCR_LOCATION("points", (1724, 741, 458, 96), True),
    ],
    [
        # OCR_LOCATION("position", (818, 902, 87, 94), True),
        OCR_LOCATION("name", (790, 872, 695, 63), False),
        OCR_LOCATION("points", (1724, 872, 458, 96), True),
    ],
    [
        # OCR_LOCATION("position", (818, 1036, 87, 94), True),
        OCR_LOCATION("name", (790, 1004, 695, 63), False),
        OCR_LOCATION("points", (1724, 1004, 458, 96), True),
    ],
    [
        # OCR_LOCATION("position", (818, 1169, 87, 94), True),
        OCR_LOCATION("name", (790, 1137, 695, 63), False),
        OCR_LOCATION("points", (1724, 1137, 458, 96), True),
    ],
    [
        # OCR_LOCATION("position", (818, 1304, 87, 94), True),
        OCR_LOCATION("name", (790, 1270, 695, 63), False),
        OCR_LOCATION("points", (1724, 1270, 458, 96), True),
    ],
    [
        # OCR_LOCATION("position", (818, 1435, 87, 94), True),
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


def save_data_into_file(filename, data):
    # Save data into an .xlsx file
    d_now = datetime.utcnow()
    date = d_now.strftime('%d_%m_%Y')
    ts = calendar.timegm(d_now.timetuple())
    filename = "%s-%s-%s" % (filename, date, ts)
    file_destination = os.path.abspath("./%s.xlsx" % (filename))
    pe.save_as(array=data, dest_file_name=file_destination)


def get_rankings_scientist(folder: str, locations: List[List[OCR_LOCATION]], save=True):
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
                files_values += [values]

    rankings = []
    for i, player in enumerate(files_values):
        rank = i + 1
        if len(player) == 2:
            data = [rank] + player
        else:
            data = [rank] + player[1:]
        rankings += [data]

    save_data_into_file("rok_alliance_rankings_scientist", rankings)


def get_rankings(folder: str, locations: List[List[OCR_LOCATION]], export_filename, save=True):
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
                files_values += [values]

    save_data_into_file(export_filename, files_values)


get_rankings_scientist(folder_scientist, players_on_screenshot_scientist)
get_rankings(folder_builder, players_on_screenshot_builder_help, "rok_alliance_rankings_builder")
get_rankings(folder_help, players_on_screenshot_builder_help, "rok_alliance_rankings_help")
