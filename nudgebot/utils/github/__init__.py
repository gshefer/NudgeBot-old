from github import Github

from config import conf
from common import Singleton


class env(object):

    __metaclass__ = Singleton

    def __init__(self):

        login_info = conf().github.login
        self.GIT = Github(client_id=login_info.client_id, client_secret=login_info.client_secret)
        self.repos = []
        for org_repo in conf().github.repos:
            org_nm, repo_nm = org_repo.split('/')
            self.repos.append(self.GIT.get_organization(org_nm).get_repo(repo_nm))
