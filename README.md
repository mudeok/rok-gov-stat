# rok-gov-stat 🚀

😈 *Needs [Tesseract](https://tesseract-ocr.github.io/tessdoc/#compiling-and-installation) and [OpenCV](https://opencv.org/) installed*

## Documentation

🚧 **Work In Progress**

Will do one day 😈😱

### Install deps

```
virtualenv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Getting started

`gov_stats.py` Line 199

```
folders = [
    ("alliance_gov_hs", "HS"),
    ("alliance_gov_bw", "BW"),
    ("alliance_gov_hw", "HW"),
    ("alliance_gov_sa", "SA"),
]
```
-> This should be updated according to your case. "alliance_gov_hs" is a folder containing screenshot for "HS" alliance.

# SUPER IMPORTANT NOTE:
screenshot should be taken in order starting by "MORE INFO" screen following by "GOVERNOR PROFILE" screen (with the kill points open)

Make sure to test with only one alliance and one governor.

`gov_stats.py` Line 19
```
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
```
-> This are coordinates for data and should be the same for all screenshot!
(I used photoshop to get coordinate, take a screenshot, open with photoshop and draw rectangle selection to get coordinates x, y, width and height)


