param(
    [string]$ip,
    [string]$user,
    [string]$pass
)

Write-Host "=== DIAGNOSTICO WMI ==="
Write-Host ("Alvo: " + $ip)
Write-Host ("Usuario: " + $user)
Write-Host ""

# 1. Teste de ping
Write-Host "--- 1. Teste de ping ---"
try {
    $ping = Test-Connection -ComputerName $ip -Count 1 -Quiet -ErrorAction Stop
    if ($ping) {
        Write-Host ("PING: OK (" + $ip + " responde)")
    } else {
        Write-Host "PING: Sem resposta"
    }
} catch {
    Write-Host ("PING: ERRO - " + $_.Exception.Message)
}

# 2. Teste de conexao WMI
Write-Host "`n--- 2. Teste WMI (Get-WmiObject) ---"
try {
    $secpass = ConvertTo-SecureString $pass -AsPlainText -Force
    $cred = New-Object System.Management.Automation.PSCredential($user, $secpass)
    
    # Tenta Win32_ComputerSystem primeiro (mais simples)
    Write-Host "--- 2a. Win32_ComputerSystem.UserName ---"
    try {
        $cs = Get-WmiObject -Class Win32_ComputerSystem -ComputerName $ip -Credential $cred -ErrorAction Stop
        Write-Host ("UserName: " + $cs.UserName)
        Write-Host ("Domain: " + $cs.Domain)
        Write-Host ("Model: " + $cs.Model)
    } catch {
        Write-Host ("ERRO: " + $_.Exception.Message)
        
        # Tenta sem credencial
        Write-Host "`n--- 2b. Tentando sem credencial ---"
        try {
            $cs2 = Get-WmiObject -Class Win32_ComputerSystem -ComputerName $ip -ErrorAction Stop
            Write-Host ("UserName: " + $cs2.UserName)
        } catch {
            Write-Host ("ERRO: " + $_.Exception.Message)
        }
    }
    
    # Tenta Win32_LoggedOnUser
    Write-Host "`n--- 2c. Win32_LoggedOnUser ---"
    try {
        $loggedOn = Get-WmiObject -Class Win32_LoggedOnUser -ComputerName $ip -Credential $cred -ErrorAction Stop
        $loggedOn | ForEach-Object {
            Write-Host ("  Dependent: " + $_.Dependent)
            Write-Host ("  Antecedent: " + $_.Antecedent)
            Write-Host "---"
        }
    } catch {
        Write-Host ("ERRO: " + $_.Exception.Message)
    }
    
    # Tenta Win32_LogonSession
    Write-Host "`n--- 2d. Win32_LogonSession (LogonType 2 ou 10) ---"
    try {
        $sessions = Get-WmiObject -Query "SELECT * FROM Win32_LogonSession WHERE LogonType = 2 OR LogonType = 10" -ComputerName $ip -Credential $cred -ErrorAction Stop
        foreach ($s in $sessions) {
            Write-Host ("  LogonId: " + $s.LogonId + ", LogonType: " + $s.LogonType + ", StartTime: " + $s.StartTime)
        }
        if (-not $sessions) {
            Write-Host "  Nenhuma sessao interativa encontrada"
        }
    } catch {
        Write-Host ("ERRO: " + $_.Exception.Message)
    }
    
} catch {
    Write-Host ("ERRO GERAL: " + $_.Exception.Message)
}

# 3. Teste de firewall
Write-Host "`n--- 3. Teste de porta (WMI/DCOM - TCP 135) ---"
try {
    $socket = New-Object System.Net.Sockets.TcpClient
    $connect = $socket.BeginConnect($ip, 135, $null, $null)
    $wait = $connect.AsyncWaitHandle.WaitOne(2000, $false)
    if ($wait) {
        Write-Host "PORTA 135 (DCOM): ABERTA"
        $socket.EndConnect($connect)
    } else {
        Write-Host "PORTA 135 (DCOM): FECHADA ou FILTRADA"
    }
    $socket.Close()
} catch {
    Write-Host ("PORTA 135: ERRO - " + $_.Exception.Message)
}

Write-Host "`n=== FIM DO DIAGNOSTICO ==="
