import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import COMMASPACE, formatdate

from config import config
from nudgebot.lib.github.pull_request import PullRequest, PullRequestTag,\
    PRstate
from nudgebot.lib.github.cases import NoPullRequestStateSet
from nudgebot.lib.github.actions import PullRequestTagSet, CreateIssueComment
from nudgebot.lib.github.users import BotUser


class NudgeBot(object):

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

    def process(self, pull_request):
        actions_to_perfoem = []
        if NoPullRequestStateSet(pull_request).state:
            actions_to_perfoem.extend([
                PullRequestTagSet(pull_request, BotUser(), PullRequestTag(PRstate.WIP)),
                CreateIssueComment(pull_request, BotUser(),
                    'Please add a state to the PR title - setting state as [WIP]')
            ])
        for act in actions_to_perfoem:
            act.run()
            

    def work(self):
        for pr_status in PullRequest.get_all():
            self.process(pr_status)

    def run(self):
        while True:
            try:
                self.work()
            except KeyboardInterrupt:
                break


if __name__ == '__main__':

    nudge_bot = NudgeBot()
    nudge_bot.run()
