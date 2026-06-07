$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

New-Item -ItemType Directory -Force -Path ".\data\raw\cpsc" | Out-Null
New-Item -ItemType Directory -Force -Path ".\data\raw\manual_exports" | Out-Null
New-Item -ItemType Directory -Force -Path ".\data\raw\reference_docs" | Out-Null

function Save-Url {
    param(
        [Parameter(Mandatory = $true)][string]$Url,
        [Parameter(Mandatory = $true)][string]$OutFile
    )

    curl.exe -L --fail --retry 3 --retry-delay 2 --connect-timeout 30 $Url -o $OutFile
}

function Get-CmsZipFromDetailPage {
    param(
        [Parameter(Mandatory = $true)][string]$DetailUrl
    )

    $detailHtml = (Invoke-WebRequest -Uri $DetailUrl -UseBasicParsing).Content
    $zipMatch = [regex]::Match($detailHtml, 'href="([^"]*\.zip[^"]*)"')
    if (-not $zipMatch.Success) {
        return $null
    }

    $url = [System.Net.WebUtility]::HtmlDecode($zipMatch.Groups[1].Value)
    if ($url.StartsWith("/")) {
        $url = "https://www.cms.gov$url"
    }
    return $url
}

# Optional higher-granularity enrollment source: monthly enrollment by
# contract/plan/state/county (CPSC), matching the same history window as MA SCP.
$start = Get-Date "2024-01-01"
$end = Get-Date "2026-05-01"
$cpscOverview = "https://www.cms.gov/data-research/statistics-trends-and-reports/medicare-advantagepart-d-contract-and-enrollment-data/monthly-enrollment-contract/plan/state/county"
$cpscHtml = (Invoke-WebRequest -Uri $cpscOverview -UseBasicParsing).Content
$cpscMatches = [regex]::Matches($cpscHtml, 'href="([^"]*monthly-enrollment-cpsc-(\d{4})-(\d{2})[^"]*)"')
$cpscPages = @{}

foreach ($m in $cpscMatches) {
    $ym = "$($m.Groups[2].Value)-$($m.Groups[3].Value)"
    $href = [System.Net.WebUtility]::HtmlDecode($m.Groups[1].Value)
    if ($href.StartsWith("/")) {
        $href = "https://www.cms.gov$href"
    }
    $cpscPages[$ym] = $href
}

for ($d = $start; $d -le $end; $d = $d.AddMonths(1)) {
    $ym = $d.ToString("yyyy-MM")
    $out = ".\data\raw\cpsc\monthly-enrollment-cpsc-$ym.zip"
    if ((Test-Path $out) -and ((Get-Item $out).Length -gt 0)) {
        Write-Host "Already present monthly-enrollment-cpsc-$ym.zip"
        continue
    }

    try {
        if (-not $cpscPages.ContainsKey($ym)) {
            Write-Warning "No CMS CPSC detail page found for $ym"
            continue
        }

        $url = Get-CmsZipFromDetailPage $cpscPages[$ym]
        if ($null -eq $url) {
            Write-Warning "No CPSC ZIP link found for $ym"
            continue
        }

        Save-Url $url $out
        Write-Host "Downloaded CPSC $ym from $url"
    }
    catch {
        Write-Warning "Skipped CPSC ${ym}: $($_.Exception.Message)"
    }
}

# Data.CMS.gov optional public-use sources. These are intentionally kept as
# registered export/API targets so the project stays lightweight and reproducible.
$manualSources = @"
source,title,url,notes
data_cms,Medicare Geographic Variation - by National State and County,https://data.cms.gov/summary-statistics-on-use-and-payments/medicare-geographic-comparisons/medicare-geographic-variation-by-national-state-county,Optional manual/API export for geographic spending and utilization context
data_cms,Medicare Physician and Other Practitioners - by Provider and Service,https://data.cms.gov/provider-summary-by-type-of-service/medicare-physician-other-practitioners/medicare-physician-other-practitioners-by-provider-and-service,Optional large public-use file for specialty/procedure/payment proxy features
oig,HHS OIG Medicare Advantage prior authorization denial report,https://oig.hhs.gov/reports/all/2022/some-medicare-advantage-organization-denials-of-prior-authorization-requests-raise-concerns-about-beneficiary-access-to-medically-necessary-care/,Optional benchmark/context source
"@
$manualSources | Set-Content ".\data\raw\manual_exports\optional_source_links.csv"

Save-Url "https://data.cms.gov/sites/default/files/2021-08/medicare-geographic-variation-by-national-state-county-data-dictionary.pdf" ".\data\raw\manual_exports\medicare-geographic-variation-data-dictionary.pdf"
Save-Url "https://data.cms.gov/sites/default/files/2020-09/Medicare%20Physician%20%26%20Other%20Practitioners%20-%20by%20Provider%20and%20Service-Data-Dictionary.pdf" ".\data\raw\manual_exports\medicare-physician-provider-service-data-dictionary.pdf"
