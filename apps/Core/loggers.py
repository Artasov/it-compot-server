import os
import time
from logging.handlers import TimedRotatingFileHandler


class CustomTimedRotatingFileHandler(TimedRotatingFileHandler):
    def __init__(self, dir_log, when='midnight', interval=1, backupCount=0, encoding=None, delay=False, utc=False,
                 atTime=None):
        # Генерируем начальное имя файла лога
        self.dir_log = dir_log  # Директория для файлов логов
        filename = self.generate_log_name()
        super().__init__(filename, when, interval, backupCount, encoding, delay, utc, atTime)

    def generate_log_name(self):
        # Генерация имени файла из текущей даты
        today = time.strftime("%Y-%m-%d")
        return os.path.join(self.dir_log, f"{today}.log")

    def doRollover(self):
        """
        Выполнить ротацию логов.
        """
        # Закрываем текущий файл лога
        if self.stream:
            self.stream.close()
            self.stream = None

        # Создаем новый файл лога с именем на основе текущей даты
        self.baseFilename = self.generate_log_name()
        if not os.path.exists(self.baseFilename):
            # Открываем новый файл лога
            self.mode = 'a'
            self.stream = self._open()

        # Удаляем старые файлы логов, если это необходимо
        if self.backupCount > 0:
            for s in self.getFilesToDelete():
                os.remove(s)

