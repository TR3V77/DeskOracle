"""
Canonical ticket category names.

Shared by the triage engine, the analytics evaluation, and the synthetic
data generator so the three can't silently drift apart -- a typo or a
renamed category in only one of those places used to fail silently
(e.g. a confusion matrix column just showing zero matches instead of
raising an error).
"""

NETWORK_VPN = "Network_VPN"
ACCOUNT_ACCESS = "Account_Access"
HARDWARE = "Hardware"
SOFTWARE = "Software"
PRINTER = "Printer"
EMAIL = "Email"
SECURITY = "Security"
OTHER = "Other"

# Order matches the rule-based fallback classifier's match priority: more
# specific/urgent categories are checked before general ones. "Other" is
# the classifier's default and deliberately excluded from this list.
CATEGORIES = [SECURITY, NETWORK_VPN, ACCOUNT_ACCESS, PRINTER, EMAIL, HARDWARE, SOFTWARE]
