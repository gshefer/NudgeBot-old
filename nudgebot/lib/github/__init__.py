from datetime import datetime
from enum import Enum

from github import Github
from github.GithubException import UnknownObjectException

from config import config
from common import Singleton


class env(object):

    __metaclass__ = Singleton

    def __init__(self):

        login_info = config().credentials.github
        self.GIT = Github(login_info.get('username'), login_info.get('password'),
                          client_id=login_info.client_id, client_secret=login_info.client_secret)
        self.repos = []
        for org_repo in config().config.github.repos:
            org_nm, repo_nm = org_repo.split('/')
            try:
                org = self.GIT.get_organization(org_nm)
            except UnknownObjectException:
                org = self.GIT.get_user(org_nm)
            self.repos.append(org.get_repo(repo_nm))


class USER_TYPES(Enum):
    """Enum of the user types"""
    BOT = 'NudgeBot'
    CONTRIBUTOR = 'Contributor'
    REVIEWER = 'Reviewer'


def action_run_wrapper(run_func):
    def wrapped(self):
        if not self.is_done():
            self.ACTIONS_LOG.append(self)
            self.done_at = datetime.now()
            return run_func(self)
    return wrapped


class Action(object):
    """An abstract class for action"""
    ACTIONS_LOG = []

    def __init__(self, user):
        self._user = user

    def run(self):
        if self._user is not USER_TYPES.BOT:
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
