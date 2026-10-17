#!/usr/bin/env python3
"""Negative-space audit (XP + Win11 aware): classify HVEA-omitted files."""
import json, sys, re
from collections import Counter

if len(sys.argv) < 2:
    sys.exit("usage: classify_omitted.py <reasoning_trace.jsonl> [residue_out.txt]")
TRACE = sys.argv[1]
RESIDUE_OUT = sys.argv[2] if len(sys.argv) > 2 else "omitted_residue.txt"

USERROOT = re.compile(r'^/(users|documents and settings)/[^/]+', re.I)

def rules():
    R = []; add = lambda n, fn: R.append((n, fn))
    add("NTFS metadata / directory pseudo-entry", lambda p: (
        p.rstrip('/').endswith(('/.', '/..'))
        or re.search(r'/\$(mft|mftmirr|logfile|bitmap|boot|badclus|secure|volume|'
                     r'attrdef|upcase|extend|objid|quota|reparse|usnjrnl)', p) is not None
        or p.lower() in ('/$fat1', '/$fat2', '/$mbr')))
    add("Registry hive journal (hive acquired by Layer B)", lambda p: bool(
        re.search(r'ntuser\.dat.*(\.log\d?|\.blf|\.regtrans-ms|\.tm\b)', p)
        or re.search(r'/ntuser\.ini$', p)
        or re.search(r'usrclass\.dat.*(\.log|\.blf|\.regtrans-ms)', p)))
    add("OS core (Windows system tree)", lambda p: any(s in p for s in (
        '/windows/winsxs/', '/windows/system32/', '/windows/syswow64/',
        '/windows/servicing/', '/windows/assembly/', '/windows/microsoft.net/',
        '/windows/inf/', '/windows/policydefinitions/', '/windows/systemapps/',
        '/windows/systemresources/', '/windows/rescache/', '/windows/uus/',
        '/windows/immersivecontrolpanel/', '/windows/apppatch/', '/windows/branding/',
        '/windows/cursors/', '/windows/media/', '/windows/waas/', '/windows/schemas/',
        '/windows/web/', '/windows/security/', '/windows/provisioning/', '/windows/pla/',
        '/windows/resources/', '/windows/appcompat/', '/windows/l2schemas/',
        '/windows/systemtemp/', '/windows/speech_onecore/', '/windows/diagtrack/',
        '/windows/inputmethod/', '/windows/shellexperiences/', '/windows/installer/',
        '/windows/servicestate/', '/windows/speech/', '/windows/performance/',
        '/windows/inboxapps/', '/windows/skb/', '/windows/vss/', '/windows/csc/',
        '/windows/microsoft/', '/windows/')))
    add("Driver store", lambda p: '/driverstore/' in p or '/drivers/' in p)
    add("Installed applications", lambda p: any(s in p for s in (
        '/program files/', '/program files (x86)/', '/programdata/package cache/')))

    add("Installed application (root-level)", lambda p: bool(
        re.search(r'^/(python\d*|perl|ruby|php|node|go|rust|java|jdk|jre\d*)/', p)
        or re.search(r'^/\$avg', p) or '/$avg/' in p
        or re.search(r'^/(dell|hp|lenovo|intel|nvidia|amd|realtek)/', p)))

    add("Boot / firmware files", lambda p: bool(
        re.search(r'^/(bootsect\.bak|bootmgr|ntldr|ntdetect\.com|io\.sys|msdos\.sys|'
                  r'config\.sys|autoexec\.bat|boot\.ini|winpepge\.sys)/?$', p)
        or re.search(r'^/boot/', p) or '/perflogs/' in p))

    add("Fonts / help / localization", lambda p: any(s in p for s in (
        '/windows/fonts/', '/windows/help/', '/windows/ime/', '/windows/globalization/',
        '/_mui', '.mui')) or re.search(r'/[a-z]{2}-[a-z]{2}/', p) is not None)
    add("Recovery / boot / system volume", lambda p: any(s in p for s in (
        '/recovery/', '/boot/', '/$winre', '/bootmgr', '/system volume information/')))
    add("User-space application cache", lambda p: bool(
        re.search(r'/(users|documents and settings)/[^/]+/appdata/', p)
        or re.search(r'/(users|documents and settings)/[^/]+/local settings/', p)
        or re.search(r'/(users|documents and settings)/[^/]+/application data/', p)
        or re.search(r'/(users|documents and settings)/[^/]+/\.[a-z0-9_]+', p)))
    add("System cache / logs / telemetry / ProgramData", lambda p: any(s in p for s in (
        '/windows/logs/', '/windows/temp/', '/windows/softwaredistribution/',
        '/windows/prefetch/', '/windows/diagnostics/', '/windows/debug/',
        '/windows/panther/', '/windows/serviceprofiles/', '/config/systemprofile/',
        '/programdata/', '/windowsapps/', '/$orphanfiles/')))
    add("Page/hiber/swap files", lambda p: any(s in p for s in (
        'pagefile.sys', 'hiberfil.sys', 'swapfile.sys', 'dumpstack.log')))
    add("OS-seeded user default (shortcut/metadata/avatar/library/search)", lambda p: bool(
        re.search(r'(/desktop\.ini$|/bing\.url$|\.lnk$|\.search-ms$|\.searchconnector-ms$|'
                  r'getting started with onedrive\.pdf$|/\.849c|personal vault\.lnk$|'
                  r'\.library-ms$|/accountpictures/)', p)))
    add("User-profile default directory stub (contents captured separately)", lambda p: (
        bool(re.search(r'/(users|documents and settings)/[^/]+/('
                       r'contacts|cookies|desktop|documents|downloads|favorites|links|'
                       r'music|pictures|videos|searches|templates|sendto|recent|nethood|'
                       r'printhood|start menu|saved games|local settings|application data|'
                       r'my documents|my music|my pictures|my videos|onedrive|appdata|'
                       r'accountpictures|libraries)(/links)?$', p))
        or re.search(r'/(users|documents and settings)/[^/]+$', p) is not None
        or re.search(r'/(users|documents and settings)$', p) is not None
        or re.search(r'/users/(all users|default|default user|public)$', p) is not None))
    return R

RULES = rules()
def classify(path):
    p = path.lower()
    for name, fn in RULES:
        if fn(p): return name
    if USERROOT.search(p): return "** USER CONTENT (REVIEW) **"
    return "** UNCLASSIFIED (REVIEW) **"

cats = Counter(); residue = []; total = 0
with open(TRACE) as f:
    for line in f:
        r = json.loads(line)
        if r["decision"] in ("acquired", "also_serves"): continue
        total += 1
        c = classify(r["inventory_path"]); cats[c] += 1
        if c.startswith("**"): residue.append(r["inventory_path"])

print(f"\n=== OMITTED-SET CLASSIFICATION ===\nTrace: {TRACE}\nTotal omitted: {total:,}\n")
print(f"{'category':58s} {'count':>9s}  {'pct':>7s}\n" + "-"*80)
for c, n in cats.most_common():
    print(f"{c:58s} {n:>9,d}  {100*n/total:6.3f}%")
inert = sum(n for c, n in cats.items() if not c.startswith("**"))
flagged = total - inert
print("-"*80)
print(f"{'INERT / explained':58s} {inert:>9,d}  {100*inert/total:7.4f}%")
print(f"{'** FLAGGED FOR REVIEW **':58s} {flagged:>9,d}  {100*flagged/total:7.4f}%")
with open(RESIDUE_OUT, "w") as out:
    for p in sorted(residue): out.write(p + "\n")
print(f"\nResidue -> {RESIDUE_OUT}  ({len(residue):,} paths)")
