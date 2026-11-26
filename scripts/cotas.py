"""Padroniza a fonte das cotas de um desenho vetorial recortado de um catálogo PDF.

Lê os números das cotas por OCR (horizontal e vertical), apaga os números
originais (curvas ou texto) com redação e reescreve em Bahnschrift, com
vírgula decimal, centralizado no mesmo lugar. Exporta SVG (texto em curvas)
e PNG de conferência.
"""
import re
import subprocess
import tempfile
import os
import fitz

FONT = '/home/claude/alcoa/build/bahnschrift.ttf'
_font = fitz.Font(fontfile=FONT)
CAP = 0.70          # altura dos algarismos / tamanho da fonte (Bahnschrift)
NUM = re.compile(r'^\d{1,4}([.,]\d{1,2})?$')
DPI = 600


def _ocr(img_path):
    out = img_path + '.tsv'
    subprocess.run(['tesseract', img_path, img_path, '--psm', '11', '-c',
                    'tessedit_char_whitelist=0123456789,.R', 'tsv'], capture_output=True)
    rows = []
    with open(out) as f:
        next(f)
        for line in f:
            p = line.rstrip('\n').split('\t')
            if len(p) < 12 or not p[11].strip():
                continue
            t = p[11].strip()
            if NUM.match(t) and float(p[10]) > 40:
                rows.append((t, int(p[6]), int(p[7]), int(p[8]), int(p[9]), float(p[10])))
    return rows


def _dbg():
    return bool(os.environ.get('COTAS_DEBUG'))


SHEAR = 0.0


def _ocr1(img, psm=7):
    import numpy as np
    from PIL import Image
    if SHEAR:
        w, h = img.size; pad = int(abs(SHEAR) * h) + 4
        im2 = Image.new('L', (w + 2 * pad, h), 255); im2.paste(img.convert('L'), (pad, 0))
        img = im2.transform(im2.size, Image.AFFINE, (1, -SHEAR, SHEAR * h / 2, 0, 1, 0), fillcolor=255)
    tmp = tempfile.mktemp(suffix='.png'); img.save(tmp)
    r = subprocess.run(['tesseract', tmp, '-', '--psm', str(psm), '-c', 'tessedit_char_whitelist=0123456789,.', 'tsv'],
                       capture_output=True, text=True).stdout.splitlines()[1:]
    words = [l.split('\t') for l in r]
    words = [(w[11].strip(), float(w[10])) for w in words if len(w) > 11 and w[11].strip()]
    if not words: return '', 0
    t = ''.join(w[0] for w in words); c = sum(w[1] for w in words) / len(words)
    return t, c


def ler_cotas(page, clip, dpi=300, engr=0):
    """Localiza números (grupos de algarismos soltos) e lê cada um. Retorna [(texto, Rect, vertical?)]."""
    import numpy as np, cv2
    from PIL import Image
    k = 72 / dpi
    pm = page.get_pixmap(dpi=dpi, clip=clip, colorspace=fitz.csGRAY)
    g = np.frombuffer(pm.samples, np.uint8).reshape(pm.height, pm.width)
    if engr:
        g = (255 - 255 * cv2.dilate((g < 215).astype(np.uint8), np.ones((3, 3), np.uint8), iterations=engr)).astype(np.uint8)
    bw = (g < 140).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(bw, connectivity=8)
    cand = []
    for i in range(1, n):
        x, y, w, h, a = st[i]
        big, small = max(w, h), min(w, h)
        if 14 <= big <= 70 and small >= 2 and a < 0.75 * w * h + 10 and not (big > 4 * small and small < 5 and big > 40):
            cand.append((x, y, w, h, i))
    # agrupa: horizontal (mesma faixa vertical) ou vertical (mesma faixa horizontal)
    def grupos(vert):
        used = set(); out = []
        for i, c in enumerate(cand):
            if i in used: continue
            grp = [c]; used.add(i); changed = True
            while changed:
                changed = False
                for j, d in enumerate(cand):
                    if j in used: continue
                    for e in grp:
                        if not vert:
                            ok = abs((d[1] + d[3] / 2) - (e[1] + e[3] / 2)) < 0.35 * max(d[3], e[3]) and abs(d[3] - e[3]) < 0.33 * max(d[3], e[3]) \
                                 and (d[0] - (e[0] + e[2]) < 0.75 * e[3] and e[0] - (d[0] + d[2]) < 0.75 * e[3])
                        else:
                            ok = abs((d[0] + d[2] / 2) - (e[0] + e[2] / 2)) < 0.35 * max(d[2], e[2]) and abs(d[2] - e[2]) < 0.33 * max(d[2], e[2]) \
                                 and (d[1] - (e[1] + e[3]) < 0.75 * e[2] and e[1] - (d[1] + d[3]) < 0.75 * e[2])
                        if ok:
                            grp.append(d); used.add(j); changed = True; break
            out.append(grp)
        return out
    res = []
    img = Image.fromarray(g)
    for passo in (False, True):
        for grp in grupos(passo):
            vert = passo
            x0 = min(c[0] for c in grp); y0 = min(c[1] for c in grp)
            x1 = max(c[0] + c[2] for c in grp); y1 = max(c[1] + c[3] for c in grp)
            hh = (x1 - x0) if vert else (y1 - y0)
            if len(grp) == 1 and vert: continue          # 1 algarismo: decide pela leitura horizontal e vertical abaixo
            pad = int(hh * 0.5)
            ids = [c[4] for c in grp]
            # inclui vírgulas/pontos (componentes minúsculos dentro da faixa do grupo)
            sub = lab[max(0, y0 - 2):y1 + 3, max(0, x0 - 2):x1 + 3]
            for lid in np.unique(sub):
                if lid and st[lid][4] < 0.08 * hh * hh * 4 and max(st[lid][2], st[lid][3]) < 0.5 * hh: ids.append(lid)
            m = np.isin(lab, ids)
            if len(grp) >= 2:
                _ys, _xs = np.nonzero(np.isin(lab, [q[4] for q in grp]))
                (_c), (_w, _h), _a = cv2.minAreaRect(np.column_stack([_xs, _ys]).astype(np.float32))
                if _w < _h: _a += 90
                _a = ((_a + 90) % 180) - 90
                if 8 < abs(_a) < 82: continue
            iso = np.where(m, g, 255).astype(np.uint8)
            img_iso = Image.fromarray(iso)
            crop = img_iso.crop((max(0, x0 - pad), max(0, y0 - pad), x1 + pad, y1 + pad))
            grp_rect_extra = [st[l] for l in ids]
            x0 = min(r[0] for r in grp_rect_extra); y0 = min(r[1] for r in grp_rect_extra)
            x1 = max(r[0] + r[2] for r in grp_rect_extra); y1 = max(r[1] + r[3] for r in grp_rect_extra)
            if vert:
                tu, cu = _ocr1(crop.rotate(-90, expand=True))
                td, cd = _ocr1(crop.rotate(90, expand=True))
                (t, c), vert = ((tu, cu), 'up') if (NUM.match(tu) and cu >= cd) or not NUM.match(td) else ((td, cd), 'down')
            else:
                t, c = _ocr1(crop)
            if _dbg(): print('GRP', vert, [(cc[0],cc[1],cc[2],cc[3]) for cc in grp], repr(t), round(c))
            if len(grp) == 1:   # testa também como vertical
                ops = [(_ocr1(crop, psm=10), False), (_ocr1(crop.rotate(-90, expand=True), psm=10), 'up'), (_ocr1(crop.rotate(90, expand=True), psm=10), 'down')]
                ops = [o for o in ops if NUM.match(o[0][0])] or ops
                (t, c), vert = max(ops, key=lambda o: o[0][1])
                hh = (x1 - x0) if vert else (y1 - y0)
            if NUM.match(t) and not re.search(r'[.,]', t) and len(grp) >= 2:
                digs = sorted(grp, key=lambda q: (q[0] if not vert else (-q[1] if vert == 'up' else q[1])))
                extra = [st[l] for l in ids if l not in [q[4] for q in grp]]
                for e in extra:
                    ex, ey = e[0] + e[2] / 2, e[1] + e[3] / 2
                    pos = sum(1 for q in digs if ((q[0] + q[2] / 2) < ex if not vert else ((q[1] + q[3] / 2) > ey if vert == 'up' else (q[1] + q[3] / 2) < ey)))
                    if 0 < pos < len(t) and len(t) == len(digs):
                        t = t[:pos] + '.' + t[pos:]; break
            if NUM.match(t) and c > 30:
                res.append((t, fitz.Rect(clip.x0 + x0 * k, clip.y0 + y0 * k, clip.x0 + x1 * k, clip.y0 + y1 * k), vert, c))
    # 3ª passada: números inclinados (agrupa por proximidade, mede o ângulo, endireita e lê)
    res = [z for z in res if not (len(z[0]) == 1 and z[3] < 80)]
    usados = [z[1] for z in res if z[3] > 85]
    pend = [c for c in cand if not any(fitz.Rect(clip.x0 + c[0] * k, clip.y0 + c[1] * k, clip.x0 + (c[0] + c[2]) * k, clip.y0 + (c[1] + c[3]) * k).intersects(u) for u in usados)]
    vis = set()
    for i, c in enumerate(pend):
        if i in vis: continue
        grp = [c]; vis.add(i); mud = True
        while mud:
            mud = False
            for j, e in enumerate(pend):
                if j in vis: continue
                if any(max(e[0] - (q[0] + q[2]), q[0] - (e[0] + e[2]), e[1] - (q[1] + q[3]), q[1] - (e[1] + e[3])) < 0.7 * max(q[2], q[3]) for q in grp):
                    grp.append(e); vis.add(j); mud = True
        if _dbg(): print('OBL', [(q[0], q[1], q[2], q[3]) for q in grp])
        if len(grp) < 2: continue
        ids = [q[4] for q in grp]
        x0 = min(q[0] for q in grp); y0 = min(q[1] for q in grp); x1 = max(q[0] + q[2] for q in grp); y1 = max(q[1] + q[3] for q in grp)
        sub = lab[max(0, y0 - 3):y1 + 4, max(0, x0 - 3):x1 + 4]
        hh = max(max(q[2], q[3]) for q in grp)
        for lid in np.unique(sub):
            if lid and lid not in ids and st[lid][4] < 0.3 * hh * hh and max(st[lid][2], st[lid][3]) < 0.5 * hh: ids.append(lid)
        m = np.isin(lab, ids)
        ys, xs = np.nonzero(m)
        (cx, cy), (rw, rh), ang = cv2.minAreaRect(np.column_stack([xs, ys]).astype(np.float32))
        if rw < rh: ang += 90
        ang = ((ang + 90) % 180) - 90
        if abs(ang) < 8 or abs(ang) > 82: continue
        pad = int(hh)
        iso = Image.fromarray(np.where(m, g, 255).astype(np.uint8)).crop((max(0, x0 - pad), max(0, y0 - pad), x1 + pad, y1 + pad))
        best = None
        for a in (ang, -ang, ang + 180, 180 - ang):
            t, cc = _ocr1(iso.rotate(a, expand=True, fillcolor=255))
            if NUM.match(t) and (best is None or cc > best[1]): best = (t, cc, a)
        if _dbg(): print('OBL-R', best, round(ang))
        if best and best[1] > 50:
            t, cc, a = best
            if not re.search(r'[.,]', t) and len(ids) > len(grp): pass
            rr = fitz.Rect(clip.x0 + x0 * k, clip.y0 + y0 * k, clip.x0 + x1 * k, clip.y0 + y1 * k)
            res.append((t, rr, ('ang', a, (clip.x0 + cx * k, clip.y0 + cy * k), max(rw, rh) * k, min(rw, rh) * k), cc))
    import os as _os
    if _os.environ.get('COTAS_DEBUG'): print('RES', [(z[0], z[2], round(z[3])) for z in res])
    res.sort(key=lambda z: (-len(z[0].replace(',', '').replace('.', '')), -z[3])); final = []
    for z in res:
        if all((z[1] & f[1]).is_empty or (z[1] & f[1]).get_area() < 0.3 * min(z[1].get_area(), f[1].get_area()) for f in final):
            final.append(z)
    return [(t, r, v) for t, r, v, c in final]


