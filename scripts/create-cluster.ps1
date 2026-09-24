$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
Set-Location $projectRoot
docker info --format '{{.OSType}}'
if ($LASTEXITCODE -ne 0) { throw 'Docker is unavailable. Resolve its warning without resetting existing coursework.' }
$kindExe = Join-Path $projectRoot '.local\kind.exe'
if (-not (Test-Path $kindExe)) { $kindExe = 'kind' }
if (-not (Get-Command $kindExe -ErrorAction SilentlyContinue)) {
    throw 'Install kind from https://kind.sigs.k8s.io/docs/user/quick-start/ and rerun. No changes were made.'
}
$clusters = @(& $kindExe get clusters)
if ($LASTEXITCODE -ne 0) { throw 'Cannot inspect existing kind clusters' }
$kubeconfig = Join-Path $projectRoot '.local\kubeconfig'
New-Item -ItemType Directory -Force -Path '.local' | Out-Null
if ($clusters -contains 'cloudboard-coursework') {
    & $kindExe export kubeconfig --name cloudboard-coursework --kubeconfig $kubeconfig
} else {
    if (Get-NetTCPConnection -State Listen -LocalPort 18081 -ErrorAction SilentlyContinue) {
        throw 'Port 18081 is occupied. Stop here and select another port in k8s/kind.yaml.'
    }
    & $kindExe create cluster --name cloudboard-coursework --config k8s/kind.yaml --kubeconfig $kubeconfig --wait 120s
}
if ($LASTEXITCODE -ne 0) { throw 'Cluster creation/export failed; no automatic reset or cleanup will be attempted.' }
Write-Host 'New project kubeconfig:' $kubeconfig
Write-Host 'Other clusters and the default kubeconfig have not been modified.'
