# -*- coding: utf-8 -*-
import github
import md5
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import COMMASPACE, formatdate

from config import config
from common import Singleton
from nudgebot.lib.github.actions import Action, RUN_TYPES
from nudgebot.db import db
from nudgebot.lib.github.pull_request_stat_collection import PullRequestStatCollection
from nudgebot.flow import FLOW
from nudgebot.lib.github import GithubEnv


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

    def _process_flow(self, session_id, stat_collection, tree, cases_checksum=None):
        if not cases_checksum:
            cases_checksum = md5.new()
        if isinstance(tree, dict):
            for case, node in tree.items():
                case.define_stat_collection(stat_collection)
                if case.state:
                    cases_checksum.update(case.hash)
                    return self._process_flow(session_id, stat_collection, node, cases_checksum)
        elif isinstance(tree, (list, tuple)):
            for action in tree:
                self._process_flow(session_id, stat_collection, action, cases_checksum)
        elif isinstance(tree, Action):
            action = tree
            action.define_stat_collection(stat_collection)
            is_done = ([record for record in db().records.find({
                           'case_checksum': cases_checksum.hexdigest(),
                           'action.checksum': action.hash})
                        ])
            if not is_done or action.run_type == RUN_TYPES.ALWAYS:
                action_properties = action.run()
                db().add_record(session_id, cases_checksum.hexdigest(), action, action_properties)

    def process(self, session_id,  pull_request_stat_collection):
        return self._process_flow(session_id, pull_request_stat_collection, FLOW)

    def work(self):
        session = db().new_session()
        for repo in GithubEnv().repos:
            repo.reviewers_pool.sync()
            for pr in repo.get_pull_requests():
                pr_stat = PullRequestStatCollection(pr)
                self.process(session['id'], pr_stat)
                if config().config.report.send_report:
                    db().add_stat(session['id'], pr_stat.json)
        if config().config.report.send_report:
            pass  # TODO: Create and send report

    def run(self, one_session=True):
        if config().config.debug_mode:
            github.enable_console_debug_logging()
        while True:
            try:
                self.work()
            except KeyboardInterrupt:
                break
            if one_session:
                break


if __name__ == '__main__':

    nudge_bot = NudgeBot()
    nudge_bot.run(one_session=True)
