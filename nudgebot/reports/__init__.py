import os
import inspect

from jinja2 import Template

from nudgebot import NudgeBot


class Report(object):
    """A Base report object
    static attributes:
        * CRONTAB: The crontab schedule of the report. Must be defined if the report is periodic.
        * SUBJECT: The subject of the report, could be also formatted in jinja2 format and will
                   be rendered with the data.
        * TEMPLATE: The template of the report body, could be either a path to a template
                    file or the template content itself.
        * TEXT_FORMAT: the text format of the report body. could be either `html` or `plain`"""
    CRONTAB = None
    SUBJECT = None
    TEMPLATE = None
    TEXT_FORMAT = 'plain'
    RECEIVERS = []

    def __init__(self):
        assert self.SUBJECT, 'SUBJECT should be defined in the report class'
        assert self.TEMPLATE, 'TEMPLATE should be defined in the report class'
        assert self.RECEIVERS, 'No receivers for the report, please define RECEIVERS'

    @classmethod
    def get_reports(cls):
        """Collect and return all the subclasses under the report.py file."""
        from nudgebot.reports import periodic_reports
        collected_reports = []
        for v in dir(periodic_reports):
            attr = getattr(periodic_reports, v)
            if inspect.isclass(attr) and issubclass(attr, cls) and attr is not cls:
                collected_reports.append(attr)
        return collected_reports

    @classmethod
    def get_name(cls):
        return cls.__name__

    @property
    def data(self):
        """In this function we should implement the data calculation for the report.
        This data will be used for the template. The property should return the data dictionary
        used for the report rendering
        """
        return NotImplementedError()

    @property
    def subject(self):
        return Template(self.SUBJECT).render(data=self.data)

    @property
    def body(self):
        """Rendering the body of the report with the data"""
        if os.path.exists(self.TEMPLATE):
            with open(self.TEMPLATE, 'r') as f:
                template_raw = f.read().encode('UTF-8')
        else:
            template_raw = self.TEMPLATE
        return Template(template_raw).render(data=self.data)

    def send(self):
        """Sending the report"""
        NudgeBot().send_email(self.RECEIVERS, self.subject, self.body, text_format=self.TEXT_FORMAT)

    @property
    def json(self):
        """Json representation of the report info"""
        return {
            'name': self.name,
            'invocation_period': self.INVOCATION_PERIOD,
            'subject': self.SUBJECT,
            'receivers': self.RECEIVERS,
            'sending_time': self._sending_time
        }
