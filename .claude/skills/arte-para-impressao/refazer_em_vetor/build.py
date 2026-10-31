import sys, cv2, numpy as np, potrace
from PIL import Image
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen
from fontTools.pens.boundsPen import BoundsPen
from reportlab.pdfgen import canvas

BLUE=(92,118,125); GOLD=(182,152,118)
F=4  # fator de vetorização
orig=np.asarray(Image.open('orig.webp').convert('RGB')).astype(np.float32)
H,W=orig.shape[:2]
bg=cv2.medianBlur(orig.astype(np.uint8),45).astype(np.float32)
m=np.load('masks.npz'); reg=m['reg']
def alpha(C):
    v=np.array(C,np.float32)-bg; n=(v*v).sum(-1)+1e-6
    return np.clip(((orig-bg)*v).sum(-1)/n,0,1)
aB,aG=alpha(BLUE),alpha(GOLD)
dd=cv2.GaussianBlur(orig-bg,(0,0),1.0)
ratio=dd[...,0]/np.where(dd[...,2]<-1e-3,dd[...,2],-1e-3)
cls=np.where(ratio>0.9,0,1)  # 0=azul (R cai mais), 1=dourado

# ---------- linhas de texto refeitas com fonte (caixas no original) ----------
FONTS={k:TTFont(f'fonts/{k}.ttf') for k in ['Poppins-Regular','Poppins-Medium','Poppins-SemiBold']}
LINES=[ # texto, fonte, caixa, tracking_fixo(None=ajusta pela largura)
 ("ODONTOLOGIA ESPECIALIZADA","Poppins-Medium",(855,200,1230,228)),
 ("ORTODONTIA","Poppins-Medium",(1265,290,1495,316)),
 ("PRÓTESE DENTÁRIA","Poppins-Medium",(1265,351,1495,380)),
 ("CLÍNICA GERAL","Poppins-Medium",(1265,418,1495,444)),
 ("REABILITAÇÃO ORAL","Poppins-Medium",(1265,484,1495,513)),
 ("Av. Francisco Azevedo Moraes","Poppins-Regular",(750,572,1085,600)),
 ("(Rua Chile), 37. 1 andar","Poppins-Regular",(750,600,1085,628)),
 ("75 991005920","Poppins-SemiBold",(750,645,945,680)),
 ("Isabela.odontoespecializada","Poppins-Regular",(750,695,1080,727)),
]
class RLPen(BasePen):
    def __init__(s,gs,path,x,y,k): super().__init__(gs); s.p=path; s.x=x; s.y=y; s.k=k; s.cur=None
    def T(s,pt): return (s.x+pt[0]*s.k, s.y-pt[1]*s.k)
    def _moveTo(s,pt): s.p.moveTo(*s.T(pt)); s.cur=pt
    def _lineTo(s,pt): s.p.lineTo(*s.T(pt)); s.cur=pt
    def _curveToOne(s,a,b,c): s.p.curveTo(*s.T(a),*s.T(b),*s.T(c)); s.cur=c
    def _qCurveToOne(s,q,e):
        c=s.cur; a=(c[0]+2/3*(q[0]-c[0]),c[1]+2/3*(q[1]-c[1])); b=(e[0]+2/3*(q[0]-e[0]),e[1]+2/3*(q[1]-e[1]))
        s._curveToOne(a,b,e)
    def _closePath(s): s.p.close()
def run_info(font,text):
    cm=font.getBestCmap(); gs=font.getGlyphSet(); hm=font['hmtx']
    names=[cm[ord(c)] for c in text]; adv=[hm[n][0] for n in names]
    bp=BoundsPen(gs); gs[names[0]].draw(bp); xmin=bp.bounds[0] if bp.bounds else 0
    bp=BoundsPen(gs); gs[names[-1]].draw(bp); xmax=bp.bounds[2]
    return names,adv,xmin,xmax,gs
def measure(box,sel):
    x0,y0,x1,y1=box; a=(aB[y0:y1,x0:x1]>0.4)&sel[y0:y1,x0:x1]
    cols=np.where(a.any(0))[0]; X0=x0+cols[0]; X1=x0+cols[-1]+1
    dens=a.sum(1); thr=0.4*dens.max(); rows=np.where(dens>=thr)[0]
    return X0,X1,y0+rows[0],y0+rows[-1]+1  # topo e base (linha-base)
