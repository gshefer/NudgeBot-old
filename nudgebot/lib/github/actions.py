from datetime import datetime

from nudgebot.lib.github.users import BotUser


class Action(object):
    """An abstract class for action"""
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
        self._pull_request.create_issue_comment(self._body)

    def is_done(self):
        return bool(filter(lambda comm: (self._body == comm.body
                                         and self._user.login == comm.user.login),
                           self._pull_request.get_issue_comments()))
