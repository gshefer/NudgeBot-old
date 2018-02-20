# NudgeBot

NudgeBot is a Pull request review and repository tracking bot which collect statistics and perform actions in a Github repository.

It's called "NudgeBot" since origininally it used to "nudge" reviewers to review pull request after some period without comment.
## Functionality:
- Perform actions in the pull request, i.e. add reviewers, post comment, etc.
- Collect pull requests statistics and repository statistics.
- Send reports to the repository maintainers.
- Provide a live dashboard which present the current statistics/status of the review process. E.g.

  ![alt text](https://raw.githubusercontent.com/gshefer/NudgeBot/master/doc/reviewers_pool_table.png)
  ![alt text](https://raw.githubusercontent.com/gshefer/NudgeBot/master/doc/pull_request_statistics_table.png)

## Design:
### Base components:

- [flow tree](https://github.com/gshefer/NudgeBot/blob/master/nudgebot/flow.py), A tree that describing the action to perform for each case in the pull request. This flow tree consists of:
  - [Case](https://github.com/gshefer/NudgeBot/blob/master/nudgebot/lib/actions/__init__.py) - Describing a situation in the pull request, a "Case".
  - [Action](https://github.com/gshefer/NudgeBot/blob/master/nudgebot/lib/cases/__init__.py) - Describing an action to perform in that situations/cases.
- [Pull request statistics](https://github.com/gshefer/NudgeBot/blob/master/nudgebot/lib/github/pull_request_statistics.py) Containing various statistics of a pull request.
- [Reviewers pool](https://github.com/gshefer/NudgeBot/blob/master/nudgebot/lib/github/reviewers_pool.py) a pool that containing the reviewers of the repository, including number of PRs per reviewer, this object used to decide which reviewer to set per pull request.
- [The bot](https://github.com/gshefer/NudgeBot/blob/master/nudgebot/__init__.py) The NudgeBot that handling the events, process the flow and performing actions.
- [Reports](https://github.com/gshefer/NudgeBot/blob/master/nudgebot/reports) Provides the ability to easily produce, trigger reporting about the repository.
- [Server](https://github.com/gshefer/NudgeBot/tree/master/nudgebot/server) The server side.
- [Config](https://github.com/gshefer/NudgeBot/tree/master/config) Includes the configuration file and credentials.

## Future plans:
- Change the server to use Django instead of flask.
- Extend the functionality to include more statistics about the repository.
### Notes:
- This project is still not a generic framework (not enough). Currently it's under development and in use and tested internaly.
- More documentation will be released later.
