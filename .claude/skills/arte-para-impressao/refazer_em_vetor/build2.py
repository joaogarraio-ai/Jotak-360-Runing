"""Refação em vetor LIMPA: ícones geométricos, dentes simétricos, linhas por spline, blocos em elipse, texto em curvas."""
import sys, cv2, numpy as np, potrace
from PIL import Image, ImageFilter
from fontTools.ttLib import TTFont
from reportlab.pdfgen import canvas
import vec
exec(open('build.py').read().split("# ---------- vetorização do restante")[0].split("# ---------- linhas de texto refeitas")[0])  # carrega orig,bg,aB,aG,cls...

BLUE=(92,118,125); GOLD=(182,152,118); HEART=(220,200,178); BLOBC=(136,155,162)
OUT=sys.argv[1] if len(sys.argv)>1 else 'jotak_vetor2.pdf'
Lum=orig@np.array([0.299,0.587,0.114],np.float32)
lum=lambda c: 0.299*c[0]+0.587*c[1]+0.114*c[2]

# ---------------- textos refeitos com fonte (igual ao build.py) ----------------
src=open('build.py').read(); a=src.index("# ---------- linhas de texto refeitas"); b=src.index("# ---------- vetorização do restante")
exec(src[a:b])   # define LINES, placed, RLPen, tracedmask...

# ---------------- elementos geométricos ----------------
aBc=np.clip(((orig-bg)*(np.array(BLUE,np.float32)-bg)).sum(-1)/(((np.array(BLUE,np.float32)-bg)**2).sum(-1)+1e-6),0,1)
aGc=np.clip(((orig-bg)*(np.array(GOLD,np.float32)-bg)).sum(-1)/(((np.array(GOLD,np.float32)-bg)**2).sum(-1)+1e-6),0,1)
vecs=[]   # (subpaths, rgb, even_odd)
icons_boxes=[(700,570,745,615),(700,640,745,684),(700,689,745,732)]+[(1204,279,1252,327),(1204,339,1252,394),(1204,408,1252,456),(1204,472,1252,529)]+[(1155,270,1175,532)]
vecs.append((vec.build_pin(aBc,(700,570,745,615)),BLUE,True))
vecs.append((vec.build_whatsapp(aBc,(700,640,745,684)),BLUE,True))
vecs.append((vec.build_instagram(aBc,(700,689,745,732)),BLUE,True))
for bx in [(1204,279,1252,327),(1204,339,1252,394),(1204,408,1252,456),(1204,472,1252,529)]:
    vecs.append((vec.build_traced(aGc,bx,F=12,blur=0.5,sym=True,alphamax=1.25,opttol=1.2,thr=0.55),GOLD,True))
# divisória vertical: retângulo exato
sub=aGc[270:535,1158:1172]; cols=sub.sum(0); cx=1158+ (cols*np.arange(14)).sum()/cols.sum()+0.5; wdt=cols.sum()/ (sub>0.3).any(1).sum()
rows=np.where((sub>0.3).any(1))[0]; yt,yb=270+rows[0],270+rows[-1]+1
vecs.append(([[('M',cx-wdt/2,yt),('L',cx+wdt/2,yt),('L',cx+wdt/2,yb),('L',cx-wdt/2,yb)]],GOLD,True))

# ---------------- blocos de cor chapada: elipse ajustada ----------------
ex=np.load('extra.npz'); blob=ex['blob']
def ellipse_from(mask):
    big=cv2.resize((mask>0.5).astype(np.uint8),(W*4,H*4),interpolation=cv2.INTER_NEAREST)
    cs,_=cv2.findContours(big,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE); out=[]
    for c in cs:
        if cv2.contourArea(c)<800: continue
        p=c[:,0,:]; ok=(p[:,0]>8)&(p[:,1]>8)&(p[:,0]<W*4-8)&(p[:,1]<H*4-8)
        # tira pontos junto às emendas das caixas de região
        for x_ in (1455*4,1340*4,235*4): ok&=np.abs(p[:,0]-x_)>12
        for y_ in (722*4,165*4,600*4): ok&=np.abs(p[:,1]-y_)>12
        q=p[ok].astype(np.float64); cx,cy,r=vec.fit_circle(q); res=np.abs(np.hypot(q[:,0]-cx,q[:,1]-cy)-r)
        print('bloco: círculo c=(%.0f,%.0f) r=%.0f erro médio %.2f px, máx %.2f px (arte)'%(cx/4,cy/4,r/4,res.mean()/4,res.max()/4))
        out.append(vec.circle_ops(cx/4,cy/4,r/4))
    return out
for e in ellipse_from(blob): vecs.insert(0,([e],BLOBC,True))

# ---------------- linhas finas: spline + espessura medida ----------------
diff=np.clip(cv2.medianBlur(Lum.astype(np.uint8),21).astype(np.float32)-Lum,0,None)
strokes=[]
line=ex['line']
for box,col in [((0,0,235,165),GOLD),((1330,0,1600,330),HEART),((1340,590,1600,800),GOLD)]:
    cfg={0:dict(tol=1.6,corner_deg=120),1330:dict(tol=3.2,corner_deg=32),1340:dict(tol=7.0,corner_deg=120,close_px=10,step=34)}[box[0]]
    sp,L=vec.fit_stroke(line,box,**cfg)
    msk=cv2.dilate((line>0.5).astype(np.uint8),np.ones((5,5),np.uint8))
    x0,y0,x1,y1=box; m=(msk*(blob<0.05))[y0:y1,x0:x1].astype(bool)
    wall=np.median(Lum[y0:y1,x0:x1][~m]) if (~m).any() else 235
    w=0.88*diff[y0:y1,x0:x1][m].sum()/L/max(wall-lum(col),20)
    strokes.append((sp,col,float(np.clip(w,1.0,7))))
    print('traço',box,'nós',vec.count_nodes(sp),'largura %.2f'%w)

