import json,re,openpyxl,collections
def nk(c):
  c=str(c).replace(' ','').upper()
  m=re.match(r'^([A-Z]+)-?0*(\d+)([A-Z]?)$',c)
  return f'{m[1]}{m[2]}{m[3]}' if m else c
S=collections.defaultdict(list)
for stl,pg,w,m in json.load(open('stelman_merc.json')):
  S[nk(stl)].append((stl,pg,w,'código STL'))
  for mm in re.split(r'[/;]| E ',m or ''):
    mm=mm.strip()
    if mm and not mm.startswith('-'): S[nk(mm)].append((stl,pg,w,f'Merc. {mm}'))
I=collections.defaultdict(list)
for k,v in json.load(open('isal_idx2.json')).items():
  if k.startswith('AP-'): continue
  for x in v: I[nk(k)].append(x)
uw=openpyxl.load_workbook('user_cruz.xlsx',data_only=True)['Lista completa']
UC={str(r[0]):str(r[3]) for r in uw.iter_rows(min_row=2,values_only=True) if r[3]}
