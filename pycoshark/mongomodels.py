from datetime import datetime
from mongoengine import Document, StringField, ListField, DateTimeField, IntField, BooleanField, ObjectIdField, \
    DictField, DynamicField, LongField, EmbeddedDocument, EmbeddedDocumentField, FileField, FloatField
import hashlib


class Refactoring(Document):
    """
    Refactoring
    Inherits from :class:`mongoengine.Document`

    :property ce_state: (:class:`~mongoengine.fields.DictField`) The code entity state of changed enteties in the current commit.
    :property commit_id: (:class:`~mongoengine.fields.ObjectIdField`) :class:`~pycoshark.mongomodels.Commit` id in which this refactoring occured
    :property description: (:class:`~mongoengine.fields.StringField`) The description of the refactoring provided by RefDiff.
    :property parent_commit_ce_states: ((:class:`~mongoengine.fields.ListField` of (:class:`~mongoengine.fields.DictField`)) The code entity states of changed enteties in the parent commits.
    :property type: (:class:`~mongoengine.fields.StringField`) Name of the refactoring type.
    :property detection_tool: (:class:`~mongoengine.fields.StringField`) The refactoring detection tool, e.g., refdiff or rminer.
    :property hunks: ((:class:`~mongoengine.fields.ListField` of (:class:`~mongoengine.fields.DictField`)) The hunks that were detected.
    """

    # PK: _id
    ce_state = DictField()
    commit_id = ObjectIdField()
    description = StringField()
    parent_commit_ce_states = ListField(DictField())
    type = StringField()
    detection_tool = StringField()
    hunks = ListField(DictField())


class Identity(Document):
    meta = {
        'indexes': [
            '#id',
        ],
        'shard_key': ('id', ),
    }

    people = ListField(ObjectIdField())


class TravisJob(Document):
    meta = {
        'indexes': [
            'build_id'
        ],
        'shard_key': ('tr_id',),
    }
    tr_id = IntField(unique=True)
    build_id = ObjectIdField(required=True)
    allow_failure = BooleanField(required=True)
    number = StringField(required=True)
    state = StringField(max_length=8, required=True)
    started_at = DateTimeField()
    finished_at = DateTimeField()
    stages = ListField(StringField())
    metrics = DictField()
    config = DictField()
    job_log = StringField()

    def __repr__(self):
        return "<TravisJob allow_failure:%s number:%s state:%s started_at:%s finished_at:%s stages:%s metrics:%s " \
               "config:%s>" % \
               (self.allow_failure, self.number, self.state, self.started_at, self.finished_at, self.stages,
                self.metrics, self.config)


class TravisBuild(Document):
    meta = {
        'indexes': [
            'number',
            ('vcs_system_id', 'number'),
            'tr_id'
        ],
        'shard_key': ('tr_id',),
    }

    tr_id = IntField(unique=True)
    vcs_system_id = ObjectIdField()
    commit_id = ObjectIdField()
    number = IntField(required=True)
    state = StringField(max_length=8, required=True)
    duration = LongField(default=None)
    event_type = StringField(max_length=15, required=True)
    pr_number = IntField()
    started_at = DateTimeField(default=None)
    finished_at = DateTimeField(default=None)
    stages = ListField(StringField())

    def __repr__(self):
        return "<TravisBuild vcs_system_id:%s commit_id:%s number:%s duration:%s event_type:%s " \
               "pr_number:%s started_at:%s finished_at:%s stages:%s>" % \
               (self.vcs_system_id, self.commit_id, self.number, self.duration, self.event_type, self.pr_number,
                self.started_at, self.finished_at, self.stages)


class Project(Document):
    """
    Project class.
    Inherits from :class:`mongoengine.Document`

    Index: #name

    ShardKey: name

    :property name: (:class:`~mongoengine.fields.StringField`) name of the project
    """
    meta = {
        'indexes': [
            '#name'
        ],
        'shard_key': ('name', ),
    }

    # PK: name
    # Shard Key: hashed name
    name = StringField(max_length=200, required=True, unique=True)


class MailingList(Document):
    """
        MailingList class.
        Inherits from :class:`mongoengine.Document`

        Index: #name

        ShardKey: name

        :property project_id: (:class:`~mongoengine.fields.ObjectIdField`) :class:`~pycoshark.mongomodels.Project` id id to which the mailing list belongs
        :property name: (:class:`~mongoengine.fields.StringField`) name of the mailing list
        :property last_updated: (:class:`~mongoengine.fields.DateTimeField`) date when the data of the mailing list was last updated in the database
    """
    meta = {
        'indexes': [
            '#name'
        ],
        'shard_key': ('name', ),
    }

    # PK: name
    # Shard Key: hashed name

    project_id = ObjectIdField(required=True)
    name = StringField(required=True)
    last_updated = DateTimeField()


class Message(Document):
    """
    Message class.
    Inherits from :class:`mongoengine.Document`

    Index: message_id

    ShardKey: message_id, mailing_list_id

    :property message_id: (:class:`~mongoengine.fields.StringField`) id of the message (worldwide unique)
    :property mailing_list_id: (:class:`~mongoengine.fields.ObjectIdField`) id of the :class:`~pycoshark.mongomodels.MailingList` to which the message belongs
    :property reference_ids: ((:class:`~mongoengine.fields.ListField` of (:class:`~mongoengine.fields.ObjectIdField`)) id to messages that are referenced by this message
    :property in_reply_to_id: (:class:`~mongoengine.fields.ObjectIdField`) id of a message to which this message is a reply
    :property from_id: (:class:`~mongoengine.fields.ObjectIdField`) id of a person :class:`~pycoshark.mongomodels.People` from which this message is
    :property to_ids: ((:class:`~mongoengine.fields.ListField` of (:class:`~mongoengine.fields.ObjectIdField`)) ids of persons :class:`~pycoshark.mongomodels.People` to which this message was sent
    :property cc_ids: ((:class:`~mongoengine.fields.ListField` of (:class:`~mongoengine.fields.ObjectIdField`)) ids of persons :class:`~pycoshark.mongomodels.People` to which this message was sent (cc)
    :property subject: (:class:`~mongoengine.fields.StringField`) subject of the message
    :property body: (:class:`~mongoengine.fields.StringField`) message text
    :property date: (:class:`~mongoengine.fields.DateTimeField`)  date when the message was sent
    :property patches: ((:class:`~mongoengine.fields.ListField` of (:class:`~mongoengine.fields.StringField`))  if patches were applied to the message
    """

    meta = {
        'indexes': [
            'message_id'
        ],
        'shard_key': ('message_id', 'mailing_list_id'),
    }

    # PK: message_id
    # Shard Key: message_id, mailing_list_id

    message_id = StringField(required=True, unique_with=['mailing_list_id'])
    mailing_list_id = ObjectIdField(required=True)
    reference_ids = ListField(ObjectIdField())
    in_reply_to_id = ObjectIdField()
    from_id = ObjectIdField()
    to_ids = ListField(ObjectIdField())
    cc_ids = ListField(ObjectIdField())
    subject = StringField()
    body = StringField()
    date = DateTimeField()
    patches = ListField(StringField())


class PullRequestSystem(Document):
    """
    PullRequestSystem class.
    Inherits from :class:`mongoengine.Document`

    Index: #url

    ShardKey: url

    :property project_id: (:class:`~mongoengine.fields.ObjectIdField`) :class:`~pycoshark.mongomodels.Project` id to which the pull request system belongs
    :property url: (:class:`~mongoengine.fields.StringField`) url to the pull request system
    :property last_updated: (:class:`~mongoengine.fields.DateTimeField`)  date when the data of the pull request system was last updated in the database
    """

    meta = {
        'indexes': [
            '#url'
        ],
        'shard_key': ('url', ),
    }

    project_id = ObjectIdField(required=True)
    url = StringField(required=True)
    last_updated = DateTimeField()


