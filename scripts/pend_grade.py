import sys,glob,os
sys.path.insert(0,'/home/claude')
from folha import folha
D='/home/claude/alcoa/pend/v1'
ks=sorted(os.path.basename(f)[:-4] for f in glob.glob(D+'/*.svg'))
ks=[k for k in ks if os.path.exists(f'{D}/o_{k}.png')]
for i in range(0,len(ks),8):
    folha([(k,f'{D}/o_{k}.png',f'{D}/{k}.png') for k in ks[i:i+8]],f'/tmp/r8/pg_{i//8:02d}.png',larg=300)
print(len(ks))
