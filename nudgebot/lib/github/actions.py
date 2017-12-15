import md5
from datetime import datetime

from common import ExtendedEnum
from nudgebot.lib.github.users import BotUser
from config import config
from nudgebot.lib.github.pull_request import PullRequestTitleTag


class RUN_TYPES(ExtendedEnum):
    ONCE = 'Once'
    ALWAYS = 'Always'


class Action(object):
    """A base class for action"""
    DEFAULT_RUNTYPE = RUN_TYPES.ONCE
    _github_obj = BotUser()

    def __init__(self, run_type=DEFAULT_RUNTYPE):
        self.run_type = run_type

    @property
    def name(self):
        return self.__class__.__name__

    def define_stat_collection(self, stat_collection):
        self._stat_collection = stat_collection

    def run(self):
        if config().config.testing_mode:
            return {}
        return self.action()

    def action(self):
        raise NotImplementedError()

    def _md5(self, *strings):
        checksum = md5.new()
        checksum.update(str(self._stat_collection.number))
        for str_ in strings:
            checksum.update(str_)
        return checksum.hexdigest()

    @property
    def hash(self):
        raise NotImplementedError()


class PullRequestTitleTagSet(Action):

    def __init__(self, *tags, **kwargs):
        self._tags = [tag if isinstance(tag, PullRequestTitleTag)
                      else PullRequestTitleTag(tag)
                      for tag in tags]
        super(PullRequestTitleTagSet, self).__init__(
            kwargs.get('run_type', Action.DEFAULT_RUNTYPE))

    def action(self):
        self._stat_collection.pull_request.tags = self._tags
        return {'tags': [tag.raw for tag in self._tags]}

    @property
    def hash(self):
        return self._md5('+', *[tag.raw for tag in self._tags])


class PullRequestTitleTagRemove(Action):

    def __init__(self, *tags, **kwargs):
        self._tags = tags
        super(PullRequestTitleTagRemove, self).__init__(
            kwargs.get('run_type', Action.DEFAULT_RUNTYPE))

    def action(self):
        self._stat_collection.pull_request.remove_tags(*self._tags)
        return {'tags': [tag.raw for tag in self._tags]}

    @property
    def hash(self):
        return self._md5('-', *[tag.raw for tag in self._tags])


class AddReviewer(Action):

    def __init__(self, reviewer, **kwargs):
        self._reviewer = reviewer
        super(AddReviewer, self).__init__(
            kwargs.get('run_type', Action.DEFAULT_RUNTYPE))

    def action(self):
        self._stat_collection.pull_request.add_reviewers([self._reviewer])
        return {'reviewer': reviewer.login for reviewer in self._reviewer}

    @property
    def hash(self):
        return self._md5('+', self._reviewer)


class AddReviewerFromPool(Action):

    def __init__(self, level, **kwargs):
        self._level = level
        self._reviewer = None  # Defined in action
        super(AddReviewerFromPool, self).__init__(
            kwargs.get('run_type', Action.DEFAULT_RUNTYPE))

    def action(self):
        self._reviewer = self._stat_collection.repo.reviewers_pool.pull_reviewer(self._level)
        return AddReviewer(self._reviewer).action()

    @property
    def hash(self):
        return self._md5('+', self._reviewer.login)


class RemoveReviewer(Action):

    def __init__(self, reviewer, **kwargs):
        self._reviewer = reviewer
        super(RemoveReviewer, self).__init__(
            kwargs.get('run_type', Action.DEFAULT_RUNTYPE))

    def action(self):
        self._stat_collection.pull_request.remove_reviewers([self._reviewer])
        return {'reviewer': [reviewer.login for reviewer in self._reviewer]}

    @property
    def hash(self):
        return self._md5('-', self._reviewer)


class CreateIssueComment(Action):

    def __init__(self, body, **kwargs):
        self._body = body
        super(CreateIssueComment, self).__init__(
            kwargs.get('run_type', Action.DEFAULT_RUNTYPE))

    def action(self):
        comment = self._stat_collection.pull_request.create_issue_comment(self._body)
        return {'body': self._body, 'created_at': comment.created_at}

    @property
    def hash(self):
        return self._md5(self._body)


class _ReviewStateActionBase(Action):
    STATE = 'PENDING'

    def __init__(self, body=None, **kwargs):
        self._body = body
        super(_ReviewStateActionBase, self).__init__(
            kwargs.get('run_type', Action.DEFAULT_RUNTYPE))

    @property
    def event(self):
        return getattr(self, 'EVENT', self.STATE)

    def action(self):
        self._stat_collection.pull_request.add_reviewers([self._github_obj])
        review = self._stat_collection.pull_request.create_review(
            list(self._stat_collection.commits)[-1], self._body or self.STATE, self.event)
        return {'review_id': review.id}

    @property
    def hash(self):
        return self._md5('+', self.event, self._body)


