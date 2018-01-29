import os

from celery.schedules import crontab

from config import config
from nudgebot.reports import Report
from nudgebot.db import db
from nudgebot.globals import PUBLIC_IP, SERVER_PORT


TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), 'templates')
DAILY_REPORT_TIME = [int(t) for t in config().config.reports.daily.split(':')]


class DailyStatusReport(Report):
    CRONTAB = crontab(hour=DAILY_REPORT_TIME[0], minute=DAILY_REPORT_TIME[1])
    SUBJECT = '{{ data["stats"][0]["repository"] }} daily report'
    TEMPLATE = os.path.join(TEMPLATES_DIR, 'daily_status_report.j2')
    TEXT_FORMAT = 'html'
    RECEIVERS = config().config.reports.receivers

    @property
    def data(self):
        return {
            'stat_url': 'http://{}:{}/statistics'.format(PUBLIC_IP, SERVER_PORT),
            'stats': db().pull_request_statistics,
            'reviewers_pool_items': sorted(db().get_reviewers_pool().items(),
                                           key=lambda d: len(d[1]['pull_requests']))
        }