def _desenha_em(sh, x):
    for it in x['items']:
        if it[0] == 'l': sh.draw_line(it[1], it[2])
        elif it[0] == 'c': sh.draw_bezier(it[1], it[2], it[3], it[4])
        elif it[0] == 're': sh.draw_rect(it[1])
        elif it[0] == 'qu': sh.draw_quad(it[1])


def padronizar(src, pno, clip, out_svg, out_png=None, cotas=None, fs=None, cor=(0, 0, 0), limpar_fora=True, remover_texto=False, cinza_para_preto=False, apagar=None, solidificar=False, branco=None, manter_rotulos=False, setas=False, remover=None, normalizar=False, criar=False, enxugar=False, encher=False, sem_imagens=False, apagar_num=1, costura=False):
    clip = fitz.Rect(clip)
    d = fitz.open(src)
    t = fitz.open(); t.insert_pdf(d, from_page=pno - 1, to_page=pno - 1); p = t[0]; p.wrap_contents()
    cotas_txt = []
    if remover_texto:   # texto real: números viram cotas (valor exato do PDF); o resto (código/peso/rótulos) sai
        for b in p.get_text('dict', clip=clip)['blocks']:
            for l in b.get('lines', []):
                tx = ''.join(sp['text'] for sp in l['spans']).strip()
                r = fitz.Rect(l['bbox'])
                mo = re.match(r'^[oøØ∅]\s?(\d{1,4}([.,]\d{1,2})?)$', tx)
                if mo and abs(l['dir'][0]) > 0.9:
                    h = (l['spans'][0]['size'] * 0.716 if l['spans'] else r.height * 0.62); cy = (r.y0 + r.y1) / 2 + r.height * 0.05
                    cotas_txt.append(('Ø' + mo.group(1), fitz.Rect(r.x0, cy - h / 2, r.x1, cy + h / 2), False))
                    p.add_redact_annot(r); continue
                tk = tx.split()
                if len(tk) > 1 and all(NUM.match(q) for q in tk) and abs(l['dir'][0]) > 0.9:
                    # vários números na mesma linha de texto ("12 22.6") -> uma cota por palavra
                    for w in p.get_text('words', clip=r + (-0.5, -0.5, 0.5, 0.5)):
                        if NUM.match(w[4]):
                            wr = fitz.Rect(w[:4]); h = (l['spans'][0]['size'] * 0.716 if l['spans'] else wr.height * 0.62); cy = (wr.y0 + wr.y1) / 2 + wr.height * 0.05
                            cotas_txt.append((w[4], fitz.Rect(wr.x0, cy - h / 2, wr.x1, cy + h / 2), False))
                    p.add_redact_annot(r)
                    continue
                if (NUM.match(tx) or re.match(r'^\d{1,3}°$', tx)) and not re.match(r'^0\d', tx) and not any(r.intersects(fitz.Rect(a)) for a in (apagar or [])[:apagar_num]):
                    dx, dy = l['dir']
                    v = False if abs(dx) > 0.9 else ('up' if dy < 0 else 'down')
                    # caixa da linha inclui ascendente/descendente -> reduz para a altura dos algarismos
                    if v is False:
                        h = (l['spans'][0]['size'] * 0.716 if l['spans'] else r.height * 0.62); cy = (r.y0 + r.y1) / 2 + r.height * 0.05
                        rr = fitz.Rect(r.x0, cy - h / 2, r.x1, cy + h / 2)
                    else:
                        w = (l['spans'][0]['size'] * 0.716 if l['spans'] else r.width * 0.62); cx = (r.x0 + r.x1) / 2
                        rr = fitz.Rect(cx - w / 2, r.y0, cx + w / 2, r.y1)
                    cotas_txt.append((tx, rr, v))
                elif manter_rotulos and (re.match(r'^[A-Z]{1,4}-?\d{2,4}[A-Z]?( ?\*)?$', tx) or re.match(r'^BMT-[A-Z0-9-]+ ?\*?$', tx)) and not any(r.intersects(fitz.Rect(a)) for a in (apagar or [])):
                    continue   # rótulo de peça de referência dentro do desenho (ex.: SU-102)
                p.add_redact_annot(r)
        p.apply_redactions(images=0, graphics=0, text=0)
    for rr in (apagar or []):
        p.add_redact_annot(fitz.Rect(rr)); 
    if apagar: p.apply_redactions(images=0, graphics=1, text=0)
    if remover:   # remove desenhos específicos (pelo retângulo exato) e redesenha o que mais estava dentro
        alvo = [fitz.Rect(a) for a in remover]
        ds = p.get_drawings()
        def eh_alvo(r): return any(abs(r.x0-a.x0)+abs(r.y0-a.y0)+abs(r.x1-a.x1)+abs(r.y1-a.y1) < 0.6 for a in alvo)
        cola = [d for d in ds if not eh_alvo(d['rect']) and any((a+(-0.5,-0.5,0.5,0.5)).contains(d['rect']) for a in alvo)]
        for a in alvo: p.add_redact_annot(a + (-0.3, -0.3, 0.3, 0.3))
        p.apply_redactions(images=0, graphics=1, text=1)   # text=1: não apaga textos (rótulos) dentro da área
        resto = [d for d in p.get_drawings() if eh_alvo(d['rect'])]   # a redação às vezes não tira o traço: cobre de branco
        if resto:
            sh = p.new_shape()
            for d in resto:
                for it in d['items']:
                    if it[0] == 'l': sh.draw_line(it[1], it[2])
                    elif it[0] == 'c': sh.draw_bezier(it[1], it[2], it[3], it[4])
                    elif it[0] == 're': sh.draw_rect(it[1])
                    elif it[0] == 'qu': sh.draw_quad(it[1])
                sh.finish(fill=(1, 1, 1) if d.get('fill') else None, color=(1, 1, 1), width=(d.get('width') or 0.3) + 0.6, closePath=d.get('closePath', False))
            sh.commit()
        for d in cola:
            sh = p.new_shape()
            for it in d['items']:
                if it[0] == 'l': sh.draw_line(it[1], it[2])
                elif it[0] == 'c': sh.draw_bezier(it[1], it[2], it[3], it[4])
                elif it[0] == 're': sh.draw_rect(it[1])
                elif it[0] == 'qu': sh.draw_quad(it[1])
            sh.finish(fill=d.get('fill'), color=d.get('color'), width=d.get('width') or 0, closePath=d.get('closePath', False), even_odd=d.get('even_odd', False), dashes=d.get('dashes') if d.get('dashes') and not d['dashes'].startswith('[]') else None)
            sh.commit()
    if cotas is None:
        cotas = ler_cotas(p, clip)
    cotas = cotas_txt + [c for c in cotas if not any(c[1].intersects(x[1]) for x in cotas_txt)]
    R = p.rect
    if limpar_fora:
        for r in [fitz.Rect(R.x0, R.y0, R.x1, clip.y0), fitz.Rect(R.x0, clip.y1, R.x1, R.y1),
                  fitz.Rect(R.x0, clip.y0, clip.x0, clip.y1), fitz.Rect(clip.x1, clip.y0, R.x1, clip.y1)]:
            p.add_redact_annot(r)
    brancos = []
    for txt, r, vert in cotas:
        if isinstance(vert, tuple):
            _, a, (ccx, ccy), L, S = vert
            L += 1.2; S += 1.2
            mat = fitz.Matrix(-a)
            pts = [fitz.Point(dx, dy) * mat + fitz.Point(ccx, ccy) for dx, dy in ((-L/2, -S/2), (L/2, -S/2), (L/2, S/2), (-L/2, S/2))]
            inv = fitz.Matrix(-a)
            for dr in p.get_drawings():
                rr = dr['rect']
                loc = (fitz.Point((rr.x0 + rr.x1) / 2, (rr.y0 + rr.y1) / 2) - fitz.Point(ccx, ccy)) * inv
                if max(rr.width, rr.height) < L * 1.15 and abs(loc.x) <= L / 2 + 1.5 and abs(loc.y) <= S * 1.1:
                    brancos.append(rr + (-0.4, -0.4, 0.4, 0.4))
            continue
        m = 0.12 * min(r.width, r.height) + 0.4
        p.add_redact_annot(r + (-m, -m, m, m))
    p.apply_redactions(images=2, graphics=1, text=0)
    for rr in brancos:   # algarismos de cotas inclinadas: remove um a um (juntas, algumas curvas sobrevivem)
        p.add_redact_annot(rr); p.apply_redactions(images=0, graphics=1, text=0)
    # 2ª passada: restos do glifo antigo — só peças do tamanho de um algarismo que tocam o miolo do número
    for txt, r, vert in cotas:
        if isinstance(vert, tuple): continue
        cx, cy = (r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2
        core = fitz.Rect(cx - r.width * 0.3, cy - r.height * 0.3, cx + r.width * 0.3, cy + r.height * 0.3)
        hmax = max(r.width, r.height) * 1.05
        for dr in p.get_drawings():
            rr = dr['rect']
            if rr.intersects(core) and max(rr.width, rr.height) <= hmax and r.contains(fitz.Point((rr.x0 + rr.x1) / 2, (rr.y0 + rr.y1) / 2)):
                p.add_redact_annot(rr + (-0.4, -0.4, 0.4, 0.4)); p.apply_redactions(images=0, graphics=1, text=0)
    if sem_imagens:   # fundo em imagem (marca d'água, degradê) dentro do recorte
        p.add_redact_annot(clip); p.apply_redactions(images=1, graphics=0, text=1)
    if encher:   # perfil desenhado só com contorno (preenchimento branco + traço preto): preenche de preto
        sh = p.new_shape(); ne = 0
        for x in p.get_drawings():
            f, c, r = x.get('fill'), x.get('color'), x['rect']
            if x['type'] == 'fs' and f and min(f) > 0.95 and c and max(c) < 0.3 and (x.get('width') or 0) >= 0.5 and max(r.width, r.height) > 15 and _toca(clip, r):
                for it in x['items']:
                    if it[0] == 'l': sh.draw_line(it[1], it[2])
                    elif it[0] == 'c': sh.draw_bezier(it[1], it[2], it[3], it[4])
                    elif it[0] == 're': sh.draw_rect(it[1])
                    elif it[0] == 'qu': sh.draw_quad(it[1])
                sh.finish(fill=(0, 0, 0), color=(0, 0, 0), width=x.get('width') or 0.5, even_odd=x.get('even_odd', True), closePath=True); ne += 1
        if ne: sh.commit()
    if cinza_para_preto:   # perfil desenhado em cinza claro -> preto (depois das remoções, para não sobrar cinza)
        sh = p.new_shape()
        alvo_c = [x for x in p.get_drawings() if x.get('fill') and (min(x['fill']) > 0.3 or (0.02 < max(x['fill']) < 0.35 and max(x['rect'].width, x['rect'].height) > 15)) and max(x['fill']) < 0.97 and max(x['fill']) - min(x['fill']) < 0.05 and _toca(clip, x['rect'])]
        _pmc = p.get_pixmap(matrix=fitz.Matrix(3, 3), clip=clip, colorspace=fitz.csGRAY)
        alvo_c = [x for x in alvo_c if _visivel(x, _pmc, clip, 3.0, 0.3)]   # só o que aparece no original
        tiras = len(alvo_c) >= 15 and all(min(x['rect'].width, x['rect'].height) < 3.5 for x in alvo_c)   # perfil desenhado em tiras: um único preenchimento, senão ficam frestas brancas entre as tiras
        def _desenha(x):
            for it in x['items']:
                if it[0] == 'l': sh.draw_line(it[1], it[2])
                elif it[0] == 'c': sh.draw_bezier(it[1], it[2], it[3], it[4])
                elif it[0] == 're': sh.draw_rect(it[1])
                elif it[0] == 'qu': sh.draw_quad(it[1])
        for x in alvo_c:
            if tiras and not x.get('even_odd'): continue
            _desenha(x)
            sh.finish(fill=(0, 0, 0), color=(0, 0, 0), width=0.35, even_odd=x.get('even_odd', False), closePath=x.get('closePath', True))
        if tiras:
            for x in alvo_c:
                if not x.get('even_odd'): _desenha(x); sh.draw_line(sh.last_point, sh.last_point) if False else None
            sh.finish(fill=(0, 0, 0), color=(0, 0, 0), width=0.35, even_odd=False, closePath=True)
        # câmaras brancas que no original vinham por cima do perfil escuro: voltam por cima do preto
        ja = [x['rect'] for x in alvo_c]
        for x in p.get_drawings():
            f = x.get('fill')
            if f and min(f) > 0.97 and _toca(clip, x['rect']) and any(q.contains(x['rect']) and q != x['rect'] for q in ja):
                _desenha(x); sh.finish(fill=(1, 1, 1), color=None, width=0, even_odd=x.get('even_odd', False), closePath=True)
        sh.commit()
    if branco:   # tampa com branco o que a redação não consegue tirar (caminho composto)
        shb = p.new_shape()
        for r in branco: shb.draw_rect(fitz.Rect(r))
        shb.finish(fill=(1, 1, 1), color=None, width=0); shb.commit()
    if solidificar:   # preenchimento em hachura de filetes finos (Geral Alcoa) -> sólido preto
        sh = p.new_shape(); nfi = 0
        for x in p.get_drawings():
            r = x['rect']
            if x.get('fill') and len(x['items']) == 1 and x['items'][0][0] == 're' and min(r.width, r.height) < 0.45 and _toca(clip, r):
                rr = fitz.Rect(r)
                if r.height <= r.width: rr.y0 -= 0.22; rr.y1 += 0.22
                else: rr.x0 -= 0.22; rr.x1 += 0.22
                sh.draw_rect(rr); nfi += 1
        if nfi: sh.finish(fill=(0, 0, 0), color=None, width=0); sh.commit()
    if fs is None:   # tamanho único no desenho: mediana das alturas dos algarismos
        hs = sorted((v[4] if isinstance(v, tuple) else (r.width if v else r.height)) for _, r, v in cotas) or [6]
        fs = hs[(len(hs) - 1) // 2] / CAP
    if criar: p.wrap_contents(); criar_setas(p, clip, fs)
    if setas: padronizar_setas(p, clip, fs, excl=[fitz.Rect(a) for a in (branco or [])] + [fitz.Rect(a) for a in (apagar or [])])
    if costura:   # perfil feito de tiras (hachura Alumil/Binkafer): contorno fino na cor da tira fecha as frestas claras
        sh = p.new_shape(); nc = 0
        for x in p.get_drawings():
            f = x.get('fill'); r = x['rect']
            if f and max(f) < 0.2 and _toca(clip, r) and len(x['items']) <= 8 and min(r.width, r.height) < 2.5:
                _desenha_em(sh, x); sh.finish(fill=f, color=f, width=0.3, closePath=True, even_odd=x.get('even_odd', False)); nc += 1
        if nc: sh.commit()
    if enxugar: cotas = enxugar_cotas(p, clip, cotas, fs)
    if normalizar: cotas = normalizar_leitura(p, cotas)
    cotas = [(sem_tol(t_), r_, v_) for t_, r_, v_ in cotas]   # sem tolerância (±) — pedido do cliente 25/11
    for txt, r, vert in cotas:
        s = txt.replace('.', ',')
        tw = _font.text_length(s, fs)
        cx, cy = (r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2
        if not vert:
            p.insert_text((cx - tw / 2, cy + CAP * fs / 2), s, fontsize=fs, fontname='bahn', fontfile=FONT, color=cor)
        elif isinstance(vert, tuple):
            _, a, (ccx, ccy), _L, _S = vert
            p.insert_text((ccx - tw / 2, ccy + CAP * fs / 2), s, fontsize=fs, fontname='bahn', fontfile=FONT, color=cor, morph=(fitz.Point(ccx, ccy), fitz.Matrix(-a)))
        elif vert == 'down':
            p.insert_text((cx - CAP * fs / 2, cy - tw / 2), s, fontsize=fs, fontname='bahn', fontfile=FONT, color=cor, rotate=270)
        else:
            p.insert_text((cx + CAP * fs / 2, cy + tw / 2), s, fontsize=fs, fontname='bahn', fontfile=FONT, color=cor, rotate=90)
    n = fitz.open(); q = n.new_page(width=clip.width, height=clip.height)
    q.show_pdf_page(q.rect, t, 0, clip=clip)
    open(out_svg, 'w').write(q.get_svg_image(text_as_path=True))
    if out_png:
        q.get_pixmap(dpi=150).save(out_png)
    return cotas, fs


def _potrace_svg(gray, out):
    import potrace, re as _re, numpy as np
    P = 12
    gray = np.pad(gray, P, constant_values=255)
    path = potrace.Bitmap(gray < 128).trace(turdsize=6, alphamax=1.0, opticurve=True, opttolerance=0.2)
    H, W = gray.shape; parts = []
    for c in path:
        s = c.start_point; seg = [f'M{s.x:.1f},{s.y:.1f}']
        for q in c:
            if q.is_corner: seg.append(f'L{q.c.x:.1f},{q.c.y:.1f}L{q.end_point.x:.1f},{q.end_point.y:.1f}')
            else: seg.append(f'C{q.c1.x:.1f},{q.c1.y:.1f} {q.c2.x:.1f},{q.c2.y:.1f} {q.end_point.x:.1f},{q.end_point.y:.1f}')
        parts.append(''.join(seg) + 'Z')
    def bb(p):
        n = [float(v) for v in _re.findall(r'-?\d+\.?\d*', p)]; return min(n[0::2]), max(n[0::2]), min(n[1::2])
    if parts and bb(parts[0])[0] <= 1 and bb(parts[0])[1] >= W - 1 and bb(parts[0])[2] <= 1: parts = parts[1:]
    W0, H0 = W - 2 * P, H - 2 * P
    open(out, 'w').write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W0}" height="{H0}" viewBox="{P} {P} {W0} {H0}"><path fill="#000" fill-rule="evenodd" d="{"".join(parts)}"/></svg>')


def padronizar_raster(png, out_svg, out_png=None, dpi_img=300, cor=(0, 0, 0), cotas=None, extra=None, fs=None):
    """Desenho em imagem (já preenchido): lê cotas, apaga na imagem, vetoriza e reescreve em Bahnschrift."""
    import numpy as np, cv2
    g = cv2.imread(png, 0); H, W = g.shape; k = 72 / dpi_img
    d = fitz.open(); p = d.new_page(width=W * k, height=H * k); p.insert_image(p.rect, filename=png)
    if cotas is None: cotas = ler_cotas(p, p.rect, dpi=dpi_img)
    g2 = g.copy()
    for txt, r, v in cotas:
        m = 0.15 * min(r.width, r.height) + 0.5
        x0, y0, x1, y1 = [int(round(z / k)) for z in (r.x0 - m, r.y0 - m, r.x1 + m, r.y1 + m)]
        g2[max(0, y0):y1, max(0, x0):x1] = 255
    g3 = cv2.resize(g2, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
    tmp = out_svg + '.base.svg'; _potrace_svg(g3, tmp)
    base = fitz.open(tmp); bpdf = fitz.open('pdf', base.convert_to_pdf())
    n = fitz.open(); q = n.new_page(width=W * k, height=H * k); q.show_pdf_page(q.rect, bpdf, 0)
    if fs is None:
        hs = sorted((r.width if v else r.height) for _, r, v in cotas) or [6]
        fs = hs[len(hs) // 2] / CAP
    if extra: extra(q, fs)
    cotas = [(sem_tol(t_), r_, v_) for t_, r_, v_ in cotas]
    for txt, r, vert in cotas:
        s = txt.replace('.', ','); tw = _font.text_length(s, fs); cx, cy = (r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2
        if not vert: q.insert_text((cx - tw / 2, cy + CAP * fs / 2), s, fontsize=fs, fontname='bahn', fontfile=FONT, color=cor)
        elif vert == 'down': q.insert_text((cx - CAP * fs / 2, cy - tw / 2), s, fontsize=fs, fontname='bahn', fontfile=FONT, color=cor, rotate=270)
        else: q.insert_text((cx + CAP * fs / 2, cy + tw / 2), s, fontsize=fs, fontname='bahn', fontfile=FONT, color=cor, rotate=90)
    open(out_svg, 'w').write(q.get_svg_image(text_as_path=True))
    os.remove(tmp)
    if out_png: q.get_pixmap(dpi=150).save(out_png)
    return cotas, fs


def cota_manual(q, k, a, b, pos, txt, fs, ch_a=None, ch_b=None, lado=-1):
    """Desenha uma cota no padrão (linha preta fina, setas cheias, chamadas) e devolve (txt, rect, dir) do número.
    k='H': de x=a a x=b na altura pos; k='V': de y=a a y=b em x=pos. ch_a/ch_b: onde começa cada chamada (coordenada do perfil)."""
    A = SETA_L * fs; LW = max(0.15, LINHA_W * fs); sh = q.new_shape()
    P = (lambda u, v: fitz.Point(u, v)) if k == 'H' else (lambda u, v: fitz.Point(v, u))
    sh.draw_line(P(a, pos), P(b, pos))
    for qq, ch in ((a, ch_a), (b, ch_b)):
        if ch is not None: sh.draw_line(P(qq, ch), P(qq, pos + (1.5 if pos > ch else -1.5)))
    sh.finish(color=(0, 0, 0), width=LW, lineCap=0)
    fora = (b - a) < 2.4 * A
    for qq, sg in ((a, -1), (b, 1)):
        u = (sg if not fora else -sg)
        tip = P(qq, pos); base = P(qq - u * A, pos); nr = P(0, A * SETA_A) if k == 'H' else fitz.Point(A * SETA_A, 0)
        sh.draw_polyline([tip, base + nr, base - nr, tip]); sh.finish(fill=(0, 0, 0), color=None, width=0, closePath=True)
    sh.commit()
    tw = _font.text_length(txt, fs); h = CAP * fs; m = (a + b) / 2; off = 0.45 * fs + h / 2
    if k == 'H': r = fitz.Rect(m - tw / 2, pos + lado * off - h / 2, m + tw / 2, pos + lado * off + h / 2); return (txt, r, False)
    r = fitz.Rect(pos + lado * off - h / 2, m - tw / 2, pos + lado * off + h / 2, m + tw / 2); return (txt, r, 'up')


def preencher(png_in, png_out, limiar=225, media_max=6.5, area_min=1500):
    """Desenho só em contorno: preenche de preto as paredes (regiões brancas finas fechadas); câmaras ficam vazadas."""
    import numpy as np, cv2
    g = cv2.imread(png_in, 0)
    bw = (g < limiar).astype(np.uint8); white = 1 - bw
    n, lab, st, _ = cv2.connectedComponentsWithStats(white, connectivity=4)
    dist = cv2.distanceTransform(white, cv2.DIST_L2, 3)
    H, W = g.shape; out = bw.copy()
    for i in range(1, n):
        x, y, w, h, a = st[i]
        if x == 0 or y == 0 or x + w >= W or y + h >= H: continue
        m = lab == i
        if a > area_min and dist[m].mean() <= media_max: out[m] = 1
    cv2.imwrite(png_out, 255 - out * 255)


SETA_L = 0.70      # comprimento da seta = SETA_L x tamanho da fonte da cota
SETA_A = 0.27      # meia-largura / comprimento (abertura ~19 graus)
LINHA_W = 0.030    # espessura das linhas de cota e de chamada = LINHA_W x tamanho da fonte


def _pts(items):
    pts = []
    for it in items:
        if it[0] == 'l':
            for q in (it[1], it[2]):
                if not pts or abs(pts[-1].x - q.x) + abs(pts[-1].y - q.y) > 1e-3: pts.append(fitz.Point(q))
        else:
            return None
    if len(pts) > 1 and abs(pts[0].x - pts[-1].x) + abs(pts[0].y - pts[-1].y) < 1e-3: pts.pop()
    return pts


def _dseg(q, a, b):
    v = b - a; L2 = v.x * v.x + v.y * v.y
    if L2 < 1e-9: return abs(q - a)
    t = max(0, min(1, ((q.x - a.x) * v.x + (q.y - a.y) * v.y) / L2))
    return abs(q - (a + v * t))


def _toca(a, r):
    r = fitz.Rect(r)
    return r.x0 <= a.x1 and r.x1 >= a.x0 and r.y0 <= a.y1 and r.y1 >= a.y0


def _escuro(c):
    return c is not None and len(c) >= 3 and max(c) < 0.72 and max(c) - min(c) < 0.12


def criar_setas(p, clip, fs):
    """Desenho sem pontas de seta (redesenhos): põe seta cheia nas duas pontas de cada linha de cota
    (traço fino reto cujas duas pontas encostam numa linha de chamada perpendicular)."""
    segs = []
    for d in p.get_drawings():
        if d['type'] != 's' or (d.get('width') or 0) > 0.8 or not _toca(clip, d['rect']): continue
        for it in d['items']:
            if it[0] == 'l' and abs(it[2] - it[1]) > 2: segs.append((it[1], it[2]))
    A = SETA_L * fs; sh = p.new_shape(); n = 0
    for a, b in segs:
        v = b - a; L = abs(v); u = v / L
        def encosta(q):
            for c, e in segs:
                w = e - c; Lw = abs(w)
                if Lw < 1e-6 or (c == a and e == b): continue
                uw = w / Lw
                if abs(u.x * uw.x + u.y * uw.y) < 0.1 and _dseg(q, c, e) < 0.6: return True
            return False
        if L < 2.4 * A or not (encosta(a) and encosta(b)): continue
        nrm = fitz.Point(-u.y, u.x)
        for tip, dirv in ((a, u), (b, -u)):
            base = tip + dirv * A
            sh.draw_polyline([tip, base + nrm * (A * SETA_A), base - nrm * (A * SETA_A), tip]); n += 1
    if n: sh.finish(fill=(0, 0, 0), color=None, width=0, closePath=True); sh.commit()
    return n


def _visivel(x, pm, clip, Z, limiar=0.5):
    """O preenchimento aparece de fato no desenho original? (peças de outras células ficam escondidas por recorte/máscara)"""
    import numpy as np
    r = fitz.Rect(x['rect']) & clip
    if r.is_empty or r.width * r.height < 0.05: return False
    t = fitz.open(); q = t.new_page(width=clip.x1 + 10, height=clip.y1 + 10); sh = q.new_shape()
    for it in x['items']:
        if it[0] == 'l': sh.draw_line(it[1], it[2])
        elif it[0] == 'c': sh.draw_bezier(it[1], it[2], it[3], it[4])
        elif it[0] == 're': sh.draw_rect(it[1])
        elif it[0] == 'qu': sh.draw_quad(it[1])
    sh.finish(fill=(0, 0, 0), color=None, width=0, even_odd=x.get('even_odd', False), closePath=True); sh.commit()
    m = q.get_pixmap(matrix=fitz.Matrix(Z, Z), clip=clip, colorspace=fitz.csGRAY)
    a = np.frombuffer(m.samples, np.uint8).reshape(m.height, m.stride)[:, :m.width]
    o = np.frombuffer(pm.samples, np.uint8).reshape(pm.height, pm.stride)[:, :pm.width]
    h = min(a.shape[0], o.shape[0]); w = min(a.shape[1], o.shape[1])
    msk = a[:h, :w] < 100
    if msk.sum() < 3: return True
    return (o[:h, :w][msk] < 235).mean() >= limiar


def _refaz_perfil(p, clip, caixas, aceita=lambda x: True, pular=(), pm=None, Z=4.0):
    """Redesenha, na ordem original, os preenchimentos escuros do perfil tocados pelas faixas brancas
    e, por cima deles, as câmaras em branco que ficam dentro (senão as câmaras ficariam pretas)."""
    sh = p.new_shape(); nr = 0; feitos = []
    for x in p.get_drawings():
        f = x.get('fill')
        if not f or not _toca(clip, x['rect']): continue
        r = x['rect']
        if max(f) < 0.2:
            if not aceita(x) or any(abs(r.x0 - q.x0) + abs(r.y0 - q.y0) + abs(r.x1 - q.x1) + abs(r.y1 - q.y1) < 0.3 for q in pular): continue
            if not any(r.intersects(c) for c in caixas): continue
            if pm is not None and not _visivel(x, pm, clip, Z): continue   # peça de outra célula (escondida no PDF) não volta
            cor_ = (0, 0, 0); feitos.append(r)
        elif min(f) > 0.97 and feitos and any(r.intersects(q) for q in feitos):   # branco que vinha por cima no original (câmara, máscara do vizinho)
            cor_ = (1, 1, 1)
        else: continue
        for it in x['items']:
            if it[0] == 'l': sh.draw_line(it[1], it[2])
            elif it[0] == 'c': sh.draw_bezier(it[1], it[2], it[3], it[4])
            elif it[0] == 're': sh.draw_rect(it[1])
            elif it[0] == 'qu': sh.draw_quad(it[1])
        sh.finish(fill=cor_, color=None, width=0, even_odd=x.get('even_odd', False), closePath=True); nr += 1
    if nr: sh.commit()
    return nr


def padronizar_setas(p, clip, fs, excl=()):
    """Linhas de cota/chamada e setas num estilo único: linha preta fina e seta triangular cheia."""
    import math
    A = SETA_L * fs; LW = max(0.15, LINHA_W * fs)
    p.wrap_contents()   # as redações reescrevem o conteúdo; sem isto o que se desenha a seguir pode ficar recortado
    Z = 4.0; pm = p.get_pixmap(matrix=fitz.Matrix(Z, Z), clip=clip, colorspace=fitz.csGRAY)
    def _px(q):
        x = int((q.x - clip.x0) * Z); y = int((q.y - clip.y0) * Z)
        if 0 <= x < pm.width and 0 <= y < pm.height: return pm.samples[y * pm.stride + x]
        return 255
    def _borda(a, b):   # traço que contorna o perfil (há preenchimento de um dos lados) não é linha de cota
        v = b - a; L = abs(v)
        if L < 1e-6: return False
        n = fitz.Point(-v.y / L, v.x / L); lado = [0, 0]; tot = 0
        for t in (0.2, 0.35, 0.5, 0.65, 0.8):
            m = a + v * t; tot += 1
            if _px(m + n * 1.1) < 200: lado[0] += 1
            if _px(m - n * 1.1) < 200: lado[1] += 1
        return max(lado) >= 3
    setas, linhas = [], []
    cheios = [x for x in p.get_drawings() if x.get('fill') and max(x['fill']) < 0.2 and _toca(clip, x['rect']) and not (x['type'] == 'fs' and (x.get('width') or 0) <= 0.25)]
    for d in p.get_drawings():
        r = d['rect']
        if not _toca(clip, r): continue
        if any(e.intersects(r) for e in excl) and max(r.width, r.height) < 80: continue
        pts = _pts(d['items'])
        if pts is None: continue
        f, c = d.get('fill'), d.get('color')
        big = max(r.width, r.height)
        # seta: triângulo cheio pequeno
        if f is not None and _escuro(f) and len(pts) == 3 and big <= max(9.5, 1.5 * fs) and min(r.width, r.height) >= max(0.4, 0.09 * big):   # tira fina de hachura (Binkafer) não é seta
            sides = [abs(pts[(i + 1) % 3] - pts[(i + 2) % 3]) for i in range(3)]
            i = min(range(3), key=lambda k: sides[k])
            tip = pts[i]; base = (pts[(i + 1) % 3] + pts[(i + 2) % 3]) / 2
            if sides[i] < 0.95 * max(sides):
                setas.append((d, tip, base)); continue
            # quase equilátero (Decamp): a ponta é o vértice que fica alinhado com a linha de cota (decide depois)
            for i in range(3): setas.append((d, pts[i], (pts[(i + 1) % 3] + pts[(i + 2) % 3]) / 2))
            continue
        # linha traço (stroke reto)
        if d['type'] == 's' and _escuro(c) and (d.get('width') or 0) <= 0.8 and len(pts) >= 2 and not d.get('fill') and (d.get('dashes') or '[] 0').startswith('[]'):   # tracejado (peça vizinha) fica como está
            segs = [(it[1], it[2]) for it in d['items'] if not _borda(it[1], it[2])]
            if segs: linhas.append((d, segs))
            continue
    # setas abertas (duas farpas curtas que se encontram na ponta de uma linha reta) dentro de caminhos de traço
    import math as _m
    farpas = []; retas = []
    for d in p.get_drawings():
        if d['type'] != 's' or not _escuro(d.get('color')) or (d.get('width') or 0) > 0.8: continue
        if not _toca(clip, d['rect']): continue
        for it in d['items']:
            if it[0] != 'l': continue
            a, b = it[1], it[2]; L = abs(b - a)
            if not (clip.contains(a) or clip.contains(b)): continue
            if any(e.contains(a) or e.contains(b) for e in excl): continue
            if 0.8 < L < max(4.5, 1.2 * fs) and abs(a.x - b.x) > 0.15 and abs(a.y - b.y) > 0.15: farpas.append((d, a, b, L))
            elif L >= 2.5 and (abs(a.x - b.x) < 0.05 or abs(a.y - b.y) < 0.05): retas.append((a, b))
    usadas = set(); abertas = []
    for i, (d1, a1, b1, L1) in enumerate(farpas):
        if i in usadas: continue
        for j2 in range(i + 1, len(farpas)):
            if j2 in usadas: continue
            d2, a2, b2, L2 = farpas[j2]
            if abs(L1 - L2) > 0.25 * max(L1, L2): continue
            tip = None
            for p1, q1 in ((a1, b1), (b1, a1)):
                for p2, q2 in ((a2, b2), (b2, a2)):
                    if abs(p1 - p2) < 0.25: tip, o1, o2 = p1, q1, q2
            if tip is None: continue
            u1 = (o1 - tip) / max(abs(o1 - tip), 1e-6); u2 = (o2 - tip) / max(abs(o2 - tip), 1e-6)
            ang = _m.degrees(_m.acos(max(-1, min(1, u1.x * u2.x + u1.y * u2.y))))
            if not 12 < ang < 75: continue
            base = (o1 + o2) / 2
            ax = (base - tip) / max(abs(base - tip), 1e-6)
            # tem de estar na ponta de uma reta alinhada com o eixo da seta
            ok = any(_dseg(tip, ra, rb) < 0.4 and _dseg(base, ra, rb) < 0.45 and abs(((rb - ra) / max(abs(rb - ra), 1e-6)).x * ax.y - ((rb - ra) / max(abs(rb - ra), 1e-6)).y * ax.x) < 0.1 for ra, rb in retas)
            if not ok: continue
            usadas.update((i, j2)); abertas.append((tip, base, (a1, b1), (a2, b2)))
            break
    # seta cheia só vale se estiver na ponta de uma reta alinhada com o seu eixo (fatias do perfil também são triângulos)
    _retas = [(it[1], it[2]) for d in p.get_drawings() if d['type'] in ('s', 'fs') and _escuro(d.get('color')) and (d.get('width') or 0) <= 0.8 and _toca(clip, d['rect'])
              for it in d['items'] if it[0] == 'l' and abs(it[2] - it[1]) >= 2.0]
    def _na_reta(tip, base):
        ax = (base - tip) / max(abs(base - tip), 1e-6)
        for ra, rb in _retas:
            u = (rb - ra) / max(abs(rb - ra), 1e-6)
            if abs(u.x * ax.y - u.y * ax.x) < 0.12 and _dseg(base, ra, rb) < 0.45:
                if _dseg(tip, ra, rb) < 0.9 and abs(rb - ra) > 1.2 * abs(base - tip): return True
                far = ra if abs(ra - base) > abs(rb - base) else rb
                if (far - base).x * ax.x + (far - base).y * ax.y > 1.0 and min(abs(ra - base), abs(rb - base)) < 0.8: return True
                perto = rb if far is ra else ra   # reta que atravessa a base e termina dentro da seta (Tera)
                if (far - base).x * ax.x + (far - base).y * ax.y > 1.0 and abs(perto - tip) < abs(base - tip) and _dseg(perto, tip, base) < 0.45: return True
        return False
    setas = [s_ for s_ in setas if _na_reta(s_[1], s_[2])]
    _vist = set(); _s2 = []
    for s_ in setas:   # do quase equilátero fica uma só orientação
        if id(s_[0]) in _vist: continue
        _vist.add(id(s_[0])); _s2.append(s_)
    setas = _s2
    if not setas and not linhas and not abertas: return 0
    if abertas:
        sh = p.new_shape()
        for tip, base, f1, f2 in abertas:
            sh.draw_line(*f1); sh.draw_line(*f2)
        sh.finish(color=(1, 1, 1), width=0.7, lineCap=1); sh.commit()
        for tip, base, f1, f2 in abertas: setas.append((None, tip, base))
    sh = p.new_shape()
    for d, tip, base in setas:   # apaga as setas originais
        if d is None: continue
        pts = _pts(d['items']); sh.draw_polyline(pts + [pts[0]])
    sh.finish(fill=(1, 1, 1), color=(1, 1, 1), width=0.45, closePath=True); sh.commit()
    sh = p.new_shape()
    for d, segs in linhas:
        w = (d.get('width') or 0.3) + 0.4
        for a, b in segs: sh.draw_line(a, b)
        sh.finish(color=(1, 1, 1), width=w, lineCap=0, closePath=False)
    sh.commit()
    # o apagamento em branco das linhas antigas não pode comer o perfil onde a linha o atravessa: redesenha os preenchimentos escuros tocados
    if linhas:
        caixas = [fitz.Rect(min(a.x, b.x), min(a.y, b.y), max(a.x, b.x), max(a.y, b.y)) + (-1, -1, 1, 1) for d, segs in linhas for a, b in segs]
        _refaz_perfil(p, clip, caixas, aceita=lambda x: not (min(x['rect'].width, x['rect'].height) < 1.5 and len(x['items']) <= 8) and max(x['rect'].width, x['rect'].height) > max(9, 1.6 * fs), pular=[d['rect'] for d, t_, b_ in setas if d is not None], pm=pm, Z=Z)
    sh = p.new_shape()
    for d, segs in linhas:
        for a, b in segs: sh.draw_line(a, b)
    sh.finish(color=(0, 0, 0), width=LW, lineCap=0, closePath=False); sh.commit()
    sh = p.new_shape()
    for d, tip, base in setas:
        v = tip - base; L = abs(v)
        if L < 1e-6: continue
        u = v / L; nrm = fitz.Point(-u.y, u.x)
        b = tip - u * A
        sh.draw_polyline([tip, b + nrm * (A * SETA_A), b - nrm * (A * SETA_A), tip])
        sh.finish(fill=(0, 0, 0), color=None, width=0, closePath=True)   # uma seta por caminho (para poder achá-las depois)
        if L > A + 0.2:   # seta original mais comprida que a padrão: a linha some entre as duas bases -> refaz o trecho
            sh.draw_line(b, base); sh.finish(color=(0, 0, 0), width=LW, lineCap=0, closePath=False)
    if sh.text_cont or sh.totalcont: sh.commit()
    return len(setas), len(linhas), len(abertas)


DEBUG_ENX = False


def sem_tol(t):
    return re.sub(r'\s*(±|\+/-|\+-).*$', '', t).strip()


def _val(t):
    m = re.match(r'^[ØR]?(\d+(?:[.,]\d+)?)', t.replace(' ', ''))
    return float(m.group(1).replace(',', '.')) if m else 0.0


def enxugar_cotas(p, clip, cotas, fs):
    """Deixa só as cotas principais (padrão dos outros fabricantes): maior horizontal, maior vertical e, se trouxer
    informação nova, a 2ª maior de cada direção (< 85% da maior). Ø, R e ângulos ficam. Apaga o número, a linha de cota,
    as setas e as linhas de chamada que só serviam às cotas retiradas."""
    import math
    def dirc(v):
        if isinstance(v, tuple): return 'I'
        return 'H' if v is False else 'V'
    # segmentos retos finos (linhas de cota/chamada) e setas
    segs = []
    for d in p.get_drawings():
        if not _toca(clip, d['rect']): continue
        w = d.get('width') or 0
        if d['type'] in ('s', 'fs') and w <= 0.8:
            for it in d['items']:
                if it[0] == 'l' and abs(it[2] - it[1]) > 1.0: segs.append((fitz.Point(it[1]), fitz.Point(it[2])))
    tris = [d['rect'] for d in p.get_drawings() if d.get('fill') and len(d['items']) <= 4 and max(d['rect'].width, d['rect'].height) < max(9, 1.6 * fs) and _toca(clip, d['rect'])]
    def eixo_da(c):
        t, r, v = c
        cx, cy = (r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2; L = max(r.width, r.height)
        best = None
        for k in ('H', 'V'):
            for a, b in segs:
                if k == 'H' and abs(a.y - b.y) < 0.3:
                    y = (a.y + b.y) / 2; x0, x1 = sorted((a.x, b.x))
                    dd = abs(y - cy)
                    if dd < 1.3 * L and (x0 - 2.5 * L < cx < x1 + 2.5 * L):
                        sc = dd + (0 if x0 <= cx <= x1 else 0.5 * min(abs(cx - x0), abs(cx - x1)))
                        if best is None or sc < best[0]: best = (sc, 'H', y)
                if k == 'V' and abs(a.x - b.x) < 0.3:
                    x = (a.x + b.x) / 2; y0, y1 = sorted((a.y, b.y))
                    dd = abs(x - cx)
                    if dd < 1.3 * L and (y0 - 2.5 * L < cy < y1 + 2.5 * L):
                        sc = dd + (0 if y0 <= cy <= y1 else 0.5 * min(abs(cy - y0), abs(cy - y1)))
                        if best is None or sc < best[0]: best = (sc, 'V', x)
        return best
    grupos = {'H': [], 'V': []}
    fica = []; inclinadas = []
    for c in cotas:
        t, r, v = c
        if re.match(r'^[ØR]', t) or not re.match(r'^\d', t): fica.append(c); continue
        if dirc(v) == 'I' or '°' in t: inclinadas.append(c); continue
        e_ = eixo_da(c)
        if e_ is None: continue
        grupos[e_[1]].append(c)
        if DEBUG_ENX: print('  ', t, e_)
    # direção real pela linha de cota (número em pé numa cota horizontal etc.)
    for k in ('H', 'V'):
        g = sorted(grupos[k], key=lambda c: -_val(c[0]))
        if not g: continue
        fica.append(g[0])
        resto = [c for c in g[1:] if _val(c[0]) < 0.85 * _val(g[0][0]) and abs(_val(c[0]) - _val(g[0][0])) > 0.01]
        if resto: fica.append(resto[0])
    A_ = SETA_L * fs
    def extensao(k, pos, c):
        t, r, v = c; cx, cy = (r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2; L = max(r.width, r.height)
        m = cx if k == 'H' else cy
        cs_ = []
        for tr in tris:
            tc = fitz.Point((tr.x0 + tr.x1) / 2, (tr.y0 + tr.y1) / 2)
            if k == 'H' and abs(tc.y - pos) < 1.5: cs_.append(tc.x)
            if k == 'V' and abs(tc.x - pos) < 1.5: cs_.append(tc.y)
        esq = [q for q in cs_ if q < m - 0.3]; dir_ = [q for q in cs_ if q > m + 0.3]
        if esq and dir_: return max(esq) - 0.5 * A_, min(dir_) + 0.5 * A_
        best = None
        for a, b in segs:
            if k == 'H' and abs(a.y - pos) < 0.35 and abs(b.y - pos) < 0.35: s0, s1 = sorted((a.x, b.x))
            elif k == 'V' and abs(a.x - pos) < 0.35 and abs(b.x - pos) < 0.35: s0, s1 = sorted((a.y, b.y))
            else: continue
            dd = 0 if s0 <= m <= s1 else min(abs(m - s0), abs(m - s1))
            if best is None or dd < best[0]: best = (dd, s0, s1)
        if best and best[0] < 2.5 * L: return min(best[1], m - 0.6 * L), max(best[2], m + 0.6 * L)
        return m - 0.6 * L, m + 0.6 * L
    if not grupos['H'] and not grupos['V']: return cotas   # só cotas inclinadas: não mexe
    manter_incl = inclinadas and len(fica) + 0 < 2 + len([c for c in fica if re.match(r'^[ØR]', c[0])])
    if manter_incl: fica += inclinadas
    sai = [c for c in cotas if c not in fica]
    if not sai: return cotas
    # 1) vão e chamadas de cada cota que fica (geometria original)
    def perp(k, pos, q, tol):
        out = []
        for a, b in segs:
            if k == 'H' and abs(a.x - b.x) < 0.3:
                qq = (a.x + b.x) / 2; y0, y1 = sorted((a.y, b.y))
                if abs(qq - q) < tol and y0 - 1.0 <= pos <= y1 + 1.0: out.append((qq, a, b))
            if k == 'V' and abs(a.y - b.y) < 0.3:
                qq = (a.y + b.y) / 2; x0, x1 = sorted((a.x, b.x))
                if abs(qq - q) < tol and x0 - 1.0 <= pos <= x1 + 1.0: out.append((qq, a, b))
        return out
    redesenho = []
    for c in fica:
        e = eixo_da(c)
        if not e: continue
        _, k, pos = e; lo, hi = extensao(k, pos, c)
        ch = []
        for i_, q in enumerate((lo, hi)):
            pp = perp(k, pos, q, 1.6 * A_)
            if pp:
                qq, a, b = min(pp, key=lambda z: abs(z[0] - q))
                if i_ == 0: lo = qq
                else: hi = qq
                ch.append((a, b))
        # vão para o número quando ele fica em cima da linha (Belmetal/Euroshow escrevem o número sobre a linha)
        t_, r_, v_ = c; cx_, cy_ = (r_.x0 + r_.x1) / 2, (r_.y0 + r_.y1) / 2
        tw_ = _font.text_length(sem_tol(t_).replace('.', ','), fs); ch_ = CAP * fs; pad_ = 0.35 * fs
        gap = None
        if k == 'H' and abs(cy_ - pos) < 0.75 * ch_ + 0.3:
            w_ = tw_ if v_ is False else ch_
            gap = (cx_ - w_ / 2 - pad_, cx_ + w_ / 2 + pad_)
        if k == 'V' and abs(cx_ - pos) < (0.5 * tw_ if v_ is False else 0.75 * ch_) + 0.3:
            w_ = ch_ if v_ is False else tw_
            gap = (cy_ - w_ / 2 - pad_, cy_ + w_ / 2 + pad_)
        redesenho.append((k, pos, lo, hi, ch, gap))
    # 2) apaga todas as linhas finas de cota/chamada e as setas (o contorno do perfil fica)
    Z = 4.0; pm = p.get_pixmap(matrix=fitz.Matrix(Z, Z), clip=clip, colorspace=fitz.csGRAY)
    def px(q):
        x = int((q.x - clip.x0) * Z); y = int((q.y - clip.y0) * Z)
        return pm.samples[y * pm.stride + x] if 0 <= x < pm.width and 0 <= y < pm.height else 255
    def borda(a, b):
        v = b - a; L = abs(v)
        if L < 1e-6: return False
        n = fitz.Point(-v.y / L, v.x / L); lado = [0, 0]
        for t in (0.2, 0.35, 0.5, 0.65, 0.8):
            m = a + v * t
            if px(m + n * 0.75) < 225: lado[0] += 1
            if px(m - n * 0.75) < 225: lado[1] += 1
        return max(lado) >= 4
    apagar = [fitz.Rect(r) + (-0.6, -0.6, 0.6, 0.6) for t, r, v in sai]
    linhas_ = []
    _rot = [fitz.Rect(w_[:4]) + (-4, -4, 4, 4) for w_ in p.get_text('words', clip=clip) if not re.match(r'^[\d.,]+$', w_[4])]
    for d in p.get_drawings():
        if any(_toca(rr_, d['rect']) for rr_ in _rot) and max(d['rect'].width, d['rect'].height) < 40: continue   # chamada de rótulo (BMT-…, FA-237 *) fica
        if not _toca(clip, d['rect']) or d.get('dashes') not in (None, '', '[] 0') and '[]' not in str(d.get('dashes')): continue
        w = d.get('width') or 0
        if d['type'] in ('s', 'fs') and w <= 0.8 and d.get('color') and max(d['color']) < 0.6 and len(d['items']) <= 24 and not any(it[0] == 'c' for it in d['items']):   # contorno de peça de referência (com curvas) fica
            for it in d['items']:
                if it[0] == 'l' and not borda(it[1], it[2]) and not (manter_incl and abs(it[1].x - it[2].x) > 0.3 and abs(it[1].y - it[2].y) > 0.3): linhas_.append((it[1], it[2], w))
    sh = p.new_shape()
    for a, b, w in linhas_: sh.draw_line(a, b)
    if linhas_: sh.finish(color=(1, 1, 1), width=max(w for a, b, w in linhas_) + 1.0, lineCap=1)
    def _no_eixo(tr):
        cc = fitz.Point((tr.x0 + tr.x1) / 2, (tr.y0 + tr.y1) / 2)
        return any((abs(a.y - b.y) < 0.3 and abs(cc.y - a.y) < 1.5 and min(a.x, b.x) - 8 <= cc.x <= max(a.x, b.x) + 8) or (abs(a.x - b.x) < 0.3 and abs(cc.x - a.x) < 1.5 and min(a.y, b.y) - 8 <= cc.y <= max(a.y, b.y) + 8) for a, b in segs)
    for tr in tris:
        if manter_incl and not _no_eixo(tr): continue
        sh.draw_rect(tr + (-0.4, -0.4, 0.4, 0.4))
    for a in apagar: sh.draw_rect(a)
    sh.finish(fill=(1, 1, 1), color=None, width=0); sh.commit()
    # perfil tocado pelo branco volta por cima
    _refaz_perfil(p, clip, [fitz.Rect(clip)], aceita=lambda x: not (min(x['rect'].width, x['rect'].height) < 1.5 and len(x['items']) <= 8) and max(x['rect'].width, x['rect'].height) > max(9, 1.6 * fs), pm=pm, Z=Z)
    # 3) redesenha só as cotas que ficam: chamadas, linha e setas no padrão
    LW = max(0.15, LINHA_W * fs)
    sh = p.new_shape(); nl = 0
    for k, pos, lo, hi, ch, gap in redesenho:
        for a, b in ch: sh.draw_line(a, b); nl += 1
        trechos = [(lo, hi)]
        if gap and lo < gap[0] and gap[1] < hi: trechos = [(lo, gap[0]), (gap[1], hi)]
        for q0, q1 in trechos:
            if k == 'H': sh.draw_line(fitz.Point(q0, pos), fitz.Point(q1, pos))
            else: sh.draw_line(fitz.Point(pos, q0), fitz.Point(pos, q1))
            nl += 1
    if nl: sh.finish(color=(0, 0, 0), width=LW, lineCap=0); sh.commit()
    sh = p.new_shape(); ns = 0
    for k, pos, lo, hi, ch, gap in redesenho:
        fora = (hi - lo) < 2.4 * A_
        for q, sgn in ((lo, -1), (hi, 1)):
            tip = fitz.Point(q, pos) if k == 'H' else fitz.Point(pos, q)
            u = fitz.Point(sgn, 0) if k == 'H' else fitz.Point(0, sgn)
            if fora: u = -u
            nrm = fitz.Point(-u.y, u.x); bb = tip - u * A_
            sh.draw_polyline([tip, bb + nrm * (A_ * SETA_A), bb - nrm * (A_ * SETA_A), tip])
            sh.finish(fill=(0, 0, 0), color=None, width=0, closePath=True); ns += 1
    if ns: sh.commit()
    return fica


def normalizar_leitura(p, cotas):
    """Leitura normal: cota horizontal com texto horizontal; vertical sempre de baixo para cima (lida pela direita)."""
    segs = []
    for d in p.get_drawings():
        rr = d['rect']
        if rr.height < 0.8 and rr.width > 4: segs.append(('H', (rr.y0 + rr.y1) / 2, rr.x0, rr.x1))
        elif rr.width < 0.8 and rr.height > 4: segs.append(('V', (rr.x0 + rr.x1) / 2, rr.y0, rr.y1))
        for it in d['items']:
            if it[0] == 'l':
                a, b = it[1], it[2]
                if abs(a.y - b.y) < 0.3 and abs(a.x - b.x) > 4: segs.append(('H', a.y, min(a.x, b.x), max(a.x, b.x)))
                elif abs(a.x - b.x) < 0.3 and abs(a.y - b.y) > 4: segs.append(('V', a.x, min(a.y, b.y), max(a.y, b.y)))
            elif it[0] == 're':
                r = it[1]
                if r.height < 0.6 and r.width > 4: segs.append(('H', (r.y0 + r.y1) / 2, r.x0, r.x1))
                elif r.width < 0.6 and r.height > 4: segs.append(('V', (r.x0 + r.x1) / 2, r.y0, r.y1))
    setas_ = []
    for d in p.get_drawings():
        rr = d['rect']
        if d.get('fill') and len(d['items']) <= 4 and 1.5 < max(rr.width, rr.height) < 9: setas_.append(((rr.x0 + rr.x1) / 2, (rr.y0 + rr.y1) / 2))
    out = []
    for t, r, v in cotas:
        if isinstance(v, tuple): out.append((t, r, v)); continue
        cx, cy = (r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2
        L = max(r.width, r.height)
        # linha de cota passando junto do número
        h = any(k == 'H' and abs(c - cy) < 0.9 * L and a0 < cx - L * 0.4 and a1 > cx + L * 0.4 and (a1 - a0) > 2.2 * L for k, c, a0, a1 in segs)
        vv = any(k == 'V' and abs(c - cx) < 0.9 * L and a0 < cy - L * 0.4 and a1 > cy + L * 0.4 and (a1 - a0) > 2.2 * L for k, c, a0, a1 in segs)
        if not h:   # linha de cota interrompida no número: um trecho à esquerda e outro à direita
            h = any(k == 'H' and abs(c - cy) < 0.9 * L and cx - 2.5 * L < a1 <= cx for k, c, a0, a1 in segs) and any(k == 'H' and abs(c - cy) < 0.9 * L and cx <= a0 < cx + 2.5 * L for k, c, a0, a1 in segs)
            if h and any(k == 'V' and abs(c - cx) < 0.9 * L and cy - 2.5 * L < a1 <= cy for k, c, a0, a1 in segs) and any(k == 'V' and abs(c - cx) < 0.9 * L and cy <= a0 < cy + 2.5 * L for k, c, a0, a1 in segs): h = False
        if not h:
            esq = any(abs(sy - cy) < 1.5 and cx - 6 * L < sx < cx for sx, sy in setas_)
            dir_ = any(abs(sy - cy) < 1.5 and cx < sx < cx + 6 * L for sx, sy in setas_)
            cima = any(abs(sx - cx) < 1.5 and cy - 6 * L < sy < cy for sx, sy in setas_)
            baixo = any(abs(sx - cx) < 1.5 and cy < sy < cy + 6 * L for sx, sy in setas_)
            h = esq and dir_ and not (cima and baixo)
        nv = v
        if v and h and not vv:                     # número girado numa cota horizontal
            nv = False; dy = r.width * 0.55 + 1.0
            r = fitz.Rect(cx - r.height / 2, cy - dy - r.width / 2, cx + r.height / 2, cy - dy + r.width / 2)
        elif v == 'down': nv = 'up'
        out.append((t, r, nv))
    return out
