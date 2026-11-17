#!/usr/bin/env python3
from pathlib import Path
import argparse, base64, hashlib, json, shutil, subprocess, tempfile, zipfile, zlib

root = Path(__file__).resolve().parents[1]
src = root / 'source'
out = root / 'dist'
p = argparse.ArgumentParser()
p.add_argument('--with-source', action='store_true', help='Include the original SoundFont and source archive (requires network and dpkg-deb).')
args = p.parse_args()
out.mkdir(exist_ok=True)
bank = b''.join(x.read_bytes() for x in sorted((src/'bank').glob('*.part')))
assert hashlib.sha256(bank).hexdigest() == 'f58163ad4d50badceff3e6e706ac47b1057e69dff2d532b72b906d8acfca9dd1', 'Sound bank checksum mismatch'
assert sum(map(len,json.loads(bank).values())) == 188
template = (src/'semitone_template.html').read_bytes()
assert template.count(b'/*BANK*/{}') == 1
html = template.replace(b'/*BANK*/{}',bank)
(out/'index.html').write_bytes(html)
print('HTML SHA-256:',hashlib.sha256(html).hexdigest())
for n in ['manifest.webmanifest','sw.js','.nojekyll']:
    shutil.copyfile(src/n,out/n)
(out/'icons').mkdir(exist_ok=True)
for n, data in json.loads((src/'icons.json').read_text()).items():
    (out/'icons'/n).write_bytes(zlib.decompress(base64.b64decode(data)))
if args.with_source:
    with tempfile.TemporaryDirectory() as tmp:
        tmp=Path(tmp)
        pkg=tmp/'soundfont.deb'
        subprocess.run(['curl','--fail','--location','--retry','3','--output',str(pkg),'https://ftp.debian.org/debian/pool/main/t/timgm6mb-soundfont/timgm6mb-soundfont_1.3-5_all.deb'],check=True)
        subprocess.run(['dpkg-deb','-x',str(pkg),str(tmp/'unpack')],check=True)
        sf=tmp/'unpack/usr/share/sounds/sf2/TimGM6mb.sf2'
        assert hashlib.sha256(sf.read_bytes()).hexdigest()=='c5378b62028c920cb11e4803327983fee2f2cdff5dc89c708e39da417e51c854'
        with zipfile.ZipFile(out/'source.zip','w',zipfile.ZIP_DEFLATED) as z:
            z.write(sf,'source/TimGM6mb.sf2')
            z.write(tmp/'unpack/usr/share/doc/timgm6mb-soundfont/copyright','source/SOUNDFONT-CREDITS.txt')
            z.write('/usr/share/common-licenses/GPL-2','source/LICENSE-GPL-2.txt')
            z.write(src/'semitone_template.html','source/semitone_template.html')
            z.write(src/'generate_bank.py','source/generate_bank.py')
            z.writestr('source/bank.json',bank)
            z.writestr('source/rebuild.py',"from pathlib import Path\np=Path(__file__).parent\n(p.parent/'index.html').write_bytes((p/'semitone_template.html').read_bytes().replace(b'/*BANK*/{}',(p/'bank.json').read_bytes()))\n")
            z.write(root/'README.md','README.md')
            for n in ['manifest.webmanifest','sw.js','.nojekyll']:
                z.write(out/n,n)
            for f in (out/'icons').glob('*.png'):
                z.write(f,'icons/'+f.name)
print('Built',out)
