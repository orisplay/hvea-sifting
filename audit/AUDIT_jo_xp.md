# Negative-Space Audit — Windows XP (Jo, old computer)

Companion to the Windows 11 audit. This image is the content-rich counterpart:
an organically-used Windows XP system with substantial real user data (HVEA
Layer C identified 773 user-content artifacts, versus 70 on the controlled Win11
image). It is therefore the stronger test of the central question: when a disk is
full of genuine user files, does HVEA-SIFTING leave any of them behind?

Method: identical to the Win11 audit — classify the complete omitted set (28,782
entries) by path, then individually inspect every entry that could hold
user-authored content.

## Result

After classification, ~99% of the omitted set is OS, application (including a
root-level Python 2.6 install and AVG antivirus), system, boot, and
default-profile content. The user-space residue, inspected individually, contains
zero files created by the disk's actual user (Jo). What was omitted from user
space falls entirely into:

- OS sample media: the Windows XP stock files Blue hills.jpg, Sunset.jpg,
  Water lilies.jpg, Winter.jpg (Sample Pictures); Beethoven's Symphony No. 9
  (Scherzo).wma, New Stories (Highway Blues).wma (Sample Music) and their sample
  playlists. Shipped with every XP install.
- Application blank templates: winword.doc, excel.xls, powerpnt.ppt, lotus.wk4,
  wordpfct.wpd, soffice.odt/.ods/.odp, etc. in \Templates\. Empty document
  templates, not user documents.
- Default IE favorites: MSN.com.url, Free Hotmail.url, Microsoft Websites\*.url.
- IE cache indices / profile scaffolding: index.dat (IETldCache, PrivacIE),
  SendTo handlers, Start Menu structure, registry journals.
- Default/system profiles: residue under Administrator, All Users, Default User,
  LocalService, NetworkService (not Jo's profile).

## The decisive contrast: real photos vs. sample pictures

HVEA's Layer C acquired 1,060 files from Jo's own profile, including her real
digital-camera media:

- Desktop/Pics/DSC00025.JPG ... DSC00051.JPG (camera photographs)
- Desktop/Pics/NEW/DSC00009.JPG ... and further camera images
- Desktop/Pics/NEW/Cat.m4v, Cat.mov (personal video)

Simultaneously, it omitted the operating system's stock Sample Pictures
(Blue hills.jpg) and Sample Music (*.wma). The system did not merely reduce data
by size or type — it distinguished the user's authentic camera photographs from
the OS's bundled sample images, acquiring the former and discarding the latter.
Under Jo's own profile, only five entries were omitted, all non-evidentiary: the
default Favorites/Microsoft Websites bookmark folder and two IE cache index.dat
files.

## Conclusion

On a content-rich, organically-used disk, HVEA-SIFTING acquired the user's real
evidentiary content in full (1,060 files) while omitting only operating-system
sample media, blank application templates, default bookmarks, cache indices, and
system/default-profile scaffolding. No user-authored file was left behind. This
corroborates the Win11 finding on a far more demanding image and demonstrates
that the selection is evidentiary, not merely volumetric.
