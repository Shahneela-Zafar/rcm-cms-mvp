$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

New-Item -ItemType Directory -Force -Path ".\data\raw\plan_directory" | Out-Null
New-Item -ItemType Directory -Force -Path ".\data\raw\ma_penetration" | Out-Null
New-Item -ItemType Directory -Force -Path ".\data\raw\benefits" | Out-Null
New-Item -ItemType Directory -Force -Path ".\data\raw\reference_docs" | Out-Null
New-Item -ItemType Directory -Force -Path ".\data\raw\ma_scp" | Out-Null
New-Item -ItemType Directory -Force -Path ".\data\raw\cpsc" | Out-Null

function Save-Url {
    param(
        [Parameter(Mandatory = $true)][string]$Url,
        [Parameter(Mandatory = $true)][string]$OutFile
    )

    curl.exe -L --retry 3 --retry-delay 2 --connect-timeout 30 $Url -o $OutFile
}

Save-Url "https://www.cms.gov/files/zip/ma-plan-directory.zip" ".\data\raw\plan_directory\ma-plan-directory.zip"
Save-Url "https://www.cms.gov/files/zip/ma-state-county-penetration-january-2026.zip" ".\data\raw\ma_penetration\ma-state-county-penetration-2026-01.zip"
Save-Url "https://www.cms.gov/files/zip/pbp-benefits-2026-json.zip" ".\data\raw\benefits\pbp-benefits-2026-json.zip"
Save-Url "https://www.cms.gov/files/document/prior-authorization-metrics-reporting-overview-template.pdf" ".\data\raw\reference_docs\prior-authorization-metrics-reporting-overview-template.pdf"
Save-Url "https://www.cms.gov/files/document/cms-0057-f.pdf" ".\data\raw\reference_docs\cms-0057-f.pdf"
Save-Url "https://www.cms.gov/medicare/health-plans/healthplansgeninfo/downloads/ma_step_therapy_hpms_memo_8_7_2018.pdf" ".\data\raw\reference_docs\ma_step_therapy_hpms_memo_8_7_2018.pdf"

$start = Get-Date "2024-01-01"
$end = Get-Date "2026-05-01"
$overview = "https://www.cms.gov/data-research/statistics-trends-and-reports/medicare-advantagepart-d-contract-and-enrollment-data/monthly-ma-enrollment-state/county/plan-type"
$overviewHtml = (Invoke-WebRequest -Uri $overview -UseBasicParsing).Content
$detailMatches = [regex]::Matches($overviewHtml, 'href="([^"]*ma-enrollment-scp-(\d{4})-(\d{2})[^"]*)"')
$detailPages = @{}

foreach ($m in $detailMatches) {
    $ym = "$($m.Groups[2].Value)-$($m.Groups[3].Value)"
    $href = [System.Net.WebUtility]::HtmlDecode($m.Groups[1].Value)
    if ($href.StartsWith("/")) {
        $href = "https://www.cms.gov$href"
    }
    $detailPages[$ym] = $href
}

# CMS has a couple of 2025 archive pages whose slugs do not match the report
# month cleanly, so keep explicit fallbacks for a complete 2024-01..2026-05 run.
$detailPages["2025-02"] = "https://www.cms.gov/data-research/statistics-trends-and-reports/medicare-advantagepart-d-contract-and-enrollment-data/monthly-ma-enrollment-state/county/plan-type/ma-enrollment-scp-2025-01-0"

for ($d = $start; $d -le $end; $d = $d.AddMonths(1)) {
    $ym = $d.ToString("yyyy-MM")
    $out = ".\data\raw\ma_scp\ma-scp-$ym.zip"
    if ((Test-Path $out) -and ((Get-Item $out).Length -gt 0)) {
        Write-Host "Already present ma-scp-$ym.zip"
        continue
    }

    try {
        if (-not $detailPages.ContainsKey($ym)) {
            Write-Warning "No CMS detail page found for $ym"
            continue
        }

        $detailHtml = (Invoke-WebRequest -Uri $detailPages[$ym] -UseBasicParsing).Content
        $zipMatch = [regex]::Match($detailHtml, 'href="([^"]*\.zip[^"]*)"')
        if (-not $zipMatch.Success) {
            Write-Warning "No ZIP link found for $ym"
            continue
        }

        $url = [System.Net.WebUtility]::HtmlDecode($zipMatch.Groups[1].Value)
        if ($url.StartsWith("/")) {
            $url = "https://www.cms.gov$url"
        }

        curl.exe -L --fail --retry 3 --retry-delay 2 $url -o $out
        Write-Host "Downloaded $ym from $url"
    }
    catch {
        Write-Warning "Skipped missing/renamed file for ${ym}: $($_.Exception.Message)"
    }
}
