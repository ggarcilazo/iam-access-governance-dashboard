# get_users_roles.ps1
# Extrae usuarios y sus grupos/roles desde Microsoft Entra ID vía Microsoft Graph API
# Requiere: app registrada en Entra ID con permisos User.Read.All y Directory.Read.All (consentimiento de administrador otorgado)

# --- 1. Cargar variables desde .env (PowerShell no lee .env de forma nativa) ---
$envPath = Join-Path $PSScriptRoot "..\..\.env"
$envVars = @{}
Get-Content $envPath | ForEach-Object {
    if ($_ -match "^\s*([^#][^=]*)=(.*)$") {
        $envVars[$matches[1].Trim()] = $matches[2].Trim()
    }
}

$tenantId     = $envVars["ENTRA_TENANT_ID"]
$clientId     = $envVars["ENTRA_CLIENT_ID"]
$clientSecret = $envVars["ENTRA_CLIENT_SECRET"]

if (-not $tenantId -or -not $clientId -or -not $clientSecret) {
    Write-Error "Faltan ENTRA_TENANT_ID / ENTRA_CLIENT_ID / ENTRA_CLIENT_SECRET en .env"
    exit 1
}

# --- 2. Obtener token de acceso (client credentials flow) ---
$tokenBody = @{
    grant_type    = "client_credentials"
    client_id     = $clientId
    client_secret = $clientSecret
    scope         = "https://graph.microsoft.com/.default"
}

$tokenResponse = Invoke-RestMethod -Method Post `
    -Uri "https://login.microsoftonline.com/$tenantId/oauth2/v2.0/token" `
    -Body $tokenBody

$accessToken = $tokenResponse.access_token
$headers = @{ Authorization = "Bearer $accessToken" }

# --- 3. Obtener usuarios ---
$usersUri = "https://graph.microsoft.com/v1.0/users?`$select=id,displayName,userPrincipalName,createdDateTime,accountEnabled"
$usersResponse = Invoke-RestMethod -Method Get -Uri $usersUri -Headers $headers

$results = @()

foreach ($user in $usersResponse.value) {
    # --- 4. Grupos/roles del usuario ---
    $groupsUri = "https://graph.microsoft.com/v1.0/users/$($user.id)/memberOf"
    $groupsResponse = Invoke-RestMethod -Method Get -Uri $groupsUri -Headers $headers
    $groupNames = $groupsResponse.value | ForEach-Object { $_.displayName }

    $daysSinceCreated = (New-TimeSpan -Start ([datetime]$user.createdDateTime) -End (Get-Date)).Days

    $results += [PSCustomObject]@{
        username           = $user.userPrincipalName
        display_name       = $user.displayName
        user_id            = $user.id
        created            = $user.createdDateTime
        days_since_created = $daysSinceCreated
        account_enabled    = $user.accountEnabled
        groups             = $groupNames
    }
}

# --- 5. Guardar snapshot ---
$outputPath = Join-Path $PSScriptRoot "snapshot_entra_latest.json"
$results | ConvertTo-Json -Depth 5 | Out-File -FilePath $outputPath -Encoding utf8

Write-Host "✅ Snapshot de Entra ID guardado con $($results.Count) usuario(s) en $outputPath"
