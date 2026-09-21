# Submission checklist

Use actual evidence, not planned features. This AI-generated draft is subject to the course policy; see AI-DISCLOSURE.md.

| Requirement | Relevant material / evidence |
|---|---|
| Description of the application | README; explain features in your own words |
| Architecture, component mapping and principles | README diagram and ARCHITECTURE.md review draft |
| Benefits, challenges, business implications, security | ARCHITECTURE.md; distinguish present and proposed controls |
| Source repository, including Kubernetes code | Verified public repository: https://github.com/runlinlong/cloudboard |
| 5–10 minute recording | Local 9:22 reference video is ready and not uploaded; student will record and submit their own final video |
| Two different REST microservices | Dashboard and Tasks; show dashboard's programmatic call to task API |
| Kubernetes execution and outside access | Pods/Services ready and localhost:18081 browser demonstration |
| Independent horizontal scaling | Both Deployments can be scaled separately; verify-kubernetes.ps1 |
| Docker Hub images | Public runlinlong/cloudboard-tasks and runlinlong/cloudboard-dashboard; deployed using registry images |
| Separate persistent database | PostgreSQL Deployment and PVC; restart evidence and persistence limitations |
| Understanding and provenance | Review code, reproduce behavior, retain truthful attribution; follow course-specific AI rules |

The software artifacts cannot replace account authorization, policy compliance, personal understanding, or an actual required recording. Current measurements and outstanding items are tracked in VERIFICATION.md.
