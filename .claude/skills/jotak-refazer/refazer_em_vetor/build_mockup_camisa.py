import sys, cv2, numpy as np, potrace
from PIL import Image
from reportlab.pdfgen import canvas
OUT=sys.argv[1] if len(sys.argv)>1 else 'camisa.pdf'
im=np.asarray(Image.open('camisa.jpg').convert('RGB'))
AX0,AY0,AX1,AY1=255,410,795,1130          # área da arte (540x720) -> 30x40 cm
art=im[AY0:AY1,AX0:AX1]; H,W=art.shape[:2]
lum=art.astype(np.float32)@np.array([.299,.587,.114],np.float32)
m=(lum>165).astype(np.uint8)
n,lab,st,cen=cv2.connectedComponentsWithStats(m,8)
sel=np.zeros((H,W),bool); birds=np.zeros((H,W),bool); info=[]
for i in range(1,n):
    a=st[i,4]; x,y,w,h=st[i,:4]; cx,cy=cen[i]
    if a<35 or (a<80 and w<12): continue
    # fora da região do texto/lua/pássaros
    if not (0<=y<=300 and 0<=x<=560): pass
    moon = (a>3000 and w>130 and h>200) or (a>3000 and h<70 and w>120 and x>100 and x<260 and y>230)   # crescente: peça grande e peça inferior
    edge = x<=1 or x+w>=W-1 or y+h>=H-1
    if moon or edge: continue
    if y>260 or y<10 and False: continue
    isbird = cx>380 and cy<100 and a<2500 and w>30
    (birds if isbird else sel)[lab==i]=True; info.append((int(a),int(x),int(y),int(w),int(h),'ave' if isbird else 'txt'))
print(len(info),'componentes'); [print(t) for t in sorted(info,reverse=True)[:30]]
np.savez('cam_masks.npz',sel=sel,birds=birds)

# ---------- hi-res: máscara do texto/pássaros com borda suave ----------
F=6
lum_hi=cv2.resize(lum,(W*F,H*F),interpolation=cv2.INTER_CUBIC)
def hires(mask1x):
    reg=cv2.dilate(mask1x.astype(np.uint8),np.ones((3,3),np.uint8))
    reg=cv2.resize(reg,(W*F,H*F),interpolation=cv2.INTER_NEAREST)>0
    return reg&(cv2.GaussianBlur(lum_hi,(0,0),F*0.3)>135)
def clean_trace(mk,turd=20):
    return potrace.Bitmap(~mk).trace(turdsize=turd*F*F//4,alphamax=1.1,opticurve=True,opttolerance=0.6)
txt_m=hires(sel); bird_m=hires(birds)
txt_c=clean_trace(txt_m); bird_c=clean_trace(bird_m,4)
col_txt=tuple(np.median(art[sel&(lum>185)],0).round().astype(int)); col_bird=tuple(np.median(art[birds&(lum>150)],0).round().astype(int))
print('cor texto',col_txt,'pássaros',col_bird,'nós texto',sum(len(c.segments) for c in txt_c))

# ---------- fundo: tira texto/pássaros (e o contorno escuro) e amplia ----------
rm=cv2.dilate((sel|birds).astype(np.uint8),cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(7,7)))
bg=cv2.inpaint(art,rm*255,4,cv2.INTER_AREA if False else cv2.INPAINT_TELEA)
bg=cv2.fastNlMeansDenoisingColored(bg,None,3,3,5,15)
FB=4
bgb=cv2.resize(bg,(W*FB,H*FB),interpolation=cv2.INTER_LANCZOS4).astype(np.float32)
bgb=np.clip(bgb+0.4*(bgb-cv2.GaussianBlur(bgb,(0,0),2.2)),0,255)
bgb=bgb+np.random.default_rng(2).normal(0,0.8,bgb.shape[:2])[...,None]    # dither, evita bandas no azul
Image.fromarray(np.clip(bgb,0,255).astype(np.uint8)).save('cam_bg.jpg',quality=95,subsampling=0)

# ---------- PDF 30x40 cm ----------
PW=30/2.54*72; PH=40/2.54*72; s_=PW/W; c=canvas.Canvas(OUT,pagesize=(PW,PH))
c.drawImage('cam_bg.jpg',0,0,PW,PH)
c.saveState(); c.translate(0,PH); c.scale(s_,-s_)
def path_of(curves):
    p=c.beginPath()
    for cv in curves:
        sp=cv.start_point; p.moveTo(sp.x/F,sp.y/F)
        for sg in cv.segments:
            if sg.is_corner: p.lineTo(sg.c.x/F,sg.c.y/F); p.lineTo(sg.end_point.x/F,sg.end_point.y/F)
            else: p.curveTo(sg.c1.x/F,sg.c1.y/F,sg.c2.x/F,sg.c2.y/F,sg.end_point.x/F,sg.end_point.y/F)
        p.close()
    return p
OUTL=(28,44,118)
c.setLineJoin(1); c.setLineCap(1)
for curves,col,w_ in ((txt_c,col_txt,5.0),(bird_c,col_bird,0)):
    p=path_of(curves)
    if w_: c.setStrokeColorRGB(*[v/255 for v in OUTL]); c.setLineWidth(w_); c.drawPath(p,stroke=1,fill=0)
    c.setFillColorRGB(*[v/255 for v in col]); c.drawPath(p,stroke=0,fill=1,fillMode=0)
c.restoreState(); c.showPage(); c.save(); print('PDF ok')
