
from absl.testing import absltest
from absl.testing import parameterized
import emoji

class EmojiTest(parameterized.TestCase):
  @parameterized.parameters(
    (1.0, 1264),
    (2.0, 343),
    (3.0, 179),
    (4.0, 628),
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
    ((0x1F44D,), 21, True),
    ((0x1F9B5,), 21, False),
    ((0x1F469, 0x1F3FB, 0x200D, 0x1F9B0,), 27, False),
    ((0x1F469, 0x1F3FB, 0x200D, 0x1F9B0,), 28, True),
  )
  def test_supports(self, cp_seq, api_level, expected_result):
    filename = f'./api_level/{api_level}/NotoColorEmoji.ttf'
    self.assertEqual(emoji.supports(filename, cp_seq), expected_result)

if __name__ == '__main__':
  absltest.main()
