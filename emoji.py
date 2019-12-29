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
import os
import pandas
import regex
import subprocess

def _parse_emoji_test(filename):
  result = []
  #line_pat = regex.compile(r'^(?:([a-zA-Z0-9]+)(?:\s+|;))+;\s*([^#\s]+)\s*#\s*(.*)\s*$')
  line_pat = regex.compile(r'^(?:(?:([a-zA-Z0-9]+)(?:\s+|;))+|([a-zA-Z0-9]+[.][.][a-zA-Z0-9]+)(?:\s*));\s*([^#\s]+)\s*#\s*(.*)\s*$')
  with open(filename) as f:
    for l in f:
      match = line_pat.match(l)
      if not match:
        continue
      codepoints = tuple(int(s, 16) for s in match.captures(1))
      codepoint_range = match.group(2)
      if codepoints and codepoint_range:
        raise ValueError(f'Parse {l} failed horribly, {codepoints}, {codepoints_range}')
      status = match.group(3)
      notes = match.group(4)
      if codepoints:
        result.append((codepoints, status, notes))
      else:
        start, end = [int(s, 16) for s in codepoint_range.split('..')]
        for cp in range(start, end + 1):
          result.append(((cp,), status, notes))
  return result

def metadata():
  """Load metadata for Android emoji.

  Returns a pandas DataFrame with columns
  ['emoji_level', 'codepoints', 'status', 'notes']"""
  seq_min_level = {}
  seq_to_meta = {}
  for root, dirs, files in os.walk('emoji'):
    for file in files:
      should_parse = (file == 'emoji-test.txt'
                      or (file == 'emoji-data.txt'
                          and not os.path.isfile(os.path.join(root, 'emoji-test.txt'))))
      if should_parse:
        current_level = float(os.path.basename(root))
        recs = _parse_emoji_test(os.path.join(root, file))
        for codepoints, status, notes in recs:
          # Sequences should be attributed to the earliest level seen
          seq_min_level[codepoints] = min(seq_min_level.get(codepoints, current_level),
                                          current_level)

          # metadata is better when newer
          seq_to_meta[codepoints] = (status, notes)


  records = ((seq_min_level[codepoints], codepoints, status, notes)
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
  match = regex.match(r'\[(?:(\d+)[|\]]?)+\]', shape_result.stdout)
  if not match:
    raise IOError(f'Unable to parse {shape_result.stdout} from {" ".join(cmd)}')

    # if anything shaped to notdef we're borked
  return 0 not in {int(t) for t in match.captures(1)}


