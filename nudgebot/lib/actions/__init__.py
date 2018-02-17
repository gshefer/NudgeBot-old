import md5
import logging

from common import Age, skip_if_testing_mode
from nudgebot.lib.github.users import BotUser
from nudgebot.lib.github.pull_request import PullRequestTitleTag
from nudgebot.lib import FlowObject


logging.basicConfig()
logger = logging.getLogger('ActionsLogger')
logger.setLevel(logging.INFO)


class RUN_TYPES:
    ONCE = 'Once'
    ALWAYS = 'Always'


class Action(FlowObject):
    """A base class for an action"""
    _github_obj = BotUser()

    def __init__(self, *args, **kwargs):
        self.run_type = kwargs.get('run_type', RUN_TYPES.ONCE)

    @skip_if_testing_mode
    def run(self):
        logger.info('Running action: {}'.format(self))
        self.action()
        self._pr_statistics.uncache_all()

    def action(self):
        raise NotImplementedError()

    def _md5(self, *strings):
        checksum = md5.new()
        checksum.update(str(self._pr_statistics.number()))
        for str_ in strings:
            checksum.update(str(str_))
        return checksum.hexdigest()


class PullRequestTitleTagSet(Action):
    def __init__(self, title_tags, override=False, **kwargs):
        self.title_tags = title_tags
        self.override = override
        Action.__init__(self, **kwargs)

    def action(self):
        if isinstance(self.title_tags, basestring):
            self.title_tags = [self.title_tags]
        current_tags = self._pr_statistics.pull_request.title_tags
        new_tags = (self.title_tags if self.override
                    else list(set(self.title_tags + current_tags)))
        self._pr_statistics.pull_request.title_tags = new_tags

    @property
    def hash(self):
        return self._md5('+', *[PullRequestTitleTag(tag).raw for tag in self.title_tags])


class PullRequestTitleTagRemove(Action):
    def __init__(self, title_tags, **kwargs):
        self.title_tags = title_tags
        Action.__init__(self, **kwargs)

    def action(self):
        self._pr_statistics.pull_request.remove_title_tags(*self.title_tags)

    @property
    def hash(self):
        return self._md5('-', *[PullRequestTitleTag(tag).raw for tag in self.title_tags])


class AddReviewer(Action):
    def __init__(self, reviewer=None, level=1, **kwargs):
        self.reviewer = reviewer
        self.level = level
        Action.__init__(self, **kwargs)

    def action(self):
        if not self.reviewer:
            self.reviewer = self._pr_statistics.repo().reviewers_pool.pull_reviewer(
                self.level, self._pr_statistics.pull_request)
        self._pr_statistics.pull_request.add_reviewers([self.reviewer])

    @property
    def hash(self):
        return self._md5('+', self.reviewer)


class RemoveReviewer(Action):
    def __init__(self, reviewer, **kwargs):
        self.reviewer = reviewer
        Action.__init__(self, **kwargs)

    def action(self):
        self._pr_statistics.pull_request.remove_reviewers([self.reviewer])

    @property
    def hash(self):
        return self._md5('-', self.reviewer)


class CreateIssueComment(Action):
    def __init__(self, body, **kwargs):
        self.body = body
        Action.__init__(self, **kwargs)

    def action(self):
        self._pr_statistics.pull_request.create_issue_comment(self.body)

    @property
    def hash(self):
        return self._md5(self.body)


class _ReviewStateActionBase(Action):
    STATE = 'PENDING'

    def __init__(self, body, **kwargs):
        self.body = body
        Action.__init__(self, **kwargs)

    @property
    def event(self):
        return getattr(self, 'EVENT', self.STATE)

    def action(self):
        self._pr_statistics.pull_request.add_reviewers([self._github_obj])
        self._pr_statistics.pull_request.create_review(
            list(self._pr_statistics.commits())[-1], self.body or self.STATE, self.event)

    @property
    def hash(self):
        return self._md5('+', self.event, self.body)


