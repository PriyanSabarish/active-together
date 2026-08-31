$ErrorActionPreference = 'Stop'
$inputPath = 'D:\xwechat_files\wxid_fynu0rcjs47f21_b973\msg\file\2026-08\vicmap_qa_sample(1).csv'
$rows = Import-Csv -LiteralPath $inputPath
$headers = @{ 'User-Agent' = 'Codex-Vicmap-QA/1.0'; Accept = 'application/json' }
$all = @()

for ($start = 0; $start -lt $rows.Count; $start += 15) {
    $end = [math]::Min($start + 14, $rows.Count - 1)
    $chunk = $rows[$start..$end]
    $parts = $chunk | ForEach-Object { 'nwr(around:45,' + $_.latitude + ',' + $_.longitude + ');' }
    $query = '[out:json][timeout:90];(' + ($parts -join '') + ');out tags center;'

    try {
        $response = Invoke-RestMethod -Uri 'https://overpass.kumi.systems/api/interpreter' -Method Post -ContentType 'application/x-www-form-urlencoded; charset=UTF-8' -Headers $headers -Body @{ data = $query }
        foreach ($row in $chunk) {
            $lat = [double]$row.latitude
            $lon = [double]$row.longitude
            $matches = @()
            foreach ($element in $response.elements) {
                if ($null -ne $element.lat) {
                    $elementLat = [double]$element.lat
                    $elementLon = [double]$element.lon
                }
                elseif ($null -ne $element.center.lat) {
                    $elementLat = [double]$element.center.lat
                    $elementLon = [double]$element.center.lon
                }
                else { continue }

                $dy = ($elementLat - $lat) * 111320
                $dx = ($elementLon - $lon) * 111320 * [math]::Cos($lat * [math]::PI / 180)
                $distance = [math]::Sqrt($dx * $dx + $dy * $dy)
                if ($distance -le 60) {
                    $tags = $element.tags
                    $description = @($tags.name, $tags.leisure, $tags.sport, $tags.landuse, $tags.amenity, $tags.highway, $tags.natural, $tags.tourism, $tags.place) | Where-Object { $_ }
                    if ($description.Count) {
                        $matches += ([math]::Round($distance).ToString() + 'm:' + ($description -join '/'))
                    }
                }
            }
            $osmText = (($matches | Select-Object -Unique -First 8) -join '; ')
            $all += [pscustomobject]@{ sample_id = $row.sample_id; osm = $osmText }
        }
    }
    catch {
        foreach ($row in $chunk) {
            $all += [pscustomobject]@{ sample_id = $row.sample_id; osm = 'QUERY_FAILED' }
        }
    }
}

$all | ConvertTo-Json -Depth 3
