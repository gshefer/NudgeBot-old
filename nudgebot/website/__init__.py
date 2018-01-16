import os

from jinja2 import Template

from common import Singleton
from nudgebot.db import db


class WebSite(object):
    __metaclass__ = Singleton
    STATISTICS_TEMPLATE_PATH = '{}/statistics.j2'.format(os.path.dirname(__file__))

    @property
    def statistics_html(self):
        with open(self.STATISTICS_TEMPLATE_PATH, 'r') as f:
            template = Template(f.read().encode('UTF-8'))
        html = template.render(stats=[stat for stat in db().pr_stats.find()])
        return html
