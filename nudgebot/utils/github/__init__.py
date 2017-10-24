from github import Github

from config import conf
from common import Singleton


class env(object):

    __metaclass__ = Singleton

    def __init__(self):

        login_info = conf().github.login
        self.GIT = Github(login_info.user, login_info.password)
        self.ORG = self.GIT.get_organization(conf().github.org)
        self.REPO = self.ORG.get_repo(conf().github.repo)
