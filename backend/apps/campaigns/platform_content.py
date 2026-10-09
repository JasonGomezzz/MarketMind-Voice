"""Saved platform copies; legacy campaigns retain their approved content."""
from twitter_text import parse_tweet


def platforms(campaign):
    return campaign.plataformas or [campaign.plataforma]


def platform_copy(campaign, platform):
    return (campaign.textos_por_plataforma or {}).get(platform, campaign.texto_generado) or ''


def content_errors(campaign):
    errors = {}
    for platform in platforms(campaign):
        text = platform_copy(campaign, platform)
        if not text.strip():
            errors[platform] = 'El texto no puede estar vacío.'
        elif platform == 'twitter' and (len(text) > 10000 or not parse_tweet(text).valid):
            errors[platform] = 'X permite 280 caracteres ponderados. Edita esta versión.'
        elif platform == 'instagram' and len(text) > 2200:
            errors[platform] = 'Instagram permite 2200 caracteres.'
    return errors
