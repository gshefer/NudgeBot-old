from cached_property import cached_property

from config import config
from nudgebot.lib.github.pull_request import PullRequest
from nudgebot.lib.github.reviewers_pool import ReviewersPool


class Repository(object):

    def __init__(self, organization, github_obj):
        self.org = organization
        self._github_obj = github_obj

    def __getattr__(self, name):
        return getattr(self._github_obj, name)

    def get_pull_request(self, number):
        return PullRequest(self, self._github_obj.get_pull(number))

    def get_pull_requests(self, **filters):
        """
        Args (filters):
            * state (optional): (str) the state of the pull requests to grab (open || closed).
            * logins (optional): (list || tuple) a list of the logins.
        """
        state = filters.get('state', 'open')
        logins = [login.lower() for login in filters.get('logins', [])]
        prs = []
        for pr in self._github_obj.get_pulls(state=state):
            if logins and pr.user.login.lower() not in logins:
                continue
            prs.append(PullRequest(self, pr))
        return prs

    @cached_property
    def config(self):
        org_name = (getattr(self._github_obj.organization, 'name', None) or
                    self._github_obj.owner.login)
        return [repo for repo in config().config.github.repos
                if repo.org == org_name
                and repo.repo == self._github_obj.name].pop()

    @cached_property
    def reviewers_pool(self):
        return ReviewersPool(self)
