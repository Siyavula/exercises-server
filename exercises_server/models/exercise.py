from sqlalchemy import (
    Column,
    DateTime,
    String,
    Binary,
    PrimaryKeyConstraint,
    func,
    event,
    )
from sqlalchemy.orm import relationship, backref

import json, base64

from exercises_server.models.support import Base, DBSession
from exercises_server.utils import now_utc, force_utc

import logging
log = logging.getLogger(__name__)


class Exercise(Base):
    __tablename__ = "exercises"

    id = Column(String, nullable=False)
    version = Column(String, nullable=False)
    data = Column(Binary, nullable=False)
    created = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    last_updated = Column(DateTime(timezone=True))

    __table_args__ = (PrimaryKeyConstraint('id', 'version', name='exercises_primary_key'),)

    def __json__(self, request):
        return {
            'id': self.id,
            'version': self.version,
            'data_b64': base64.b64encode(self.data),
            'created': self.created.isoformat(),
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
        }


    def update(self, data):
        self.data = data
        self.last_updated = now_utc()


    def __str__(self):
        return "<Exercise id=%s, version=%s, created=%s, last_updated=%s>" % (self.id, self.version, self.created, self.last_updated)


    @classmethod
    def get_by_id(cls, id, version):
        query = DBSession.query(Exercise)
        return query.get((id, version))


    @classmethod
    def inserted(cls, mapper, connection, target):
        # ensure timestamps have timezones (SQLite doesn't support timezones)
        target.created = force_utc(target.created)
        target.last_updated = force_utc(target.last_updated)


    @classmethod
    def loaded(cls, target, context):
        # ensure timestamps have timezones (SQLite doesn't support timezones)
        target.created = force_utc(target.created)
        target.last_updated = force_utc(target.last_updated)


event.listen(Exercise, 'after_insert', Exercise.inserted)
event.listen(Exercise, 'load', Exercise.loaded)
