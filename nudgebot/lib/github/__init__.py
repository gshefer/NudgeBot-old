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


class Action(object):
    """An abstract class for action"""
    USER_TYPE = None  # The user type (USER_TYPES)
    SINGLE_RUN = True  # Define whether this action is a single run or could be
    #                    run multiple times

    def run(self):
        raise NotImplementedError()

    def is_done(self):
        raise NotImplementedError()


class PullRequestTagSet(Action):
    SINGLE_RUN = False

    def __init__(self, pull_request, user, *tags, **options):
        self._pull_request = pull_request
        self._user = user
        self._tags = tags
        self._options = options

    def run(self):
        self._pull_request.set_tags(*self._tags, **self._options)

    def is_done(self):
        pr_tags = self._pull_request.tags
        return (
            pr_tags == self._tags if self._options.get('absolute_set')
            else bool(all([tag in pr_tags for tag in self.tags]))
        )
