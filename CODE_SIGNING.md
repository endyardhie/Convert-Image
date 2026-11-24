# Code signing policy

## Current status

Convert Image is preparing an application to **SignPath Foundation** for free
open-source code signing. The project has not yet been accepted, and the current
Windows preview release is **unsigned**. Preparing a workflow or calculating a
checksum does not make a file digitally signed.

If the application is accepted and signing is enabled, the acknowledgement will
be: **Free code signing provided by [SignPath.io](https://signpath.io), certificate
by [SignPath Foundation](https://signpath.org).** The publisher on those signatures
will be SignPath Foundation.

## Maintainer and responsibilities

| Role | Responsible maintainer |
| --- | --- |
| Committer | [Endy Ardhie — endyardhie](https://github.com/endyardhie) |
| Reviewer | [Endy Ardhie — endyardhie](https://github.com/endyardhie) |
| Signing approver | [Endy Ardhie — endyardhie](https://github.com/endyardhie) |

This is an individually maintained project. Proposed changes from other authors
must be reviewed by the maintainer. Signing access requires multi-factor
authentication on the source repository and signing accounts. Each production
signing request must be approved by the maintainer in SignPath; release signing
must not be configured for automatic approval.

## Build and signing process

Release artifacts are built from the public source repository on GitHub-hosted
Windows runners. Linux and Windows checks must pass before distribution.
The optional signing workflow is started manually from `main` and remains
disabled until the Foundation application, account, and signing policies are ready.

Signing is limited to the project's `ConvertImage.exe`, native
`ConvertImageShell.dll`, and final Windows installer. Product name and version
restrictions must be enforced in the SignPath artifact configurations. The
application and shell extension are signed before they are packaged; the final
installer is signed in a separate request. Signed artifacts are verified and
tested before they are made available for a maintainer to publish.

Python, Tcl/Tk, Pillow, ReportLab, pypdf, codec executables and other upstream
components retain their own licensing and signing identity. They must not be
re-signed with the Foundation certificate for this project. The Inno Setup
uninstaller and upstream runtime files are outside the initial signing scope.
The workflow does not claim that every bundled executable is signed.

Signing credentials stay in the signing service and GitHub's encrypted secrets.
Certificates, private keys and API tokens must not be committed to the repository.

## Privacy policy

**The application processes images locally and does not upload them.** It does
not collect analytics, telemetry, advertising identifiers, or account details.
Image conversion does not require an online account or send image contents or
file paths to the maintainer or SignPath.

Settings and conversion logs remain on the user's computer. Logs may contain
local filenames, paths and conversion errors. They are only shared if the user
chooses to send them. Uninstall preserves images, settings and logs.

Installing missing Linux packages and building from source may contact package
repositories and upstream download services. Downloading releases, using GitHub,
or applying to SignPath is subject to those services' privacy policies. The
signing workflow submits software build artifacts and build metadata to SignPath,
not end-user images or conversion logs.

## Checking a Windows download

Open the file's **Properties → Digital Signatures** to inspect a signature, when
one is available. Use the release's checksum to compare the exact downloaded
bytes. Read each release's signing status; existing unsigned downloads do not
gain a signature retroactively. Signing identifies the publisher and protects
file integrity; it does not guarantee that every Windows security warning will
disappear.

Reference: [SignPath Foundation conditions](https://signpath.org/terms).