class PullRequest(Document):
    """
    PullRequest class.

    Inherits from :class:`mongoengine.Document`

    Index: pull_request_system_id

    ShardKey: external_id, pull_request_system_id

    :property pull_request_system_id: (:class:`~mongoengine.fields.ObjectIdField`) :class:`~pycoshark.mongomodels.PullRequestSystem` id of the system to which the pull request belongs
    :property external_id: (:class:`~mongoengine.fields.StringField`) number of the pull request

    :property title: (:class:`~mongoengine.fields.StringField`) title of the pull request
    :property description: (:class:`~mongoengine.fields.StringField`) description of the pull request
    :property is_draft (:class:`~mongoengine.fields.BooleanField`) true if this pull request is a draft
    :property is_locked (:class:`~mongoengine.fields.BooleanField`) true if this pull request is locked
    :property lock_reason: (:class:`~mongoengine.fields.StringField`) reason for the locking
    :property author_association: (:class:`~mongoengine.fields.StringField`) github author association, e.g., owner, NONE, collaborator

    :property created_at: (:class:`~mongoengine.fields.DateTimeField`) date, when this pr was created
    :property updated_at: (:class:`~mongoengine.fields.DateTimeField`) date, when this pr was updated
    :property merged_at: (:class:`~mongoengine.fields.DateTimeField`)  date, when this pr was merged
    :property merge_commit_id: (:class:`~mongoengine.fields.ObjectIdField`) id of the :class:`~pycoshark.mongomodels.Commit`

    :property creator_id: (:class:`~mongoengine.fields.ObjectIdField`) id of the :class:`~pycoshark.mongomodels.People` author of the pr
    :property assignee_id: (:class:`~mongoengine.fields.ObjectIdField`) id of the :class:`~pycoshark.mongomodels.People` assignee of the pr
    :property linked_user_ids: (:class:`~mongoengine.fields.ListField` of :class:`~mongoengine.fields.ObjectIdField` of the :class:`~pycoshark.mongomodels.People`) list of linked user ids
    :property requested_reviewer_ids: (:class:`~mongoengine.fields.ListField` of :class:`~mongoengine.fields.ObjectIdField` of the :class:`~pycoshark.mongomodels.People`) list of requested reviewer ids

    :property state: (:class:`~mongoengine.fields.StringField`) state of the pr
    :property labels: (:class:`~mongoengine.fields.ListField` of :class:`~mongoengine.fields.StringField` list of labels for this pr

    :property source_repo_url: (:class:`~mongoengine.fields.StringField`) source repository of this pr, can be a fork
    :property source_branch: (:class:`~mongoengine.fields.StringField`) source branch of this pr
    :property source_commit_sha: (:class:`~mongoengine.fields.StringField`) source commit sha of this pr
    :property source_commit_id: (:class:`~mongoengine.fields.ObjectIdField`) id of the :class:`~pycoshark.mongomodels.Commit` commit id if available in local VCSSystem

    :property target_repo_url: (:class:`~mongoengine.fields.StringField`) target repository of this pr, should be our VCSSystem
    :property target_branch: (:class:`~mongoengine.fields.StringField`) target branch of this pr
    :property target_commit_sha: (:class:`~mongoengine.fields.StringField`) target commit sha of this pr
    :property target_commit_id: (:class:`~mongoengine.fields.ObjectIdField`) id of the :class:`~pycoshark.mongomodels.Commit` commit id if available in local VCSSystem
    """

    meta = {
        'indexes': [
            'pull_request_system_id'
        ],
        'shard_key': ('external_id', 'pull_request_system_id'),
    }

    pull_request_system_id = ObjectIdField(required=True)
    external_id = StringField(unique_with=['pull_request_system_id'])

    title = StringField()
    description = StringField()
    is_draft = BooleanField()
    is_locked = BooleanField()
    lock_reason = StringField()
    author_association = StringField()

    created_at = DateTimeField()
    updated_at = DateTimeField()
    merged_at = DateTimeField()
    merge_commit_id = ObjectIdField()

    creator_id = ObjectIdField()
    assignee_id = ObjectIdField()
    linked_user_ids = ListField(ObjectIdField())
    requested_reviewer_ids = ListField(ObjectIdField())

    state = StringField()
    labels = ListField(StringField())

    source_repo_url = StringField()
    source_branch = StringField()
    source_commit_sha = StringField()
    source_commit_id = ObjectIdField()

    target_repo_url = StringField()
    target_branch = StringField()
    target_commit_sha = StringField()
    target_commit_id = ObjectIdField()


class PullRequestReview(Document):
    """
    PullRequestReview class.

    Inherits from :class:`mongoengine.Document`

    Index: pull_request_id

    ShardKey: external_id, pull_request_id

    :property pull_request_id: (:class:`~mongoengine.fields.ObjectIdField`) :class:`~pycoshark.mongomodels.PullRequest` id to which the pull request review belongs
    :property external_id: (:class:`~mongoengine.fields.StringField`) number of the review

    :property state: (:class:`~mongoengine.fields.StringField`) state of the pull request review
    :property description: (:class:`~mongoengine.fields.StringField`) body of the pull request review
    :property creator_id: (:class:`~mongoengine.fields.ObjectIdField`) id of the :class:`~pycoshark.mongomodels.People` author of review
    :property submitted_at: (:class:`~mongoengine.fields.DateTimeField`)  date, when this review was submitted
    :property author_association: (:class:`~mongoengine.fields.StringField`) github author association, e.g., owner, NONE, collaborator

    :property commit_sha: (:class:`~mongoengine.fields.StringField`) commit sha
    :property pull_request_commit_id: (:class:`~mongoengine.fields.ObjectIdField`) id of the :class:`~pycoshark.mongomodels.PullRequestCommit` pull request commit id (if available)
    """

    meta = {
        'indexes': [
            'pull_request_id'
        ],
        'shard_key': ('external_id', 'pull_request_id'),
    }

    pull_request_id = ObjectIdField(required=True)
    external_id = StringField(unique_with=['pull_request_id'])

    state = StringField()
    description = StringField()
    creator_id = ObjectIdField()
    submitted_at = DateTimeField()
    author_association = StringField()

    commit_sha = StringField()
    pull_request_commit_id = ObjectIdField()


