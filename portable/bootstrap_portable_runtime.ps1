param(
    [switch]$Lan,
    [switch]$ResetDb,
    [switch]$NoBrowser
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PackageRoot = Split-Path -Parent $ScriptRoot
$RuntimeRoot = Join-Path $PackageRoot '.portable_runtime'
$PythonRoot = Join-Path $RuntimeRoot 'python'
$EmbedZip = Join-Path $PackageRoot 'portable_assets\python-embed-cp312.zip'
$Wheelhouse = Join-Path $PackageRoot 'portable_assets\wheelhouse'
$Port = if ($env:BORNA_PORT) { $env:BORNA_PORT } else { '8000' }
$BindHost = if ($Lan) { '0.0.0.0' } else { '127.0.0.1' }
$LocalConsoleUrl = "http://localhost:$Port/console"
$LocalDocsUrl = "http://localhost:$Port/docs"

function Write-Step([string]$Message) {
    Write-Host "[Borna Portable] $Message"
}

function Ensure-Directory([string]$PathValue) {
    if (-not (Test-Path $PathValue)) {
        New-Item -ItemType Directory -Path $PathValue -Force | Out-Null
    }
}

function Expand-ZipContents([string]$ZipPath, [string]$Destination) {
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    Ensure-Directory $Destination
    $archive = [System.IO.Compression.ZipFile]::OpenRead($ZipPath)
    try {
        foreach ($entry in $archive.Entries) {
            $targetPath = Join-Path $Destination $entry.FullName
            if ([string]::IsNullOrWhiteSpace($entry.Name)) {
                Ensure-Directory $targetPath
                continue
            }
            $targetDir = Split-Path -Parent $targetPath
            Ensure-Directory $targetDir
            $entryStream = $entry.Open()
            try {
                $fileStream = [System.IO.File]::Open($targetPath, [System.IO.FileMode]::Create, [System.IO.FileAccess]::Write)
                try {
                    $entryStream.CopyTo($fileStream)
                }
                finally {
                    $fileStream.Dispose()
                }
            }
            finally {
                $entryStream.Dispose()
            }
        }
    }
    finally {
        $archive.Dispose()
    }
}

function Remove-DirectoryIfExists([string]$PathValue) {
    if (Test-Path $PathValue) {
        Remove-Item -Path $PathValue -Recurse -Force
    }
}

function Initialize-EmbeddedPython {
    if (Test-Path (Join-Path $PythonRoot 'python.exe')) {
        Write-Step 'Portable runtime already prepared.'
        return
    }

    if (-not (Test-Path $EmbedZip)) {
        throw "Embedded Python payload not found: $EmbedZip"
    }
    if (-not (Test-Path $Wheelhouse)) {
        throw "Wheelhouse not found: $Wheelhouse"
    }

    Write-Step 'Preparing embedded Python runtime...'
    Ensure-Directory $RuntimeRoot
    $ExtractRoot = Join-Path $RuntimeRoot '_extract'
    Remove-DirectoryIfExists $ExtractRoot
    Ensure-Directory $ExtractRoot
    Expand-ZipContents -ZipPath $EmbedZip -Destination $ExtractRoot

    $EmbeddedFolder = Get-ChildItem -Path $ExtractRoot -Directory | Where-Object { Test-Path (Join-Path $_.FullName 'python.exe') } | Select-Object -First 1
    if (-not $EmbeddedFolder) {
        throw 'Embedded Python folder was not found after extraction.'
    }

    if (Test-Path $PythonRoot) {
        Remove-DirectoryIfExists $PythonRoot
    }
    Move-Item -Path $EmbeddedFolder.FullName -Destination $PythonRoot
    Remove-DirectoryIfExists $ExtractRoot

    $PthFile = Get-ChildItem -Path $PythonRoot -Filter 'python*._pth' | Select-Object -First 1
    if (-not $PthFile) {
        throw 'Embedded Python ._pth file was not found.'
    }

    $ZipLine = (Get-Content $PthFile.FullName | Where-Object { $_ -match '^python\d+\.zip$' } | Select-Object -First 1)
    if (-not $ZipLine) { $ZipLine = 'python312.zip' }
    @(
        $ZipLine,
        '.',
        '.\\site-packages',
        'import site'
    ) | Set-Content -Path $PthFile.FullName -Encoding ASCII

    $SitePackages = Join-Path $PythonRoot 'site-packages'
    Ensure-Directory $SitePackages

    Write-Step 'Installing bundled runtime dependencies offline...'
    $WheelFiles = Get-ChildItem -Path $Wheelhouse -Filter '*.whl' | Sort-Object Name
    foreach ($wheel in $WheelFiles) {
        Write-Step ("Installing wheel: {0}" -f $wheel.Name)
        Expand-ZipContents -ZipPath $wheel.FullName -Destination $SitePackages
    }

    $ReadyMarker = Join-Path $RuntimeRoot 'runtime.ready.txt'
    @(
        'Borna Portable Runtime Ready',
        (Get-Date).ToString('s')
    ) | Set-Content -Path $ReadyMarker -Encoding UTF8
}

function Ensure-EnvFile {
    $EnvPath = Join-Path $PackageRoot '.env'
    $ExamplePath = Join-Path $PackageRoot '.env.example'
    if ((-not (Test-Path $EnvPath)) -and (Test-Path $ExamplePath)) {
        Copy-Item -Path $ExamplePath -Destination $EnvPath
        Write-Step 'Created .env from .env.example'
    }
}

function Reset-DemoDbIfNeeded {
    if (-not $ResetDb) { return }
    $DbPath = Join-Path $PackageRoot 'borna_chart.db'
    if (Test-Path $DbPath) {
        Remove-Item -Path $DbPath -Force
        Write-Step 'Existing demo database removed.'
    }
}

function Show-LanHints {
    if (-not $Lan) { return }
    try {
        $ip = Get-NetIPAddress -AddressFamily IPv4 |
            Where-Object { $_.IPAddress -notmatch '^127\.' -and $_.PrefixOrigin -ne 'WellKnown' } |
            Select-Object -ExpandProperty IPAddress -First 1
        if ($ip) {
            Write-Step ("LAN Console: http://{0}:{1}/console" -f $ip, $Port)
            Write-Step ("LAN Swagger: http://{0}:{1}/docs" -f $ip, $Port)
        }
        else {
            Write-Step ("LAN mode enabled. Use http://SERVER-IP:{0}/console if needed." -f $Port)
        }
    }
    catch {
        Write-Step ("LAN mode enabled. Use http://SERVER-IP:{0}/console if needed." -f $Port)
    }
}

Initialize-EmbeddedPython
Ensure-EnvFile
Reset-DemoDbIfNeeded

Write-Step ("Local Console: {0}" -f $LocalConsoleUrl)
Write-Step ("Local Swagger: {0}" -f $LocalDocsUrl)
Show-LanHints

if (-not $NoBrowser) {
    Start-Process $LocalConsoleUrl | Out-Null
}

$PythonExe = Join-Path $PythonRoot 'python.exe'
Push-Location $PackageRoot
try {
    & $PythonExe -m uvicorn app.main:app --host $BindHost --port $Port
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
