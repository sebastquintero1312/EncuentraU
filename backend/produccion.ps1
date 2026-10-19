# Ejecuta un comando de terminal de EncuentraU (flask ...) contra la base de
# datos de PRODUCCIÓN (Supabase), leyendo las conexiones de .env.produccion.
#
# Uso, desde la carpeta backend:
#   powershell -ExecutionPolicy Bypass -File .\produccion.ps1 crear-admin correo@sanmateo.edu.co
#   powershell -ExecutionPolicy Bypass -File .\produccion.ps1 verificar-correo correo@sanmateo.edu.co
#   powershell -ExecutionPolicy Bypass -File .\produccion.ps1 vencer-reservas
#
# Cuidado: todo lo que hace este script cambia datos REALES.
# Al terminar restaura las variables de entorno, para que la terminal no
# quede apuntando a producción (python app.py seguiría usando la base local).

param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Argumentos)

$ErrorActionPreference = 'Stop'
$archivo = Join-Path $PSScriptRoot '.env.produccion'
if (-not (Test-Path $archivo)) {
    Write-Host 'No existe backend\.env.produccion (contiene las conexiones de producción).'
    exit 1
}
if (-not $Argumentos) {
    Write-Host 'Falta el comando. Ejemplo: .\produccion.ps1 crear-admin correo@sanmateo.edu.co'
    exit 1
}

# Lee las líneas CLAVE=valor del archivo (ignora comentarios y líneas vacías)
$valores = @{}
foreach ($linea in Get-Content $archivo -Encoding UTF8) {
    $texto = $linea.Trim()
    if ($texto -and -not $texto.StartsWith('#') -and $texto.Contains('=')) {
        $partes = $texto.Split('=', 2)
        $valores[$partes[0].Trim()] = $partes[1].Trim()
    }
}
if (-not $valores['SUPABASE_URL_APP']) {
    Write-Host 'Falta SUPABASE_URL_APP en .env.produccion.'
    exit 1
}

$anteriores = @{
    FLASK_APP        = $env:FLASK_APP
    DATABASE_URL     = $env:DATABASE_URL
    PYTHONIOENCODING = $env:PYTHONIOENCODING
}
try {
    # La aplicación se conecta con encuentrau_app (permisos mínimos), igual que en Render.
    $env:FLASK_APP = 'app.py'
    $env:DATABASE_URL = $valores['SUPABASE_URL_APP']
    $env:PYTHONIOENCODING = 'utf-8'
    Write-Host "PRODUCCIÓN (Supabase) -> flask $($Argumentos -join ' ')"
    Push-Location $PSScriptRoot
    & (Join-Path $PSScriptRoot 'venv\Scripts\python.exe') -W ignore -m flask @Argumentos
}
finally {
    Pop-Location
    foreach ($nombre in $anteriores.Keys) {
        Set-Item -Path "env:$nombre" -Value $anteriores[$nombre] -ErrorAction SilentlyContinue
        if ($null -eq $anteriores[$nombre]) { Remove-Item -Path "env:$nombre" -ErrorAction SilentlyContinue }
    }
}
