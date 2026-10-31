"""Etapa extra: vetoriza blocos de cor chapada e traços finos dourados e remove do fundo."""
import cv2, numpy as np
from PIL import Image
orig=np.asarray(Image.open('orig.webp').convert('RGB')).astype(np.float32)
H,W=orig.shape[:2]
clean=np.asarray(Image.open('bg_clean.png').convert('RGB')).copy()
BLOB=np.array([136,155,162],np.float32); CREAM=np.array([243,238,230],np.float32)
GOLD=np.array([182,152,118],np.float32); HEART=np.array([220,200,178],np.float32)
REGS=[((0,0,235,165),GOLD),((1330,0,1600,291),HEART),((1420,291,1600,330),HEART),((1455,590,1600,800),GOLD),((1340,722,1455,800),GOLD)]
BLOBREG=[(0,0,235,165),(1455,600,1600,800),(1340,722,1455,800)]
rb=orig[...,0]-orig[...,2]; rb_s=cv2.GaussianBlur(rb,(0,0),1.2)
v=BLOB-CREAM; aBlob=np.clip(((orig-CREAM)*v).sum(-1)/(v*v).sum(),0,1)
# --- bloco: cor chapada azulada (R<B), ignora traço dourado e texto fora da área
blob=np.zeros((H,W),np.float32)
for x0,y0,x1,y1 in BLOBREG: blob[y0:y1,x0:x1]=((aBlob>0.5)&(rb_s<-8))[y0:y1,x0:x1]
blob=cv2.morphologyEx(blob,cv2.MORPH_CLOSE,np.ones((7,7),np.uint8))
band=cv2.dilate(blob,np.ones((9,9),np.uint8))-cv2.erode(blob,np.ones((9,9),np.uint8))
blobsoft=cv2.GaussianBlur(blob,(0,0),0.8)
# --- traços: fora do bloco por contraste de luminosidade; sobre o bloco pelo tom (R sobe)
Lum=orig@np.array([0.299,0.587,0.114],np.float32)
diff=cv2.medianBlur(Lum.astype(np.uint8),21).astype(np.float32)-Lum
blobfill=cv2.erode(blob,np.ones((5,5),np.uint8))>0.5
line=np.zeros((H,W),np.float32); erase=np.zeros((H,W),np.float32); cols=[]
for (x0,y0,x1,y1),C in REGS:
    d=diff[y0:y1,x0:x1]; pk=np.percentile(d[d>6],95) if (d>6).any() else 1
    out=(d>(0.55 if x0 in (1330,1420) else 0.45)*pk); outE=(d>(0.10 if x0 in (1330,1420) else 0.22)*pk)
    inb=blobfill[y0:y1,x0:x1]; chroma=(rb_s[y0:y1,x0:x1]>-6)
    ok=(band[y0:y1,x0:x1]<0.5)
    m=((out&~inb.astype(bool))|(inb.astype(bool)&chroma))&ok
    me=((outE&~inb.astype(bool))|(inb.astype(bool)&chroma))&ok
    m=m.astype(np.uint8); me=me.astype(np.uint8)
    m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((21,21),np.uint8) if x0==0 else np.ones((5,5),np.uint8))
    n,lab,st,_=cv2.connectedComponentsWithStats(m,8)  # tira poeira
    for i in range(1,n):
        if st[i,4]<40: m[lab==i]=0
    if x0==0:  # arco liso: ajusta curva nos pedaços detectados e preenche a emenda sobre o bloco
        ys,xs=np.nonzero(m); p=np.polyfit(ys,xs,3); yy=np.arange(ys.min(),ys.max()+1)
        m[:]=0; cv2.polylines(m,[np.stack([np.polyval(p,yy),yy],1).round().astype(np.int32)],False,1,2)
    if x0==1330:  # ponta que sai pelo topo: prolonga a reta até a borda da arte
        ys,xs=np.nonzero(m[:40,150:]); k=np.polyfit(ys,xs+150,1); yt=int(ys.min())
        cv2.line(m,(int(np.polyval(k,yt)),yt),(int(np.polyval(k,0)),0),1,5)
    line[y0:y1,x0:x1]=np.maximum(line[y0:y1,x0:x1],m.astype(np.float32)); erase[y0:y1,x0:x1]=np.maximum(erase[y0:y1,x0:x1],me.astype(np.float32))
    cols.append(tuple(C))
er=cv2.dilate(((blobsoft>0.05)|(line>0.05)|(erase>0.5)).astype(np.uint8),np.ones((9,9),np.uint8))
clean=cv2.inpaint(clean,er*255,8,cv2.INPAINT_TELEA)
Image.fromarray(clean).save('bg_clean2.png')
np.savez('extra.npz',blob=blobsoft,line=line,BLOB=BLOB,cols=np.array(cols),regs=np.array([r for r,_ in REGS]))
