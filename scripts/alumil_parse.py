import csv,glob,re,collections,json
pat=re.compile(r'^([A-Z]{1,4})[-.]?(\d{2,4}[A-Z]?)[,;:]?$')
wp=re.compile(r'(\d+[,.]\d{3})')
idx=collections.defaultdict(list)
for f in sorted(glob.glob('ocr_alumil2/p*.tsv')):
  pg=int(f[-7:-4])+1
  toks=[(r['text'].strip(),int(r['left']),int(r['top']),int(r['height'])) for r in csv.DictReader(open(f),delimiter='\t',quoting=csv.QUOTE_NONE) if (r['text'] or '').strip() and float(r['conf'])>30]
  for t in toks:
    m=pat.match(t[0])
    if m and t[3]>=24:
      c=f'{m[1]}-{m[2]}'
      cand=[(x[2]-t[2]+abs(x[1]-t[1])/3,x[0]) for x in toks if -10<x[2]-t[2]<160 and -80<x[1]-t[1]<400 and wp.search(x[0]) and x is not t]
      w=wp.search(min(cand)[1])[1] if cand else ''
      idx[c].append((pg,w))
json.dump(idx,open('alumil_idx.json','w'))
