# Cloudboard — architecture and trade-offs (AI-assisted review draft)

This is reference material to inspect and rewrite in accordance with the course policy, not a claim of student authorship. See AI-DISCLOSURE.md.

## Application and assumed business context

Cloudboard lets a small project team create tasks with priorities, move them through To do / In progress / Done, and view completion statistics. It is intentionally too small to justify microservices commercially. For the scaling exercise, assume a larger hosted task-management business with many users and a dashboard viewed more frequently than tasks are edited. The implementation is a single shared workspace; multi-tenant isolation is an assumed future requirement, not a delivered feature.

## Component-to-service mapping

| Software component | Microservice / deployment | Responsibility and access |
|---|---|---|
| Browser interface | Dashboard | Serves HTML/CSS/JS and receives browser HTTP requests |
| REST gateway and summary computation | Dashboard | Python requests calls task REST API; derives totals and completion rate at `/api/dashboard` |
| Task domain logic / persistence adapter | Tasks | Validates task input, exposes CRUD REST endpoints, executes parameterized SQL |
| Persistent data store | PostgreSQL | Separate single-replica database Deployment, internal Service, mounted PVC |

The two Python services run in separate images and Deployments. They do not share source imports at runtime, process memory, filesystem task data or browser sessions. Both application microservices expose REST APIs. PostgreSQL is the separate storage component; the task service accesses it using SQL and exposes the task data through REST.

## Interaction and patterns

The browser requests the dashboard through a Kubernetes NodePort Service. Browser JavaScript uses same-origin JSON endpoints. The dashboard is a **backend for frontend / API gateway**: it makes bounded HTTP calls to the task service using Kubernetes DNS (`http://tasks:8001`) and computes the progress summary. A task request travels browser → dashboard → task API → PostgreSQL; the response returns in reverse. The dashboard has no database credentials or direct SQL connection.

Kubernetes Services supply stable discovery addresses and route requests to ready replicas. Separate Deployments supply independent horizontal scaling and rolling updates. The database has one replica and uses a Recreate strategy to avoid two independent PostgreSQL processes writing the same data directory. Stateless application replicas put durable state in PostgreSQL, so adding or replacing replicas does not lose tasks. Atomic SQL operations handle concurrent writes; conflicting status edits use last-writer-wins semantics.

Both services expose liveness endpoints. Task readiness tests the database, while task liveness does not: a database outage should not trigger endless application restarts. The dashboard stays ready to serve the UI and a friendly 503 when upstream is unavailable. HTTP connect/read timeouts bound upstream waits. Writes are not automatically retried because a lost response could otherwise create duplicate tasks. Startup retries allow the database to become available, and an advisory lock serializes initial schema creation across replicas. Production schema changes should use explicit migrations.

## Benefits and business implications

Independent scaling permits more dashboard capacity without proportionally replicating every component, and independent releases can reduce coordination between teams. Container images make packaging repeatable, and Kubernetes replaces failed application Pods. Resource requests and limits make scheduling and capacity needs explicit. Separation of database credentials limits what a compromised dashboard can access directly.

These benefits cost engineering time, infrastructure memory, network hops and operational effort. For the actual small board, a single application and a database would be cheaper and easier to maintain. The microservices split is educational; expected traffic or organizational independence must justify it in a real business. More replicas do not guarantee more throughput: this dashboard currently reads all tasks, and a single PostgreSQL instance eventually limits the whole system. Scaling without measurement can increase database load and cloud costs without improving latency.

## Challenges, security and mitigation

| Challenge | Present implementation | Remaining work for production |
|---|---|---|
| SQL injection / invalid data | Parameterized SQL, UUID validation, bounded title length, priority/status allowlists, database constraints, 16 KiB request cap | Pagination, abuse protection and load testing |
| Browser script injection | Task titles assigned with DOM `textContent`, restrictive same-origin CSP, nosniff and frame denial | Security review and authentication-related CSRF controls when sessions are introduced |
| Secrets | Random password generated locally; `.env` ignored; Kubernetes Secret injected only where needed; password not logged | Encryption at rest, narrow RBAC, external secret manager and credential rotation |
| Excess privileges | Non-root Python images, dropped capabilities, read-only root filesystems, no service-account token mounts | Restrict database application role; image scanning, signed images and immutable digests |
| Public access | Local kind port bound to 127.0.0.1; database and task API have internal Services | Authentication, per-user authorization, HTTPS ingress and rate limits before Internet exposure |
| Network isolation | Separate services and no host-published database port | NetworkPolicies with a CNI that actually enforces them; internal Services alone do not prevent lateral access |
| Dependency failure | Timeouts, readiness probes, safe 503 responses, request duration/status/instance logs | Central monitoring, traces, backoff/circuit breaking if justified; a lost response to POST remains ambiguous |
| Data loss / downtime | PVC independent of Deployment; Retain reclaim policy; one DB replica | Off-machine backups with restore tests, durable cloud disks, optional managed HA database |
| Concurrent edits | Transactional SQL statements and shared database | Optimistic concurrency/version checks where lost updates are unacceptable |

There is no authentication or TLS in the delivered local demo: any visitor can read and modify every task. The initial PostgreSQL role is an owner/superuser in this minimal setup. Neither the local cluster nor replica counts provide host-level availability: all Pods share one machine. A single database is permitted by the assignment but is still a single point of failure.

## Persistence boundary

PersistentVolumeClaims separate the lifetime of data from that of Pods and Deployments. The local kind provider stores data on node storage, which persists across ordinary node-container stop/start or restart. `Retain` prevents automatic underlying volume disposal when releasing the claim; it cannot protect against deleting the kind node, resetting Docker, deleting its storage or losing the host disk. A cluster deletion is different from an infrastructure restart. Any stronger availability claim requires different storage and verified backups.

## Primary references

- [Kubernetes Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/): replicas, updates and rollout behavior.
- [Kubernetes Services](https://kubernetes.io/docs/concepts/services-networking/service/): discovery, ClusterIP and NodePort.
- [Kubernetes persistent volumes](https://kubernetes.io/docs/concepts/storage/persistent-volumes/): PVC/PV lifetime and reclaim policy.
- [Kubernetes Secrets](https://kubernetes.io/docs/concepts/configuration/secret/): secret handling and encryption caveats.
- [kind quick start](https://kind.sigs.k8s.io/docs/user/quick-start/): separate local clusters and loading images.
- [Psycopg parameter binding](https://www.psycopg.org/psycopg3/docs/basic/params.html): SQL parameters supplied separately from SQL text.
- [Flask testing](https://flask.palletsprojects.com/en/stable/testing/): request testing via the test client.
- [Docker Hub repositories](https://docs.docker.com/docker-hub/repos/): image publication and access.

The source code and measured evidence determine which mitigations are actually present; proposed future measures must not be described as implemented.