class PullRequestReviewComment(Document):
    """
    PullRequestReviewComment class.

    These are comments on pull requests. They link to PullRequestCommits if they are available.
    The path and diff_hunk can be the same as a PullRequestFile, however that is not always the case as PullRequestFile are only the currently active PullRequestFiles
    and the PullRequestReviewComment may reference an older commit.

    Inherits from :class:`mongoengine.Document`

    Index: pull_request_review_id

    ShardKey: external_id, pull_request_review_id

    :property pull_request_review_id: (:class:`~mongoengine.fields.ObjectIdField`) :class:`~pycoshark.mongomodels.PullRequestReview` id to which the pull request review comment belongs
    :property external_id: (:class:`~mongoengine.fields.StringField`) number of the review comment

    :property comment: (:class:`~mongoengine.fields.StringField`) text of the comment
    :property author_association: (:class:`~mongoengine.fields.StringField`) github author association, e.g., owner, NONE, collaborator
    :property in_reply_to_id: (:class:`~mongoengine.fields.ObjectIdField`) :class:`~pycoshark.mongomodels.PullRequestReviewComment` id which the pull request review comment replies to (if any)

    :property creator_id: (:class:`~mongoengine.fields.ObjectIdField`) id of the :class:`~pycoshark.mongomodels.People` author of comment
    :property created_at: (:class:`~mongoengine.fields.DateTimeField`)  date, when this comment was created
    :property updated_at: (:class:`~mongoengine.fields.DateTimeField`)  date, when this comment was updated

    :property path: (:class:`~mongoengine.fields.StringField`) file which this comment refers to
    :property diff_hunk: (:class:`~mongoengine.fields.StringField`) diff which this comment refers to
    :property position: (:class:`~mongoengine.fields.IntField`) position in the file this comment refers to
    :property original_position: (:class:`~mongoengine.fields.IntField`) original position in the file this comment refers to (deleted line instead of added line)

    :property commit_sha: (:class:`~mongoengine.fields.StringField`) commit sha
    :property original_commit_sha: (:class:`~mongoengine.fields.StringField`) parent commit sha
    :property pull_request_commit_id: (:class:`~mongoengine.fields.ObjectIdField`) id of the :class:`~pycoshark.mongomodels.PullRequestCommit` pull request commit id (if available)
    :property original_pull_request_commit_id: (:class:`~mongoengine.fields.ObjectIdField`) id of the :class:`~pycoshark.mongomodels.PullRequestCommit` pull request commit id (if available)

    :property start_line: (:class:`~mongoengine.fields.IntField`) position in the file this comment refers to (new)
    :property original_start_line: (:class:`~mongoengine.fields.IntField`) position in the file this comment refers to (new)
    :property start_side: (:class:`~mongoengine.fields.StringField`) position in the diff editor LEFT/RIGHT for deleted or added

    :property line: (:class:`~mongoengine.fields.IntField`) position in the file this comment refers to (new)
    :property original_line: (:class:`~mongoengine.fields.IntField`) position in the file this comment refers to (new)
    :property side: (:class:`~mongoengine.fields.StringField`) position in the diff editor LEFT/RIGHT for deleted or added
    """

    meta = {
        'indexes': [
            'pull_request_review_id'
        ],
        'shard_key': ('external_id', 'pull_request_review_id'),
    }

    pull_request_review_id = ObjectIdField(required=True)
    external_id = StringField(unique_with=['pull_request_review_id'])

    comment = StringField()
    author_association = StringField()
    in_reply_to_id = ObjectIdField()  # we assume that this only refers to other PullRequestReviewComments

    creator_id = ObjectIdField()
    created_at = DateTimeField()
    updated_at = DateTimeField()

    path = StringField()  # file name, not necessarily a link to PullRequestFile
    diff_hunk = StringField()  # unified diff
    position = IntField()
    original_position = IntField()

    commit_sha = StringField()
    original_commit_sha = StringField()
    pull_request_commit_id = ObjectIdField()
    original_pull_request_commit_id = ObjectIdField()

    start_line = IntField()
    original_start_line = IntField()
    start_side = StringField()
    line = IntField()
    original_line = IntField()
    side = StringField()


class PullRequestComment(Document):
    """
    PullRequestComment class.

    These comments are fetched via the issues api endpoint for github.

    Inherits from :class:`mongoengine.Document`

    Index: pull_request_id

    ShardKey: external_id, pull_request_id

    :property pull_request_id: (:class:`~mongoengine.fields.ObjectIdField`) :class:`~pycoshark.mongomodels.PullRequest` id to which the pull request commit belongs
    :property external_id: (:class:`~mongoengine.fields.StringField`) number of the comment

    :property created_at: (:class:`~mongoengine.fields.DateTimeField`)  date, when this comment was created
    :property updated_at: (:class:`~mongoengine.fields.DateTimeField`)  date, when this comment was updated
    :property author_id: (:class:`~mongoengine.fields.ObjectIdField`) id of the :class:`~pycoshark.mongomodels.People` author of commit
    :property comment: (:class:`~mongoengine.fields.StringField`) text of the comment
    :property author_association: (:class:`~mongoengine.fields.StringField`) github author association, e.g., owner, NONE, collaborator
    """

    meta = {
        'indexes': [
            'pull_request_id'
        ],
        'shard_key': ('external_id', 'pull_request_id'),
    }

    pull_request_id = ObjectIdField(required=True)
    external_id = StringField(unique_with=['pull_request_id'])
    created_at = DateTimeField()
    updated_at = DateTimeField()
    author_id = ObjectIdField()
    comment = StringField()
    author_association = StringField()


class PullRequestEvent(Document):
    """
    PullRequestEvent class.

    These events are fetched via the issues api endpoint for github.

    Inherits from :class:`mongoengine.Document`

    Index: pull_request_id

    ShardKey: external_id, pull_request_id

    :property pull_request_id: (:class:`~mongoengine.fields.ObjectIdField`) :class:`~pycoshark.mongomodels.PullRequest` id to which the pull request commit belongs
    :property external_id: (:class:`~mongoengine.fields.StringField`) number of the event

    :property created_at: (:class:`~mongoengine.fields.DateTimeField`)  date, when this event was created
    :property author_id: (:class:`~mongoengine.fields.ObjectIdField`) id of the :class:`~pycoshark.mongomodels.People` author of commit
    :property commit_id: (:class:`~mongoengine.fields.ObjectIdField`) :class:`~pycoshark.mongomodels.Commit` id to which the pull request event links, only if it is in our repository
    :property commit_sha: (:class:`~mongoengine.fields.StringField`) commit_sha of the commit
    :property commit_repo_url: (:class:`~mongoengine.fields.StringField`) url of the repository of the commit
    :property event_type: (:class:`~mongoengine.fields.StringField`) event type name

    :property additional_data: (:class:`~mongoengine.fields.DictField`) additional data from the backend not common for all event types
    """

    meta = {
        'indexes': [
            'pull_request_id',
        ],
        'shard_key': ('external_id', 'pull_request_id'),
    }

    pull_request_id = ObjectIdField(required=True)
    external_id = StringField(unique_with=['pull_request_id'])

    created_at = DateTimeField()
    author_id = ObjectIdField()
    commit_id = ObjectIdField()
    commit_sha = StringField()
    commit_repo_url = StringField()
    event_type = StringField()

    additional_data = DictField()


class PullRequestCommit(Document):
    """
    PullRequestCommit class.

    We have this extra class because not every PullRequestCommit is a Commit in our collection.
    Sometimes, the source of the PullRequestCommit is the source repository of the pull request, i.e. a fork of our VCSSystem.

    Inherits from :class:`mongoengine.Document`

    Index: pull_request_id

    ShardKey: commit_sha, pull_request_id

    :property pull_request_id: (:class:`~mongoengine.fields.ObjectIdField`) :class:`~pycoshark.mongomodels.PullRequest` id to which the pull request commit belongs
    :property author_id: (:class:`~mongoengine.fields.ObjectIdField`) id of the :class:`~pycoshark.mongomodels.People` author of commit
    :property committer_id: (:class:`~mongoengine.fields.ObjectIdField`) id of the :class:`~pycoshark.mongomodels.People` committer of commit
    :property message: (:class:`~mongoengine.fields.StringField`) commit message

    :property commit_id: (:class:`~mongoengine.fields.ObjectIdField`) :class:`~pycoshark.mongomodels.Commit` id to which the pull request commit links, only if it is in our repository
    :property commit_sha: (:class:`~mongoengine.fields.StringField`) commit_sha of the commit, could be the hash from the source repo of the pull request
    :property commit_repo_url: (:class:`~mongoengine.fields.StringField`) url of the repository of the commit
    :property parents: ((:class:`~mongoengine.fields.ListField` of (:class:`~mongoengine.fields.StringField`))  list of parents (revision hashes) of this commit
    """

    meta = {
        'indexes': [
            'pull_request_id',
        ],
        'shard_key': ('commit_sha', 'pull_request_id'),
    }

    pull_request_id = ObjectIdField(required=True)

    author_id = ObjectIdField()
    committer_id = ObjectIdField()
    message = StringField()

    commit_id = ObjectIdField()
    commit_sha = StringField(required=True, unique_with=['pull_request_id'])
    commit_repo_url = StringField()
    parents = ListField(StringField())


