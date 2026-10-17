# Negative-Space Audit — Windows Vista (Terry, 2009-11-12)

Third OS variant, completing the audit across all three validated platforms
(Windows XP, Windows Vista, Windows 11). This is the setup-phase Vista capture
with high deletion/transient residue, giving a large omitted set (116,745
entries) and therefore a demanding test.

Method: identical to the XP and Win11 audits — classify the complete omitted set
by path, then inspect individually every entry that could hold user-authored
content.

## Result

~99.96% of the omitted set is OS, application (including a root-level Python 2.6
install and AVG antivirus), system, boot, and default-profile content. The
user-space residue, inspected in full (40 entries), contains zero files created
by the disk's actual user (Terry):

- Vista sample media: the stock bundled files Public\Music\Sample Music\
  (Amanda.wma, Despertar.wma, Symphony_No_3.wma, etc.) and
  Public\Videos\Sample Videos\ (Bear.wmv, Butterfly.wmv, Lake.wmv). Shipped with
  every Vista install.
- Default IE7 bookmarks: Terry\Favorites\ entries under MSN Websites\,
  Microsoft Websites\, and Windows Live\. OS-seeded, not user-created.
- Default account files: Terry\Contacts\Terry.contact (empty default contact),
  a GUID-named system-generated entry.

The UNCLASSIFIED bucket was almost entirely a root-level Python26\ installation
(~3,000 entries), AVG antivirus, and boot files (BOOTSECT.BAK, config.sys,
Boot\), all application/system, no user content.

## Confirmation: Layer C reached Terry's content

HVEA acquired 1,257 entries under Terry's profile. As a setup-phase capture, the
machine held limited organic user content, but what existed was acquired,
including Downloads\OOo_3.1.1_Win32Intel_install_wJRE_en-US.exe (a downloaded
OpenOffice installer, software-provenance evidence) and desktop application
shortcuts. The omitted Vista sample media and default bookmarks were the only
user-space content left behind.

## Three-OS summary (complete)

| | Win 11 | XP (Jo) | Vista (Terry) |
|---|---|---|---|
| Omitted entries | 308,833 | 28,782 | 116,745 |
| Classified inert | 99.99% | 99.16% | 99.96% |
| User-authored files omitted | 0 | 0 | 0 |
| Real user content acquired | documents, installers | 1,060 files (camera photos/video) | 1,257 entries (downloaded installer) |
| Omitted user-space character | empty dirs, OS defaults | OS sample pictures, blank templates | Vista sample media, default bookmarks |

Across three operating systems and three markedly different disk profiles
(modern controlled, content-rich organic, high-residue setup-phase), HVEA-SIFTING
omitted no user-authored content while acquiring the user's evidentiary material
where present. The negative space is forensically inert on every image tested.
