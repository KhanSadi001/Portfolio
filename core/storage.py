from whitenoise.storage import CompressedManifestStaticFilesStorage


class ForgivingManifestStorage(CompressedManifestStaticFilesStorage):
    """Hashed, cache-busting file names, but never crash a page if the manifest is missing."""
    manifest_strict = False
