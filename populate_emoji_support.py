"""Generate a csv of emoji sequence support.

Saves time when running utilities that use the data.
Takes ~30M to rebuild from scratch.
Specify --font_file api_level/##/NotoColorEmoji.ttf to update
a single emoji file.
"""
from absl import app
from absl import flags
import android_fonts
import base64
import emoji
from operator import itemgetter
import pandas as pd


FLAGS = flags.FLAGS

flags.DEFINE_string('font_file', None,
                    'file_path, e.g. api_level/29/NotoColorEmoji.ttf.'
                    ' Any existing entries for this path will be removed.'
                    ' New entries will be generated for this font.'
                    ' Entries for any other file will be untouched.')


def _build_dataset():
  emoji_meta = emoji.metadata()
  emoji_levels = sorted(emoji_meta['emoji_level'].unique())

  fonts = android_fonts.metadata()
  fonts = fonts[fonts.font_file.str.endswith('Emoji.ttf')]

  support = []
  if FLAGS.font_file:
    fonts = fonts[fonts.font_file == FLAGS.font_file]
    support = android_fonts.emoji_support()
    support_len_before = support.shape[0]
    support = support[support.font_file != FLAGS.font_file]
    support = [tuple(r) for r in support.values]
    support_len_after = len(support)
    print(f'Dropped {support_len_before - support_len_after} entries'
          f', keeping {support_len_after}.')

  for emoji_level in emoji_levels:
    cp_seqs = emoji_meta[emoji_meta.emoji_level == emoji_level].codepoints
    # cp_seqs = cp_seqs[:2] # Uncomment for faster exec
    for font_file in sorted(fonts.font_file):
      print(f'Working on emoji {emoji_level}, {font_file}...')
      for cp_seq in cp_seqs:
        supported = emoji.supports(font_file, cp_seq)
        hash_of_render = ''
        if supported:
          hash_of_render = emoji.hash_of_render(font_file, cp_seq)
          hash_of_render = base64.b64encode(hash_of_render).decode('ascii')
        support.append((emoji_level, font_file, cp_seq,
                        supported, f'{int(supported)}_{hash_of_render}')) 

  support.sort(key=itemgetter(0, 1, 2))
  df = pd.DataFrame(support)
  df.columns=['emoji_level', 'font_file', 'cp_seq', 'supported', 'hash_of_render']

  return df


def main(_):
  df = _build_dataset()
  df.to_csv(android_fonts._SUPPORT_CACHE_CSV, index=False)
  print(f'Wrote {android_fonts._SUPPORT_CACHE_CSV}')


if __name__ == '__main__':
  app.run(main)
