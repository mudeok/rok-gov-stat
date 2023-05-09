# -*- coding: utf-8 -*-
from datetime import datetime
from typing import List
from collections import namedtuple
import pyexcel as pe
import calendar
import csv
import cv2
import glob
import pytesseract
import os


OCR_LOCATION = namedtuple("ORC_LOCATION", ["id", "bbox", "number"])
TESSERACT_ARGS_NUMBER = "--oem 3 --psm 7 digits -c tessedit_char_whitelist=0123456789"
TESSERACT_ARGS_TEXT = "--oem 3 --psm 7"


# bluestack
more_info_screen = [
    OCR_LOCATION("name", (391, 127, 344, 60), False),
    OCR_LOCATION("power", (816, 127, 247, 60), True),
    OCR_LOCATION("kills_points", (1208, 127, 195, 60), True),
    OCR_LOCATION("dead", (937, 439, 376, 48), True),
    OCR_LOCATION("ressource_gathered", (937, 608, 376, 48), True),
    OCR_LOCATION("ressource_assistance", (937, 672, 376, 48), True),
    OCR_LOCATION("alliance_help_times", (937, 731, 376, 48), True),
]

governor_profile_screen = [
    OCR_LOCATION("id", (774, 231, 115, 39), True),
    OCR_LOCATION("kills_t4", (861, 595, 267, 34), True),
    OCR_LOCATION("kills_t5", (861, 639, 267, 34), True),
    OCR_LOCATION("ranged_points", (1127, 741, 239, 36), True),
]

# folder name where screenshots are located, alliance name or kingdom name
folders = [
    ("alliance_gov_kd58", "KD58"),
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
            values += ["ERROR, VERIFY!"]
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
    export_header = [
        "ID",
        "ALLIANCE",
        "NAME",
        "POWER",
        "KILLS POINTS",
        "DEAD",
        "RSS GATHERED",
        "RSS ASSISTANCE",
        "ALLIANCE HELP",
        "KILLS T4",
        "KILLS T5",
        "RANGED POINTS",
    ]
    export_content = []
    export_content.append(export_header)
    export_content += data

    d_now = datetime.utcnow()
    date = d_now.strftime('%d_%m_%Y')
    ts = calendar.timegm(d_now.timetuple())
    filename = "%s-%s-%s" % (filename, date, ts)
    file_destination = os.path.abspath("./%s.xlsx" % (filename))

    # Save data into an .xlsx file
    pe.save_as(array=export_content, dest_file_name=file_destination)


def get_gov_stats(folder, alliance):
    files = glob.glob(f"{folder}/*")
    files = sorted(files, key=lambda t: os.stat(t).st_mtime, reverse=True)
    root_path = ""

    governors = dict()
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

        file_path = os.path.abspath(f"{root_path}{a_file}")
        print(f"...processing {file_path}")

        # we treat the file only if it exists
        if not os.path.exists(file_path):
            print(f"{file_path} does not exist!")
            continue

        image = cv2.imread(file_path)
        # 2 following screenshot should belong to one governor
        if i % 2 == 0:
            # we get id, kills_t4, kills_t5, ranged_points
            values = get_text(image, governor_profile_screen)
            current_gov_id = values[0]
            governors[current_gov_id] = values[1:]
        else:
            # we get name, power, kills_points, dead, ressource_gathered, ressource_assistance, alliance_help_times
            values = get_text(image, more_info_screen)
            if current_gov_id is not None:
                _old = governors[current_gov_id]
                """
                    We save a new array with column in order
                    - id
                    - alliance
                    - name
                    - power
                    - kills_points
                    - dead
                    - ressource_gathered
                    - ressource_assistance
                    - alliance_help_times
                    - kills_t4,
                    - kills_t5
                    - ranged_points
                """
                governors[current_gov_id] = [current_gov_id] + [alliance] + values + _old
            else:
                print(f"could not read More Info from {file_path}")

    return governors


def parse_folder_alliance(folder, alliance):
    data = get_gov_stats(folder, alliance)
    values = list(data.values())
    save_data_into_file(f"rok_gov_stats_{folder}", values)
    return data


def import_old_data():
    """ Allows to import old data for "merging purpose".
    Example:
    During KvK, you import your first data.
    Then you have somewhere (in google sheet) your governors data.
    You then use this script to update data.
    This will allow to keep the same order from your main data.
    Thus, with copy paste, you can update more easily.
    """
    history = dict()
    order_ids = []
    filename = "data/export.csv"
    path_filename = os.path.abspath(filename)
    if not os.path.exists(path_filename):
        return None, []
    with open(path_filename, "r") as f:
        reader = csv.reader(f)
        for row in reader:
            player_id = row[0]
            if player_id == "ID" or player_id == "":
                continue
            else:
                try:
                    player_id = int(player_id)
                except Exception as e:
                    print(row)
                    raise e
            order_ids += [player_id]
            history[player_id] = row[1:]
    return history, order_ids


if __name__ == "__main__":
    # Step 1 - Retrieve old data if any
    history, order_ids = import_old_data()

    # Step 2 - Initialize list of governors
    existing_governors = []
    new_governors = []

    # Step 3 - Parse all folders and save governors data
    all_govs = dict()
    for folder in folders:
        folder_name, alliance_name = folder
        data = parse_folder_alliance(folder_name, alliance_name)
        all_govs = {**all_govs, **data}

    # Step 4 - Saving existing governors following the same order that old data imported
    for player_id in order_ids:
        player = all_govs.get(player_id, None)
        if player is None:
            # we have an old player registered but no new data, we put 0 for each columns
            existing_governors += [[player_id] + [0] * 11]
        else:
            existing_governors += [[player_id] + player[1:]]

    # Step 5 - Save new governors for which data was never collected
    for gov_id in all_govs.keys():
        if gov_id not in order_ids:
            player = all_govs.get(gov_id, None)
            if player:
                new_governors += [player]

    # Step 6 - Save files
    save_data_into_file(f"rok_gov_stats_all_aggregated", existing_governors)
    save_data_into_file(f"rok_gov_stats_all_new_gov", new_governors)
