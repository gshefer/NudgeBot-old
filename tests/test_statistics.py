from datetime import datetime
import time

from nudgebot.lib.statistics import Statistics, stat_property


def test_statistics():

    class Times(Statistics):
        @property
        def local_time(self):
            return datetime.now()

        @stat_property
        def first_call(self):
            return self.local_time

    T = Times()
    for _ in range(3):
        print(T.first_call())
        time.sleep(1)
    T.first_call.uncache()
    for _ in range(3):
        print(T.first_call())
        time.sleep(1)
    T.uncache_all()
    for _ in range(3):
        print(T.first_call())
        time.sleep(1)
