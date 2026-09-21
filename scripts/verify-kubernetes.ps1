param([string]$BaseUrl = 'http://127.0.0.1:18081')
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
Set-Location $projectRoot
$kubeArgs = @('--kubeconfig', (Join-Path $projectRoot '.local\kubeconfig'), '--context', 'kind-cloudboard-coursework', '-n', 'cloudboard')
$oldTasks = kubectl @kubeArgs get deployment tasks -o 'jsonpath={.spec.replicas}'
if ($LASTEXITCODE -ne 0) { throw 'Project cluster not available' }
$oldDashboard = kubectl @kubeArgs get deployment dashboard -o 'jsonpath={.spec.replicas}'
if ($LASTEXITCODE -ne 0) { throw 'Dashboard deployment not available' }
$title = 'Persistence check ' + [guid]::NewGuid().ToString()
$task = Invoke-RestMethod "$BaseUrl/api/tasks" -Method Post -ContentType 'application/json' -Body (@{title=$title; priority='low'} | ConvertTo-Json)
try {
    kubectl @kubeArgs scale deployment tasks --replicas=3
    if ($LASTEXITCODE -ne 0) { throw 'Task scaling failed' }
    kubectl @kubeArgs rollout status deployment/tasks --timeout=120s
    if ($LASTEXITCODE -ne 0) { throw 'Task replicas not ready' }
    $stillDashboard = kubectl @kubeArgs get deployment dashboard -o 'jsonpath={.spec.replicas}'
    if ($stillDashboard -ne $oldDashboard) { throw 'Dashboard replica count unexpectedly changed' }
    kubectl @kubeArgs scale deployment dashboard --replicas=3
    if ($LASTEXITCODE -ne 0) { throw 'Dashboard scaling failed' }
    kubectl @kubeArgs rollout status deployment/dashboard --timeout=120s
    if ($LASTEXITCODE -ne 0) { throw 'Dashboard replicas not ready' }
    $stillTasks = kubectl @kubeArgs get deployment tasks -o 'jsonpath={.spec.replicas}'
    if ($stillTasks -ne '3') { throw 'Task replica count unexpectedly changed' }
    Write-Host 'PASS: each application service scaled independently.'
    # Only the database deployment IN THIS PROJECT is restarted.
    kubectl @kubeArgs rollout restart deployment/postgres
    if ($LASTEXITCODE -ne 0) { throw 'Postgres rollout restart failed' }
    kubectl @kubeArgs rollout status deployment/postgres --timeout=180s
    if ($LASTEXITCODE -ne 0) { throw 'Postgres not ready' }
    $found = $false
    for ($attempt=0; $attempt -lt 30; $attempt++) {
        try {
            $loaded = Invoke-RestMethod "$BaseUrl/api/tasks/$($task.id)"
            if ($loaded.title -eq $title) { $found = $true; break }
        } catch { Start-Sleep -Seconds 2 }
    }
    if (-not $found) { throw 'Persistence check failed' }
    Write-Host 'PASS: the task survived replacement of the PostgreSQL pod.'
    Write-Host 'This does not test Docker/WSL/host restart, cluster deletion, or disaster recovery.'
} finally {
    kubectl @kubeArgs scale deployment tasks "--replicas=$oldTasks"
    kubectl @kubeArgs scale deployment dashboard "--replicas=$oldDashboard"
    try { Invoke-RestMethod "$BaseUrl/api/tasks/$($task.id)" -Method Delete | Out-Null } catch { Write-Warning 'Temporary verification task could not be removed.' }
}
