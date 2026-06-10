$ErrorActionPreference = "Continue"

$Ports = @(8000, 8501, 8502)
foreach ($Port in $Ports) {
    $Connections = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    foreach ($Connection in $Connections) {
        if ($Connection.OwningProcess) {
            Stop-Process -Id $Connection.OwningProcess -Force
            Write-Host "Stopped process on port $Port"
        }
    }
}
