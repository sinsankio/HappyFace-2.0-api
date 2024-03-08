from abc import ABC, abstractmethod


class AbstractLoggingHelper(ABC):
    @abstractmethod
    def log_debug_message(self, message):
        pass

    @abstractmethod
    def log_info_message(self, message):
        pass

    @abstractmethod
    def log_warn_message(self, message):
        pass

    @abstractmethod
    def log_error_message(self, message):
        pass

    @abstractmethod
    def log_critical_message(self, message):
        pass
