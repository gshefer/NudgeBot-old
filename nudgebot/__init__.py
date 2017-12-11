# -*- coding: utf-8 -*-
import md5
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import COMMASPACE, formatdate

from config import config
from common import Singleton
from nudgebot.lib.github.pull_request import PullRequest
from nudgebot.lib.github.actions import Action, RUN_TYPES
from nudgebot.db import db
from nudgebot.lib.github.pull_request_stat_collection import PullRequestStatCollection
from nudgebot.flow import FLOW


class NudgeBot(object):

    __metaclass__ = Singleton

    def __init__(self):
        self._email_addr = config().credentials.email.address

    def send_email(self, receivers, subject, body):
        """Sending the message <body> to the <recievers>"""
        if isinstance(receivers, basestring):
            receivers = [receivers]
        msg = MIMEMultipart()
        msg['From'] = self._email_addr
        msg['To'] = COMMASPACE.join(receivers)
        msg['Date'] = formatdate(localtime=True)
        msg['Subject'] = subject

        msg.attach(MIMEText(body))

        smtpObj = smtplib.SMTP('localhost')
        smtpObj.sendmail(self._email_addr, receivers, msg.as_string())

    def add_record(self, cases_checksum, action, action_properties):
        db().records.insert_one({
            'case_checksum': cases_checksum,
            'action': {
                'checksum': action.hash,
                'name': action.name,
                'properties': action_properties
            }
        })

    def _process_flow(self, stat_collection, tree, cases_checksum=None):
        if not cases_checksum:
            cases_checksum = md5.new()
        if isinstance(tree, dict):
            for case, node in tree.items():
                case.define_stat_collection(stat_collection)
                if case.state:
                    cases_checksum.update(case.hash)
                    return self._process_flow(stat_collection, node, cases_checksum)
        elif isinstance(tree, (list, tuple)):
            for action in tree:
                self._process_flow(stat_collection, action, cases_checksum)
        elif isinstance(tree, Action):
            action = tree
            action.define_stat_collection(stat_collection)
            is_done = (action.run_type != RUN_TYPES.ALWAYS or
                       [record for record in db().records.find({
                           'case_checksum': cases_checksum.hexdigest(),
                           'action': {'checksum': action.hash}})
                        ]
                       )
            if not is_done:
                action_properties = action.run()
                self.add_record(cases_checksum.hexdigest(), action, action_properties)

    def process(self, pull_request_stat_collection):
        return self._process_flow(pull_request_stat_collection, FLOW)

    def work(self):
        for pr_status in PullRequest.get_all():
            pr_stat = PullRequestStatCollection(pr_status)
            self.process(pr_stat)

    def run(self):
        while True:
            try:
                self.work()
            except KeyboardInterrupt:
                break


if __name__ == '__main__':

    nudge_bot = NudgeBot()
    nudge_bot.run()
