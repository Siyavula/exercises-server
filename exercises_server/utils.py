from datetime import *

from dateutil.parser import parse
from dateutil.tz import tzutc


def parse_iso8601(s, field=None):
    """
    Parse a string, possibly None, from ISO8601
    into a UTC-based datetime instance.

    If the value is None, None is returned.

    If the value is bad, a ValueError with a user-friendly
    error is raised, including the field name +field+ if given.
    """
    if not s:
        return None

    try:
        dt = parse(s)
        return dt.astimezone(tzutc())
    except ValueError:
        if field:
            raise ValueError("The ISO8601 timestamp '%s' for %s is not valid" % (s, field))
        else:
            raise ValueError("The ISO8601 timestamp '%s' is not valid" % s)


def now_utc():
    """
    Return now in UTC, with second precision.
    """
    return datetime.now(tzutc()).replace(microsecond=0)


def force_utc(dt):
    """
    If the given datetime +dt+ does not have a timezone associated with it,
    force it to be UTC.
    """
    if dt and not dt.tzinfo:
        return dt.replace(tzinfo=tzutc())
    else:
        return dt


def parse_json_body(json_body, required_keys=[], optional_keys=[], defaults={}):
    from pyramid.httpexceptions import HTTPBadRequest

    missing_keys = set(required_keys) - set(json_body.keys())
    if len(missing_keys) > 0:
        raise HTTPBadRequest("JSON body has missing required keys: " + repr(list(missing_keys)))

    extra_keys = set(json_body.keys()) - set(required_keys) - set(optional_keys) - set(defaults.keys())
    if len(extra_keys) > 0:
        raise HTTPBadRequest("JSON body has extra keys: " + repr(list(extra_keys)))

    params = dict(defaults)
    params.update(json_body)
    return params
