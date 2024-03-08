from abc import ABC, abstractmethod


class AbstractDbHelper(ABC):
    @abstractmethod
    def get_connected(self, db_uri, db, log_helper):
        pass

    @abstractmethod
    def get_disconnected(self, log_helper):
        pass
