from celery import Celery

from nudgebot.reports import Report, periodic_reports
from celery.schedules import crontab


celery_app = Celery()


@celery_app.on_after_configure.connect
def setup_periodic_reports(sender, **kwargs):
    for report_class in Report.get_reports():
        print report_class
        assert isinstance(report_class.CRONTAB, crontab), \
            ('CRONTAB static attribute should be deifned in periodic '
             'report and must be an instance of {}'.format(crontab))
        sender.add_periodic_task(
            report_class.CRONTAB,
            send_report.s(report_class.get_name()),
        )


@celery_app.task
def send_report(report_class_name):
    report = getattr(periodic_reports, report_class_name)
    report().send()


if __name__ == '__main__':
    celery_app.worker_main(['--loglevel=info', '--beat'])
