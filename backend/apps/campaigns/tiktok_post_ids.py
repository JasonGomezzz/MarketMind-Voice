"""Normalize only IDs from authenticated Content Posting responses/events."""
import re
from urllib.parse import urlsplit


def public_post_id(value):
    if type(value) is int and 0 < value <= 2**63 - 1:
        return str(value)
    if isinstance(value, str) and re.fullmatch(r'[0-9]{1,19}', value) and 0 < int(value) <= 2**63 - 1:
        return value
    return None


def parse_publication(value):
    """Accept only an ID or a canonical public TikTok post URL, never fetch URLs."""
    if not isinstance(value, str) or len(value) > 512:
        return None, ''
    value = value.strip()
    identifier = public_post_id(value)
    if identifier:
        return identifier, ''
    try:
        url = urlsplit(value)
        match = re.fullmatch(r'/@[A-Za-z0-9._-]{1,64}/(?:photo|video)/([0-9]{1,19})/?', url.path)
        if url.scheme == 'https' and url.netloc in ('www.tiktok.com', 'tiktok.com') and match:
            identifier = public_post_id(match[1])
            if identifier:
                return identifier, 'https://www.tiktok.com' + url.path.rstrip('/')
    except ValueError:
        pass
    return None, ''


def effective_public_post_ids(upload):
    ids = upload.public_post_ids
    if (not isinstance(ids, list) or any(not isinstance(i, str) or public_post_id(i) != i for i in ids)
            or len(set(ids)) != len(ids)):
        return ids
    link = getattr(upload, 'publication_link', None)
    return sorted(set(ids + ([link.post_id] if link else [])))