class PullRequestFile(Document):
    """
    PullRequestFile class.
    Inherits from :class:`mongoengine.Document`

    The current set of Files associated with the pull request.
    The PullRequestReviewComment has its own path for a file, however this may link to an older file no longer present in the current HEAD of the pull request.

    Index: pull_request_id

    ShardKey: path, sha, pull_request_id

    :property pull_request_id: (:class:`~mongoengine.fields.ObjectIdField`) :class:`~pycoshark.mongomodels.PullRequest` id to which the pull request file belongs
    :property sha: (:class:`~mongoengine.fields.StringField`) sha hash, maybe file hash (only present if a file is changed, not for changing rights)
    :property path: (:class:`~mongoengine.fields.StringField`) filename
    :property status: (:class:`~mongoengine.fields.StringField`) status (e.g., added)
    :property additions: (:class:`~mongoengine.fields.IntField`) added lines
    :property deletions: (:class:`~mongoengine.fields.IntField`) deleted lines
    :property changes: (:class:`~mongoengine.fields.IntField`) changed lines
    :property patch: (:class:`~mongoengine.fields.StringField`) diff hunk of the change
    """

    meta = {
        'indexes': [
            'pull_request_id',
        ],
        'shard_key': ('path', 'pull_request_id'),
    }

    pull_request_id = ObjectIdField(required=True)
    sha = StringField()  # this is not a sha of PullRequestCommit

    path = StringField(required=True)

    status = StringField()
    additions = IntField()
    deletions = IntField()
    changes = IntField()
    patch = StringField()


class IssueSystem(Document):
    """
    IssueSystem class.
    Inherits from :class:`mongoengine.Document`

    Index: #url

    ShardKey: url

    :property project_id: (:class:`~mongoengine.fields.ObjectIdField`) :class:`~pycoshark.mongomodels.Project` id to which the issue system belongs
    :property url: (:class:`~mongoengine.fields.StringField`) url to the issue system
    :property last_updated: (:class:`~mongoengine.fields.DateTimeField`)  date when the data of the mailing list was last updated in the database
    """
    meta = {
        'indexes': [
            '#url'
        ],
        'shard_key': ('url', ),
    }

    # PK: url
    # Shard Key: hashed url

    project_id = ObjectIdField(required=True)
    url = StringField(required=True)
    last_updated = DateTimeField()


class Issue(Document):
    """
    Issue class.
    Inherits from :class:`mongoengine.Document`

    Index: external_id, issue_system_id

    ShardKey: external_id, issue_system_id

    :property external_id: (:class:`~mongoengine.fields.StringField`) id that was assigned from the issue system to this issue
    :property issue_system_id: (:class:`~mongoengine.fields.ObjectIdField`) id of the :class:`~pycoshark.mongomodels.IssueSystem` to which this issue belongs
    :property title: (:class:`~mongoengine.fields.StringField`) title of the issue
    :property desc: (:class:`~mongoengine.fields.StringField`) description of the issue
    :property created_at: (:class:`~mongoengine.fields.DateTimeField`)  date, when this issue was created
    :property updated_at: (:class:`~mongoengine.fields.DateTimeField`)  date, when this issue was last updated
    :property creator_id: (:class:`~mongoengine.fields.ObjectIdField`) id of the :class:`~pycoshark.mongomodels.People` document which created this issue
    :property reporter_id: (:class:`~mongoengine.fields.ObjectIdField`) id of the :class:`~pycoshark.mongomodels.People` document which reported this issue
    :property issue_type: (:class:`~mongoengine.fields.StringField`) type of the issue
    :property priority: (:class:`~mongoengine.fields.StringField`) priority of the issue
    :property status: (:class:`~mongoengine.fields.StringField`) status of the issue
    :property affects_versions: ((:class:`~mongoengine.fields.ListField` of (:class:`~mongoengine.fields.StringField`)) list of affected versions by this issue
    :property components: ((:class:`~mongoengine.fields.ListField` of (:class:`~mongoengine.fields.StringField`))  list, which componenets are affected
    :property labels: ((:class:`~mongoengine.fields.ListField` of (:class:`~mongoengine.fields.StringField`))  list of labels for this issue
    :property issue_type_manual: (:class:`~mongoengine.fields.DictField`) for manual issue types for this issue, contains information about the issue_type and the author, the author is the key and the issue_type is the value
    :property issue_type_verified: (:class:`~mongoengine.fields.StringField`) verified issue_type of the issue; source is manual issue types
    :property resolution: (:class:`~mongoengine.fields.StringField`) resolution for this issue
    :property fix_versions: ((:class:`~mongoengine.fields.ListField` of (:class:`~mongoengine.fields.StringField`))  list of versions on which this issue is fixed
    :property assignee_id: (:class:`~mongoengine.fields.ObjectIdField`) id of the :class:`~pycoshark.mongomodels.People` document to which this issue was assigned
    :property issue_links: ((:class:`~mongoengine.fields.ListField` of (:class:`~mongoengine.fields.DictField`)) to which this issue is linked
    :property parent_issue_id: (:class:`~mongoengine.fields.ObjectIdField`) id of the :class:`~pycoshark.mongomodels.Issue` document that is the parent of this issue
    :property original_time_estimate: (:class:`~mongoengine.fields.IntField`)  estimated time to solve this issue
    :property environment: (:class:`~mongoengine.fields.StringField`) environment that is affected by this issue
    :property platform: (:class:`~mongoengine.fields.StringField`) platform that is affected by this issue
    :property is_pull_request: (:class:`~mongoengine.fields.BoleanField`) true if this issue is a pull request, Github issues can be pull requests
    """
    meta = {
        'indexes': [
            'issue_system_id'
        ],
        'shard_key': ('external_id', 'issue_system_id'),
    }

    # PK: external_id, issue_system_id
    # Shard Key: external_id, issue_system_id

    external_id = StringField(unique_with=['issue_system_id'])
    issue_system_id = ObjectIdField(required=True)
    title = StringField()
    desc = StringField()
    created_at = DateTimeField()
    updated_at = DateTimeField()
    creator_id = ObjectIdField()
    reporter_id = ObjectIdField()

    issue_type = StringField()
    priority = StringField()
    status = StringField()
    affects_versions = ListField(StringField())
    components = ListField(StringField())
    labels = ListField(StringField())
    issue_type_manual = DictField()
    issue_type_verified = StringField()
    resolution = StringField()
    fix_versions = ListField(StringField())
    assignee_id = ObjectIdField()
    issue_links = ListField(DictField())
    parent_issue_id = ObjectIdField()
    original_time_estimate = IntField()
    environment = StringField()
    platform = StringField()
    is_pull_request = BooleanField(default=False)

    def __str__(self):
        return "System_id: %s, issue_system_id: %s, title: %s, desc: %s, created_at: %s, updated_at: %s, issue_type: %s," \
               " priority: %s, affects_versions: %s, components: %s, labels: %s, resolution: %s, fix_versions: %s," \
               "assignee: %s, issue_links: %s, status: %s, time_estimate: %s, environment: %s, creator: %s, " \
               "reporter: %s" % (
            self.external_id, self.issue_system_id, self.title, self.desc, self.created_at, self.updated_at, self.issue_type,
            self.priority, ','.join(self.affects_versions), ','.join(self.components), ','.join(self.labels),
            self.resolution, ','.join(self.fix_versions), self.assignee_id, str(self.issue_links), self.status,
            str(self.original_time_estimate), self.environment, self.creator_id, self.reporter_id
        )