tracedmask=np.zeros((H,W),bool)
placed=[]
for text,fk,box in LINES:
    X0,X1,top,base=measure(box,np.ones((H,W),bool))
    f=FONTS[fk]; upm=f['head'].unitsPerEm; capr=f['OS/2'].sCapHeight/upm
    names,adv,xmin,xmax,gs=run_info(f,text)
    allcaps = text.upper()==text
    if allcaps: size=(base-top)/capr
    else: size=None
    inkw=(sum(adv[:-1])+xmax-xmin)/upm  # em
    if size is None: size=(X1-X0)/inkw; track=0
    else: track=((X1-X0)-size*inkw)/(len(text)-1)
    placed.append((text,fk,X0-xmin/upm*size,base,size,track,names,adv))
    x0,y0,x1,y1=box; tracedmask[y0:y1,x0:x1]=True
    print(f'{text:30s} size={size:5.1f}px track={track:5.2f}px base={base}')


# ---- normaliza grupo da lista (mesmo tamanho/tracking/linha-base por primeira letra)
grp=[p for p in placed if p[0] in("ORTODONTIA","PRÓTESE DENTÁRIA","CLÍNICA GERAL","REABILITAÇÃO ORAL")]
placed=[p for p in placed if p not in grp]
for p,(text,fk,box) in zip(grp,[l for l in LINES if l[0] in[g[0] for g in grp]]):
    x0,y0,x1,y1=box; a=aB[y0:y1,x0:x1+0]>0.4; a=a[:, :14]  # primeira letra
    rows=np.where(a.any(1))[0]; base=y0+rows[-1]+1
    placed.append((text,"Poppins-Medium",p[2],base,17.2,2.92,p[6],p[7]))

# ---------- vetorização do restante ----------
def trace_class(a,color,minarea=6):
    big=cv2.resize(a,(W*F,H*F),interpolation=cv2.INTER_CUBIC)
    big=cv2.GaussianBlur(big,(0,0),F*0.35)
    bm=potrace.Bitmap(~(big>0.5))
    return bm.trace(turdsize=minarea*F, alphamax=1.0, opticurve=True, opttolerance=0.35)
M=reg&~tracedmask
paths=[]
for a,col in ((aB*((cls==0)&M),BLUE),(aG*((cls==1)&M),GOLD)):
    a=np.where(a>0.12,a,0).astype(np.float32)
    paths.append((trace_class(a,col),col))

# ---------- fundo ampliado ----------
bgc=Image.open('bg_clean.png').convert('RGB')
big=bgc.resize((W*F,H*F),Image.LANCZOS)
from PIL import ImageFilter
big=big.filter(ImageFilter.UnsharpMask(radius=2,percent=35,threshold=3))
big.save('bg_big.jpg',quality=95,subsampling=0,dpi=(150,150))

# ---------- PDF ----------
PW=108/2.54*72; s=PW/W; PH=H*s
c=canvas.Canvas(sys.argv[1] if len(sys.argv)>1 else 'jotak_vetor.pdf',pagesize=(PW,PH))
c.drawImage('bg_big.jpg',0,0,PW,PH)
c.saveState(); c.translate(0,PH); c.scale(s,-s)
def rgb(col): return [v/255 for v in col]
for tr,col in paths:
    c.setFillColorRGB(*rgb(col)); p=c.beginPath()
    for curve in tr:
        sp=curve.start_point; p.moveTo(sp.x/F,sp.y/F)
        for sg in curve.segments:
            if sg.is_corner:
                p.lineTo(sg.c.x/F,sg.c.y/F); p.lineTo(sg.end_point.x/F,sg.end_point.y/F)
            else:
                p.curveTo(sg.c1.x/F,sg.c1.y/F,sg.c2.x/F,sg.c2.y/F,sg.end_point.x/F,sg.end_point.y/F)
        p.close()
    c.drawPath(p,stroke=0,fill=1,fillMode=0)  # fillMode 0 = even-odd
c.setFillColorRGB(*rgb(BLUE))
for text,fk,x,base,size,track,names,adv in placed:
    f=FONTS[fk]; upm=f['head'].unitsPerEm; gs=f.getGlyphSet(); k=size/upm; p=c.beginPath(); pen_x=x
    for n,a_ in zip(names,adv):
        gs[n].draw(RLPen(gs,p,pen_x,base,k)); pen_x+=a_*k+track
    c.drawPath(p,stroke=0,fill=1,fillMode=1)
c.restoreState(); c.showPage(); c.save()
print('PDF ok')
