"""Regression tests for labels when UTF-8 characters cross token boundaries."""

import unittest

from token_labels import BYTE_DECODER, decode_token_labels


BYTE_ENCODER = {byte: char for char, byte in BYTE_DECODER.items()}


class ByteLevelTokenizer:
    class Backend:
        class ByteLevel:
            pass

        decoder = ByteLevel()

    backend_tokenizer = Backend()
    all_special_ids = [0]

    def __init__(self, pieces):
        self.pieces = pieces

    def convert_ids_to_tokens(self, token_id):
        return "".join(BYTE_ENCODER[byte] for byte in self.pieces[token_id])

    def decode(self, token_ids, skip_special_tokens=False):
        if token_ids == [0]:
            return "<|im_start|>"
        return self.pieces[token_ids[0]].decode("utf-8", errors="replace")


class TokenLabelTests(unittest.TestCase):
    def test_qwen_split_characters_keep_nine_positions(self):
        pieces = {
            68990: bytes.fromhex("E5 8C 97 E4 BA AC"),
            43589: bytes.fromhex("20 E7 9A 84"),
            40666: bytes.fromhex("20 E5 A4"),
            102: bytes.fromhex("A9"),
            99180: bytes.fromhex("E6 B0 94"),
            90476: bytes.fromhex("20 E6 80"),
            236: bytes.fromhex("8E"),
            81596: bytes.fromhex("E4 B9 88"),
            90885: bytes.fromhex("E6 A0 B7"),
        }
        ids = list(pieces)
        labels = decode_token_labels(ByteLevelTokenizer(pieces), ids)
        self.assertEqual(labels, ["北京", " 的", " ", "天", "气", " ", "怎", "么", "样"])
        self.assertEqual("".join(labels), "北京 的 天气 怎么样")

    def test_special_tokens_end_pending_bytes(self):
        tokenizer = ByteLevelTokenizer({1: b"\xe5\xa4", 2: b"\xa9"})
        self.assertEqual(
            decode_token_labels(tokenizer, [0, 1, 2, 0]),
            ["<|im_start|>", "", "天", "<|im_start|>"],
        )
        self.assertEqual(
            decode_token_labels(tokenizer, [1, 0, 2]),
            ["�", "<|im_start|>", "�"],
        )

    def test_other_tokenizer_uses_regular_decode(self):
        class PlainTokenizer:
            def decode(self, ids, skip_special_tokens=False):
                return str(ids[0])

        self.assertEqual(decode_token_labels(PlainTokenizer(), [1, 2]), ["1", "2"])


if __name__ == "__main__":
    unittest.main()