class Event(Document):
    """
    Event class.
    Inherits from :class:`mongoengine.Document`

    Index: issue_id, #external_id, (issue_id, -created_at)

    ShardKey: external_id, issue_id

    :property external_id: (:class:`~mongoengine.fields.StringField`) id that was assigned from the issue system to this event
    :property issue_id: (:class:`~mongoengine.fields.ObjectIdField`) id of the :class:`~pycoshark.mongomodels.Issue` to which this event belongs
    :property created_at: (:class:`~mongoengine.fields.DateTimeField`)  date when the event was created
    :property status: (:class:`~mongoengine.fields.StringField`) shows, what part of the issue was changed
    :property author_id: (:class:`~mongoengine.fields.ObjectIdField`) id of the :class:`~pycoshark.mongomodels.People` document that created the event
    :property old_value: (:class:`~mongoengine.fields.DynamicField`) value before the event happened
    :property new_value: (:class:`~mongoengine.fields.DynamicField`) value after the event happened

    """
    meta = {
        'indexes': [
            'issue_id',
        ],
        'shard_key': ('external_id', 'issue_id'),
    }

    # PK: external_id, issue_id
    # Shard Key: external_id, issue_id

    external_id = StringField(unique_with=['issue_id'])
    issue_id = ObjectIdField()
    created_at = DateTimeField()
    status = StringField(max_length=50)
    author_id = ObjectIdField()
    commit_id = ObjectIdField()

    old_value = DynamicField()
    new_value = DynamicField()

    def __str__(self):
        return "external_id: %s, issue_id: %s, created_at: %s, status: %s, author_id: %s, " \
               "old_value: %s, new_value: %s, commit_id: %s" % (
                    self.external_id,
                    self.issue_id,
                    self.created_at,
                    self.status,
                    self.author_id,
                    self.old_value,
                    self.new_value,
                    self.commit_id
               )


class IssueComment(Document):
    """
    IssueComment class.
    Inherits from :class:`mongoengine.Document`

    Index: issue_id, #external_id, (issue_id, -created_at)

    ShardKey: external_id, issue_id

    :property external_id: (:class:`~mongoengine.fields.StringField`) id that was assigned from the issue system to this comment
    :property issue_id: (:class:`~mongoengine.fields.ObjectIdField`) id of the :class:`~pycoshark.mongomodels.Issue` to which this event belongs
    :property created_at: (:class:`~mongoengine.fields.DateTimeField`)  date when the event was created
    :property author_id: (:class:`~mongoengine.fields.ObjectIdField`) id of the :class:`~pycoshark.mongomodels.People` document that created the event
    :property comment: (:class:`~mongoengine.fields.StringField`) comment that was given

    """

    meta = {
        'indexes': [
            'issue_id',
        ],
        'shard_key': ('external_id', 'issue_id'),
    }

    external_id = StringField(unique_with=['issue_id'])
    issue_id = ObjectIdField()
    created_at = DateTimeField()
    author_id = ObjectIdField()
    comment = StringField()

    def __str__(self):
        return "external_id: %s, issue_id: %s, created_at: %s, author_id: %s, comment: %s" % (
            self.external_id, self.issue_id, self.created_at, self.author_id, self.comment
        )


class VCSSystem(Document):
    """
    VCSSystem class.
    Inherits from :class:`mongoengine.Document`

    Index: #url

    ShardKey: #url

    :property url: (:class:`~mongoengine.fields.StringField`) url to the repository
    :property project_id: (:class:`~mongoengine.fields.ObjectIdField`) :class:`~pycoshark.mongomodels.Project` id to which this vcs system belongs
    :property repository_type: (:class:`~mongoengine.fields.StringField`) type of the repository (e.g., git)
    :property last_updated: (:class:`~mongoengine.fields.DateTimeField`)  date when the data in the database for this repository was last updates

    """
    meta = {
        'collection': 'vcs_system',
        'indexes': [
            '#url'
        ],
        'shard_key': ('url', ),
    }

    # PK: url
    # Shard Key: hashed url

    url = StringField(required=True, unique=True)
    project_id = ObjectIdField(required=True)
    repository_type = StringField(required=True)
    last_updated = DateTimeField()
    submodules = ListField(ObjectIdField())
    repository_file = FileField(collection_name='repository_data')


class VCSSubmodule(Document):
    """
    VCSSubmodule class.
    Inherits from :class:`mongoengine.Document`

    Index: vcs_system_id

    ShardKey: vcs_system_id

    :property path: (:class:`~mongoengine.fields.StringField`) submodule path relative to the parent repository root
    :property project_id: (:class:`~mongoengine.fields.ObjectIdField`) :class:`~pycoshark.mongomodels.VCSSystem` id of this submodule
    """
    meta = {
        'collection': 'vcs_submodule',
        'indexes': [
            'vcs_system_id'
        ],
        'shard_key': ('vcs_system_id', ),
    }

    # PK: vcs_system_id
    # Shard Key: vcs_system_id

    vcs_system_id = ObjectIdField(required=True)
    path = StringField(required=True)


class FileAction(Document):
    """
    FileAction class.
    Inherits from :class:`mongoengine.Document`

    Index: #id, commit_id, (commit_id, file_id)

    ShardKey: #id

    :property file_id: (:class:`~mongoengine.fields.ObjectIdField`) :class:`~pycoshark.mongomodels.File` id that was changed with this action
    :property commit_id: (:class:`~mongoengine.fields.ObjectIdField`) :class:`~pycoshark.mongomodels.Commit` id in which this change occured
    :property mode: (:class:`~mongoengine.fields.StringField`) type of file change (e.g., A for added)
    :property size_at_commit: (:class:`~mongoengine.fields.IntField`)  size of the file at commit time
    :property lines_added: (:class:`~mongoengine.fields.IntField`)  number of lines added
    :property lines_deleted: (:class:`~mongoengine.fields.IntField`)  number of lines deleted
    :property is_binary: (:class:`~mongoengine.fields.BooleanField`)  shows, if file is binary
    :property old_file_id: (:class:`~mongoengine.fields.ObjectIdField`) :class:`~pycoshark.mongomodels.File` id of the old file (if it was moved, none otherwise)
    :property induces: (:class:`~mongoengine.fields.ListField`) list of :class:`~mongoengine.fields.DictField` contains change_file_action_id, label and lines of the changing commit to the inducing commit in this FileAction.
    """

    meta = {
        'indexes': [
            '#id',
            'commit_id',
            ('commit_id', 'file_id'),
        ],
        'shard_key': ('id',),
    }

    # PK: file_id, commit_id
    # Shard Key: hashed id. Reasoning: The id is most likely the most queried part. Furthermore, a shard key consisting
    # of commit_id and file_id would be very bad.

    MODES = ('A', 'M', 'D', 'C', 'T', 'R')
    file_id = ObjectIdField(required=True)
    commit_id = ObjectIdField(required=True)
    mode = StringField(max_length=1, required=True, choices=MODES)
    parent_revision_hash = StringField(max_length=50)
    size_at_commit = IntField()
    lines_added = IntField()
    lines_deleted = IntField()
    is_binary = BooleanField()

    # old_file_id is only set, if we detected a copy or move operation
    old_file_id = ObjectIdField()

    induces = ListField(DictField())


class Hunk(Document):
    """
    Hunk class.
    Inherits from :class:`mongoengine.Document`. See: https://en.wikipedia.org/wiki/Diff_utility#Unified_format

    Index: #file_action_id

    ShardKey: #file_action_id

    :property file_action_id: (:class:`~mongoengine.fields.ObjectIdField`) :class:`~pycoshark.mongomodels.FileAction` id to which this hunk belongs
    :property new_start: (:class:`~mongoengine.fields.IntField`)  start line of the new file
    :property new_lines: (:class:`~mongoengine.fields.IntField`)  new line of the new file
    :property old_start: (:class:`~mongoengine.fields.IntField`)  start line in the old file
    :property old_lines: (:class:`~mongoengine.fields.IntField`)  old lines in the new file
    :property content: (:class:`~mongoengine.fields.StringField`) textual change
    :property lines_manual: (:class:`~mongoengine.fields.DictField`) for manual line labels for this hunk, contains information about the different labels of lines and the author, the author is the key and the value is a (:class:`~mongoengine.fields.DictField`) of different label types and their belonging lines. Therefore, the key is the label type and the value is an array of line numbers
    :property lines_verified: (:class:`~mongoengine.fields.DictField`) the verified labels for the lines of the hunk. The key is the label and the value is an array of line numbers
    :property uncorrected_lines_manual: (:class:`~mongoengine.fields.DictField`) copy of uncorrected labels, temporary. Structure is the same as lines_manual
    """

    meta = {
        'indexes': [
            '#file_action_id',
        ],
        'shard_key': ('file_action_id',),
    }

    # PK: id
    # Shard Key: file_action_id. Reasoning: file_action_id is most likely often queried

    file_action_id = ObjectIdField()
    new_start = IntField(required=True)
    new_lines = IntField(required=True)
    old_start = IntField(required=True)
    old_lines = IntField(required=True)
    content = StringField(required=True)
    lines_manual = DictField()
    lines_verified = DictField()
    uncorrected_lines_manual = DictField()


