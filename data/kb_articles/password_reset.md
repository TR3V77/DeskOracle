# Password Reset / Account Lockout

Category: Account_Access

Symptoms: Employee locked out of Windows login or SSO portal, forgot password, account shows as locked in directory.

Resolution steps:
1. Verify identity per standard IT verification policy before resetting.
2. Use the self-service password reset portal if the account is not locked, otherwise unlock via the directory admin console.
3. Force a password change at next login.
4. If lockouts are repeated within a short window, check for a cached credential on a mobile device or mapped drive causing repeated failed attempts.
5. Remind employee of the 90-day password rotation policy.
