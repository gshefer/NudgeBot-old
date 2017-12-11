from cached_property import cached_property

from . import GithubEnv
from github.NamedUser import NamedUser
from common import Singleton
from config import config


class User(object):

    def __init__(self, user):
        self._user = user

    def __eq__(self, other):
        return self.login == other or self.login == getattr(other, 'login', None)

    @cached_property
    def user(self):
        if isinstance(self._user, NamedUser):
            return self._user
        self._user = GithubEnv().GIT.get_user(self._user)
        return self._user

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
