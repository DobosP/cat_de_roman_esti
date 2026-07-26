"""Accounts app: profile, consent, private score copy, repeats, and verified records.

Only installed when ``CAT_ACCOUNTS_ENABLED=1``. The stateless anonymous arcade never
imports this package. See ``web/settings.py`` for the mode switch and ``docs/compliance/``
for the data-protection posture this app implements (age gate, consent record, DSAR delete).
"""
