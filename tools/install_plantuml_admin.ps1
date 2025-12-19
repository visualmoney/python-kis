<#
.SYNOPSIS
  관리자 권한으로 PlantUML 관련 의존성(Java, Graphviz)을 설치합니다.

.DESCRIPTION
  이 스크립트는 Chocolatey를 통해 Amazon Corretto (OpenJDK) 및 Graphviz를 설치합니다.
  관리자 권한으로 실행되어야 하며, 실패 시 대체(winget) 시도를 합니다.
  설치 진행과 결과는 `install_plantuml_admin.log`에 기록됩니다.

.NOTES
  사용법(관리자 PowerShell에서 실행):
    powershell -ExecutionPolicy Bypass -File .\tools\install_plantuml_admin.ps1
#>

$ScriptName = $MyInvocation.MyCommand.Name
$LogFile = Join-Path $PSScriptRoot "install_plantuml_admin.log"

function Log {
    param([string]$msg)
    $entry = "$(Get-Date -Format o) `t $msg"
    $entry | Out-File -FilePath $LogFile -Encoding UTF8 -Append
    Write-Host $msg
}

# 관리자 권한 확인
Add-Type -AssemblyName System.Security
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Log "[WARN] 관리자 권한이 필요합니다. 스크립트를 관리자 권한으로 재실행합니다..."
    # 관리자 권한으로 재실행 시도
    $ps = "$PSHOME\powershell.exe"
    $args = "-NoProfile -ExecutionPolicy Bypass -File `"$PSScriptRoot\$ScriptName`""
    try {
        Start-Process -FilePath $ps -ArgumentList $args -Verb RunAs -WindowStyle Normal
        Log "[INFO] 관리자 권한으로 재시작 명령을 보냈습니다. 원래 세션은 종료합니다."
        exit 0
    } catch {
        Log "[ERROR] 관리자 권한으로 재시작을 시도했으나 실패했습니다: $_"
        exit 1
    }
}

Log "[INFO] 시작: PlantUML 의존성 관리자 설치 스크립트"
Log "[INFO] 로그 파일: $LogFile"

function Run-Install {
    param(
        [string]$cmd,
        [string]$label
    )
    Log "[CMD] 시작: $label -> $cmd"
    try {
        & powershell -NoProfile -Command $cmd 2>&1 | ForEach-Object { Log "[OUT] $_" }
        $rc = $LASTEXITCODE
        if ($rc -ne 0) {
            Log "[WARN] 명령이 비정상 종료 (exit code=$rc): $cmd"
            return $false
        }
        Log "[OK] 완료: $label"
        return $true
    } catch {
        Log "[ERROR] 예외 발생: $_"
        return $false
    }
}

# 1) Chocolatey가 설치되었는지 확인
if (Get-Command choco -ErrorAction SilentlyContinue) {
    Log "[INFO] Chocolatey가 감지되었습니다. choco 사용을 시도합니다."
    $chocoAvailable = $true
} else {
    Log "[WARN] Chocolatey가 감지되지 않았습니다. choco가 없으면 winget 또는 수동 설치로 대체합니다."
    $chocoAvailable = $false
}

$javaOk = $false
$graphvizOk = $false

if ($chocoAvailable) {
    # Amazon Corretto 설치 시도
    $ok = Run-Install -cmd "choco install amazoncorretto21 --yes --no-progress" -label "choco: amazoncorretto21"
    if (-not $ok) {
        Log "[WARN] choco로 amazoncorretto21 설치 실패 — winget/수동 설치 시도 예정"
    } else { $javaOk = $true }

    # Graphviz 설치 시도
    $ok2 = Run-Install -cmd "choco install graphviz -y --no-progress" -label "choco: graphviz"
    if (-not $ok2) {
        Log "[WARN] choco로 graphviz 설치 실패 — winget/수동 설치 시도 예정"
    } else { $graphvizOk = $true }
}

if (-not $javaOk) {
    # winget 시도 (존재 시)
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        Log "[INFO] winget이 있어 OpenJDK (Corretto) 설치를 시도합니다."
        $ok = Run-Install -cmd "winget install --id Amazon.Corretto.21 -e --silent" -label "winget: Amazon.Corretto.21"
        if ($ok) { $javaOk = $true } else { Log "[WARN] winget으로도 설치 실패했습니다." }
    } else {
        Log "[WARN] winget이 없어 자동 설치를 시도할 수 없습니다. 수동 설치 안내를 참조하세요."
    }
}

if (-not $graphvizOk) {
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        Log "[INFO] winget으로 graphviz 설치 시도합니다."
        $ok = Run-Install -cmd "winget install --id Graphviz.Graphviz -e --silent" -label "winget: Graphviz"
        if ($ok) { $graphvizOk = $true } else { Log "[WARN] winget으로도 graphviz 설치 실패했습니다." }
    } else {
        Log "[WARN] winget이 없어 graphviz 자동 설치를 시도할 수 없습니다. 수동 설치 안내를 참조하세요."
    }
}

# 설치 확인
try {
    $javaVer = & java -version 2>&1
    Log "[CHECK] java -version 결과:"
    $javaVer | ForEach-Object { Log "  $_" }
    if ($javaVer) { $javaOk = $true }
} catch {
    Log "[CHECK] java -version 실행 실패: $_"
}

try {
    $dotVer = & dot -V 2>&1
    Log "[CHECK] dot -V 결과:"
    $dotVer | ForEach-Object { Log "  $_" }
    if ($dotVer) { $graphvizOk = $true }
} catch {
    Log "[CHECK] dot -V 실행 실패: $_"
}

Log "[SUMMARY] javaOk=$javaOk, graphvizOk=$graphvizOk"

if ($javaOk -and $graphvizOk) {
    Log "[SUCCESS] 모든 의존성 설치/확인 완료"
    exit 0
} else {
    Log "[FAILED] 일부 의존성 설치 또는 확인에 실패했습니다. 로그를 확인하세요: $LogFile"
    exit 2
}