# ---------------- vetorização suave do restante (script, logo, título, frase) ----------------
excl=np.zeros((H,W),bool)
for x0,y0,x1,y1 in icons_boxes: excl[y0:y1,x0:x1]=True
for x0,y0,x1,y1 in [l[2] for l in LINES]: excl[y0:y1,x0:x1]=True
excl|=tracedmask
excl[28:152,983:1077]=True   # logomarca SP: vetorizada à parte (separação de 2 tintas)
excl[704:722,1436:1456]=True   # emenda da linha do canto (já vetorizada como traço)
traced=[]
for rg in [(790,30,1290,232),(640,265,1140,530),(1200,575,1455,722)]:
    x0,y0,x1,y1=rg
    for A,col in ((aB,BLUE),(aG,GOLD)):
        al=np.where(((cls==(0 if col==BLUE else 1))&~excl),A,0).astype(np.float32)
        al=np.where(al>0.12,al,0)
        if rg[1]==30: al=np.clip(al*1.45,0,1)          # logo/título: realça traços finos antes de vetorizar
        cur=vec.build_traced(al,rg,F=6,blur=(0.3 if rg[1]==30 else 0.5),alphamax=1.2,opttol=0.9,turd=(30 if rg[1]==30 else 80),thr=0.5)
        traced.append((cur,col,True)); print('trace',rg,col,'nós',vec.count_nodes(cur))

# ---------------- logomarca SP (azul + dourado) ----------------
LOGO=(985,30,1075,150)
img8=np.asarray(Image.open('orig.webp').convert('RGB'))
lb,lg,lcb,lcg=vec.unmix_two_inks(img8,LOGO,thr=(0.45,0.33))
traced.append((lg,BLUE if False else tuple(int(v) for v in lcg),True)); traced.append((lb,tuple(int(v) for v in lcb),True))
print('logo cores',lcb,lcg)

# ---------------- fundo: suaviza parede (gradiente) e limpa a foto sem mexer no rosto ----------------
bg2=np.asarray(Image.open('bg_clean2.png').convert('RGB'))
photo=cv2.fastNlMeansDenoisingColored(bg2,None,3,3,5,15)       # tira ruído/bloco de JPEG da pele, bem leve
wall=bg2.astype(np.float32); k=np.ones((H,W),np.float32)
sm=cv2.GaussianBlur(wall,(0,0),7)                              # parede lisa = gradiente limpo
wx=np.clip((np.arange(W)-640)/20.0,0,1)[None,:,None]           # só à direita da modelo
final=(photo.astype(np.float32)*(1-wx)+sm*wx)
final=np.clip(final,0,255).astype(np.uint8)
finalf=np.clip(final.astype(np.float32),0,255)
# (usa a versão float para não criar faixas no gradiente)
finalf=(photo.astype(np.float32)*(1-wx)+sm*wx)
bigf=cv2.resize(finalf,(W*4,H*4),interpolation=cv2.INTER_LANCZOS4)
wxb=np.clip((np.arange(W*4)-640*4)/80.0,0,1)[None,:,None]
sharp=bigf+0.35*(bigf-cv2.GaussianBlur(bigf,(0,0),2.0))
bigf=sharp*(1-wxb)+bigf*wxb
rng=np.random.default_rng(1); bigf=bigf+rng.normal(0,0.8,bigf.shape[:2])[...,None]   # dither: elimina bandas
Image.fromarray(np.clip(bigf,0,255).astype(np.uint8)).save('bg_big2.jpg',quality=95,subsampling=0)

# ---------------- PDF ----------------
PW=108/2.54*72; s=PW/W; PH=H*s
c=canvas.Canvas(OUT,pagesize=(PW,PH)); c.drawImage('bg_big2.jpg',0,0,PW,PH)
c.saveState(); c.translate(0,PH); c.scale(s,-s)
c.setLineCap(1); c.setLineJoin(1)
for sp,col,eo in vecs[:0]: pass
def draw_set(items):
    for sp,col,eo in items: vec.draw_ops(c,sp,col,eo)
draw_set([v for v in vecs if v[1]==BLOBC])          # blocos por baixo
for sp,col,w in strokes:                              # linhas finas
    c.setStrokeColorRGB(*[v/255 for v in col]); c.setLineWidth(w)
    for ops in sp:
        p=c.beginPath()
        for op in ops:
            (p.moveTo if op[0]=='M' else p.curveTo)(*op[1:])
        c.drawPath(p,stroke=1,fill=0)
draw_set(traced); draw_set([v for v in vecs if v[1]!=BLOBC])
c.setFillColorRGB(*[v/255 for v in BLUE])
for text,fk,x,base,size,track,names,adv in placed:
    f=FONTS[fk]; upm=f['head'].unitsPerEm; gs=f.getGlyphSet(); kk=size/upm; p=c.beginPath(); px=x
    for n,a_ in zip(names,adv):
        gs[n].draw(RLPen(gs,p,px,base,kk)); px+=a_*kk+track
    c.drawPath(p,stroke=0,fill=1,fillMode=1)
c.restoreState(); c.showPage(); c.save(); print('PDF ok')