class RequestChanges(_ReviewStateActionBase):
    EVENT = 'REQUEST_CHANGES'
    STATE = 'CHANGES_REQUESTED'


class Approve(_ReviewStateActionBase):
    EVENT = 'APPROVE'
    STATE = 'APPROVED'


class CreateReviewComment(Action):

    def __init__(self, body, path=None, position=None, **kwargs):
        self._body = body
        self._path = path
        self._position = position
        super(CreateReviewComment, self).__init__(
            kwargs.get('run_type', Action.DEFAULT_RUNTYPE))

    def action(self):
        commit = list(self._stat_collection.commits)[-1]
        review_comment = self._stat_collection.pull_request.create_review_comment(
            self._body, commit, self._path, self._position)
        return {
            'review_comment': {
                'body': review_comment.body,
                'path': review_comment.path,
                'line': review_comment.original_position
            }
        }

    @property
    def hash(self):
        return self._md5('+', self._body, self._path, self._position)


class EditDescription(Action):

    def __init__(self, description, **kwargs):
        self._description = description
        super(EditDescription, self).__init__(
            kwargs.get('run_type', Action.DEFAULT_RUNTYPE))

    def action(self):
        self._stat_collection.pull_request.edit(body=self._description)
        return {'description': self._description}

    @property
    def hash(self):
        return self._md5(self._description)


class SendEmailToUsers(Action):

    def __init__(self, receivers, subject, body, **kwargs):
        self._receivers = receivers
        self._subject = subject
        self._body = body
        super(SendEmailToUsers, self).__init__(
            kwargs.get('run_type', Action.DEFAULT_RUNTYPE))

    def action(self):
        from nudgebot import NudgeBot
        # TODO: Check if the user has email - if not ask for it
        receivers = [user.email for user in self._receivers]
        NudgeBot().send_email(receivers, self._subject, self._body)
        return {
            'receivers': receivers,
            'subject': self._subject,
            'body': self._body
        }

    @property
    def hash(self):
        return self._md5(
            ''.join([receiver.login for receiver in self._receivers]) +
            self._subject + self._body
        )


class ReportForInactivity(Action):

    def __init__(self, **kwargs):
        super(ReportForInactivity, self).__init__(
            kwargs.get('run_type', Action.DEFAULT_RUNTYPE))

    def action(self):
        last_update = self._stat_collection.last_update
        seconds_ago = int((datetime.now() - last_update).total_seconds())
        days = seconds_ago / 86400
        hours = (seconds_ago - days * 86400) / 3600
        comment = self._stat_collection.pull_request.create_issue_comment(
            ('Pull request is inactive for {} days and {} hours- please do'
             ' some action - update it or close it').format(days, hours)
        )
        return {
            'inactivity': {'days': days, 'hours': hours},
            'comment': {'body': comment.body, 'created_at': comment.created_at}
        }

    @property
    def hash(self):
        return self._md5(self._stat_collection.last_update)


class AskForReviewCommentReactions(Action):

    def __init__(self, days, hours, **kwargs):
        self._days = days
        self._hours = hours
        super(AskForReviewCommentReactions, self).__init__(
            kwargs.get('run_type', Action.DEFAULT_RUNTYPE))

    def action(self):
        emails_content, receviers = 'The following action required for this PR:\n', []
        for status in self._stat_collection.review_comment_reaction_statuses:
            if status['age_seconds'] > (self._days * 86400 + self._hours * 3600):
                days = int(status['age_seconds']) / 86400
                hours = (int(status['age_seconds']) - days * 86400) / 3600
                emails_content += ('{} is waiting for response for {} '
                                   'days and {} hours - comment: {}\n').format(
                    status['last_comment'].user.login, days, hours,
                    status['last_comment'].comment_url)
                receviers.extend([
                    status['last_comment'].user.email,
                    status['contributor'].user.email,
                    status['reviewer'].user.email
                ])
        if not receviers:
            return
        receviers = list(set(receviers))
        subject = 'PR#{} is waiting for response'.format(self._stat_collection.number)
        from nudgebot import NudgeBot
        NudgeBot().send_email(receviers, subject, emails_content)
        return {
            'receivers': receviers, 'subject': subject, 'body': emails_content
        }

    @property
    def hash(self):
        return self._md5()  # TODO: find better hash and a way to get receivers
