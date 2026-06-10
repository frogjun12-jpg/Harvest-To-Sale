$ErrorActionPreference = "Continue"

$Targets = @(
    @{ Name = "API"; Url = "http://127.0.0.1:8000/health"; Port = 8000 },
    @{ Name = "Admin"; Url = "http://127.0.0.1:8501"; Port = 8501 },
    @{ Name = "Market"; Url = "http://127.0.0.1:8502"; Port = 8502 }
)

foreach ($Target in $Targets) {
    $Connection = Get-NetTCPConnection -LocalPort $Target.Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    try {
        $StatusCode = (Invoke-WebRequest -UseBasicParsing $Target.Url -TimeoutSec 5).StatusCode
    } catch {
        $StatusCode = "DOWN"
    }

    $PidText = if ($Connection) { $Connection.OwningProcess } else { "-" }
    Write-Host "$($Target.Name): port=$($Target.Port) pid=$PidText status=$StatusCode"
}
