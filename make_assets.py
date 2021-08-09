"""Generates assets for web display of Android font info."""
from absl import app
from absl import flags
import android_fonts
import copy
import emoji
import json
from lxml import etree
import os

FLAGS = flags.FLAGS

flags.DEFINE_boolean('generate_legacy_images', True,
                     'Whether to generate images for web-incompatible fonts.'
                     ' Turn off if you already have them and want to save time.')

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
  # df['hashes_of_renders'] = (df[['api_level', 'hash_of_render']]
  #                            .apply(lambda t: (t.api_level, t.hash_of_render), axis=1))

  df = (df.groupby(['codepoints', 'emoji_level'])
        .agg({
              'api_support': lambda t: sorted({api for api, supported in t if supported}),
              #'hashes_of_renders': lambda t: {api: hash for api, hash in t},
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

def remove_svg_width_height(svg_file):
  svg = etree.parse(svg_file)
  del svg.getroot().attrib['width']
  del svg.getroot().attrib['height']
  with open(svg_file, 'wb') as f:
    svg.write(f, pretty_print=True)

def _make_legacy_images():
  df = android_fonts.emoji_detail();
  df = df[(df['supported'] == 1)
          & (df['font_file'] == 'AndroidEmoji.ttf')]
  print(f'Saving {df.shape[0]} images...')
  for _, row in df.iterrows():
    api = row.api_level
    codepoints = row.codepoints
    font_file = f'api_level/{row.api_level}/{row.font_file}'
    img_dir = _out(f'api_level/{row.api_level}')
    os.makedirs(img_dir, exist_ok=True)
    img_file = os.path.join(img_dir,
                            'emoji_u'
                            + '_'.join(['%04x' % v for v in row.codepoints])
                            + '.svg')
    emoji.render(font_file, codepoints, img_file)
    remove_svg_width_height(img_file)


def main(_):
  _make_summary_json()
  _make_emoji_json()
  _make_graphs()
  if FLAGS.generate_legacy_images:
    _make_legacy_images()

if __name__ == "__main__":
    app.run(main)