class File(Document):
    """
    File class.
    Inherits from :class:`mongoengine.Document`.

    Index: vcs_system_id

    ShardKey: path, vcs_system_id

    :property vcs_system_id: (:class:`~mongoengine.fields.ObjectIdField`) :class:`~pycoshark.mongomodels.VCSSystem` id to which this file
    :property path: (:class:`~mongoengine.fields.StringField`) path of the file

    """
    meta = {
        'indexes': [
            'vcs_system_id',
        ],
        'shard_key': ('path', 'vcs_system_id',),
    }

    # PK: path, vcs_system_id
    # Shard Key: path, vcs_system_id

    vcs_system_id = ObjectIdField(required=True)
    path = StringField(max_length=300, required=True, unique_with=['vcs_system_id'])


class Tag(Document):
    """
    Tag class.
    Inherits from :class:`mongoengine.Document`.

    Index: commit_id, name, (name, commit_id)

    ShardKey: name, commit_id

    :property vcs_system_id: (:class:`~mongoengine.fields.ObjectIdField`) :class:`~pycoshark.mongomodels.VCSSystem` id to which this tag belongs
    :property name: (:class:`~mongoengine.fields.StringField`) name of the tag
    :property commit_id: (:class:`~mongoengine.fields.ObjectIdField`) :class:`~pycoshark.mongomodels.Commit` id to which this tag belongs
    :property message: (:class:`~mongoengine.fields.StringField`) message of the tagger (if applicable)
    :property tagger_id: (:class:`~mongoengine.fields.ObjectIdField`) :class:`~pycoshark.mongomodels.People` id of the person that created the tag
    :property date: (:class:`~mongoengine.fields.DateTimeField`)  date when the tag was created
    :property date_offset: (:class:`~mongoengine.fields.IntField`)  offset for the date
    :property stored_at: (:class:`~mongoengine.fields.IntField`)  latest time when the tag was created
    :property deleted_at: (:class:`~mongoengine.fields.IntField`)  time when the tag was not found, Null value means that the tag is either recreated or still exists
    :property previous_states: ((:class:`~mongoengine.fields.ListField` of (:class:`~mongoengine.fields.DictField`)) It contains change history for tag.

    """
    meta = {
        'indexes': [
            'commit_id',
            'name',
            ('name', 'commit_id'),
        ],
        'shard_key': ('name', 'commit_id'),
    }

    # PK: commit_id
    # Shard Key: hashed commit_id

    name = StringField(max_length=150, required=True, unique_with=['commit_id'])
    commit_id = ObjectIdField(required=True)
    vcs_system_id = ObjectIdField(required=True)
    message = StringField()
    tagger_id = ObjectIdField()
    date = DateTimeField()
    date_offset = IntField()
    stored_at = DateTimeField()
    deleted_at = DateTimeField()
    previous_states = ListField(DictField())

    def __eq__(self, other):
        return self.commit_id, self.name == other.commit_id, other.name

    def __hash__(self):
        return hash((self.commit_id, self.name))


class People(Document):
    """
    People class.
    Inherits from :class:`mongoengine.Document`.

    ShardKey: email name

    :property email: (:class:`~mongoengine.fields.StringField`) email of the person
    :property name: (:class:`~mongoengine.fields.StringField`) name of the person
    :property username: (:class:`~mongoengine.fields.StringField`) username of the person

    """
    meta = {
        'shard_key': ('email', 'name',)
    }

    # PK: email, name
    # Shard Key: email, name

    email = StringField(max_length=150, required=True, unique_with=['name'])
    name = StringField(max_length=150, required=True)
    username = StringField(max_length=300)

    def __hash__(self):
        return hash(self.name + self.email)


class Commit(Document):
    """
    Commit class.

    Inherits from :class:`mongoengine.Document`.

    Index: vcs_system_id

    ShardKey: revision_hash, vcs_system_id

    :property vcs_system_id: (:class:`~mongoengine.fields.ObjectIdField`) :class:`~pycoshark.mongomodels.VCSSystem` id to which this commit belongs
    :property revision_hash: (:class:`~mongoengine.fields.StringField`) revision hash for this commit
    :property branches: ((:class:`~mongoengine.fields.ListField` of (:class:`~mongoengine.fields.StringField`))  list of branches to which this commit belongs
    :property parents: ((:class:`~mongoengine.fields.ListField` of (:class:`~mongoengine.fields.StringField`))  list of parents (revision hashes) of this commit
    :property author_id: (:class:`~mongoengine.fields.ObjectIdField`) :class:`~pycoshark.mongomodels.People` id of the person that authored this commit
    :property author_date: (:class:`~mongoengine.fields.DateTimeField`)  date of the authored commit
    :property author_date_offset: (:class:`~mongoengine.fields.IntField`)  offset for the author date
    :property committer_id: (:class:`~mongoengine.fields.ObjectIdField`) :class:`~pycoshark.mongomodels.People` id of the person that committed this commit
    :property committer_date: (:class:`~mongoengine.fields.DateTimeField`)  date of the committed commit
    :property committer_date_offset: (:class:`~mongoengine.fields.IntField`)  offset for the committer date
    :property message: (:class:`~mongoengine.fields.StringField`) message of the commit
    :property linked_issue_ids: ((:class:`~mongoengine.fields.ListField` of (:class:`~mongoengine.fields.ObjectIdField`))  :class:`~pycoshark.mongomodels.Issue` ids linked to this commit
    :property code_entity_states: ((:class:`~mongoengine.fields.ListField` of (:class:`~mongoengine.fields.ObjectIdField`))  :class:`~pycoshark.mongomodels.CodeEntityState` code entity states for this commit
    :property labels: (:class:`~mongoengine.fields.DictField`) dictionary of different labels for this commit, is_bugfix etc.
    :property validations: ((:class:`~mongoengine.fields.ListField` of (:class:`~mongoengine.fields.StringField`))  list of different validations on this commit
    :property fixed_issue_ids: ((:class:`~mongoengine.fields.ListField` of (:class:`~mongoengine.fields.ObjectIdField`)) verified :class:`~pycoshark.mongomodels.Issue` ids linked to this commit
    :property szz_issue_ids: ((:class:`~mongoengine.fields.ListField` of (:class:`~mongoengine.fields.ObjectIdField`)) verified :class:`~pycoshark.mongomodels.Issue` issues linked by the SZZ algorithm
    :property stored_date: (:class:`~mongoengine.fields.DateTimeField`) date of the commit stored in database. If this is None then it will store committer_date as initial stored_date
    :property modified_date: (:class:`~mongoengine.fields.DateTimeField`) date of modification of this record. If this is None then it will store current data as initial modified_date
    :property previous_states: ((:class:`~mongoengine.fields.ListField` of (:class:`~mongoengine.fields.DictField`)) It contains change history.
    :property deleted_at: (:class:`~mongoengine.fields.DateTimeField`) date when commit marked as deleted
    """

    meta = {
        'indexes': [
            'vcs_system_id',
        ],
        'shard_key': ('revision_hash', 'vcs_system_id'),
    }

    # PK: revision_hash, vcs_system_id
    # Shard Key: revision_hash, vcs_system_id

    vcs_system_id = ObjectIdField(required=True)
    revision_hash = StringField(max_length=50, required=True, unique_with=['vcs_system_id'])
    branches = ListField(StringField(max_length=500), null=True)
    parents = ListField(StringField(max_length=50))
    author_id = ObjectIdField()
    author_date = DateTimeField()
    author_date_offset = IntField()
    committer_id = ObjectIdField()
    committer_date = DateTimeField()
    committer_date_offset = IntField()
    message = StringField()
    linked_issue_ids = ListField(ObjectIdField())
    code_entity_states = ListField(ObjectIdField())
    labels = DictField()
    validations = ListField(StringField(max_length=50))
    fixed_issue_ids = ListField(ObjectIdField())
    szz_issue_ids = ListField(ObjectIdField())
    modified_date = DateTimeField(default=datetime.now)
    previous_states = ListField(DictField())
    deleted_at = DateTimeField()

