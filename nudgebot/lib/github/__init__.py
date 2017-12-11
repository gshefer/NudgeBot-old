from github import Github
from github.GithubException import UnknownObjectException

from config import config
from common import Singleton


class GithubEnv(object):

    __metaclass__ = Singleton

    def __init__(self):

        login_info = config().credentials.github
        self.GIT = Github(login_info.get('username'), login_info.get('password'),
                          client_id=login_info.client_id, client_secret=login_info.client_secret)
        self.repos = []
        for repo in config().config.github.repos:
            try:
                org = self.GIT.get_organization(repo.org)
            except UnknownObjectException:
                org = self.GIT.get_user(repo.org)
            self.repos.append(org.get_repo(repo.repo))
            setattr(self.repos[-1], 'maintainers', repo.reviewers)
