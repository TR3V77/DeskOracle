# VPN Connection Failure

Category: Network_VPN

Symptoms: Unable to connect to corporate VPN, "authentication failed" errors, VPN client hangs on connecting.

Resolution steps:
1. Confirm the employee's network credentials have not expired (password resets can break saved VPN credentials).
2. Restart the VPN client and the local network adapter.
3. Check that the VPN client is on the latest approved version; outdated clients are the top cause of handshake failures.
4. Verify the corporate firewall/VPN gateway is not under a scheduled maintenance window.
5. If multi-factor authentication push notifications are not arriving, confirm the MFA app is not rate-limited.

Escalate to Network Engineering if the gateway itself is timing out for multiple users at once.
