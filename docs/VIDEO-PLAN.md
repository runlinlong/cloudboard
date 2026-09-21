# 7–8 minute demonstration plan

Preparation guide, not a script to claim as independent work. An automated reference recording with synthetic narration is provided locally in `artifacts/cloudboard-demo.mp4` and is not uploaded. The student will record a separate final submission video. Explain the design in your own words after understanding it. Record the actual running cluster and your browser. Do not show `.env`, kubeconfig contents, account tokens or password dialogs.

| Time | Show | Explain |
|---|---|---|
| 0:00–0:40 | Browser at localhost:18081 | Cloudboard is a small team task board; acknowledge the educational scale |
| 0:40–1:30 | Architecture diagram in README | Dashboard owns UI/gateway/aggregation; Tasks owns task REST API and persistence; PostgreSQL owns durable storage |
| 1:30–2:40 | Create a task, choose priority, change status, delete a task | Browser uses JSON APIs; dashboard summary changes; show `/api/dashboard` and its two instance names |
| 2:40–3:35 | `get deployments,pods,services,pvc`; optionally Docker Hub repository page | Kubernetes runs two independently scalable services; images are published; database has one PVC |
| 3:35–4:25 | Scale Tasks to three, show Dashboard remains at two | Horizontal scaling adds instances; Services route requests; no HPA is claimed |
| 4:25–5:15 | Task service and dashboard logs; inspect `call_tasks()` | Programmatic REST call, status codes, timeout, and instance-level logs |
| 5:15–6:10 | Restart only PostgreSQL Deployment, refresh existing task | Persistent volume outlives the Pod; single database has temporary downtime; do not delete the PVC |
| 6:10–7:15 | Walk through `k8s/app.yaml` and deployment script | Image references, replicas, internal Services, NodePort, Secret reference, probes, resources, PVC |
| 7:15–7:50 | Architecture trade-offs and actual limitations | Simple monolith would be cheaper at this scale; no authentication/TLS; production needs restricted DB credentials and backups |

Keep a second PowerShell terminal ready in the project directory:

```powershell
$k = @('--kubeconfig', '.local/kubeconfig', '--context', 'kind-cloudboard-coursework', '-n', 'cloudboard')
kubectl @k get deployments,pods,services,pvc
kubectl @k scale deployment tasks --replicas=3
kubectl @k rollout status deployment/tasks --timeout=120s
kubectl @k get deployments,pods
kubectl @k logs -l app=dashboard --tail=15 --prefix
kubectl @k logs -l app=tasks --tail=15 --prefix
kubectl @k rollout restart deployment/postgres
kubectl @k rollout status deployment/postgres --timeout=180s
kubectl @k get pvc
kubectl @k scale deployment tasks --replicas=2
```

Show the rendered `.local/rendered.yaml` for actual image names (it contains no password), and `k8s/app.yaml` for the reusable source template. Never show `.local/kubeconfig` or `.env`.

After recording, verify that audio is audible, text is readable, duration is 5–10 minutes, and any shared video link is accessible to the examiner. A screenshot collection, script, or local browser URL is not a submitted video.