class RequestChanges(_ReviewStateActionBase):
    EVENT = 'REQUEST_CHANGES'
    STATE = 'CHANGES_REQUESTED'


class Approve(_ReviewStateActionBase):
    EVENT = 'APPROVE'
    STATE = 'APPROVED'


class CreateReviewComment(Action):
    def __init__(self, body, path=None, position=None, **kwargs):
        self.body = body
        self.path = path
        self.position = position
        Action.__init__(self, **kwargs)

    def action(self):
        commit = list(self._pr_statistics.commits())[-1]
        self._pr_statistics.pull_request.create_review_comment(
            self.body, commit, self.path, self.position)

    @property
    def hash(self):
        return self._md5('+', self.body, self.path, self.position)


class EditDescription(Action):
    def __init__(self, body, **kwargs):
        self.body = body
        Action.__init__(self, **kwargs)

    def action(self):
        self._pr_statistics.pull_request.edit(body=self._description)

    @property
    def hash(self):
        return self._md5(self.description)


class SendEmailToUsers(Action):
    def __init__(self, receivers, subject, body, **kwargs):
        self.receivers = receivers
        self.subject = subject
        self.body = body
        Action.__init__(self, **kwargs)

    def action(self):
        from nudgebot import NudgeBot
        # TODO: Check if the user has email - if not ask for it
        receivers = [user.email for user in self._receivers]
        NudgeBot().send_email(receivers, self._subject, self._body)

    @property
    def hash(self):
        return self._md5(
            ''.join([receiver.login for receiver in self._receivers]) +
            self._subject + self._body
        )


class ReportForInactivity(Action):

    def action(self):
        last_update = Age(self._pr_statistics.last_update())
        self._pr_statistics.pull_request.create_issue_comment(
            ('Pull request is inactive for {}- please do'
             ' some action, update it or close it').format(last_update.pretty)
        )

    @property
    def hash(self):
        return self._md5(self._pr_statistics.last_update())


class AskForReviewCommentReactions(Action):
    def __init__(self, days, hours, prompt_missing_emails=False, **kwargs):
        self.days = days
        self.hours = hours
        self.prompt_missing_emails = prompt_missing_emails
        Action.__init__(self, **kwargs)

    def action(self):
        # TODO: convert to age
        emails_content, receviers = 'The following action required for this PR:\n', set()
        for status in self._pr_statistics.review_comment_reaction_statuses():
            if status['age_seconds'] > (self.days * 86400 + self.hours * 3600):
                days = int(status['age_seconds']) / 86400
                hours = (int(status['age_seconds']) - days * 86400) / 3600
                emails_content += ('{} is waiting for response for {} '
                                   'days and {} hours - comment: {}\n').format(
                    status['last_comment'].user.login, days, hours,
                    status['last_comment'].url)
                missing_email_users = set()
                for part in ('last_comment', 'contributor', 'reviewer'):
                    user = status[part].user
                    if user.email:
                        receviers.add(user.email)
                    else:
                        missing_email_users.add(user.login)
        if missing_email_users:
            if self._prompt_missing_emails:
                login_marks = ' '.join(['@{}'.format(login) for login in missing_email_users])
                self._pr_statistics.pull_request.create_issue_comment(
                    '{} your email addresses are missing, please set it up ({})'
                    .format(login_marks,
                            'https://help.github.com/articles/verifying-your-email-address/')
                )
            else:
                raise Exception('Cannot send email, email addresses are missing for: {}'
                                .format(missing_email_users))
                # TODO: define appropriate exception
        if not receviers:
            return
        receviers = list(receviers)
        subject = 'PR#{} is waiting for response'.format(self._pr_statistics.number())
        from nudgebot import NudgeBot
        NudgeBot().send_email(receviers, subject, emails_content)

    @property
    def hash(self):
        return self._md5()  # TODO: find better hash and a way to get receivers
