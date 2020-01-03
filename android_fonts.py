import ast
import os
import pandas as pd

_SUPPORT_CACHE_CSV = 'emoji_support.csv'

_API_LEVELS = {
  1: ("(no codename)", "1.0"),
  2: ("(no codename)", "1.1"),
  3: ("Cupcake", "1.5 "),
  4: ("Donut", "1.6 "),
  5: ("Eclair", "2.0"),
  6: ("Eclair", "2.0.1"),
  7: ("Eclair", "2.1 "),
  8: ("Froyo", "2.2.x "),
  9: ("Gingerbread", "2.3 - 2.3.2 "),
  10: ("Gingerbread", "2.3.3 - 2.3.7"),
  11: ("Honeycomb", "3.0"),
  12: ("Honeycomb", "3.1 "),
  13: ("Honeycomb", "3.2.x"),
  14: ("Ice Cream Sandwich", "4.0.1 - 4.0.2 "),
  15: ("Ice Cream Sandwich", "4.0.3 - 4.0.4 "),
  16: ("Jelly Bean", "4.1.x"),
  17: ("Jelly Bean", "4.2.x"),
  18: ("Jelly Bean", "4.3.x"),
  19: ("KitKat", "4.4 - 4.4.4"),
  21: ("Lollipop", "5.0"),
  22: ("Lollipop", "5.1"),
  23: ("Marshmallow", "6.0"),
  24: ("Nougat", "7.0"),
  25: ("Nougat", "7.1"),
  26: ("Oreo", "8.0.0"),
  27: ("Oreo", "8.1.0"),
  28: ("Pie", "9"),
  29: ("Android10", "10"),
}

def api_levels():
  return _API_LEVELS

def is_font_file(file):
  _, ext = os.path.splitext(file)
  return ext.lower() in {'.ttf', '.otf', '.ttc'}

def metadata():
  records = []
  for root, dirs, files in os.walk('api_level'):
    for file in files:
      if is_font_file(file):
        full_file = os.path.join(root, file)
        api_level = int(os.path.basename(root))
        size = os.stat(full_file).st_size
        records.append((api_level, full_file, size))
  df = pd.DataFrame(records)
  df.columns = ['api_level', 'font_file', 'file_size']
  return df

def emoji_support():
  """Dataframe of [emoji_level, font_file, codepoints, supported].

  Includes every sequence we could find of any type.

  Requires prior execution of populate_emoji_support.py"""

  if not os.path.isfile(_SUPPORT_CACHE_CSV):
    raise IOError('Please run populate_emoji_support.py first')
  return (pd.read_csv(_SUPPORT_CACHE_CSV, converters={'cp_seq': ast.literal_eval})
          .rename(columns={'cp_seq': 'codepoints'}))

