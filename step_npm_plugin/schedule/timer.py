import time

from step_npm_plugin.schedule.parser import parse_time


class Timer:
    """
    Timer that watches a schedule and provides information based on the schedule.
    """
    _sync_to_clock: bool = True
    _next_run: int = None
    _schedule_seconds: int = None
    _skipped_runs: int = 0
    _runs: int = 0

    def __init__(self, sync_clock: bool = True):
        self._sync_to_clock = sync_clock

    def set_schedule(self, schedule: str) -> None:
        self._schedule_seconds = parse_time(schedule)

        time_now = round(time.time())

        if self._sync_to_clock:
            self._next_run = (time_now + (self._schedule_seconds - (time_now % self._schedule_seconds)))
        else:
            self._next_run = time_now + self._schedule_seconds

    @property
    def scheduled(self) -> bool:
        return False if self._next_run is None else True

    @property
    def breached(self) -> bool:
        if self.scheduled is None:
            return False

        if self._next_run > round(time.time()):
            return False

        self._next_run += self._schedule_seconds

        if self._next_run < round(time.time()):
            self._skipped_runs += 1
            return self.breached

        self._runs += 1

        return True

    @property
    def runs(self) -> int:
        return self._runs

    @property
    def skipped(self) -> int:
        return self._skipped_runs
