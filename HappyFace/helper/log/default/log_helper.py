import logging

from helper.log.abstract_log_helper import AbstractLoggingHelper


class LogHelper(AbstractLoggingHelper):
    def __init__(self, logger_name: str, log_file_name: str, log_format_template: str, log_file_open_mode: str):
        logging.basicConfig(
            level=logging.DEBUG,
            format=log_format_template,
            filename=log_file_name,
            filemode=log_file_open_mode
        )

        self.__logger = logging.getLogger(logger_name)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(logging.Formatter(log_format_template))
        self.__logger.addHandler(console_handler)

    def log_debug_message(self, message: str) -> None:
        self.__logger.debug(message)

    def log_info_message(self, message: str) -> None:
        self.__logger.info(message)

    def log_warn_message(self, message: str) -> None:
        self.__logger.warn(message)

    def log_error_message(self, message: str) -> None:
        self.__logger.error(message)

    def log_critical_message(self, message: str) -> None:
        self.__logger.critical(message)
