import requests
from bs4 import BeautifulSoup
import pdfplumber
import re
from datetime import datetime, date
import json
from pathlib import Path


def serializer(py_obj):
    if isinstance(py_obj, date):
        return py_obj.isoformat()

    raise TypeError(f'Object of {type(py_obj)} is not JSON serializable')


def ingest_powerball():
    r = requests.get('https://floridalottery.com/games/winning-numbers/history')
    r.raise_for_status()

    soup = BeautifulSoup(r.text, 'html.parser')
    link_object = soup.find("a",string="POWERBALL")

    if link_object is None:
        raise ValueError("Link not found")

    link = link_object.get('href')

    pdf_response = requests.get(link)
    pdf_response.raise_for_status()

    raw_dest_folder = Path("./data/raw")
    raw_dest_folder.mkdir(parents=True, exist_ok=True)
    raw_dest_path = raw_dest_folder/"powerball.pdf"

    parsed_dest_folder = Path("./data/parsed")
    parsed_dest_folder.mkdir(parents=True, exist_ok=True)
    parsed_dest_path = parsed_dest_folder/"powerball_data.jsonl"

    with open(raw_dest_path, "wb") as f:
        f.write(pdf_response.content)
        print("Successfully saved raw powerball data")


    return parse_powerball_pdf(raw_dest_path, parsed_dest_path)


def parse_powerball_pdf(raw_path, parsed_path):
    with pdfplumber.open(raw_path) as pdf:
        row_list = []
        bad_rows = []
        records = []

        for page in pdf.pages:
            text = page.extract_text() or ""

            for line in text.splitlines():
                if re.match(r'^\d{1,2}/\d{1,2}/\d{2}', line):
                    if len(line.split()) != 10:
                        bad_rows.append(line)
                    else:
                        row_list.append(line)

        for row in row_list:
            records_data = row.split()
            if records_data[9] == 'DP':
                multiplier = None
                game_type= "POWERBALL_DP"
            else:
                multiplier = int(records_data[8].removeprefix("X"))
                game_type = "POWERBALL"

            record = {
                "draw_date": datetime.strptime(records_data[0], "%m/%d/%y").date(),
                "ball1": int(records_data[1]),
                "ball2": int(records_data[2]),
                "ball3": int(records_data[3]),
                "ball4": int(records_data[4]),
                "ball5": int(records_data[5]),
                "powerball": int(records_data[7]),
                "multiplier": multiplier,
                "game_type": game_type
            }

            records.append(record)

    if not records:
        raise ValueError("No Powerball draw records found")

    with open(parsed_path, "w") as f:
        for record in records:
            f.write(json.dumps(record, default=serializer) + '\n')
    print(f"Saved {len(records)} Powerball records. Skipped {len(bad_rows)} unexpected dated lines.")
    return True