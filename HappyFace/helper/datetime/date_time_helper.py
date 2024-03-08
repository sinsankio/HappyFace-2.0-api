from datetime import datetime, timedelta


class DateTimeHelper:
    @staticmethod
    def get_iso_datetime(current_datetime: datetime) -> str:
        return current_datetime.isoformat()

    @staticmethod
    def get_current_iso_datetime() -> str:
        current_datetime = datetime.now()
        return DateTimeHelper.get_iso_datetime(current_datetime)

    @staticmethod
    def str_to_iso_datetime(datetime_str: str, dt_format: str = "%Y-%m-%dT%H:%M:%S.%f") -> datetime:
        return datetime.strptime(datetime_str, dt_format)

    @staticmethod
    def subtract_iso_datetime(hours: int = 0, weeks: int = 0, months: int = 0, years: int = 0):
        current_datetime = datetime.now()
        duration = timedelta(
            hours=hours,
            weeks=weeks,
            days=months * 30 + years * 365
        )
        result_datetime = current_datetime - duration
        return DateTimeHelper.get_iso_datetime(result_datetime)
