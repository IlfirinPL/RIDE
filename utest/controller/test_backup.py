from __future__ import with_statement

import unittest
from robotide.controller.chiefcontroller import Backup


class BackupTestCase(unittest.TestCase):

    def setUp(self):
        file_controller = lambda:0
        file_controller.filename = 'some_filename.txt'
        file_controller.refresh_stat = lambda:0
        self._backupper = _MyBackup(file_controller)

    def test_backup_is_restored_when_save_raises_exception(self):
        try:
            with self._backupper:
                raise _SaveFailed('expected')
            self.fail('should not get here')
        except _SaveFailed:
            self.assertTrue(self._backupper.restored)

    def test_backup_is_not_restored_when_save_passes(self):
        with self._backupper:
            self.assertNotEqual(None, self._backupper._backup)
            pass
        self.assertFalse(self._backupper.restored)
        self.assertEqual(None, self._backupper._backup)


class _SaveFailed(Exception):
    pass


class _MyBackup(Backup):

    def __init__(self, file_controller):
        Backup.__init__(self, file_controller)
        self._backup = object()
        self.restored = False

    def _move(self, from_path, to_path):
        self.restored = (self._backup == from_path)

    def _remove_backup(self):
        self._backup = None

if __name__ == '__main__':
    unittest.main()
