# rok-gov-stat 🚀

😈 *Needs [Tesseract](https://tesseract-ocr.github.io/tessdoc/#compiling-and-installation) and [OpenCV](https://opencv.org/) installed*

### Install deps

```
virtualenv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Getting started

*You will need to adjust the script to your needs*

**To work, you need to prepare two screenshots for each governor.**

- **First screenshot** should be **More Info** screen.
- **Second screenshot** should be **Governor Profile** screen.

Then,

- Save all screenshots inside a folder or multiple folders (e.g for each alliance)
- Update in file the coordinates for OCR to your needs. *(e.g use photoshop to get x, y, width and height that are coordinates of a rectangle. It should cover the area to capture)*
- **Run the program `python gov_stats.py`**


### Informations

The programm will do:

- Step 1 - Retrieve old data if any
- Step 2 - Initialize list of governors
- Step 3 - Parse all folders and save governors data
- Step 4 - Saving existing governors following the same order that old data imported
- Step 5 - Save new governors for which data was never collected
- Step 6 - Save files


# SUPER IMPORTANT NOTE:

**screenshot should be taken in order starting by "MORE INFO" screen following by "GOVERNOR PROFILE" screen (with the kill points open)**

```
more_info_screen = [
    OCR_LOCATION("name", (1142, 675, 462, 95), False),
    OCR_LOCATION("power", (1701, 675, 325, 95), True),
    OCR_LOCATION("kills_points", (2216, 675, 258, 95), True),
    OCR_LOCATION("dead", (1789, 1088, 570, 65), True),
    OCR_LOCATION("ressource_gathered", (1789, 1313, 570, 65), True),
    OCR_LOCATION("ressource_assistance", (1789, 1394, 570, 65), True),
    OCR_LOCATION("alliance_help_times", (1789, 1475, 570, 65), True),
]

governor_profile_screen = [
    OCR_LOCATION("id", (1650, 822, 145, 41), True),
    OCR_LOCATION("kills_t3", (1763, 1404, 336, 52), True),
    OCR_LOCATION("kills_t4", (1763, 1464, 336, 52), True),
    OCR_LOCATION("kills_t5", (1763, 1523, 336, 52), True),
]
```

-> This are coordinates for data and should be the same for all screenshot!
(I used photoshop to get coordinate, take a screenshot, open with photoshop and draw rectangle selection to get coordinates x, y, width and height)


# SUPER IMPORTANT NOTE 2 MEGA IMPORTANT:

**The script is also working with aggregation data into old one by using an `export.csv` in a `./data` folder. Make sure to create a folder with an empty `export.csv` file inside**

