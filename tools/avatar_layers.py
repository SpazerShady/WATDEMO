#!/usr/bin/env python3
"""สร้างภาพอวตารแบบเลเยอร์สำหรับฉากกิจกรรม BC07–BC09 ของต้นแบบ WAT-Monk

วางภาพต้นฉบับ (PNG พื้นโปร่งใส ขนาดเท่าภาพท่าเดิม) ไว้ที่ art/<รหัสท่า>/
  body.png              ตัว หน้า มือ เท้า (ผิวโทน 2) — ต้องมี
  outfit-o0.png … o3    ชุด 0 แม่ชี · 1 ชุดขาวทำบุญ · 2 ขาวนวลชาย · 3 ขาวนวลหญิง (มีเท่าที่วาด)
  hair-h0.png … h2      ทรงสั้น · ทรงยาว · ทรงรวบ ในสีน้ำตาลเข้ม (มีเท่าที่วาด)
  prop-back.png         ของถือที่อยู่หลังตัว (ถ้ามี)
  prop-front.png        ของถือที่อยู่หน้ามือ (ถ้ามี)
แล้วรัน:  python3 tools/avatar_layers.py art
ผลลัพธ์: img/avp-<รหัสท่า>-*.webp และอัปเดต WM_AVL ใน index.html ให้ฉากใช้ภาพเลเยอร์ทันที
ต้องใช้ Pillow และ numpy
"""
import json, os, re, sys
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSES = {  # รหัสท่า → ภาพเดิม (ใช้ตรวจขนาด)
    '0819022d': '0819022dd4cc63b97dd451606d4ab844.png', '3a9a9977': '3a9a9977439909815d61c2c0f5d2acc7.png',
    'dbf6e9bd': 'dbf6e9bdada703641c7bde88daf49835.png', '93680193': '93680193307946640d7b27c73066506e.png',
    '62112696': '62112696705ad8114977822d299d92d0.png', '5fea19e2': '5fea19e2122b39f1ee9167b49cc283fd.png',
    '4404c022': '4404c022cc56fb6e98f232bf180b328f.png', '1426bde0': '1426bde0638f89abdf28e6363553d348.png',
    'c38ebcb5': 'c38ebcb511ef8696d022400dec6c5a7d.png'}
# สีเดียวกับ BC06 (feColorMatrix แนวทแยง: ค่าใหม่ = s × ค่าเดิม + o)
M_h = np.array([.245, .157, .10]); M_s = np.array([.904, .628, .455])
def mat(T, s, M): return s, np.array(T) - s * M
HAIR = {0: mat([.12, .11, .11], .6, M_h), 1: mat([.47, .30, .16], 1.25, M_h), 2: mat([.29, .188, .125], 1.1, M_h)}
SKIN = {0: mat([.955, .78, .64], .85, M_s), 1: (1, np.zeros(3)), 2: mat([.776, .549, .369], .9, M_s)}

def load(p):
    im = Image.open(p).convert('RGBA'); a = np.asarray(im).astype(float) / 255; return im.size, a[..., :3], a[..., 3:4]
def save(rgb, a, p): Image.fromarray((np.dstack([np.clip(rgb, 0, 1), a]) * 255).round().astype(np.uint8), 'RGBA').save(p, quality=90, method=6)
def recolor(rgb, sv): s, o = sv; return np.clip(rgb * s + o, 0, 1)

def main(art):
    img = os.path.join(ROOT, 'img'); manifest = {}
    for pose in sorted(os.listdir(art)):
        d = os.path.join(art, pose)
        if pose not in POSES or not os.path.isdir(d): print('ข้าม', pose); continue
        ref = Image.open(os.path.join(img, POSES[pose])).size
        if not os.path.exists(os.path.join(d, 'body.png')): print(pose, ': ไม่มี body.png'); continue
        def chk(name):
            size, rgb, a = load(os.path.join(d, name))
            if size != ref: raise SystemExit(f'{pose}/{name} ขนาด {size} ต้องเท่าภาพเดิม {ref}')
            return rgb, a
        rgb, a = chk('body.png')
        r, g, b = rgb[..., 0] * 255, rgb[..., 1] * 255, rgb[..., 2] * 255
        lum = .299 * r + .587 * g + .114 * b
        skin = (((r - g) > 40) & ((g - b) > 12) & (b > .33 * r) & (b > 55) & (lum > 80))[..., None].astype(float)
        for s, sv in SKIN.items(): save(rgb * (1 - skin) + recolor(rgb, sv) * skin, a, os.path.join(img, f'avp-{pose}-body-s{s}.webp'))
        m = {'o': [], 'h': [], 'pb': 0, 'pf': 0}
        for o in range(4):
            if os.path.exists(os.path.join(d, f'outfit-o{o}.png')):
                rgb, a = chk(f'outfit-o{o}.png'); save(rgb, a, os.path.join(img, f'avp-{pose}-outfit-o{o}.webp')); m['o'].append(o)
        for h in range(3):
            if os.path.exists(os.path.join(d, f'hair-h{h}.png')):
                rgb, a = chk(f'hair-h{h}.png')
                for c, sv in HAIR.items(): save(recolor(rgb, sv), a, os.path.join(img, f'avp-{pose}-hair-h{h}-c{c}.webp'))
                m['h'].append(h)
        for nm, k in (('prop-back', 'pb'), ('prop-front', 'pf')):
            if os.path.exists(os.path.join(d, nm + '.png')):
                rgb, a = chk(nm + '.png'); save(rgb, a, os.path.join(img, f'avp-{pose}-{nm}.webp')); m[k] = 1
        if m['o'] and m['h']: manifest[pose] = m; print(pose, m)
        else: print(pose, ': ต้องมีชุดอย่างน้อย 1 และทรงผมอย่างน้อย 1')
    ix = os.path.join(ROOT, 'index.html'); s = open(ix, encoding='utf-8').read()
    s2 = re.sub(r'var WM_AVL = \{.*?\}; // WM_AVL_END', 'var WM_AVL = ' + json.dumps(manifest, separators=(',', ':')) + '; // WM_AVL_END', s, count=1, flags=re.S)
    if s2 == s and manifest: raise SystemExit('ไม่พบบรรทัด WM_AVL ใน index.html')
    open(ix, 'w', encoding='utf-8').write(s2); print('อัปเดต index.html แล้ว ·', len(manifest), 'ท่า')

if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'art'))
