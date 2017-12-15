from cached_property import cached_property


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

    @property
    def reviewers(self):
        return self._pool.keys()

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

    def pull_reviewer(self, level, pull_request_number, current_reviewers):
        reviewers = filter(lambda r: r[0] not in current_reviewers, self._pool.items())
        reviewer = min(reviewers, key=lambda rev: len(rev['pull_requests']))
        if not reviewer:
            raise Exception()  # TODO: Define appropriate exception
        self.update_reviewer_stat(reviewer[0], pull_request_number)
        return reviewer[0]

    def update_reviewer_stat(self, reviewer_login, pull_request_number):
        if reviewer_login not in self._pool:
            raise Exception()  # TODO: Define appropriate exception
        self._pool[reviewer_login]['pull_requests'].add(int(pull_request_number))
