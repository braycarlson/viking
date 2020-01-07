from datetime import datetime, timedelta


def run_at(hour: int = 0, minute: int = 0, second: int = 0):
    """
    A function that returns the seconds until a specified time.
    """

    today = datetime.today()
    midnight = today.replace(
        day=today.day,
        hour=hour,
        minute=minute,
        second=second,
        microsecond=0
    ) + timedelta(days=1)

    run = midnight - today
    return run.total_seconds()


def timeout(hours: int = 0, minutes: int = 0, seconds: int = 0):
    """
    A function that returns a timeout in seconds.
    """

    today = datetime.now()
    timeout = today.replace(
        day=today.day,
        hour=today.hour,
        minute=today.minute,
        second=today.second,
        microsecond=today.microsecond
    ) + timedelta(hours=hours, minutes=minutes, seconds=seconds)

    run = timeout - today
    return run.total_seconds()


def midnight():
    """
    A function that returns the seconds until midnight.
    """

    today = datetime.today()
    midnight = today.replace(
        day=today.day,
        hour=0,
        minute=0,
        second=0,
        microsecond=0
    ) + timedelta(days=1)

    run = midnight - today
    return run.total_seconds()
