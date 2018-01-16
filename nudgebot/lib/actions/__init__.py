import md5
import attr

from config import config
from common import Age
from nudgebot.lib.github.users import BotUser
from nudgebot.lib.github.pull_request import PullRequestTitleTag


class RUN_TYPES:
    ONCE = 'Once'
    ALWAYS = 'Always'


class Action(object):
    """A base class for an action"""
    run_type = RUN_TYPES.ONCE
    _github_obj = BotUser()

    def load_pr_statistics(self, pr_statistics):
        self._pr_statistics = pr_statistics

    @property
    def class_name(self):
        return self.__class__.__name__

    @property
    def properties(self):
        return attr.asdict(self)

    def run(self):
        if config().config.testing_mode:
            return
        return self.action()

    def action(self):
        raise NotImplementedError()

    def _md5(self, *strings):
        checksum = md5.new()
        checksum.update(str(self._pr_statistics.number))
        for str_ in strings:
            checksum.update(str(str_))
        return checksum.hexdigest()

    @property
    def hash(self):
        raise NotImplementedError()


@attr.s
class PullRequestTitleTagSet(Action):
    title_tags = attr.ib(default=attr.Factory(list))
    override = attr.ib(default=False)
    run_type = attr.ib(default=Action.run_type)

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


@attr.s
class PullRequestTitleTagRemove(Action):
    title_tags = attr.ib(default=attr.Factory(list))
    run_type = attr.ib(default=Action.run_type)

    def action(self):
        self._pr_statistics.pull_request.remove_title_tags(*self.title_tags)

    @property
    def hash(self):
        return self._md5('-', *[PullRequestTitleTag(tag).raw for tag in self.title_tags])


@attr.s
class AddReviewer(Action):
    reviewer = attr.ib(default=None)
    level = attr.ib(default=1)
    run_type = attr.ib(default=Action.run_type)

    def action(self):
        if not self.reviewer:
            self.reviewer = self._pr_statistics.repo.reviewers_pool.pull_reviewer(
                self.level, self._pr_statistics.pull_request)
        self._pr_statistics.pull_request.add_reviewers([self.reviewer])

    @property
    def hash(self):
        return self._md5('+', self.reviewer)


@attr.s
class RemoveReviewer(Action):
    reviewer = attr.ib()
    run_type = attr.ib(default=Action.run_type)

    def action(self):
        self._pr_statistics.pull_request.remove_reviewers([self.reviewer])

    @property
    def hash(self):
        return self._md5('-', self.reviewer)


@attr.s
class CreateIssueComment(Action):
    body = attr.ib()
    run_type = attr.ib(default=Action.run_type)

    def action(self):
        self._pr_statistics.pull_request.create_issue_comment(self.body)

    @property
    def hash(self):
        return self._md5(self.body)


@attr.s
class _ReviewStateActionBase(Action):
    STATE = 'PENDING'
    run_type = attr.ib(default=Action.run_type)

    @property
    def event(self):
        return getattr(self, 'EVENT', self.STATE)

    def action(self):
        self._pr_statistics.pull_request.add_reviewers([self._github_obj])
        self._pr_statistics.pull_request.create_review(
            list(self._pr_statistics.commits)[-1], self.body or self.STATE, self.event)

    @property
    def hash(self):
        return self._md5('+', self.event, self.body)


@attr.s
class RequestChanges(_ReviewStateActionBase):
    EVENT = 'REQUEST_CHANGES'
    STATE = 'CHANGES_REQUESTED'
    body = attr.ib(default=None)


@attr.s
class Approve(_ReviewStateActionBase):
    EVENT = 'APPROVE'
    STATE = 'APPROVED'
    body = attr.ib(default=None)


@attr.s
class CreateReviewComment(Action):
    body = attr.ib()
    path = attr.ib(default=None)
    position = attr.ib(default=None)
    run_type = attr.ib(default=Action.run_type)

    def action(self):
        commit = list(self._pr_statistics.commits)[-1]
        self._pr_statistics.pull_request.create_review_comment(
            self.body, commit, self.path, self.position)

    @property
    def hash(self):
        return self._md5('+', self.body, self.path, self.position)


@attr.s
class EditDescription(Action):
    description = attr.ib()
    run_type = attr.ib(default=Action.run_type)

    def action(self):
        self._pr_statistics.pull_request.edit(body=self._description)

    @property
    def hash(self):
        return self._md5(self.description)


@attr.s
class SendEmailToUsers(Action):
    receivers = attr.ib()
    subject = attr.ib()
    body = attr.ib()
    run_type = attr.ib(default=Action.run_type)

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


@attr.s
class ReportForInactivity(Action):
    run_type = attr.ib(default=Action.run_type)

    def action(self):
        last_update = Age(self._pr_statistics.last_update)
        self._pr_statistics.pull_request.create_issue_comment(
            ('Pull request is inactive for {}- please do'
             ' some action, update it or close it').format(last_update.pretty)
        )

    @property
    def hash(self):
        return self._md5(self._pr_statistics.last_update)


@attr.s
class AskForReviewCommentReactions(Action):
    days = attr.ib()
    hours = attr.ib()
    prompt_missing_emails = attr.ib(default=False)
    run_type = attr.ib(default=Action.run_type)

    def action(self):
        # TODO: convert to age
        emails_content, receviers = 'The following action required for this PR:\n', set()
        for status in self._pr_statistics.review_comment_reaction_statuses:
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
        subject = 'PR#{} is waiting for response'.format(self._pr_statistics.number)
        from nudgebot import NudgeBot
        NudgeBot().send_email(receviers, subject, emails_content)

    @property
    def hash(self):
        return self._md5()  # TODO: find better hash and a way to get receivers
