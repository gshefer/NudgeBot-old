from cached_property import cached_property

from nudgebot.lib.github.users import ReviewerUser


class ReviewersPool(object):

    def __init__(self, repository):
        self._repository = repository
        self._pool = {}

    @cached_property
    def repository(self):
        return self._repository

    @property
    def pool(self):
        return self._pool

    def get_reviewers(self, level=-1):
        out = []
        for login in self._pool:
            if level == -1:
                out.append(login)
            elif self._pool[login]['level'] == level:
                out.append(login)
        return out

    @property
    def reviewers(self):
        return self.get_reviewers()

    def get_level(self, reviewer):
        if reviewer not in self._pool:
            # TODO: define appropriate exception
            raise Exception('Reviewer not found in the pool: {}'.format(reviewer))
        return self._pool[reviewer]['level']

    def sync(self):
        for level, logins in enumerate(self._repository.config.reviewers):
            level += 1
            for login in logins:
                if login in self._pool:
                    self._pool[login]['level'] = level
                else:
                    self._pool[login] = {'level': level, 'pull_requests': set()}

            for pull_request in self._repository.get_pull_requests():
                for reviewer in pull_request.reviewers:
                    if reviewer.login not in self._pool:
                        continue
                    self._pool[reviewer.login]['pull_requests'].add(pull_request.number)

    def pull_reviewer(self, level, pull_request):
        reviewers = filter(lambda r: (r[0] not in pull_request.reviewers
                                      and r[0] != pull_request.owner.login), self._pool.items())
        reviewer = min(reviewers, key=lambda rev: len(rev[1]['pull_requests']))
        if not reviewer:
            raise Exception()  # TODO: Define appropriate exception
        self.update_reviewer_stat(reviewer[0], pull_request.number)
        return ReviewerUser(reviewer[0])

    def update_reviewer_stat(self, reviewer_login, pull_request_number):
        if reviewer_login not in self._pool:
            raise Exception()  # TODO: Define appropriate exception
        self._pool[reviewer_login]['pull_requests'].add(int(pull_request_number))
