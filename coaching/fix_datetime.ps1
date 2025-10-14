# Fix datetime.utcnow() deprecation warnings in coaching service
$files = Get-ChildItem -Path 'coaching' -Filter '*.py' -Recurse | Where-Object { $_.FullName -notmatch '__pycache__|htmlcov|\.pytest_cache' }

foreach ($file in $files) {
    $content = Get-Content $file.FullName -Raw
    if ($content -match 'datetime\.utcnow\(\)') {
        # Check if UTC is imported
        if ($content -notmatch 'from datetime import.*UTC') {
            # Add UTC import
            $content = $content -replace '(from datetime import[^
]+)', '$1, UTC'
        }
        # Replace datetime.utcnow() with datetime.now(UTC)
        $content = $content -replace 'datetime\.utcnow\(\)', 'datetime.now(UTC)'
        Set-Content -Path $file.FullName -Value $content
        Write-Host "Fixed: $($file.FullName)"
    }
}
Write-Host "Done!"
