# Convert-PptToPdf.ps1
# Converts all .pptx files in the projects/ folder to .pdf for visual reasoning.

$targetFolder = Join-Path $PSScriptRoot "..\projects"
if (-not (Test-Path $targetFolder)) {
    Write-Host "Error: Projects folder not found at $targetFolder" -ForegroundColor Red
    exit
}

$ppt = New-Object -ComObject PowerPoint.Application
$ppt.Visible = $false

Write-Host "Starting conversion in: $targetFolder" -ForegroundColor Cyan

Get-ChildItem -Path $targetFolder -Filter *.pptx | ForEach-Object {
    $pptxPath = $_.FullName
    $pdfPath  = [System.IO.Path]::ChangeExtension($pptxPath, ".pdf")

    try {
        $presentation = $ppt.Presentations.Open($pptxPath, $false, $false, $false)
        $presentation.SaveAs($pdfPath, 32) # 32 = ppSaveAsPDF
        $presentation.Close()

        Remove-Item $pptxPath -Force
        Write-Host "✓ Converted and cleaned up: $($_.Name)" -ForegroundColor Green
    }
    catch {
        Write-Host "✗ Failed to convert: $($_.Name)" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Gray
    }
}

$ppt.Quit()
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($ppt) | Out-Null
[GC]::Collect()
[GC]::WaitForPendingFinalizers()

Write-Host "Batch conversion complete." -ForegroundColor Cyan
