# Verification record

Date: 2026-09-22. This file records observed results and must be updated as additional checks finish.

| Check | Result |
|---|---|
| Isolated Python 3.13 environment | Created at `.venv` |
| Unit/API tests without a running database | 22 passed; live integration test skipped intentionally |
| Docker image builds | Both application images built successfully on Linux/amd64 |
| Compose runtime health | All three project containers healthy |
| Real PostgreSQL + inter-service HTTP integration | All 23 tests passed against localhost:18080 |
| New kind Kubernetes cluster | Created successfully; kind 0.33.0, Kubernetes 1.37.0 |
| Docker Hub publication | Both v1 images pushed; manifests verified; fresh Kubernetes nodes pulled without image credentials |
| Kubernetes application deployment | Dashboard 2/2, Tasks 2/2, PostgreSQL 1/1; all 23 tests passed against localhost:18081 |
| Independent scale verification | Each application Deployment scaled from 2 to 3 while the other's count stayed unchanged; restored to 2 |
| PostgreSQL Pod replacement persistence | A unique task survived rollout restart of only the project database Deployment |
| Dedicated Kubernetes node restart persistence | A unique task survived restart of cloudboard-coursework-control-plane; old container ID/status unchanged |
| Real browser interaction | Edge/Playwright: create, move through both statuses, reload, delete, literal XSS input, mobile width check; no page errors |
| GitHub repository | Source uploaded to https://github.com/runlinlong/cloudboard |
| Local automated reference video | Generated: 9 minutes 22 seconds, 1280×800 MP4, synthetic English narration; complete audio/video decode check passed; not uploaded |
| Final student demonstration recording | Student will re-record personally using the local reference; not yet submitted |

Original environment was inspected read-only: existing Home Assistant container `strange_kirch` was already exited when inspected. No command in this project stops, removes, reconfigures or starts that container, prunes Docker data, resets Docker/WSL, or edits the global kubeconfig. New workloads share host CPU/memory/disk and may affect available resources.

An ordinary local node restart is not a proof of survival after cluster deletion, factory reset or disk failure. No load test, public Internet security audit or high-availability claim is implied by these checks.

## Published image identifiers

- `docker.io/runlinlong/cloudboard-tasks:v1` — `sha256:15748df963a28a82a9f4bfb3fc408bca5acb6dc08bffa04600a2c48790c3deb2`
- `docker.io/runlinlong/cloudboard-dashboard:v1` — `sha256:6319dba587c548cc6241b0bb6978b3f54ab9b8694534350cfa63b16dd9588ca7`
- Both are Linux/amd64 images. Running Pod image IDs were checked against these registry digests.

Raw local evidence is saved under `artifacts/`: `kubernetes-tests.txt`, `browser-tests.txt`, `scaling-persistence.txt`, `node-restart.txt`, `kubernetes-status.txt`, `deployed-images.txt`, `tasks-logs.txt`, `dashboard-logs.txt`, and desktop/mobile screenshots. Generated files are not automatically committed to the source repository.

Selected non-secret text outputs are also published in [docs/evidence](evidence/README.md). Both Docker Hub repositories returned `is_private: false` from the unauthenticated public API; the GitHub repository returned `private: false`.

The local video is `artifacts/cloudboard-demo.mp4` (16,485,948 bytes). Measured duration: 562.32 seconds. It contains actual browser interactions, command-output captures, YAML excerpts, independent scaling and database replacement. Audio is synthetic narration; it is not a recording of the student speaking. A local transcript is in `artifacts/video-transcript.md`. Neither video nor transcript was uploaded, as requested. Final deployment counts were rechecked at 2 dashboard, 2 task and 1 PostgreSQL replicas.
