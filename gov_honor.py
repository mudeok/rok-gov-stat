# -*- coding: utf-8 -*-
from datetime import datetime
from typing import List
from thefuzz import fuzz
import pyexcel as pe
import calendar
import csv
import cv2
import os

from gov_stats import OCR_LOCATION
from gov_stats import get_text


# Sctually a list of 5 players by screenshot from the honor points alliance ranking view
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


def save_data_into_file(filename, data) -> None:
    # Save data into an .xlsx file
    d_now = datetime.utcnow()
    date = d_now.strftime('%d_%m_%Y')
    ts = calendar.timegm(d_now.timetuple())
    filename = "%s-%s-%s" % (filename, date, ts)
    file_destination = os.path.abspath("./%s.xlsx" % (filename))
    pe.save_as(array=data, dest_file_name=file_destination)


def get_honor_pts(folder: str, locations: List[List[OCR_LOCATION]], db):
    folder_path = os.path.abspath(folder)
    files = os.listdir(folder_path)

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
        print(f"...processing {file_path}")

        # we treat the file only if it exists
        if not os.path.exists(file_path):
            print(f"{file_path} does not exist!")
            continue

        image = cv2.imread(file_path)

        for location in locations:
            values = get_text(image, location)
            # we should get name and points
            if len(values) != 2:
                continue
            governor_name = values[0]
            governor_pts = values[1]
            db[governor_name] = governor_pts

    return db


def import_old_data():
    """ This is slightly different from the gov_stats.
    Here, we use also the column name to match with honor points.
    """
    history = dict()
    order_ids = []
    names = []
    filename = "data/export.csv"
    path_filename = os.path.abspath(filename)
    if not os.path.exists(path_filename):
        return None, None, None
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
            names += [row[1]]
            history[player_id] = row[1:]
    return history, order_ids, names


if __name__ == "__main__":
    # Step 1 - Retrieve old data if any
    history, order_ids, names = import_old_data()

    # Step 2 - Initialize
    folders = [
        ("honor_hs", "HS"),
        ("honor_bw", "BW"),
        ("honor_dg", "DG"),
        ("honor_hp", "HP"),
    ]
    all_govs = dict()
    all_data = []
    existing_governors = []

    # Step 3 - Parse all folders and save governors data
    for folder in folders:
        folder_name, alliance_name = folder
        governors = dict()
        governors = get_honor_pts(folder_name, ocr_locations, governors)
        for name in governors:
            points = governors.get(name, 0)
            a_player = [name, alliance_name, points]
            db = dict()
            db[name] = points
            all_govs = {**all_govs, **db}
            all_data += [a_player]

    # Step 4 - Saving existing governors
    all_names = all_govs.keys()
    for player_id in order_ids:
        player = history[player_id]
        # easider to keep first name
        last_name = player[0]
        if last_name == "0" or last_name == 0:
            existing_governors += [[player_id, last_name, 0]]
            continue

        find_player = False
        for name in all_names:
            if fuzz.partial_ratio(last_name, name) > 90:
                pts = all_govs[name]
                existing_governors += [[player_id, last_name, pts]]
                find_player = True
                break

        if find_player is False:
            existing_governors += [[player_id, last_name, 0]]

    all_governor_pts = []
    all_governor_pts.append(["NAME", "ALLIANCE", "HONOR PTS"])
    all_governor_pts += all_data

    aggregated = []
    aggregated.append(["ID", "LAST REGISTERED NAME", "HONOR PTS"])
    aggregated += existing_governors

    # Step 6 - Save files
    save_data_into_file(f"rok_gov_honor_all", all_governor_pts)
    save_data_into_file(f"rok_gov_honor_all_aggregated", aggregated)
