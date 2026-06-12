# Negative-Space Audit — Windows 11 (W11_HVEA_14D)

**Question addressed:** Does HVEA-SIFTING's selective acquisition leave behind
forensically important data? I.e., is the ~90% of the disk that is not imaged
genuinely inert?

**Method:** Every inventory entry HVEA examined carries an explicit acquire/omit
decision (Phase 1 reasoning trace, one record per file). This audit takes the
complete omitted set (308,833 entries) and classifies each by path, then
enumerates by hand every entry that could conceivably hold user-authored
content. The classifier is deterministic and reproducible (classify_omitted.py).

## Result

99.9%+ of the omitted set classifies into OS, application, and system categories
(OS core / WinSxS / System32 / SystemApps, installed applications, system cache
and telemetry, fonts, recovery, driver store, page and hibernation files). The
remainder was inspected individually and consists exclusively of:

- Empty user-profile directory stubs (Documents, Desktop, Downloads, Pictures,
  OneDrive/Documents, Videos/Captures). Directory entries with no file content;
  where these directories held files, the files were acquired (see below).
- Registry hive journals (NTUSER.DAT.LOG*, .blf, .regtrans-ms, ntuser.ini).
  The hive itself (NTUSER.DAT) is acquired by Layer B.
- OS-seeded defaults: desktop.ini, default .lnk shortcuts, Bing.url, saved
  searches, default account-picture avatars, the default OneDrive welcome PDF,
  a default library descriptor. Identical on any fresh Win11 install.
- $OrphanFiles: SleuthKit synthetic container for files with a lost parent MFT
  reference; by filename these are OneDrive/Office/Edge UI assets, installer
  binaries (OneDriveSetup.exe, old_msedge.exe), and a Chromium temp dir.
- Filesystem structures: $MBR, $FAT1, $FAT2.

## Independent confirmation: HVEA Layer C reaches user content

The omission of empty user-directory stubs is only defensible if HVEA acquires
the files in those directories when present. It does. Layer C acquired 70 entries
from user evidentiary directories on this image, including:

- Users/Alexh/Documents/differential information.odt
- Users/Alexh/Documents/Personal/How does it work.txt
- Users/Alexh/Downloads/7z2600-x64.exe
- Users/Alexh/Downloads/ChromeSetup.exe
- Users/Alexh/Downloads/npp.8.9.Installer.x64.exe
- Users/Alexh/Downloads/LibreOffice_26.2.0_Win_x86-64_helppack_en-US.msi
- Users/Public/Documents/differential information.odt
- Users/Public/Desktop/{Autopsy, Google Chrome, LibreOffice, Microsoft Edge}.lnk

The user documents, downloaded installers, and application shortcuts that
constitute the actual evidentiary footprint were all acquired. What remained in
those directories, and was therefore omitted, was only the empty container entry
or OS-default metadata.

## Conclusion

On the Windows 11 image, the data HVEA-SIFTING did not acquire is forensically
inert: no user-authored documents, media, downloads, or created files. Every
omitted entry is attributable to operating-system or application bulk, system
metadata, OS-seeded defaults, or empty directory structure, each category
enumerable and independently verifiable.
