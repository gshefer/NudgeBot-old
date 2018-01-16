# -*- coding: utf-8 -*-
import md5
import smtplib
from email import encoders
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.utils import COMMASPACE, formatdate

from config import config
from common import Singleton
from nudgebot.lib.actions import Action, RUN_TYPES
from nudgebot.db import db
from nudgebot.lib.github.pull_request_statistics import PullRequestStatistics
from nudgebot.flow import FLOW
from nudgebot.lib.github import GithubEnv


class NudgeBot(object):

    __metaclass__ = Singleton

    def __init__(self):
        self._email_addr = config().credentials.email.address

    def send_email(self, receivers, subject, body, attachments=None):
        """Sending the message <body> to the <recievers>"""
        if isinstance(receivers, basestring):
            receivers = [receivers]
        msg = MIMEMultipart()
        msg['From'] = self._email_addr
        msg['To'] = COMMASPACE.join(receivers)
        msg['Date'] = formatdate(localtime=True)
        msg['Subject'] = subject

        msg.attach(MIMEText(body))
        if attachments:
            for attachment in attachments:
                with open(attachment, "rb") as attachment_file:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment_file.read())
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', "attachment; filename= {}"
                                    .format(attachment))
                    msg.attach(part)

        smtpObj = smtplib.SMTP('localhost')
        smtpObj.sendmail(self._email_addr, receivers, msg.as_string())

    def _process_flow(self, stat_collection, tree, cases_properties=None, cases_checksum=None):
        if not cases_checksum:
            cases_checksum = md5.new()
        if cases_properties is None:
            cases_properties = []
        if isinstance(tree, dict):
            for case, node in tree.items():
                case.load_pr_statistics(stat_collection)
                if case.state:
                    cases_checksum.update(case.hash)
                    cases_properties.append(case.properties)
                    self._process_flow(stat_collection, node, cases_properties, cases_checksum)
        elif isinstance(tree, (list, tuple)):
            for action in tree:
                self._process_flow(stat_collection, action, cases_properties, cases_checksum)
        elif isinstance(tree, Action):
            action = tree
            action.load_pr_statistics(stat_collection)
            is_done = ([record for record in db().records.find({
                           'cases_checksum': cases_checksum.hexdigest(),
                           'action.checksum': action.hash})
                        ])
            if not is_done or action.run_type == RUN_TYPES.ALWAYS:
                action.run()
                db().add_record(cases_properties, cases_checksum.hexdigest(), action)

    def process(self,  pull_request_stats):
        return self._process_flow(pull_request_stats, FLOW)

    def initialize(self):
        for repo in GithubEnv().repos:
            repo.reviewers_pool.initialize()
            for pr in repo.get_pull_requests():
                pr_stat = PullRequestStatistics(pr)
                self.process(pr_stat)
                db().update_pr_stats(pr_stat.json)

    def process_github_event(self, json_data):
        if json_data['sender']['login'] == config().credentials.github.username:
            return  # In order the prevent recursion when the bot perform action and invoke webhook
        repository = [repo for repo in GithubEnv().repos
                      if repo.name == json_data.get('repository', {}).get('name')].pop()
        pull_request_number = json_data.get('pull_request', {}).get('number')
        if pull_request_number:
            pr_stat = PullRequestStatistics(repository.get_pull_request(pull_request_number))
            repository.reviewers_pool.update_from_pr_stats(pr_stat)
            self.process(pr_stat)
            db().update_pr_stats(pr_stat.json)
