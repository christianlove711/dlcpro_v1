#Requires -RunAsAdministrator
$ErrorActionPreference = "Stop"

$ip = Get-NetIPAddress -IPAddress "192.168.20.1" -AddressFamily IPv4
$adapter = $ip | Get-NetAdapter
if ($null -eq $adapter) {
    throw "No PL adapter owns 192.168.20.1. Configure that static IPv4 address first."
}

$jumbo = Get-NetAdapterAdvancedProperty -Name $adapter.Name -RegistryKeyword "*JumboPacket" -AllProperties
if (9014 -notin $jumbo.ValidRegistryValues) {
    throw "$($adapter.Name) does not support 9014-byte jumbo frames. Valid values: $($jumbo.ValidRegistryValues -join ', ')"
}

Set-NetAdapterAdvancedProperty -Name $adapter.Name -RegistryKeyword "*JumboPacket" -RegistryValue 9014 -NoRestart
Set-NetIPInterface -InterfaceAlias $adapter.Name -AddressFamily IPv4 -NlMtuBytes 9000
Restart-NetAdapter -Name $adapter.Name

$actualJumbo = Get-NetAdapterAdvancedProperty -Name $adapter.Name -RegistryKeyword "*JumboPacket"
$actualMtu = Get-NetIPInterface -InterfaceAlias $adapter.Name -AddressFamily IPv4
Write-Host "PL adapter: $($adapter.Name)"
Write-Host "Jumbo frame: $($actualJumbo.DisplayValue)"
Write-Host "IPv4 MTU: $($actualMtu.NlMtu)"
Write-Host "Done. Reconnect the PL cable, then enable jumbo mode in the GUI."
Read-Host "Press Enter to close"
