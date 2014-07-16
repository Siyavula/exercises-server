from sqlalchemy import (
    Column,
    String,
    Enum,
    PrimaryKeyConstraint,
    )
from sqlalchemy.orm import relationship, backref

import json

from exercises_server.models.support import Base, DBSession
from exercises_server.utils import now_utc, force_utc

import logging
log = logging.getLogger(__name__)


class CurrentVersion(Base):
    __tablename__ = "current_version"

    branch = Column(Enum('testing', 'published', name="BranchName"), nullable=False)
    id = Column(String, nullable=False)
    version = Column(String, nullable=False)

    __table_args__ = (PrimaryKeyConstraint('branch', 'id', name='current_version_primary_key'),)

    def __str__(self):
        return "<CurrentVersion, branch=%s, id=%s, version=%s>" % (self.branch, self.id, self.version)


    @classmethod
    def get_by_id(cls, branch, id):
        query = DBSession.query(CurrentVersion)
        return query.get((branch, id))
