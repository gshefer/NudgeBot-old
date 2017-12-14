from datetime import datetime

from cached_property import cached_property

from nudgebot.lib.github.users import ReviewerUser
from nudgebot.lib.github.actions import RequestChanges


class PullRequestStatCollection(object):

    def __init__(self, pull_request):
        self._pull_request = pull_request

    @cached_property
    def pull_request(self):
        return self._pull_request

    @cached_property
    def title(self):
        return self.pull_request.title

    @cached_property
    def description(self):
        return self._pull_request.description

    @cached_property
    def age(self):
        return self._pull_request.age

    @cached_property
    def number(self):
        return self._pull_request.number

    @cached_property
    def repo(self):
        return self._pull_request.repo

    @cached_property
    def commits(self):
        return self._pull_request.commits

    @cached_property
    def issue_comments(self):
        return self._pull_request.issue_comments

    @cached_property
    def review_comments(self):
        return self._pull_request.review_comments

    @cached_property
    def test_results(self):
        return self._pull_request.test_results

    @cached_property
    def last_code_update(self):
        return self._pull_request.last_code_update

    @cached_property
    def last_update(self):
        return self._pull_request.last_update

    @cached_property
    def tags(self):
        return self._pull_request.tags

    @cached_property
    def reviews(self):
        return self._pull_request.reviews

    @cached_property
    def reviewer_requests(self):
        return self.pull_request.get_reviewer_requests()

    @cached_property
    def reviewers(self):
        return self._pull_request.reviewers

    @cached_property
    def review_states_by_user(self):
        review_states = {}
        for review in self.reviews:
            review_states[ReviewerUser(review.user.login)] = review.state
        return review_states

    @cached_property
    def review_comment_reaction_statuses(self):
        statuses = []
        review_states = self.review_states_by_user
        review_comment_threads = self.pull_request.review_comment_threads
        for thread in review_comment_threads:
            if not thread.outdated:
                last_comment = thread.last_comment
                reviewer = ReviewerUser(thread.first_comment.user.login)
                is_require_changes = review_states.get(reviewer) == RequestChanges.STATE
                if is_require_changes:
                    age_seconds = (datetime.now() - last_comment.created_at).total_seconds()
                    statuses.append({
                        'reviewer': reviewer,
                        'contributor': self.owner,
                        'last_comment': last_comment,
                        'age_seconds': age_seconds
                    })
        return statuses
