from jinja2 import Template

from common import Singleton
from config import config


class Reporter(object):
    __metaclass__ = Singleton
    TEMPLATE_PATH = 'report/report.j2'
    REPORT_PATH = 'report/report.html'

    def send_report(self, pr_stats, **kwargs):
        receivers = kwargs.get('receivers', config().config.report.receivers)
        with open(self.TEMPLATE_PATH, 'r') as f:
            template = Template(f.read().encode('UTF-8'))
        html = template.render(stats=pr_stats)
        with open(self.REPORT_PATH, 'w') as f:
            f.write(html)
        from nudgebot import NudgeBot
        NudgeBot().send_email(receivers, 'Pull request status report', '',
                              attachments=[self.REPORT_PATH])
