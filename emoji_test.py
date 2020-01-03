
from absl.testing import absltest
from absl.testing import parameterized
import emoji
import os

class EmojiTest(parameterized.TestCase):
  # Emojipedia shows (4.0, 628), seemingly due to 0x1F46F (people w/bunny ears)
  # and 0x1F93C (people wrestling) having gender and type modifiers.
  @parameterized.parameters(
    (1.0, 1264),
    (2.0, 343),
    (3.0, 179),
    (4.0, 608), # see note above
    (5.0, 239),
    (11.0, 157),
    (12.0, 230),
    (12.1, 168),
  )
  def test_expected_emoji_added(self, level, expected_delta):
    df = emoji.metadata()
    df = df.loc[(df['emoji_level'] == level)
                & (df['status'] == 'fully-qualified')]
    self.assertEqual(df.shape[0], expected_delta)


  @parameterized.parameters(
    (16, 'AndroidEmoji.ttf'),
    (19, 'AndroidEmoji.ttf'),
    (21, 'NotoColorEmoji.ttf'),
    (28, 'NotoColorEmoji.ttf'),
  )
  def test_emoji_font(self, api_level, expected_result):
    filename = os.path.basename(emoji.emoji_font(api_level))
    self.assertEqual(filename, expected_result)


  @parameterized.parameters(
    ((0x263A,), 18, True),  # AndroidEmoji in 19 is empty?
    ((0x200D,), 21, False),  # shapes to []
    ((0x1F44D,), 21, True),
    ((0x1F9B5,), 21, False),
    ((0x1f1e7, 0x1f1e7), 21, False),  # shapes to same gid twice
    ((0x1F469, 0x1F3FB, 0x200D, 0x1F9B0,), 27, False),
    ((0x1F469, 0x1F3FB, 0x200D, 0x1F9B0,), 28, True),
    ((0x1f9d1, 0x1f3fe, 0x200d, 0x1f9b0,), 28, False),  # multiple gids
  )
  def test_supports(self, cp_seq, api_level, expected_result):
    filename = emoji.emoji_font(api_level)
    self.assertEqual(emoji.supports(filename, cp_seq), expected_result)

if __name__ == '__main__':
  absltest.main()
