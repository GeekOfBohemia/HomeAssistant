from abc import abstractmethod
from dataclasses import dataclass
import re
import datetime
from typing import Any, Union
import uuid
import pytz
from astral.location import Location
from astral import LocationInfo
import sys
import os
from overrides import override


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from appframe.ha_client import HAClientApi
from appframe.type_def import BasicEntity, StrType

ELEVATION = 179
ZONE = "Europe/Prague"
LATITUDE = 50.2779458
LONGITUDE = 14.3686039
TimeType = datetime.datetime
TimeTypeNone = Union[TimeType, None]


@dataclass
class SchedulerElement:
    handler: Any = None
    delay: int = 0
    ended: bool = False
    time_rest: int = 0

    def __post_init__(self):
        self.handler = uuid.uuid4().hex

    def set_sensor_time_left(self, time_left: int):
        pass

    def in_time(self) -> bool:
        self.time_rest = 0

        start_time = self.get_start_time()
        if start_time is None:
            self.set_sensor_time_left(0)
            return True
        elif self.end_time is not None:
            aware_datetime = datetime.datetime.now(pytz.timezone("Europe/Prague"))
            now = aware_datetime.replace(tzinfo=None)

            ret_val = start_time <= now <= self.end_time
            if ret_val:
                self.set_sensor_time_left(int((self.end_time - now).total_seconds()))
                return True
            else:
                self.set_sensor_time_left(0)
                return False
        else:
            self.set_sensor_time_left(0)
            return False

    @abstractmethod
    def finish(self):
        ...

    @abstractmethod
    def get_start_time(self) -> TimeTypeNone:
        ...

    @property
    def end_time(self) -> TimeTypeNone:
        start_time = self.get_start_time()
        if start_time is None:
            return None
        else:
            retval = start_time + datetime.timedelta(seconds=self.delay)
            return retval


@dataclass
class RunDelay(SchedulerElement):
    start_time: TimeTypeNone = None
    callback: Any = None
    parent: Any = None

    def __post_init__(self):
        super().__post_init__()
        self.start_time = datetime.datetime.now()

    def get_start_time(self) -> TimeTypeNone:
        return self.start_time

    def finish(self):
        # self.parent.remove_element()
        del self.parent.queue[self.handler]
        self.callback()


@dataclass
class SchedulerEntity(BasicEntity, SchedulerElement):
    sensor_entity_id: str = ""

    @override
    def set_sensor_time_left(self, time_left: int):
        if self.sensor_entity_id and self.ha_instance is not None:
            time_left = int(time_left / 60)
            self.ha_instance.set_sensor(self.sensor_entity_id, time_left)

    @override
    def get_start_time(self):
        if self.ha_instance is not None:
            if self.ha_instance.is_entity_on(self.entity_id):
                return self.ha_instance.get_last_update(self.entity_id)
            else:
                return None

    @override
    def finish(self):
        if self.ha_instance is None:
            return
        if self.ha_instance.is_entity_on(self.entity_id):
            self.ha_instance.turn_off(self.entity_id)


@dataclass
class SchedulerEntityDelay(SchedulerEntity):
    delay_entity_id: str = ""
    multiply: int = 1

    @property
    def end_time(self) -> TimeTypeNone:
        self.delay = (
            self.ha_instance.get_state_int(self.delay_entity_id) * self.multiply
        )
        return super().end_time


