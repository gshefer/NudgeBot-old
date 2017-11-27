from datetime import datetime

from nudgebot.lib.github.users import BotUser


class Action(object):
    """A base class for action"""
    ACTIONS_LOG = []

    def __init__(self, user):
        self._user = user

    def run(self):
        if not isinstance(self._user, BotUser):
            # TODO: Define appropriate exception (Cannot run action of other users)
            raise Exception()
        if not self.is_done():
            self.ACTIONS_LOG.append(self)
            self.done_at = datetime.now()
            return self.action()

    def action(self):
        raise NotImplementedError()

    def is_done(self):
        raise NotImplementedError()


class PullRequestTagSet(Action):

    def __init__(self, pull_request, user, *tags):
        self._pull_request = pull_request
        self._tags = tags
        super(PullRequestTagSet, self).__init__(user)

    def action(self):
        self._pull_request.tags = self._tags

    def is_done(self):
        return self._tags == self._pull_request.tags


class PullRequestTagRemove(Action):

    def __init__(self, pull_request, user, *tags):
        self._pull_request = pull_request
        self._tags = tags
        super(PullRequestTagRemove, self).__init__(user)

    def action(self):
        self._pull_request.remove_tags(*self._tags)

    def is_done(self):
        return self._tags == self._pull_request.tags


class AddReviewers(Action):

    def __init__(self, pull_request, user, *reviewers):
        self._pull_request = pull_request
        self._reviewers = reviewers
        super(AddReviewers, self).__init__(user)

    def action(self):
        self._pull_request.add_reviewers(self._reviewers)

    def is_done(self):
        reviewers = self._pull_request.reviewers
        return all(map(lambda reviewer: reviewer in reviewers, self._reviewers))


class RemoveReviewers(Action):

    def __init__(self, pull_request, user, *reviewers):
        self._pull_request = pull_request
        self._reviewers = reviewers
        super(RemoveReviewers, self).__init__(user)

    def action(self):
        self._pull_request.remove_reviewers(self._reviewers)

    def is_done(self):
        reviewers = self._pull_request.reviewers
        return all(map(lambda reviewer: reviewer not in reviewers, self._reviewers))


class CreateIssueComment(Action):

    def __init__(self, pull_request, user, body):
        self._pull_request = pull_request
        self._body = body
        super(CreateIssueComment, self).__init__(user)

    def action(self):
        return self._pull_request.create_issue_comment(self._body)

    def is_done(self):
        return bool(filter(lambda comm: (self._body == comm.body
                                         and self._user.login == comm.user.login),
                           self._pull_request.get_issue_comments()))


class ReviewStateActionBase(Action):
    STATE = 'PENDING'

    def __init__(self, pull_request, user, body=None):
        self._pull_request = pull_request
        self._body = body
        super(ReviewStateActionBase, self).__init__(user)

    @property
    def event(self):
        return getattr(self, 'EVENT', self.STATE)

    def action(self):
        return self._pull_request.create_review(
            list(self._pull_request.get_commits())[-1], self._body, self.event)

    def is_done(self):
        all_reviewes = filter(
            lambda comm: self._user.login == comm.user.login,
            self._pull_request.get_reviews()
        )
        return not all_reviewes or self.STATE == all_reviewes[-1].state


class RequestChanges(ReviewStateActionBase):
    EVENT = 'REQUEST_CHANGES'
    STATE = 'CHANGES_REQUESTED'


class Approve(ReviewStateActionBase):
    EVENT = 'APPROVE'
    STATE = 'APPROVED'


class CreateReviewComment(Action):

    def __init__(self, pull_request, user, body, path=None, position=None):
        self._pull_request = pull_request
        self._body = body
        self._path = path
        self._position = position
        super(CreateReviewComment, self).__init__(user)

    def action(self):
        commit = list(self._pull_request.get_commits())[-1]
        return self._pull_request.create_review_comment(
            self._body, commit, self._path, self._position)

    def is_done(self):
        return bool(filter(lambda comm: (self._body == comm.body
                                         and self._user.login == comm.user.login
                                         and self._path == comm.path
                                         and self._position == comm.position),
                           self._pull_request.get_review_comments()))
