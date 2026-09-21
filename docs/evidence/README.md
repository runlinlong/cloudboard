# Captured verification output

These text files contain observed output from the Cloudboard cluster on 2026-09-22. They are published to make the claims in [VERIFICATION.md](../VERIFICATION.md) inspectable.

- `kubernetes-tests.txt`: 23 tests passed against the Kubernetes NodePort.
- `browser-tests.txt`: real Edge browser interaction and layout checks.
- `scaling-persistence.txt`: independent scale operations and PostgreSQL Pod replacement.
- `node-restart.txt`: persistence across restart of this project's dedicated kind node and unchanged original coursework container ID/status.
- `kubernetes-status.txt`: resources after the node restart.
- `deployed-images.txt`: running image references and registry digests.

These are snapshots, not monitoring data or a claim of current public hosting. Cluster addresses and generated Pod names are local demonstration values. No secrets, kubeconfig, or user credentials are included.
