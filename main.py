from datetime import datetime
from collections import namedtuple
import pyexcel as pe
import calendar
import cv2
import pytesseract
import numpy as np
import os


def get_grayscale(image):
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def thresholding(image):
    return cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]


def get_text(image, orc_locations):
    line = []
    for loc in orc_locations:
        (x, y, w, h) = loc.bbox
        crop = image[y:y + h, x:x + w]
        gray = get_grayscale(crop)
        # thresh = thresholding(gray)
        # cv2.imshow("tresh image", gray)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()
        text = pytesseract.image_to_string(
            gray,
            config=tesseract_config_number if loc.number else tesseract_config_text,
        )
        text = text.strip()
        if text == "":
            continue
        if loc.number is True:
            try:
                line += [int(text.replace("\n", ""))]
            except Exception as e:
                print(text)
                raise e
        else:
            line += [text.replace("\n", "")]
    return line


def parse_files(main_folder, ocr_models, export_base):
    main_path = os.path.abspath(main_folder)
    files = os.listdir(main_path)
    players = []
    for name in files:
        if name == ".DS_Store":
            continue
        ss_path = os.path.abspath(f"{main_folder}/{name}")
        if os.path.exists(ss_path):
            img = cv2.imread(ss_path)
            line = get_text(img, ocr_models)
            players += [line]
            export_base += [line]
    return players, export_base


def save_file(name, array_data):
    d_now = datetime.utcnow()
    date = d_now.strftime('%d_%m_%Y')
    ts = calendar.timegm(d_now.timetuple())

    filename = "%s-%s-%s" % (name, date, ts)
    p_dest = os.path.abspath("./%s.xlsx" % (filename))

    pe.save_as(
        array=array_data,
        dest_file_name=p_dest
    )


OCRLocation = namedtuple("OCRLocation", ["id", "bbox", "number"])
tesseract_config_number = "--oem 3 --psm 7 digits -c tessedit_char_whitelist=0123456789"
tesseract_config_text = "--oem 3 --psm 7"


def get_data_id_name_power_kill_points(save=True):
    export_header = [
        "ID",
        "NAME",
        "POWER",
        "KILL POINTS",
    ]
    export_base = []
    export_base.append(export_header)

    OCR_LOCATIONS = [
        OCRLocation("id", (1630, 774, 140, 33), True),
        OCRLocation("name", (1449, 806, 634, 58), False),
        OCRLocation("power", (1798, 940, 279, 43), True),
        OCRLocation("kill_points", (2088, 939, 286, 40), True),
    ]

    main_folder = "rok_ss_step_1"
    players, export_base = parse_files(main_folder, OCR_LOCATIONS, export_base)

    if save is True:
        save_file("2858_gov_id_name_pwr_killpts", export_base)

    return players


def get_data_name_deads(save=True):
    export_header = [
        "NAME",
        "DEAD",
    ]
    export_base = []
    export_base.append(export_header)

    OCR_LOCATIONS = [
        OCRLocation("name", (1118, 628, 466, 85), False),
        OCRLocation("dead", (1732, 1050, 609, 45), True),
    ]

    main_folder = "rok_ss_step_2"
    players, export_base = parse_files(main_folder, OCR_LOCATIONS, export_base)

    if save is True:
        save_file("2858_gov_name_deads", export_base)
    return players


def get_data_id_kills(save=True):
    export_header = [
        "ID",
        "KILLS T3",
        "KILL POINTS T3",
        "KILLS T4",
        "KILL POINTS T4",
        "KILLS T5",
        "KILL POINTS T5",
    ]
    export_base = []
    export_base.append(export_header)

    OCR_LOCATIONS = [
        OCRLocation("id", (1628, 770, 142, 37), True),
        OCRLocation("kills_t3", (1739, 1353, 331, 49), True),
        OCRLocation("kill_points_t3", (2121, 1356, 352, 45), True),
        OCRLocation("kills_t4", (1739, 1415, 331, 49), True),
        OCRLocation("kill_points_t4", (2121, 1417, 352, 45), True),
        OCRLocation("kills_t5", (1739, 1474, 331, 49), True),
        OCRLocation("kill_points_t5", (2121, 1477, 352, 45), True),
    ]

    main_folder = "rok_ss_step_3"
    players, export_base = parse_files(main_folder, OCR_LOCATIONS, export_base)

    if save is True:
        save_file("2858_gov_id_kills", export_base)
    return players


p1 = get_data_id_name_power_kill_points(save=False)
p2 = get_data_name_deads(save=False)
p3 = get_data_id_kills(save=False)

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
export_base = []
export_base.append(export_header)

d2 = {}
for player in p2:
    d2[player[0]] = player[1]

d3 = {}
for player in p3:
    d3[player[0]] = player[1:]

for player in p1:
    copy_player = player.copy()
    name = copy_player[1]
    id_ = copy_player[0]

    # match name with p2
    list_name_in_p2 = d2.keys()
    if name in list_name_in_p2:
        copy_player += [d2[name]]
    else:
        copy_player += []

    # match id with p3
    kills = d3.get(id_, [])
    if len(kills) == 6:
        copy_player += [col for col in kills]

    export_base += [copy_player]

d_now = datetime.utcnow()
date = d_now.strftime('%d_%m_%Y')
ts = calendar.timegm(d_now.timetuple())

filename = "%s-%s-%s" % ("rok_gov_stats", date, ts)
p_dest = os.path.abspath("./%s.xlsx" % (filename))

pe.save_as(
    array=export_base,
    dest_file_name=p_dest
)
