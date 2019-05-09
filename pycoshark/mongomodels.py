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
    """

    # PK: _id
    ce_state = DictField()
    commit_id = ObjectIdField()
    description = StringField()
    parent_commit_ce_states = ListField(DictField())
    type = StringField()


class Identity(Document):
    meta = {
        'indexes': [
            '#id',
        ],
        'shard_key': ('id', ),
    }

    people = ListField(ObjectIdField())


class TravisJob(EmbeddedDocument):
    tr_id = IntField(unique=True)
    allow_failure = BooleanField(required=True)
    number = StringField(required=True)
    state = StringField(max_length=8, required=True)
    started_at = DateTimeField()
    finished_at = DateTimeField()
    stages = ListField(StringField())
    metrics = DictField()
    config = DictField()

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
    jobs = ListField(EmbeddedDocumentField(TravisJob), default=list)

    def __repr__(self):
        return "<TravisBuild vcs_system_id:%s commit_id:%s number:%s duration:%s event_type:%s " \
               "pr_number:%s started_at:%s finished_at:%s stages:%s jobs:%s>" % \
               (self.vcs_system_id, self.commit_id, self.number, self.duration, self.event_type, self.pr_number,
                self.started_at, self.finished_at, self.stages, self.jobs)


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
    original_time_estimate=IntField()
    environment = StringField()
    platform = StringField()

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
    :property inducig: (:class:`~mongoengine.fields.ListField`) list of :class:`~mongoengine.fields.DictField` contains change_file_action_id, label and lines of the changing commit to the inducing commit in this FileAction.
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
    :property committer_id: (:class:`~mongoengine.fields.ObjectIdField`) :class:`~pycoshark.mongomodels.People` id of the person that comitted this commit
    :property committer_date: (:class:`~mongoengine.fields.DateTimeField`)  date of the committed commit
    :property committer_date_offset: (:class:`~mongoengine.fields.IntField`)  offset for the committer date
    :property message: (:class:`~mongoengine.fields.StringField`) message of the commit
    :property linked_issue_ids: ((:class:`~mongoengine.fields.ListField` of (:class:`~mongoengine.fields.ObjectIdField`))  :class:`~pycoshark.mongomodels.Issue` ids linked to this commit
    :property code_entity_states: ((:class:`~mongoengine.fields.ListField` of (:class:`~mongoengine.fields.ObjectIdField`))  :class:`~pycoshark.mongomodels.CodeEntityState` code entity states for this commit
    :property labels: (:class:`~mongoengine.fields.DictField`) dictionary of different labels for this commit, is_bugfix etc.
    :property validations: ((:class:`~mongoengine.fields.ListField` of (:class:`~mongoengine.fields.StringField`))  list of different validations on this commit
    :property fixed_issue_ids: ((:class:`~mongoengine.fields.ListField` of (:class:`~mongoengine.fields.ObjectIdField`)) verified :class:`~pycoshark.mongomodels.Issue` ids linked to this commit
    :property szz_issue_ids: ((:class:`~mongoengine.fields.ListField` of (:class:`~mongoengine.fields.ObjectIdField`)) verified :class:`~pycoshark.mongomodels.Issue` issues linked by the SZZ algorithm
  
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
        concat_string = long_name+str(commit_id)+str(file_id)
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
        concat_string = long_name+str(commit_id)
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
