param(
    [ValidatePattern('^$|^[a-z0-9][a-z0-9_-]+$')][string]$DockerHubUser = '',
    [ValidatePattern('^[a-zA-Z0-9_][a-zA-Z0-9_.-]{0,127}$')][string]$Tag = 'v1',
    [string]$Kubeconfig = '',
    [string]$Context = 'kind-cloudboard-coursework',
    [switch]$LocalImages
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
Set-Location $projectRoot
if (-not $LocalImages -and -not $DockerHubUser) { throw 'Provide DockerHubUser for the submission deployment, or LocalImages for local rehearsal only.' }
if (-not $Kubeconfig) { $Kubeconfig = Join-Path $projectRoot '.local\kubeconfig' }
if (-not (Test-Path $Kubeconfig)) { throw 'Kubeconfig not found. Create the separate cluster first, or supply an existing Kubeconfig and Context explicitly.' }
$kubeArgs = @('--kubeconfig', $Kubeconfig, '--context', $Context)
kubectl @kubeArgs cluster-info
if ($LASTEXITCODE -ne 0) { throw 'Cluster unavailable' }
if (-not (Test-Path '.env')) { throw 'Run scripts/init-local.ps1 first to create a private password file.' }
$passwordLine = @(Get-Content '.env' | Where-Object { $_ -match '^DB_PASSWORD=' })
if ($passwordLine.Count -ne 1 -or $passwordLine[0].Length -lt 24) { throw 'Invalid DB_PASSWORD in .env' }
kubectl @kubeArgs apply -f k8s/namespace.yaml
if ($LASTEXITCODE -ne 0) { throw 'Namespace apply failed' }
kubectl @kubeArgs -n cloudboard get secret postgres-secret -o name 2>$null
if ($LASTEXITCODE -ne 0) {
    kubectl @kubeArgs -n cloudboard create secret generic postgres-secret --from-env-file=.env
    if ($LASTEXITCODE -ne 0) { throw 'Secret creation failed' }
} else {
    Write-Host 'Keeping existing database Secret. Changing it would not change the password already stored in PostgreSQL.'
}
$manifest = Get-Content 'k8s/app.yaml' -Raw
if ($LocalImages) {
    $manifest = $manifest.Replace('__TASKS_IMAGE__', 'cloudboard-tasks:dev')
    $manifest = $manifest.Replace('__DASHBOARD_IMAGE__', 'cloudboard-dashboard:dev')
    $manifest = $manifest.Replace('imagePullPolicy: Always', 'imagePullPolicy: Never')
    Write-Warning 'LOCAL REHEARSAL ONLY: Docker Hub publication is still required for submission.'
} else {
    $manifest = $manifest.Replace('__TASKS_IMAGE__', "docker.io/$DockerHubUser/cloudboard-tasks:$Tag")
    $manifest = $manifest.Replace('__DASHBOARD_IMAGE__', "docker.io/$DockerHubUser/cloudboard-dashboard:$Tag")
}
New-Item -ItemType Directory -Force -Path '.local' | Out-Null
[System.IO.File]::WriteAllText((Join-Path $projectRoot '.local\rendered.yaml'), $manifest)
kubectl @kubeArgs apply -f .local/rendered.yaml
if ($LASTEXITCODE -ne 0) { throw 'Deployment apply failed' }
foreach ($name in @('postgres','tasks','dashboard')) {
    kubectl @kubeArgs -n cloudboard rollout status "deployment/$name" --timeout=180s
    if ($LASTEXITCODE -ne 0) { throw "$name not ready. Inspect pods and events; do not reset the cluster." }
}
# Protect the provisioned volume from automatic disposal when the claim is removed.
$pv = kubectl @kubeArgs -n cloudboard get pvc postgres-data -o 'jsonpath={.spec.volumeName}'
if ($LASTEXITCODE -ne 0 -or -not $pv) { throw 'Database PVC is not bound' }
[System.IO.File]::WriteAllText((Join-Path $projectRoot '.local\retain-pv.json'), '{"spec":{"persistentVolumeReclaimPolicy":"Retain"}}')
kubectl @kubeArgs patch pv $pv --type=merge --patch-file=.local/retain-pv.json
if ($LASTEXITCODE -ne 0) { throw 'Could not set Retain policy; check storage permissions' }
kubectl @kubeArgs -n cloudboard get deployments,pods,services,pvc
Write-Host 'For the supplied kind configuration: http://127.0.0.1:18081'
Write-Host 'For any cluster, use kubectl with the SAME --kubeconfig and --context, then: -n cloudboard port-forward service/dashboard 18082:80'
