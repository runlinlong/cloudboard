# Cloudboard delivery

This package is an AI-assisted review draft. The source and documents disclose their provenance; the automated video uses synthetic narration. Course-policy compliance and the student's own understanding remain necessary.

## Software

Cloudboard is a browser-based task board. Users create tasks with priorities, move them between To do / In progress / Done, delete tasks, and view progress statistics. The application demonstrates two different REST microservices communicating programmatically, backed by a separate PostgreSQL database.

## Architecture and discussion

- [Architecture, service responsibilities and business/security trade-offs](ARCHITECTURE.md)
- [README: deployment instructions and architecture diagram](../README.md)
- [Observed verification results](VERIFICATION.md)
- [Chinese beginner walkthrough](START-HERE-ZH.md)
- [AI assistance disclosure](AI-DISCLOSURE.md)

## Source and images

- Public source and Kubernetes configuration: https://github.com/runlinlong/cloudboard
- Task image: https://hub.docker.com/r/runlinlong/cloudboard-tasks
- Dashboard image: https://hub.docker.com/r/runlinlong/cloudboard-dashboard
- Version tags: `runlinlong/cloudboard-tasks:v1`, `runlinlong/cloudboard-dashboard:v1`.

## Running application

On the configured machine, with Docker Desktop and the existing project node running: http://127.0.0.1:18081

This localhost address is a demonstration on the student's computer, not a public cloud deployment. Another person must deploy the public repository and images in their own Kubernetes environment to use the application, or watch the recording.

## Video

The **9 minute 22 second** automated reference recording is saved locally at `artifacts/cloudboard-demo.mp4`. It has not been uploaded. It shows the actual Kubernetes application, service roles, browser operations, logs, independent scaling, persistence and YAML, with synthetic English narration. Full-file audio/video decoding passed verification. The transcript is `artifacts/video-transcript.md`; chapter timestamps are approximate.

The student will use this reference to prepare and record a separate final submission video. See VIDEO-PLAN.md for a shorter recording outline. Add the student's own uploaded video link to the final submission when it is ready.
