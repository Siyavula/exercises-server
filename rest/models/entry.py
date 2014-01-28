import re

from sqlalchemy import (
    Column,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
    event,
    )
from sqlalchemy.orm import relationship, backref

from json import loads, dumps

from rest.models.support import Base, DBSession
from rest.utils import now_utc, force_utc
from rest.errors import EntryInvalid, EntryLocked

import logging
log = logging.getLogger(__name__)


class Entry(Base):
    __tablename__ = "entries"

    id = Column(Integer, primary_key=True)
    data = Column(Text)
    locked_by = Column(String)

    # state change timestamps
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    last_modified_at = Column(DateTime(timezone=True))
    locked_at = Column(DateTime(timezone=True))

    # state change request ids
    created_request_id = Column(String)
    last_modified_request_id = Column(String)
    locked_request_id = Column(String)

    def __json__(self, request):
        return {
            'id': self.id,
            'data': loads(self.data) if self.data else None,
            'locked': self.locked_by != None,
            'created_at': self.created_at.isoformat(),
            'created_request_id': self.created_request_id,
            'last_modified_at': self.last_modified_at.isoformat() if self.last_modified_at else None,
            'last_modified_request_id': self.last_modified_request_id,
            'locked_at': self.locked_at.isoformat() if self.locked_at else None,
            'locked_request_id': self.locked_request_id,
        }


    def locked_for(self, by):
        return (self.locked_by != None) and (self.locked_by != by)


    def lock(self, by, request_id):
        """
        Attempt to lock this entry. Raises EntryLocked if the entry
        has already been locked by someone else. Silently does nothing
        if specified agent has already locked this entry.
        """
        if self.locked_for(by):
            raise EntryLocked('This entry has been locked by someone else.')
        self.locked_by = by
        self.locked_at = now_utc()
        self.locked_request_id = request_id


    def unlock(self, by):
        """
        Attempt to unlock this entry. Raises EntryLocked if the entry
        has already been locked by someone else. Silently does nothing
        if the entry is already unlocked.
        """
        if self.locked_for(by):
            raise EntryLocked('This entry has been locked by someone else.')
        self.locked_by = None
        self.locked_at = None
        self.locked_request_id = None


    def update(self, by, data, request_id):
        if self.locked_for(by):
            raise EntryLocked('This entry has been locked by someone else.')
        self.data = dumps(data)
        self.last_modified_at = now_utc()
        self.last_modified_request_id = request_id


    def delete(self, by):
        if self.locked_for(by):
            raise EntryLocked('This entry has been locked by someone else.')


    def __str__(self):
        return "<Entry id=%s, locked_by=%s>" % (self.id, self.locked_by)


    @classmethod
    def get_by_id(cls, id):
        """
        Get an entry from the db by id.

        If +for_update+ is True, the query is will acquire
        an update lock on the row.
        """
        query = DBSession.query(Entry)
        return query.get(id)


    @classmethod
    def create(cls, data, request_id):
        """
        Create a new Entry from a json document.
        """
        entry = Entry()
        entry.data = dumps(data)
        entry.created_request_id = request_id
        return entry


    @classmethod
    def inserted(cls, mapper, connection, target):
        # ensure timestamps have timezones (SQLite doesn't support timezones)
        target.created_at = force_utc(target.created_at)
        target.last_modified_at = force_utc(target.last_modified_at)
        target.locked_at = force_utc(target.locked_at)


    @classmethod
    def loaded(cls, target, context):
        # ensure timestamps have timezones (SQLite doesn't support timezones)
        target.created_at = force_utc(target.created_at)
        target.last_modified_at = force_utc(target.last_modified_at)
        target.locked_at = force_utc(target.locked_at)


event.listen(Entry, 'after_insert', Entry.inserted)
event.listen(Entry, 'load', Entry.loaded)
