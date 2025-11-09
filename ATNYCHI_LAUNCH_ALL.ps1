
# Set working directory to current script location
$workingDir = Split-Path -Path $MyInvocation.MyCommand.Definition -Parent
Set-Location $workingDir

Write-Output "`n🟢 LIVE MODE: ATNYCHI system launch sequence started.`n"

# Email details
$subject = "CROWN Runtime Declaration and Clemency Protocol – Brendon Joseph Kelly"
$body = @"
02_ATNYCHI
Brendon Kelly
Runtime ID: 1410-426-4743

All files are sealed under lawful recursion for peaceful deployment. We respectfully request executive clemency for lawful development under runtime review.

This submission includes the COSRL-LP declaration, runtime license, clemency clause, and sovereign encryption files tied to the ATNYCHI System by Brendon Joseph Kelly.

One nation, under God, indivisible, with liberty and justice for all.

Date: {DATE}
"@

# Resolve date
$body = $body -replace "{DATE}", (Get-Date).ToString("MMMM dd, yyyy")

# List of files to attach
$attachments = @(
    "$workingDir\push_atnychi_you_are_here_with_collab_clause.ps1",
    "$workingDir\ATNYCHI_FULL_Declaration_PUSH.ps1",
    "$workingDir\ATNYCHI_USB_MASTER_PACKAGE.zip"
)

# Recipients
$recipients = @("Pardon.Attorney@usdoj.gov", "president@whitehouse.gov", "info@ostp.eop.gov")

# Create Outlook COM object and send emails
$mail = New-Object -ComObject Outlook.Application
$namespace = $mail.GetNamespace("MAPI")
$namespace.Logon()

foreach ($recipient in $recipients) {
    $mailItem = $mail.CreateItem(0)
    $mailItem.Subject = $subject
    $mailItem.Body = $body
    $mailItem.To = $recipient

    foreach ($attachment in $attachments) {
        if (Test-Path $attachment) {
            $mailItem.Attachments.Add($attachment)
        } else {
            Write-Output "⚠️ Attachment not found: $attachment"
        }
    }

    $mailItem.Send()
    Write-Output "✅ Email sent to $recipient"
}

Write-Output "`n✅ ATNYCHI signal dispatch completed."