class Scheduler(HAClientApi):
    def __init__(self):
        super().__init__()
        self.realtime = True
        self.now: TimeType = pytz.utc.localize(datetime.datetime.utcnow())
        self.location = Location(LocationInfo("", "", ZONE, LATITUDE, LONGITUDE))
        self.queue = {}

    def next_sunrise(self, offset: int = 0):
        day_offset = 0
        while True:
            try:
                candidate_date = (
                    (self.now + datetime.timedelta(days=day_offset))
                    .astimezone(self.ADtz)
                    .date()
                )
                next_rising_dt = self.location.sunrise(
                    date=candidate_date,
                    local=False,
                    observer_elevation=ELEVATION,
                )
                if next_rising_dt + datetime.timedelta(seconds=offset) > (
                    self.now + datetime.timedelta(seconds=1)
                ):
                    break
            except ValueError:
                pass
            day_offset += 1

        return next_rising_dt

    def next_sunset(self, offset: int = 0):
        day_offset = 0
        while True:
            try:
                candidate_date = (
                    (self.now + datetime.timedelta(days=day_offset))
                    .astimezone(self.ADtz)
                    .date()
                )
                next_setting_dt = self.location.sunset(
                    date=candidate_date, local=False, observer_elevation=ELEVATION
                )
                if next_setting_dt + datetime.timedelta(seconds=offset) > (
                    self.now + datetime.timedelta(seconds=1)
                ):
                    break
            except ValueError:
                pass
            day_offset += 1

        return next_setting_dt

    def todays_sunrise(self, days_offset):
        candidate_date = (
            (self.now + datetime.timedelta(days=days_offset))
            .astimezone(self.ADtz)
            .date()
        )
        next_rising_dt = self.location.sunrise(
            date=candidate_date, local=False, observer_elevation=ELEVATION
        )

        return next_rising_dt

    @property
    def ADtz(self):
        return pytz.timezone(ZONE)

    def get_now(self) -> TimeType:
        if self.realtime is True:
            return pytz.utc.localize(datetime.datetime.utcnow())
        else:
            return self.now

    def todays_sunset(self, days_offset):
        candidate_date = (
            (self.now + datetime.timedelta(days=days_offset))
            .astimezone(self.ADtz)
            .date()
        )
        next_setting_dt = self.location.sunset(
            date=candidate_date, local=False, observer_elevation=ELEVATION
        )

        return next_setting_dt

    def sunset(self, aware, today=False, days_offset=0):
        if aware is True:
            if today is True:
                return self.todays_sunset(days_offset).astimezone(self.ADtz)
            else:
                return self.next_sunset().astimezone(self.ADtz)
        else:
            if today is True:
                return self.make_naive(
                    self.todays_sunset(days_offset).astimezone(self.ADtz)
                )
            else:
                return self.make_naive(self.next_sunset().astimezone(self.ADtz))

    def sunrise(self, aware, today=False, days_offset=0):
        if aware is True:
            if today is True:
                return self.todays_sunrise(days_offset).astimezone(self.ADtz)
            else:
                return self.next_sunrise().astimezone(self.ADtz)
        else:
            if today is True:
                return self.make_naive(
                    self.todays_sunrise(days_offset).astimezone(self.ADtz)
                )
            else:
                return self.make_naive(self.next_sunrise().astimezone(self.ADtz))

    def now_is_between(self, start_time_str, end_time_str, name=None, now=None):
        start_time = (
            self._parse_time(start_time_str, name, today=True, days_offset=0)
        )["datetime"]
        end_time = (self._parse_time(end_time_str, name, today=True, days_offset=0))[
            "datetime"
        ]
        if now is not None:
            now = (self._parse_time(now, name))["datetime"]
        else:
            now = (self.get_now()).astimezone(self.ADtz)

        # self.diag.info(f"locals: {locals()}")
        # Comparisons
        if end_time < start_time:
            # self.diag.info("Midnight transition")
            # Start and end time backwards.
            # Spans midnight
            # Lets start by assuming end_time is wrong and should be tomorrow
            # This will be true if we are currently after start_time
            end_time = (
                self._parse_time(end_time_str, name, today=True, days_offset=1)
            )["datetime"]
            if now < start_time and now < end_time:
                # self.diag.info("Reverse")
                # Well, it's complicated -
                # We crossed into a new day and things changed.
                # Now all times have shifted relative to the new day, so we need to look at it differently
                # If both times are now in the future, we now actually want to set start time back a day and keep end_time as today
                start_time = (
                    self._parse_time(start_time_str, name, today=True, days_offset=-1)
                )["datetime"]
                end_time = (
                    self._parse_time(end_time_str, name, today=True, days_offset=0)
                )["datetime"]

        # self.diag.info(f"\nstart = {start_time}\nnow   = {now}\nend   = {end_time}")
        return start_time <= now <= end_time

    def _parse_time(self, time_str, name=None, today=False, days_offset=0):
        parsed_time = None
        sun = None
        offset = 0
        parts = re.search(
            r"^(\d+)-(\d+)-(\d+)\s+(\d+):(\d+):(\d+)(?:\.(\d+))?$", time_str
        )
        if parts:
            if parts.group(7) is None:
                us = 0
            else:
                us = int(float("0." + parts.group(7)) * 1000000)

            this_time = datetime.datetime(
                int(parts.group(1)),
                int(parts.group(2)),
                int(parts.group(3)),
                int(parts.group(4)),
                int(parts.group(5)),
                int(parts.group(6)),
                us,
            )
            parsed_time = self.ADtz.localize(
                this_time + datetime.timedelta(days=days_offset)
            )
        else:
            parts = re.search(r"^(\d+):(\d+):(\d+)(?:\.(\d+))?$", time_str)
            if parts:
                if parts.group(4) is None:
                    us = 0
                else:
                    us = int(float("0." + parts.group(4)) * 1000000)

                today = (self.get_now()).astimezone(self.ADtz)
                time = datetime.time(
                    int(parts.group(1)), int(parts.group(2)), int(parts.group(3)), us
                )
                parsed_time = today.replace(
                    hour=time.hour,
                    minute=time.minute,
                    second=time.second,
                    microsecond=us,
                ) + datetime.timedelta(days=days_offset)
            else:
                if time_str == "sunrise":
                    parsed_time = self.sunrise(
                        aware=True, today=today, days_offset=days_offset
                    )
                    sun = "sunrise"
                    offset = 0
                elif time_str == "sunset":
                    parsed_time = self.sunset(True, today, days_offset)
                    sun = "sunset"
                    offset = 0
                else:
                    parts = re.search(
                        r"^sunrise\s*([+-])\s*(\d+):(\d+):(\d+)(?:\.(\d+))?$", time_str
                    )
                    if parts:
                        if parts.group(5) is None:
                            us = 0
                        else:
                            us = int(float("0." + parts.group(5)) * 1000000)

                        sun = "sunrise"
                        td = datetime.timedelta(
                            hours=int(parts.group(2)),
                            minutes=int(parts.group(3)),
                            seconds=int(parts.group(4)),
                            microseconds=us,
                        )

                        if parts.group(1) == "+":
                            offset = td.total_seconds()
                            parsed_time = self.sunrise(True, today, days_offset) + td
                        else:
                            offset = td.total_seconds() * -1
                            parsed_time = self.sunrise(True, today, days_offset) - td
                    else:
                        parts = re.search(
                            r"^sunset\s*([+-])\s*(\d+):(\d+):(\d+)(?:\.(\d+))?$",
                            time_str,
                        )
                        if parts:
                            if parts.group(5) is None:
                                us = 0
                            else:
                                us = int(float("0." + parts.group(5)) * 1000000)

                            sun = "sunset"
                            td = datetime.timedelta(
                                hours=int(parts.group(2)),
                                minutes=int(parts.group(3)),
                                seconds=int(parts.group(4)),
                                microseconds=us,
                            )
                            if parts.group(1) == "+":
                                offset = td.total_seconds()
                                parsed_time = self.sunset(True, today, days_offset) + td
                            else:
                                offset = td.total_seconds() * -1
                                parsed_time = self.sunset(True, today, days_offset) - td

        if parsed_time is None:
            if name is not None:
                raise ValueError("%s: invalid time string: %s", name, time_str)
            else:
                raise ValueError("invalid time string: %s", time_str)
        return {"datetime": parsed_time, "sun": sun, "offset": offset}

    def make_naive(self, dt):
        local = dt.astimezone(self.ADtz)
        return datetime.datetime(
            local.year,
            local.month,
            local.day,
            local.hour,
            local.minute,
            local.second,
            local.microsecond,
        )

    def read(self):
        se: SchedulerEntity
        try:
            for se in self.queue.values():
                if not se.in_time():
                    se.finish()
        except:
            pass

    def get_interval_loop(self) -> int:
        return 5

    def put_se(self, se: SchedulerElement):
        self.queue[se.handler] = se
        return se.handler

    def put_entity(
        self, entity_id, delay, sensor_entity_id: str = "", ha_instance=None
    ) -> SchedulerEntity:
        se: Union[SchedulerEntity, None] = self.queue.get(entity_id)
        if se is None:
            se = SchedulerEntity(
                entity_id=entity_id,
                delay=delay,
                sensor_entity_id=sensor_entity_id,
                ha_instance=ha_instance,
            )
        se.ended = False
        return self.put_se(se)

    def put_entity_delay(
        self,
        entity_id,
        delay_entity_id,
        sensor_entity_id: str = "",
        multiply: int = 60,
        ha_instance=None,
    ) -> SchedulerEntity:
        # Zhasne po urcite dobe
        se: Union[SchedulerEntity, None] = self.queue.get(entity_id)
        if se is None:
            se = SchedulerEntityDelay(
                entity_id=entity_id,
                multiply=multiply,
                delay_entity_id=delay_entity_id,
                sensor_entity_id=sensor_entity_id,
                ha_instance=ha_instance,
            )
        se.ended = False
        return self.put_se(se)

    def run_in(self, callback, delay):
        se: RunDelay = RunDelay(parent=self, delay=delay, callback=callback)
        self.put_se(se)


sch: Scheduler = Scheduler()
sch.start()
