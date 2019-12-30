"""Generate a csv of emoji sequence support.

Saves time when running utilities that use the data.
Takes ~30M to run.
"""
import android_fonts
import emoji
import pandas as pd

def main():
  emoji_meta = emoji.metadata()
  emoji_levels = sorted(emoji_meta['emoji_level'].unique())

  fonts = android_fonts.metadata()
  fonts = fonts[fonts.font_file.str.endswith('Emoji.ttf')]

  support = []

  for emoji_level in emoji_levels:
    cp_seqs = emoji_meta[emoji_meta.emoji_level == emoji_level].codepoints
    # cp_seqs = cp_seqs[:2] # Uncomment for faster exec
    for font_file in sorted(fonts.font_file):
      print(f'Working on emoji {emoji_level}, {font_file}...')
      for cp_seq in cp_seqs:
        support.append((emoji_level, font_file, cp_seq, emoji.supports(font_file, cp_seq)))

  df = pd.DataFrame(support)
  df.columns=['emoji_level', 'font_file', 'cp_seq', 'supported']
  df.to_csv(android_fonts._SUPPORT_CACHE_CSV, index=False)
  print(f'Wrote {android_fonts._SUPPORT_CACHE_CSV}')


if __name__ == '__main__':
  main()
