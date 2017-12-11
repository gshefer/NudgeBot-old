from nudgebot.lib.github.cases import (NoPullRequestStateSet, PullRequestHasTag,
                                       ReviewerNotSet, InactivityForPeriod,
                                       ReviewerApproved, WaitingForReviewCommentReaction)
from nudgebot.lib.github.actions import (PullRequestTagSet, RUN_TYPES,
                                         CreateIssueComment, AddReviewersFromPool,
                                         ReportForInactivity, AskForReviewCommentReactions)
from nudgebot.lib.github.pull_request import PullRequestTag, PRstate, PRtag

FLOW = {
    NoPullRequestStateSet():
        [
            PullRequestTagSet(PullRequestTag(PRstate.WIP), run_type=RUN_TYPES.ALWAYS),
            CreateIssueComment('Please add a state to the PR title - setting state as [WIP]',
                               run_type=RUN_TYPES.ALWAYS)
        ],
    PullRequestHasTag(PullRequestTag(PRstate.RFR)): {
        ReviewerNotSet(level=1): AddReviewersFromPool(1),
        ReviewerApproved(level=1): [
            AddReviewersFromPool(2),
            PullRequestTagSet(PullRequestTag(PRtag.LP1))
        ],
        InactivityForPeriod(3, 0): ReportForInactivity(),
        InactivityForPeriod(7, 0): ReportForInactivity(),
        WaitingForReviewCommentReaction(2, 0): AskForReviewCommentReactions(2, 0)
    }
}
