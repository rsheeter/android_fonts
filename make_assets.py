"""Generates assets for web display of Android font info."""
import android_fonts
import copy
import emoji
import json
import os

def _out(file):
  return os.path.join(os.path.expanduser('~/oss/rsheeter.github.io/android_fonts'),
                      file)

_SUMMARY = _out('emoji_summary.json')
_EMOJI = _out('emoji_detail.json')

def _add_font_info(summary):
  sf = android_fonts.font_summary()
  for rec in json.loads(sf.to_json(orient='records')):
    api_level = rec['api_level']
    del rec['api_level']
    summary[api_level]['fonts'] = rec

def _add_emoji_info(summary):
  by_emoji_level, by_api_level = android_fonts.emoji_summary()

  for rec in json.loads(by_emoji_level.to_json(orient='records')):
    api_level = rec['api_level']
    del rec['api_level']
    del rec['font_file']
    summary[api_level]['emoji']['by_level'].append(rec)

  for _, row in by_api_level.iterrows():
    emoji = summary[row.api_level]['emoji']
    emoji['delta'] = row.delta
    emoji['supported'] = row.supported

def _make_summary_json():
  # init summary with no font or emoji data
  summary = {}
  for api_level, (name, version) in android_fonts.api_levels().items():
    summary[api_level] = {
      'name': name,
      'version': version,
      'fonts': None,
      'emoji': {
        'delta': 0,
        'supported': 0,
        'by_level': []
      },
    }

  _add_font_info(summary)
  _add_emoji_info(summary)

  with open(_SUMMARY, 'w') as f:
    f.write(json.dumps(summary, indent=2))
  print(f'Wrote {_SUMMARY}')

def _make_emoji_json():
  # meant for searching emoji sequences
  df = android_fonts.emoji_detail()
  df['api_support'] = (df[['api_level', 'supported']]
                       .apply(lambda t: (t.api_level, t.supported), axis=1))

  df = (df.groupby(['codepoints', 'emoji_level'])
        .agg({
              'api_support': lambda t: {api for api, supported in t if supported},
              'notes': lambda n: n.unique(),
             }))
  df.reset_index(inplace=True)

  with open(_EMOJI, 'w') as f:
    f.write(json.dumps(json.loads(df.to_json(orient='records')), indent=2))
  print(f'Wrote {_EMOJI}')

def _save_graph(ax, filename):
  ax.get_figure().savefig(_out(filename))
  print(f'Wrote {_out(filename)}')

def _make_graphs():
  df = android_fonts.font_summary()
  _save_graph(df.plot.bar(x='api_level', y='size_MB'),
              'size_total.png')
  _save_graph(df.plot.bar(x='api_level', y='delta_size_MB'),
              'size_change.png')

def main():
  _make_summary_json()
  _make_emoji_json()
  _make_graphs()

if __name__ == '__main__':
  main()