class Branch(Document):
    """
    Branch class.

    Inherits from :class:`mongoengine.Document`.

    Index: vcs_system_id

    ShardKey: name, vcs_system_id

    :property vcs_system_id: (:class:`~mongoengine.fields.ObjectIdField`) :class:`~pycoshark.mongomodels.VCSSystem` id to which this branch belongs
    :property commit_id: (:class:`~mongoengine.fields.ObjectIdField`) target commit of the branch (last commit on that branch)
    :property name: (:class:`~mongoengine.fields.StringField`) name of the branch
    :property is_origin_head: (:class:`~mongoengine.fields.BooleanField`) if this branch is the default origin branch (usually master)
    """

    meta = {
        'indexes': [
            'vcs_system_id',
        ],
        'shard_key': ('name', 'vcs_system_id'),
    }

    # PK: name, vcs_system_id
    # Shard Key: name, vcs_system_id

    vcs_system_id = ObjectIdField(required=True)
    commit_id = ObjectIdField(required=True)
    name = StringField(max_length=500, required=True, unique_with=['vcs_system_id'])
    is_origin_head = BooleanField(required=True, default=False)


class Mutation(Document):
    meta = {
        'shard_key': ('location', 'm_type', 'l_num'),
    }

    location = StringField(required=True, unique_with=['m_type', 'l_num'])
    m_type = StringField(required=True)
    l_num = IntField(required=True)
    classification = StringField(null=True)

    def __eq__(self, other):
        return self.m_type, self.location, self.l_num, self.classification == other.m_type, other.location, other.l_num, other.classification

    def __hash__(self):
        return hash((self.m_type, self.location, self.l_num, self.classification))


class MutationResult(EmbeddedDocument):
    mutation_id = ObjectIdField(required=True)
    num_calls = LongField()
    call_depth = LongField()
    result = StringField(required=True)


class TestState(Document):
    """
        TestState class.

        Inherits from :class:`mongoengine.Document`.

        Index: name, commit_id, file_id

        ShardKey: shard_key name, commit_id, file_id

        :property name: (:class:`~mongoengine.fields.StringField`) name of the TestState, e.g. de.ugoe.cs.Class.blub
        :property commit_id: (:class:`~mongoengine.fields.ObjectIdField`) :class:`~pycoshark.mongomodels.Commit` id to which this state belongs
        :property file_id: (:class:`~mongoengine.fields.ObjectIdField`) :class:`~pycoshark.mongomodels.File` id to which this state refers to
        :property metrics: (:class:`~mongoengine.fields.DictField`) metrics for the test state
        :property mutations: ((:class:`~mongoengine.fields.ListField` of Mutations) with extra information about mutations
        """

    meta = {
        'indexes': [
            'commit_id',
        ],
        'shard_key': ('name', 'commit_id', 'file_id'),
    }

    # PK: long_name, commit_id, file_id
    # Shard Key: long_name, commit_id, file_id

    name = StringField(required=True, unique_with=['commit_id', 'file_id'])
    file_id = ObjectIdField(required=True)
    commit_id = ObjectIdField(required=True)
    execution_time = FloatField()
    metrics = DictField()
    mutation_res = ListField(EmbeddedDocumentField(MutationResult), default=list)


class CommitChanges(Document):
    """
        CommitChanges class.

        Inherits from :class:`mongoengine.Document`.

        Index: old_commit_id, new_commit_id

        ShardKey: id

        :property old_commit_id: (:class:`~mongoengine.fields.ObjectIdField`) :class:`~pycoshark.mongomodels.Commit` id to which this state belongs (older in revision system)
        :property new_commit_id: (:class:`~mongoengine.fields.ObjectIdField`) :class:`~pycoshark.mongomodels.Commit` id to which this state belongs (newer in revision system)
        :property classification: (:class:`~mongoengine.fields.DictField`) classification for the changes
        """

    meta = {
        'indexes': [
            'old_commit_id',
            'new_commit_id'
        ],
        'shard_key': ('id', ),
    }

    # PK: old_commit_id, new_commit_id
    # Shard Key: id

    old_commit_id = ObjectIdField(required=True, unique_with=['new_commit_id'])
    new_commit_id = ObjectIdField(required=True)
    classification = DictField()


class CodeEntityState(Document):
    """
    CodeEntityState class.
    Inherits from :class:`mongoengine.Document`.

    Index: s_key, commit_id, file_id

    ShardKey: shard_key (sha1 hash of long_name, commit_id, file_id)

    :property s_key: (:class:`~mongoengine.fields.StringField`) shard key (sha1 hash of long_name, commit_id and file_id), as they can get too long for the normal shard key
    :property long_name: (:class:`~mongoengine.fields.StringField`) long name of the code entity state (e.g., package1.package2.Class)
    :property commit_id: (:class:`~mongoengine.fields.ObjectIdField`) :class:`~pycoshark.mongomodels.Commit` id to which this state belongs
    :property file_id: (:class:`~mongoengine.fields.ObjectIdField`) :class:`~pycoshark.mongomodels.File` id to which this state refers to
    :property linter: (:class:`~mongoengine.fields.ListField`) of (:class:`~mongoengine.fields.DictField`) refers to warning from linter. Has a line number and a type
    :property ce_parent_id: (:class:`~mongoengine.fields.ObjectIdField`) :class:`~pycoshark.mongomodels.CodeEntityState` id which is the parent of this state
    :property cg_ids: ((:class:`~mongoengine.fields.ListField` of (:class:`~mongoengine.fields.ObjectIdField`))  :class:`~pycoshark.mongomodels.CodeGroupState` ids to which this state belongs
    :property ce_type: (:class:`~mongoengine.fields.StringField`) type of this state (e.g., class)
    :property imports: ((:class:`~mongoengine.fields.ListField` of (:class:`~mongoengine.fields.StringField`))  list of imports of this code entity state
    :property start_line: (:class:`~mongoengine.fields.IntField`)  line, where the code entity starts
    :property end_line: (:class:`~mongoengine.fields.IntField`)  line, where the code entity ends
    :property start_column: (:class:`~mongoengine.fields.IntField`)  column, where the code entity starts
    :property end_column: (:class:`~mongoengine.fields.IntField`)  column, where the code entity ends
    :property metrics: (:class:`~mongoengine.fields.DictField`) dictionary of different metrics for this code entity state

    """
    meta = {
        'indexes': [
            'commit_id',
            'file_id',
        ],
        'shard_key': ('s_key',)
    }

    # PK: long_name, commit_id, file_id
    # Shard Key: shard_key
    s_key = StringField(required=True, unique=True)
    long_name = StringField(required=True)
    commit_id = ObjectIdField(required=True)
    file_id = ObjectIdField(required=True)
    linter = ListField(DictField())
    test_type = DictField()
    ce_parent_id = ObjectIdField()
    cg_ids = ListField(ObjectIdField())
    ce_type = StringField()
    imports = ListField(StringField())
    start_line = IntField()
    end_line = IntField()
    start_column = IntField()
    end_column = IntField()
    metrics = DictField()

    def __repr__(self):
        return "<CodeEntityState s_key:%s long_name:%s commit_id:%s file_id:%s test_type:%s ce_parent_id:%s " \
               "cg_ids:%s ce_type:%s imports:%s start_line:%s end_line:%s start_column:%s end_column: %s metrics: %s>" % \
               (self.s_key, self.long_name, self.commit_id, self.file_id, self.test_type, self.ce_parent_id,
                self.cg_ids, self.ce_type, self.imports, self.start_line, self.end_line, self.start_column,
                self.end_column, self.metrics)

    @staticmethod
    def calculate_identifier(long_name, commit_id, file_id):
        concat_string = long_name + str(commit_id) + str(file_id)
        return hashlib.sha1(concat_string.encode('utf-8')).hexdigest()

    def identifier(self):
        return self.calculate_identifier(self.long_name, self.commit_id, self.file_id)


