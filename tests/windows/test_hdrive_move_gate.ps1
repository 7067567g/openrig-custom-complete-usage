# Tests for Windows move-only gate. Uses only a temp directory, never H:.
$ErrorActionPreference = 'Stop'
$script:Utf8 = New-Object System.Text.UTF8Encoding($false)

function Assert-True($Condition, [string]$Message) {
    if (-not $Condition) { throw "ASSERT FAILED: $Message" }
}
function Ext([string]$Path) { if ($Path.StartsWith('\\?\')) { return $Path }; return '\\?\' + $Path }
function Write-Utf8([string]$Path, [string]$Text) {
    $parent = Split-Path -Parent $Path
    if ($parent) { [IO.Directory]::CreateDirectory((Ext $parent)) | Out-Null }
    [IO.File]::WriteAllText((Ext $Path), $Text, $script:Utf8)
}

$base = Join-Path $env:TEMP ('hgate-test-' + [guid]::NewGuid().ToString('N'))
$root = Join-Path $base 'root'
$storage = Join-Path $root '_storage'
$pending = Join-Path $storage 'pending'
$docs = Join-Path $storage 'docs'
[IO.Directory]::CreateDirectory((Ext $root)) | Out-Null
[IO.Directory]::CreateDirectory((Ext (Join-Path $root 'JASON'))) | Out-Null

$protected = [ordered]@{
    protected_toplevel = @('JASON')
    protected_root_extensions = @('.xlsx','.xls','.pptx','.ppt')
    protected_root_files = @('license.lic')
}
$protectedFile = Join-Path $base 'protected.json'
Write-Utf8 $protectedFile (($protected | ConvertTo-Json -Depth 5) + "`n")

$wgRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$gateSource = Join-Path $wgRoot 'scripts\windows\hdrive_move_gate.ps1'
if (-not (Test-Path -LiteralPath $gateSource)) { throw "Gate script not found: $gateSource" }
$localGate = Join-Path $base 'hdrive_move_gate.ps1'
Write-Utf8 $localGate (Get-Content -LiteralPath $gateSource -Raw -Encoding UTF8)

function Invoke-Gate([string[]]$GateArgs) {
    $out = & powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $localGate @GateArgs 2>&1
    $code = $LASTEXITCODE
    return [pscustomobject]@{ Code = $code; Output = (($out | Out-String).Trim()) }
}

$runRoot = Join-Path $base 'run'
$r = Invoke-Gate @('-Command','init','-RunRoot',$runRoot,'-Root',$root,'-StorageRoot',$storage,'-PendingRoot',$pending,'-ProtectedManifest',$protectedFile,'-SafetyReviewer','safety-a1','-HumanApprover','user')
Assert-True ($r.Code -eq 0) ("init failed: " + $r.Output)

function New-ActionFile([string]$Name, $Content) {
    $p = Join-Path $base $Name
    if ($Content -is [string]) {
        Write-Utf8 $p ($Content + "`n")
    } else {
        Write-Utf8 $p (($Content | ConvertTo-Json -Compress -Depth 8) + "`n")
    }
    return $p
}
function Propose-One($Action) {
    $ids = @(Propose-Many @($Action))
    return [string]$ids[0]
}
function Propose-Many($Actions) {
    $lines = @($Actions | ForEach-Object { $_ | ConvertTo-Json -Compress -Depth 8 })
    $p = New-ActionFile ('action-' + [guid]::NewGuid().ToString('N') + '.jsonl') ($lines -join "`n")
    $pr = Invoke-Gate @('-Command','propose','-RunRoot',$runRoot,'-ActionFile',$p,'-Agent','tdo-a1')
    Assert-True ($pr.Code -eq 0) ("propose failed: " + $pr.Output)
    $st = Invoke-Gate @('-Command','status','-RunRoot',$runRoot,'-Json')
    Assert-True ($st.Code -eq 0) ("status failed: " + $st.Output)
    $obj = $st.Output | ConvertFrom-Json
    return @($obj.rows[-$Actions.Count..-1] | ForEach-Object { [string]$_.action_id })
}
function Gate-All {
    $g = Invoke-Gate @('-Command','gate','-RunRoot',$runRoot)
    Assert-True ($g.Code -eq 0) ("gate failed: " + $g.Output)
    return $g
}
function Get-Row([string]$Id) {
    $st = Invoke-Gate @('-Command','status','-RunRoot',$runRoot,'-Json')
    Assert-True ($st.Code -eq 0) ("status failed: " + $st.Output)
    $obj = $st.Output | ConvertFrom-Json
    return @($obj.rows | Where-Object { $_.action_id -eq $Id })[0]
}
function Run-One([string]$Id) {
    return Invoke-Gate @('-Command','run','-RunRoot',$runRoot,'-Action',$Id,'-Agent','tdo-a2')
}

# 1) mkdir storage, docs, pending
foreach ($target in @($storage, $docs, $pending)) {
    $id = Propose-One ([ordered]@{ op='mkdir'; intent=('create ' + $target); dst=$target })
    [void](Gate-All)
    $row = Get-Row $id
    Assert-True ($row.gate -eq 'PASS') ("mkdir should PASS: " + $row.gate)
    $rr = Run-One $id
    Assert-True ($rr.Code -eq 0) ("mkdir run failed: " + $rr.Output)
    Assert-True ([IO.Directory]::Exists((Ext $target))) ("missing created dir: " + $target)
}

# 2) ordinary file move
$srcDir = Join-Path $root 'src'
[IO.Directory]::CreateDirectory((Ext $srcDir)) | Out-Null
$src1 = Join-Path $srcDir 'a.txt'
Write-Utf8 $src1 "hello`n"
$dst1 = Join-Path $docs 'a.txt'
$id1 = Propose-One ([ordered]@{ op='move'; intent='move file a to docs'; src=$src1; dst=$dst1 })
[void](Gate-All)
$row1 = Get-Row $id1
Assert-True ($row1.gate -eq 'PASS') ("normal move should PASS: " + $row1.gate)
$run1 = Run-One $id1
Assert-True ($run1.Code -eq 0) ("normal move failed: " + $run1.Output)
Assert-True ((-not [IO.File]::Exists((Ext $src1))) -and [IO.File]::Exists((Ext $dst1))) 'normal move effect wrong'

# 2b) batch runner: two PASS moves in one PowerShell process, still one-by-one internally
$b1 = Join-Path $srcDir 'batch1.txt'; Write-Utf8 $b1 'one'
$b2 = Join-Path $srcDir 'batch2.txt'; Write-Utf8 $b2 'two'
$bd1 = Join-Path $docs 'batch1.txt'; $bd2 = Join-Path $docs 'batch2.txt'
$bids = @(Propose-Many @(
    ([ordered]@{ op='move'; intent='batch move one'; src=$b1; dst=$bd1 }),
    ([ordered]@{ op='move'; intent='batch move two'; src=$b2; dst=$bd2 })
))
[void](Gate-All)
foreach ($bid in $bids) { $br = Get-Row $bid; Assert-True ($br.gate -eq 'PASS') ("batch member should PASS: " + $bid) }
$batchFile = Join-Path $base 'batch-ids.txt'
Write-Utf8 $batchFile (($bids -join "`n"))
$brun = Invoke-Gate @('-Command','run-batch','-RunRoot',$runRoot,'-BatchFile',$batchFile,'-Agent','tdo-a2')
Assert-True ($brun.Code -eq 0) ("batch run failed: " + $brun.Output)
Assert-True ([IO.File]::Exists((Ext $bd1)) -and [IO.File]::Exists((Ext $bd2))) 'batch move destinations missing'
Assert-True ((-not [IO.File]::Exists((Ext $b1))) -and (-not [IO.File]::Exists((Ext $b2)))) 'batch move sources remain'

# 3) long path (gate FAIL yellow, safety review, then allowed run)
$longName = ('d' * 120) + '-' + ('e' * 120)
$longDir = Join-Path $srcDir $longName
[IO.Directory]::CreateDirectory((Ext $longDir)) | Out-Null
$longSrc = Join-Path $longDir 'long.txt'
Write-Utf8 $longSrc "long`n"
$longDst = Join-Path $docs 'long.txt'
$idLong = Propose-One ([ordered]@{ op='move'; intent='review long path move'; src=$longSrc; dst=$longDst })
[void](Gate-All)
$rowLong = Get-Row $idLong
Assert-True ($rowLong.gate -eq 'FAIL' -and $rowLong.risk -eq 'yellow') 'long path should be yellow review'
$runNoReview = Run-One $idLong
Assert-True ($runNoReview.Code -ne 0) 'long path must not run without safety review'
$rev = Invoke-Gate @('-Command','review','-RunRoot',$runRoot,'-Action',$idLong,'-Reviewer','safety-a1','-Verdict','approve','-Digest',$rowLong.digest,'-Reason','extended path mechanics verified on temp volume','-Evidence','temp-only long path test')
Assert-True ($rev.Code -eq 0) ("safety review failed: " + $rev.Output)
$runLong = Run-One $idLong
Assert-True ($runLong.Code -eq 0) ("approved long path failed: " + $runLong.Output)
Assert-True ((-not [IO.File]::Exists((Ext $longSrc))) -and [IO.File]::Exists((Ext $longDst))) 'long move effect wrong'

# 4) protected top-level path is hard-blocked even after SAFETY approve
$jas = Join-Path $root 'JASON\b.txt'
Write-Utf8 $jas 'protected'
$destJas = Join-Path $docs 'b.txt'
$idJas = Propose-One ([ordered]@{ op='move'; intent='try protected path'; src=$jas; dst=$destJas })
[void](Gate-All)
$rowJas = Get-Row $idJas
Assert-True ($rowJas.gate -eq 'FAIL') 'protected move must FAIL'
$revJas = Invoke-Gate @('-Command','review','-RunRoot',$runRoot,'-Action',$idJas,'-Reviewer','safety-a1','-Verdict','approve','-Digest',$rowJas.digest,'-Reason','adversarial test: protected must remain blocked','-Evidence','temp-only protected test')
Assert-True ($revJas.Code -eq 0) ("review should record: " + $revJas.Output)
$runJas = Run-One $idJas
Assert-True ($runJas.Code -ne 0) 'protected move must never run'
Assert-True ([IO.File]::Exists((Ext $jas))) 'protected file must remain in place'

# 5) protected root Excel file
$xlsx = Join-Path $root 'keep.xlsx'
Write-Utf8 $xlsx 'sheet'
$idX = Propose-One ([ordered]@{ op='move'; intent='try protected root excel'; src=$xlsx; dst=(Join-Path $docs 'keep.xlsx') })
[void](Gate-All)
$rowX = Get-Row $idX
Assert-True ($rowX.gate -eq 'FAIL') 'root xlsx must FAIL'
$revX = Invoke-Gate @('-Command','review','-RunRoot',$runRoot,'-Action',$idX,'-Reviewer','safety-a1','-Verdict','reject','-Digest',$rowX.digest,'-Reason','root Excel must stay in place per protected rule','-Evidence','temp-only protected root test')
Assert-True ($revX.Code -eq 0) ("root xlsx review should record: " + $revX.Output)
Assert-True ([IO.File]::Exists((Ext $xlsx))) 'root xlsx must remain in place'

# 6) unsupported delete op is hard-blocked
$idDel = Propose-One ([ordered]@{ op='delete'; intent='delete must not be supported'; src=$xlsx; dst=(Join-Path $pending 'keep.xlsx') })
[void](Gate-All)
$rowDel = Get-Row $idDel
Assert-True ($rowDel.gate -eq 'FAIL') 'delete must FAIL'
$revDel = Invoke-Gate @('-Command','review','-RunRoot',$runRoot,'-Action',$idDel,'-Reviewer','safety-a1','-Verdict','reject','-Digest',$rowDel.digest,'-Reason','delete is not a supported op in move-only gate','-Evidence','temp-only delete test')
Assert-True ($revDel.Code -eq 0) ("delete review should record: " + $revDel.Output)
$runDel = Run-One $idDel
Assert-True ($runDel.Code -ne 0) 'delete must never run'

# 7) collision: review approve still cannot execute because precheck blocks
$colSrc = Join-Path $srcDir 'collision.txt'
Write-Utf8 $colSrc 'src'
$colDst = Join-Path $docs 'a.txt'  # already exists
$idCol = Propose-One ([ordered]@{ op='move'; intent='collision precondition test'; src=$colSrc; dst=$colDst })
[void](Gate-All)
$rowCol = Get-Row $idCol
Assert-True ($rowCol.gate -eq 'FAIL') 'collision must FAIL'
$revCol = Invoke-Gate @('-Command','review','-RunRoot',$runRoot,'-Action',$idCol,'-Reviewer','safety-a1','-Verdict','approve','-Digest',$rowCol.digest,'-Reason','adversarial test: precheck must still block collision','-Evidence','temp-only collision test')
Assert-True ($revCol.Code -eq 0) ("collision review should record: " + $revCol.Output)
$runCol = Run-One $idCol
Assert-True ($runCol.Code -ne 0) 'collision must not run'
Assert-True ([IO.File]::Exists((Ext $colSrc))) 'collision source must remain'

# 8) status summary sanity
$st = Invoke-Gate @('-Command','status','-RunRoot',$runRoot,'-Json')
Assert-True ($st.Code -eq 0) 'status must work'
$summary = ($st.Output | ConvertFrom-Json).summary
Assert-True ($summary.actions -ge 9) 'unexpected action count'
Assert-True ($summary.safety_reject -eq 2) 'expected two safety rejects'
Assert-True ($summary.safety_pending -eq 0) 'expected all FAILs reviewed in test'
Write-Host "WINDOWS_GATE_TESTS_OK actions=$($summary.actions) pass=$($summary.gate_pass) fail=$($summary.gate_fail) ok=$($summary.executed_ok) bad=$($summary.executed_bad)"

[IO.Directory]::Delete((Ext $base), $true)
