# -*- coding: utf-8 -*-
import md5
import smtplib
import logging
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


logging.basicConfig()
logger = logging.getLogger('NudgeBotLogger')
logger.setLevel(logging.INFO)


class NudgeBot(object):

    __metaclass__ = Singleton

    def __init__(self):
        self._email_addr = config().credentials.email.address

    def send_email(self, receivers, subject, body, attachments=None, text_format='plain'):
        logger.info('Sending Email to {}; subject="{}"'.format(receivers, subject))
        """Sending the message <body> to the <recievers>"""
        if isinstance(receivers, basestring):
            receivers = [receivers]
        msg = MIMEMultipart()
        msg['From'] = self._email_addr
        msg['To'] = COMMASPACE.join(receivers)
        msg['Date'] = formatdate(localtime=True)
        msg['Subject'] = subject

        msg.attach(MIMEText(body, text_format))
        if attachments:
            for attachment in attachments:
                with open(attachment, "rb") as attachment_file:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment_file.read())
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', "attachment; filename= {}"
                                    .format(attachment))
                    msg.attach(part)

        smtp_server = smtplib.SMTP('localhost')
        smtp_server.sendmail(self._email_addr, receivers, msg.as_string())

    def _process_flow(self, pr_stats, tree, cases_properties=None, cases_checksum=None):
        if not cases_checksum:
            cases_checksum = md5.new()
        if cases_properties is None:
            cases_properties = []
        if isinstance(tree, dict):
            for case, node in tree.items():
                case.load_pr_statistics(pr_stats)
                if case.state:
                    cases_checksum.update(case.hash)
                    cases_properties.append(case.properties)
                    self._process_flow(pr_stats, node, cases_properties, cases_checksum)
        elif isinstance(tree, (list, tuple)):
            for action in tree:
                self._process_flow(pr_stats, action, cases_properties, cases_checksum)
        elif isinstance(tree, Action):
            action = tree
            action.load_pr_statistics(pr_stats)
            is_done = ([record for record in db().records.find({
                           'cases_checksum': cases_checksum.hexdigest(),
                           'action.checksum': action.hash})
                        ])
            if not is_done or action.run_type == RUN_TYPES.ALWAYS:
                action.run()
                db().add_record(cases_properties, cases_checksum.hexdigest(), action)

    def process(self,  pull_request_stats):
        logger.info('Processing pull request statistics: {}'.format(pull_request_stats.number))
        return self._process_flow(pull_request_stats, FLOW)

    def initialize(self):
        # TODO: deal with socket.timeout
        db().set_initialization_time()
        logger.info('Initializing NudgeBot...')
        for repo in GithubEnv().repos:
            repo.reviewers_pool.initialize()
            for pr in repo.get_pull_requests():
                pr_stat = PullRequestStatistics(pr)
                self.process(pr_stat)
                db().update_pr_stats(pr_stat.get_json())

    def _fetch_pr_number(self, json_data):
        pull_request_number = json_data.get('pull_request', {}).get('number')
        issue = json_data.get('issue', {})
        if not pull_request_number and issue.get('pull_request'):
            pull_request_number = issue.get('number')
        return pull_request_number

    def process_github_event(self, json_data):
        sender = json_data['sender']['login']
        logger.info('Processing Github event: sender="{}"'.format(sender))
        if sender == config().credentials.github.username:
            logging.info('Event detected as Bot event (sender="{}")'.format(sender))
            return  # In order the prevent recursion when the bot perform action and invoke webhook
        repository = [repo for repo in GithubEnv().repos
                      if repo.name == json_data.get('repository', {}).get('name')].pop()
        pull_request_number = self._fetch_pr_number(json_data)
        if pull_request_number:
            logging.info('event data: pr#{}; sender="{}"'.format(
                pull_request_number, sender))
            pr = repository.get_pull_request(pull_request_number)
            pr_stat = PullRequestStatistics(pr)
            repository.reviewers_pool.update_from_pr_stats(pr_stat)
            if pr.state != 'open':
                logger.info('Pull request state is "{}": removing statistics...'.format(pr.state))
                db().remove_pr_stats(pull_request_number)
                return
            self.process(pr_stat)
            # TODO: Find away to 'un-cache' the object so we will not have to re-instantiate
            db().update_pr_stats(pr_stat.get_json())
        else:
            logger.info('Event detected as non pull request event...')
