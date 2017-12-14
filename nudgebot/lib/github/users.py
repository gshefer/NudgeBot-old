from cached_property import cached_property

from . import GithubEnv
from github.NamedUser import NamedUser
from common import Singleton
from config import config


class User(object):

    def __init__(self, github_obj):
        self._github_obj = github_obj

    def __hash__(self):
        return hash(self.login)

    def __repr__(self):
        return '<{} login="{}">'.format(self.__class__.__name__, self.login)

    def __eq__(self, other):
        return self.login == other or self.login == getattr(other, 'login', None)

    @cached_property
    def user(self):
        if isinstance(self._github_obj, NamedUser):
            return self._github_obj
        self._github_obj = GithubEnv().GIT.get_user(self._github_obj)
        return self._github_obj

    @cached_property
    def email(self):
        return self.user.email

    @cached_property
    def login(self):
        return self.user.login

    def __getattr__(self, name):
        return getattr(self.user, name)


class BotUser(User):
    __metaclass__ = Singleton

    def __init__(self):
        super(BotUser, self).__init__(config().credentials.github.username)


class ContributorUser(User):
    pass


class ReviewerUser(User):
    pass
