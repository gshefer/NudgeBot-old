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
