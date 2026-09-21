param(
    [Parameter(Mandatory=$true)][ValidatePattern('^[a-z0-9][a-z0-9_-]+$')][string]$DockerHubUser,
    [ValidatePattern('^[a-zA-Z0-9_][a-zA-Z0-9_.-]{0,127}$')][string]$Tag = 'v1'
)
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
docker info --format '{{.OSType}}'
if ($LASTEXITCODE -ne 0) { throw 'Docker must already be running. This script will not start or reset it.' }
foreach ($service in @('tasks','dashboard')) {
    $image = "docker.io/$DockerHubUser/cloudboard-${service}:$Tag"
    docker build -f "services/$service/Dockerfile" -t $image .
    if ($LASTEXITCODE -ne 0) { throw "Build failed: $service" }
    docker push $image
    if ($LASTEXITCODE -ne 0) { throw "Push failed: $service. Sign in with docker login and retry." }
    docker buildx imagetools inspect $image
    if ($LASTEXITCODE -ne 0) { throw "Cannot verify remote image: $image" }
}
Write-Host 'Both images were pushed and their remote manifests checked. Ensure both Docker Hub repositories are PUBLIC.'
