# Usage:
#
#  python3 size_csv.py api_level/31/*.(otf|ttf|ttc)
#

import csv
import os
import sys


def main(argv):
    font_dict = {}
    total_filesize = 0
    total_font_count = 0
    fields = ["Font", "Size (B)"]
    csv_data_list = []

    for fontpath in argv:
        size = os.path.getsize(fontpath)
        total_filesize += size
        total_font_count += 1
        font_dict[os.path.basename(fontpath)] = size

    for key in sorted(font_dict):
        print(f"{key} : {font_dict[key]}")
        csv_data_list.append({"Font": key, "Size (B)": font_dict[key]})

    print(f"\nTotal size: {total_filesize}")
    print(f"Total fonts: {total_font_count}")

    with open("fontsize.csv", "w") as csvfile:
        csvwriter = csv.DictWriter(csvfile, fieldnames=fields)
        csvwriter.writeheader()
        csvwriter.writerows(csv_data_list)


if __name__ == "__main__":
    main(sys.argv[1:])
