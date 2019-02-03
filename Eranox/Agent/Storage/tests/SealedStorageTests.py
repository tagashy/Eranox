import os
import unittest
from unittest.mock import patch, mock_open

from Eranox.Agent.Storage.SealedStorage import SealedStorage

BASE_PATH = "test/"


class SealedStorageTests(unittest.TestCase):

    def test_open(self):
        with patch("builtins.open", mock_open(read_data="data")) as mock_file:
            storage = SealedStorage(BASE_PATH)
            TEST_PATH = "BANANA"
            for path in [f"../../../{TEST_PATH}",
                         f"toto/../../../{TEST_PATH}",
                         f"tutu/toto/../../../{TEST_PATH}",
                         f"bobobo/tutu/toto/../../../{TEST_PATH}",
                         f"../tutu/../../{TEST_PATH}",
                         f"../tutu/../toto/../{TEST_PATH}",
                         f"../../../{TEST_PATH}/toto/../"]:
                print(f"path:{path}")
                storage.open(path)
                mock_file.assert_called_with(os.path.normpath(os.path.join(BASE_PATH, TEST_PATH)))
            path = "../../toto/../../../../../../../"
            storage.open(path)
            mock_file.assert_called_with(os.path.normpath(BASE_PATH))
