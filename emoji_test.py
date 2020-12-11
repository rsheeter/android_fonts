
import emoji
import itertools
from itertools import chain
import os
import pytest


# Emojipedia shows (4.0, 628), seemingly due to 0x1F46F (people w/bunny ears)
# and 0x1F93C (people wrestling) having gender and type modifiers.
@pytest.mark.parametrize(
  "level, expected_delta",
  [
    (1.0, 1264),
    (2.0, 343),
    (3.0, 179),
    (4.0, 608), # see note above
    (5.0, 239),
    (11.0, 157),
    (12.0, 230),
    (12.1, 168),
    (13.0, 117),
    (13.1, 217),
  ],
)
def test_expected_emoji_added(level, expected_delta):
  df = emoji.metadata()
  df = df.loc[(df['emoji_level'] == level)
              & (df['status'] == 'fully-qualified')]
  assert df.shape[0] == expected_delta


@pytest.mark.parametrize(
  "api_level, expected_result",
  [
    (16, 'AndroidEmoji.ttf'),
    (19, 'AndroidEmoji.ttf'),
    (21, 'NotoColorEmoji.ttf'),
    (28, 'NotoColorEmoji.ttf'),
  ],
)
def test_emoji_font(api_level, expected_result):
  filename = os.path.basename(emoji.emoji_font(api_level))
  assert filename == expected_result


@pytest.mark.parametrize(
  "cp_seq, api_level, expected_result",
  [
    ((0x263A,), 18, True),  # AndroidEmoji in 19 is empty?
    ((0x200D,), 21, False),  # shapes to []
    ((0x1F44D,), 21, True),
    ((0x1F9B5,), 21, False),
    ((0x1f1e7, 0x1f1e7), 21, False),  # shapes to same gid twice
    ((0x1F469, 0x1F3FB, 0x200D, 0x1F9B0,), 27, False),
    ((0x1F469, 0x1F3FB, 0x200D, 0x1F9B0,), 28, True),
    ((0x1f9d1, 0x1f3fe, 0x200d, 0x1f9b0,), 28, False),  # multiple gids
  ],
)
def test_supports(cp_seq, api_level, expected_result):
  filename = emoji.emoji_font(api_level)
  assert emoji.supports(filename, cp_seq) == expected_result


@pytest.mark.parametrize(
  "filename, expected_result",
  [
    ('emoji_u1f646_1f3fb_200d_2642.ai', (0x1f646, 0x1f3fb, 0x200d, 0x2642)),
    ('/duck/emoji_u1f647.png', (0x1f647,)),
  ],
)
def test_codepoints(filename, expected_result):
  assert emoji.codepoints(filename) == expected_result


@pytest.mark.parametrize(
  "level, expected_delta",
  [
    (12.1, 0),
    (13.0, 56),  # 55 new + 26A7 newly classified emoji
  ],
)
def test_expected_codepoints_added(level, expected_delta):
  df = emoji.metadata()
  level_cp = set(itertools.chain.from_iterable( df[df.emoji_level == level].codepoints))
  prior_cp = set(itertools.chain.from_iterable( df[df.emoji_level < level].codepoints))
  new_at_level = level_cp - prior_cp
  assert len(new_at_level) == expected_delta



@pytest.mark.parametrize(
  "codepoints, expected_level",
  [
    ((0x1F600,), 1.0),  # Smiley Face
    # Men holding hands, medium dark tone and medium light tone
    ((0x1F468, 0x1F3FE, 0x200D, 0x1F91D, 0x200D, 0x1F468, 0x1F3FC), 12.0),
  ],
)
def test_expected_emoji_level(codepoints, expected_level):
  df = emoji.metadata()
  df = df[df.codepoints == codepoints]
  assert df.shape[0] == 1, "Should be only one matching record"
  assert df.iloc[0].emoji_level == expected_level


@pytest.mark.parametrize(
  "cp_seq, expected_groups",
  [
    # Smile w/hearts, added in 28
    ((0x1f970,), [[25, 26, 27], [28]]),
     # Smiley consistent 21..23, 24..25, 26..28, 29
    ((0x263A,), [[21, 22, 23], [24, 25], [26, 27, 28], [29]]), 
  ]
)
def test_hash_of_render(cp_seq, expected_groups):
  hashes = []
  for api_level in chain.from_iterable(expected_groups):
    font_file = emoji.emoji_font(api_level)
    hashes.append((api_level, emoji.hash_of_render(font_file, cp_seq)))
  hashes.sort()

  actual_groups = [[i[0] for i in g] for _, g in
                   itertools.groupby(hashes, key=lambda t: t[1])]
  assert actual_groups == expected_groups

