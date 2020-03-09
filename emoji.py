"""Helpers for emoji metadata.

Assumes presence of files gathered with something like:

for e in 1.0 2.0 3.0 4.0 5.0 11.0; do \
  mkdir emoji/$e/; \
  for s in data sequences test variation-sequences zwj-sequences; do \
    curl -o emoji/$e/emoji-${s}.txt https://www.unicode.org/Public/emoji/$e/emoji-$s.txt; \
  done; \
done;

Some APIs assume harfbuzz compiled at ./harfbuzz.
"""
import collections
import os
import pandas
import regex
import subprocess


_LINE_FILTERS = {
  # 11.0 file has a bunch of things it doesn't support with this classification
  'emoji-data.txt': lambda parts: parts[1] != 'Extended_Pictographic',  
}

_LEVEL_OVERRIDES = {
  # keycaps (qualified) in 3.0 rather than 1.0
  (0x23, 0xFE0F, 0x20E3): 3.0,
  (0x2A, 0xFE0F, 0x20E3): 3.0,
  (0x30, 0xFE0F, 0x20E3): 3.0,
  (0x31, 0xFE0F, 0x20E3): 3.0,
  (0x32, 0xFE0F, 0x20E3): 3.0,
  (0x33, 0xFE0F, 0x20E3): 3.0,
  (0x34, 0xFE0F, 0x20E3): 3.0,
  (0x35, 0xFE0F, 0x20E3): 3.0,
  (0x36, 0xFE0F, 0x20E3): 3.0,
  (0x37, 0xFE0F, 0x20E3): 3.0,
  (0x38, 0xFE0F, 0x20E3): 3.0,
  (0x39, 0xFE0F, 0x20E3): 3.0,
}

_STATUS_OVERRIDES = {
  # Handshakes and Wrestlers uniquely *only* appear as Emoji_Modifier_Sequence
  (129309, 127995): 'fully-qualified',
  (129309, 127995): 'fully-qualified',
  (129309, 127996): 'fully-qualified',
  (129309, 127997): 'fully-qualified',
  (129309, 127998): 'fully-qualified',
  (129309, 127999): 'fully-qualified',
  (129340, 127995): 'fully-qualified',
  (129340, 127996): 'fully-qualified',
  (129340, 127997): 'fully-qualified',
  (129340, 127998): 'fully-qualified',
  (129340, 127999): 'fully-qualified',
}

def datafile(filename):
  return os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)


def emoji_font(api_level):
  dirpath = datafile(f'./api_level/{api_level}/')
  fonts = [f for f in os.listdir(dirpath)
           if 'Emoji' in f]
  if len(fonts) > 1:
    raise IOError(f'Too many choices in {dirpath}: {fonts}')
  return os.path.abspath(os.path.join(dirpath, fonts[0])) if fonts else None


def _parse_emoji_test(filename):
  result = []

  basename = os.path.basename(filename)
  with open(filename) as f:
    for line in f:
      line = line.strip()
      if line.startswith('#') or not line:
        continue

      # Single regex got a bit long, just split repeatedly
      parts = regex.split(r'[;]', line)
      if '#' in parts[-1]:
        parts = parts[:-1] + regex.split(r'[#]', parts[-1], maxsplit=1)
      parts = [p.strip() for p in parts]

      if not _LINE_FILTERS.get(basename, lambda _: True)(parts):
        continue

      raw_codepoints = parts[0]
      status = parts[1] if len(parts) == 3 else '?'
      notes = parts[-1]

      # raw_codepoints is either 1 or more space separated hex values or A..B range
      match = regex.match(r'^(?:([a-zA-Z0-9]+)([.][.]|\s+)?)+$', raw_codepoints)
      if not match:
        raise IOError(f'Unable to parse codepoints from "{line}"')

      codepoints = tuple(int(s, 16) for s in match.captures(1))
      if not codepoints:
        raise IOError(f'Failed to extract codepoints from "{line}"')

      if match.group(2) == '..':
        if len(codepoints) != 2:
          raise IOError(f'Bad range in "{line}"')
        for codepoint in range(codepoints[0], codepoints[1] + 1):
          result.append(((codepoint,), status, notes))  
      else:
        result.append((codepoints, status, notes))
  return result


