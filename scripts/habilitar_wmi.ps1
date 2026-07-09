<#
.SYNOPSIS
    Habilita o WMI para consultas remotas na máquina local.
.DESCRIPTION
    Configura o firewall, serviço Winmgmt, DCOM e permissões WMI
    para permitir consultas WMI remotas (usadas pelo sistema de gestão).
.NOTES
    Execute como Administrador.
#>

if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "ERRO: Execute este script como Administrador!" -ForegroundColor Red
    exit 1
}

Write-Host "=== Habilitando WMI para consultas remotas ===" -ForegroundColor Cyan

Write-Host "[1/5] Configurando servico Winmgmt..." -ForegroundColor Yellow
Set-Service -Name Winmgmt -StartupType Automatic
Start-Service -Name Winmgmt -ErrorAction SilentlyContinue
Write-Host "  OK" -ForegroundColor Green

Write-Host "[2/5] Liberando WMI no Firewall do Windows..." -ForegroundColor Yellow
netsh advfirewall firewall set rule group="Windows Management Instrumentation (WMI)" new enable=Yes | Out-Null
Write-Host "  OK" -ForegroundColor Green

Write-Host "[3/5] Configurando DCOM..." -ForegroundColor Yellow
$dcom = Get-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Ole" -Name "EnableDCOM" -ErrorAction SilentlyContinue
if ($dcom.EnableDCOM -ne "Y") {
    Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Ole" -Name "EnableDCOM" -Value "Y"
}
Write-Host "  OK" -ForegroundColor Green

Write-Host "[4/5] Testando consulta WMI local..." -ForegroundColor Yellow
try {
    $test = Get-WmiObject -Class Win32_ComputerSystem -ErrorAction Stop
    Write-Host ("  OK - Computador: " + $test.UserName) -ForegroundColor Green
} catch {
    Write-Host ("  FALHA: " + $_.Exception.Message) -ForegroundColor Red
}

Write-Host ""
Write-Host "=== Concluido ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Para testar de outra maquina, execute no PowerShell remoto:" -ForegroundColor Gray
Write-Host '  Get-WmiObject -Class Win32_ComputerSystem -ComputerName <IP> -Credential (Get-Credential)' -ForegroundColor White
