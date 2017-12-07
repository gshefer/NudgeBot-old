from nudgebot.lib.github.pull_request import PRstate


class Case(object):

    def __init__(self, pull_request):
        self._pull_request = pull_request

    @property
    def state(self):
        raise NotImplementedError()


class NoPullRequestStateSet(Case):

    @property
    def state(self):
        return not [tag for tag in self._pull_request.tags
                    if tag.type == PRstate]