def metadata():
  """Load metadata for Android emoji.

  Does NOT implement exactly http://www.unicode.org/reports/tr51/#Major_Sources
  because that didn't do well at identifying older emoji version content.

  Returns a pandas DataFrame with columns
  ['emoji_level', 'codepoints', 'status', 'notes']"""
  seq_minmax_level = {}
  seq_to_meta = {}
  for root, dirs, files in os.walk(datafile('emoji')):
    for file in files:
      current_level = float(os.path.basename(root))
      recs = _parse_emoji_test(os.path.join(root, file))
      for codepoints, status, notes in recs:
        curr_min, curr_max = seq_minmax_level.get(codepoints, (current_level, current_level))

        min_level = min(curr_min, current_level)
        max_level = max(curr_min, current_level)
        seq_minmax_level[codepoints] = (min_level, max_level)

        # metadata seems to have improved over time, prefer newest one from emoji-test.txt
        if not codepoints in seq_to_meta:
          seq_to_meta[codepoints] = (status, notes)
        elif current_level >= curr_max and file == 'emoji-test.txt':
          seq_to_meta[codepoints] = (status, notes)

  # if we've seen the unqualified version earlier, bump back qualified to match
  # seems to only apply to some of the very early versions
  for codepoints, (status, notes) in seq_to_meta.items():
    if status == 'fully-qualified' and 0xFE0F in codepoints:
      cp_unqualified = tuple((cp for cp in codepoints if cp != 0xFE0F))
      seq_minmax_level[codepoints] = min(seq_minmax_level[cp_unqualified],
                                         seq_minmax_level[codepoints])

  # apply fixups where data seemed off
  for codepoints, level in _LEVEL_OVERRIDES.items():
    if not codepoints in seq_minmax_level:
      continue
    seq_minmax_level[codepoints] = (level, level)

  for codepoints, status in _STATUS_OVERRIDES.items():
    if not codepoints in seq_to_meta:
      continue
    (_, notes) = seq_to_meta[codepoints]
    seq_to_meta[codepoints] = (status, notes)

  # attribute sequence to earliest observed level
  records = ((seq_minmax_level[codepoints][0], codepoints, status, notes)
             for codepoints, (status, notes) in seq_to_meta.items())
  df = pandas.DataFrame(records)
  df.columns = ['emoji_level', 'codepoints', 'status', 'notes']
  return df


def supports(font_file, cp_seq):
  cmd = [
    './harfbuzz/util/hb-shape',
    '--no-glyph-names',
    '--no-positions',
    '--no-advances',
    '--no-clusters',
    "-u",
    " ".join(("%x" % c for c in cp_seq)),
    font_file,
  ]

  shape_result = subprocess.run(cmd, capture_output=True, text=True)
  if shape_result.returncode != 0:
    raise IOError(f'Code {shape_result.returncode} from "{" ".join(cmd)}"'
                  f', stderr {shape_result.stderr}')
  match = regex.match(r'\[(?:(\d+)[|\]]?)*\]', shape_result.stdout)
  if not match:
    raise IOError(f'Unable to parse {shape_result.stdout} from {" ".join(cmd)}')

  # shaping to nothing or including a notdef is bad
  # a single non-zero gid is required for full support
  # otherwise [adult][red hair] is "support"
  # NOTE: this will implode horribly for a composed font
  # will need to consider positions when that comes around
  cps = [int(t) for t in match.captures(1)]
  return len(cps) == 1 and 0 not in cps


def render(font_file, cp_seq, dest_file):
  cmd = [
    './harfbuzz/util/hb-view',
    "-u",
    " ".join(("%x" % c for c in cp_seq)),
    "-o",
    dest_file,
    font_file,
  ]
  view_result = subprocess.run(cmd, capture_output=True, text=True)
  if view_result.returncode != 0:
    raise IOError(f'Code {view_result.returncode} from "{" ".join(cmd)}"'
                  f', stderr {view_result.stderr}')


def codepoints(filename):
  _, filename = os.path.split(filename)
  match = regex.match(r'^emoji_u(?:([a-zA-Z0-9]+)_?)+[.](ai|png|svg)',
                      filename)
  if not match:
    raise ValueError(f'{filename} not recognized')
  return tuple(int(v, 16) for v in match.captures(1))