class CodeGroupState(Document):
    """
    CodeGroupState class.
    Inherits from :class:`mongoengine.Document`.

    Index: s_key, commit_id

    ShardKey: shard_key (sha1 hash of long_name, commit_id)

    :property s_key: (:class:`~mongoengine.fields.StringField`) shard key (sha1 hash of long_name, commit_id), as they can get too long for the normal shard key
    :property long_name: (:class:`~mongoengine.fields.StringField`) long name of the code group state (e.g., package1.package2)
    :property commit_id: (:class:`~mongoengine.fields.ObjectIdField`) :class:`~pycoshark.mongomodels.Commit` id to which this state belongs
    :property cg_parent_ids: ((:class:`~mongoengine.fields.ListField` of (:class:`~mongoengine.fields.ObjectIdField`)) :class:`~pycoshark.mongomodels.CodeGroupState` ids which are the parent of this state
    :property cg_type: (:class:`~mongoengine.fields.StringField`) type of this state (e.g., package)
    :property metrics: (:class:`~mongoengine.fields.DictField`) dictionary of different metrics for this code group state

    """
    meta = {
        'indexes': [
            'commit_id'
        ],
        'shard_key': ('s_key',)
    }

    s_key = StringField(required=True, unique=True)
    long_name = StringField(require=True)
    commit_id = ObjectIdField(required=True)
    cg_parent_ids = ListField(ObjectIdField())
    cg_type = StringField()
    metrics = DictField()

    @staticmethod
    def calculate_identifier(long_name, commit_id):
        concat_string = long_name + str(commit_id)
        return hashlib.sha1(concat_string.encode('utf-8')).hexdigest()

    def identifier(self):
        return self.calculate_identifier(self.long_name, self.commit_id)


class CloneInstance(Document):
    """
    CloneInstance class.
    Inherits from :class:`mongoengine.Document`.

    Index: commit_id, file_id

    ShardKey: name, commit_id, file_id


    :property name: (:class:`~mongoengine.fields.StringField`) name of the clone (e.g., C1220)
    :property commit_id: (:class:`~mongoengine.fields.ObjectIdField`) :class:`~pycoshark.mongomodels.Commit` id to which this clone instance belongs
    :property file_id: (:class:`~mongoengine.fields.ObjectIdField`) :class:`~pycoshark.mongomodels.File` id to which this clone instance refers to
    :property start_line: (:class:`~mongoengine.fields.IntField`)  line, where the code clone starts
    :property end_line: (:class:`~mongoengine.fields.IntField`)  line, where the code clone ends
    :property start_column: (:class:`~mongoengine.fields.IntField`)  column, where the code clone starts
    :property end_column: (:class:`~mongoengine.fields.IntField`)  column, where the code clone ends
    :property clone_class: (:class:`~mongoengine.fields.StringField`) class to which this clone instance belongs (e.g., C12)
    :property clone_instance_metrics: (:class:`~mongoengine.fields.DictField`) dictionary of different metrics for the clone instance
    :property clone_class_metrics: (:class:`~mongoengine.fields.DictField`) dictionary of different metrics for the clone class

    """
    meta = {
        'indexes': [
            'commit_id',
            'file_id'
        ],
        'shard_key': ('name', 'commit_id', 'file_id'),
    }

    # PK: name, commit_id, file_id
    # Shard Key: name, commit_id, file_id

    name = StringField(required=True, unique_with=['commit_id', 'file_id'])
    commit_id = ObjectIdField(required=True)
    file_id = ObjectIdField(required=True)
    start_line = IntField(required=True)
    end_line = IntField(required=True)
    start_column = IntField(required=True)
    end_column = IntField(required=True)
    clone_instance_metrics = DictField(required=True)
    clone_class = StringField(required=True)
    clone_class_metrics = DictField(required=True)


class MynbouData(Document):
    """
    MynbouData
    Inherits from :class:`mongoengine.Document`.

    Index: vcs_sytem_id

    ShardKey: name, vcs_system_id


    :property vcs_system_id: (:class:`~mongoengine.fields.ObjectIdField`) :class:`~pycoshark.mongomodels.VCSSystem` id to which this clone instance belongs
    :property name: (:class:`~mongoengine.fields.StringField`) identifier of the product, e.g, the version 1.3
    :property path_approach: (:class:`~mongoengine.fields.StringField`) name of the approach used for detecting the path for labeling
    :property metric_approach: (:class:`~mongoengine.fields.StringField`) name of the approach used for metric creation and aggregation
    :property bugfix_label: (:class:`~mongoengine.fields.StringField`) name of the commit label that is used to determine bug-fixing commits.
    :property file: (:class:`~mongoengine.fields.FileField`) JSON File containing the product.
    :property last_updated: (:class:`~mongoengine.fields.DateTimeField`) time of creation of this product

    """
    meta = {
        'indexes': [
            'vcs_system_id'
        ],
        'shard_key': ('name', 'vcs_system_id'),
    }

    # PK: name, vcs_system_id, path_approach, bugfix_label, metrics_approach
    # Shard Key: name, vcs_system_id

    vcs_system_id = ObjectIdField(required=True)
    name = StringField(required=True, unique_with=['vcs_system_id', 'path_approach', 'bugfix_label', 'metric_approach'])
    path_approach = StringField(required=True)
    bugfix_label = StringField(required=True)
    metric_approach = StringField(required=True)
    file = FileField()
    last_updated = DateTimeField(default=None)


class StaticWarning(Document):
    """
    StaticWarning class.
    Inherits from :class:`mongoengine.Document`.

    Holds multiple linter results, e.g., PMD_6.2 including line number, warning type and warning message.
    Format [{'version': 'PMD_6.2', 'ln': 15, 'l_ty': 'UEO', 'msg': 'Unused something'}]

    Index: commit_id, file_id

    :property commit_id: (:class:`~mongoengine.fields.ObjectIdField`) :class:`~pycoshark.mongomodels.Commit` id to which this state belongs
    :property file_id: (:class:`~mongoengine.fields.ObjectIdField`) :class:`~pycoshark.mongomodels.File` id to which this state refers to
    :property linter: (:class:`~mongoengine.fields.ListField`) of (:class:`~mongoengine.fields.DictField`) refers to warning from linter.
    :property metrics: (:class:`~mongoengine.fields.DictField`) dictionary of additional metrics, e.g., LLoC
    """
    meta = {
        'indexes': [
            'commit_id',
            'file_id',
        ],
        'shard_key': ('commit_id', 'file_id'),
    }

    commit_id = ObjectIdField(required=True)
    file_id = ObjectIdField(required=True)
    linter = ListField(DictField())
