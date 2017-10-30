import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import COMMASPACE, formatdate

from config import conf
from nudgebot.utils.github.pull_request import PullRequest


class NudgeBot(object):

    def __init__(self):
        self._email_addr = conf().email_addr

    def _send_email(self, receivers, body):
        """Sending the message <body> to the <recievers>"""
        msg = MIMEMultipart()
        msg['From'] = self._email_addr
        msg['To'] = COMMASPACE.join(receivers)
        msg['Date'] = formatdate(localtime=True)
        msg['Subject'] = 'Pull Requests that requires your attention'

        msg.attach(MIMEText(body))

        smtpObj = smtplib.SMTP('localhost')
        smtpObj.sendmail(self._email_addr, receivers, msg.as_string())

    def check_nudge(self, pr_status):
        judgement = pr_status.judge()
        if judgement:
            self._send_email(self._email_addr, judgement)

    def work(self):
        for pr_status in PullRequest.get_all():
            self.check_nudge(pr_status)

    def run(self):
        while True:
            try:
                self.work()
            except KeyboardInterrupt:
                break


if __name__ == '__main__':

    nudge_bot = NudgeBot()
    nudge_bot.run()
