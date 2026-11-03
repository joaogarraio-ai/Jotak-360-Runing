"""Arte para sublimação: fundo estendido (sangria) ligado à cor do tecido + texto em vetor no molde."""
import sys, cv2, numpy as np
from PIL import Image
from reportlab.pdfgen import canvas
OUT=sys.argv[1] if len(sys.argv)>1 else 'sublim.pdf'
# ---- reaproveita máscaras/vetores do texto (build_camisa.py, até antes do fundo) ----
src=open('build_camisa.py').read(); exec(src[:src.index("# ---------- fundo: tira texto")])   # define art,W,H,sel,birds,txt_c,bird_c,col_txt,col_bird,F,...
art_bg=np.asarray(Image.open('fundo_limpo3_1x.png').convert('RGB')).astype(np.float32)   # 540x720 (1x)

# ---- molde (px do seu desenho): folha 496x650, contorno amarelo x22..475 y34..626 ----
SHEET_W,SHEET_H=496,650; YEL=(22,34,475,626)
K=1.25                                    # px da arte por px do molde
CW,CH=int(round(SHEET_W*K)),int(round(SHEET_H*K))      # 620 x 813
OX,OY=int(round(32*K)),int(round(122*K))                # arte centrada, topo logo abaixo da gola
NAVY=np.array([21,30,85],np.float32)

# ---- extensão do fundo ----
base=np.zeros((CH,CW,3),np.float32); inside=np.zeros((CH,CW),bool)
y1=min(OY+H,CH); base[OY:y1,OX:OX+W]=art_bg[:y1-OY]; inside[OY:y1,OX:OX+W]=True
# fonte da extensão: bordas "limpas" (sem estrelas e sem a ponta da lua) -> evita listras e brilho
es=art_bg.copy(); u8=lambda a: np.clip(a,0,255).astype(np.uint8)
for r_ in range(0,10):                                    # tira a ponta da lua do topo (interpola em x)
    xa,xb=95,245
    for ch in range(3): es[r_,xa:xb,ch]=np.linspace(es[r_,xa,ch],es[r_,xb,ch],xb-xa)
es[:8]=cv2.medianBlur(u8(es[:8].copy()).repeat(1,0),1) if False else es[:8]
top=cv2.medianBlur(u8(np.repeat(es[:1],7,0)),7)          # placeholder p/ shape
for r_ in range(8): es[r_]=cv2.blur(es[r_:r_+1],(41,1))[0]
for cidx in list(range(0,14))+list(range(W-14,W)):
    col=u8(es[:,cidx:cidx+1]); es[:,cidx:cidx+1]=cv2.medianBlur(np.repeat(col,3,1),101)[:,:1]
rep=cv2.copyMakeBorder(es[:y1-OY],OY,CH-y1,OX,CW-OX-W,cv2.BORDER_REPLICATE)
dist=cv2.distanceTransform((~inside).astype(np.uint8),cv2.DIST_L2,5)
low=cv2.GaussianBlur(rep,(0,0),16)                           # cor de transição (baixa frequência)
# textura (estrelas/nuvens): ladrilho do céu à direita da lua e do mar embaixo
def tile(src_img,h_,w_):
    t=np.concatenate([src_img,src_img[:,::-1]],1); t=np.concatenate([t,t[::-1]],0)
    return np.tile(t,(h_//t.shape[0]+1,w_//t.shape[1]+1,1))[:h_,:w_]
sky=art_bg[0:150,330:540]; sea=art_bg[560:720,200:420]
dsky=sky-cv2.GaussianBlur(sky,(0,0),5); dsea=sea-cv2.GaussianBlur(sea,(0,0),5)
det=np.zeros_like(base); ysplit=OY+330
det[:ysplit]=tile(dsky,ysplit,CW); det[ysplit:]=tile(dsea,CH-ysplit,CW)*0.0   # mar: só cor suave (sem listras)
ext=low+det*0.8
rng0=np.random.default_rng(8); ext+=cv2.GaussianBlur(rng0.normal(0,1,(CH,CW)).astype(np.float32),(0,0),0.8)[...,None]*1.6   # granulação suave
t=np.clip(dist/150.0,0,1)**1.2*0.55                           # escurece até o azul do tecido
ext=ext*(1-t[...,None])+NAVY*t[...,None]
# estrelas extras no céu estendido (rarefeitas)
rng=np.random.default_rng(21); st=np.zeros((CH,CW),np.float32)
for _ in range(260):
    x=rng.integers(0,CW); y=rng.integers(0,OY+60)
    if dist[y,x]>0: st[y,x]+=rng.uniform(0.08,0.35)*(1-min(dist[y,x]/150,1)*0.7)
ext+=np.stack([cv2.GaussianBlur(st,(0,0),0.9)*3.0*c for c in (0.85,0.95,1.0)],-1)*255*0.6
# mistura suave na emenda (24 px dentro da arte)
inner=cv2.distanceTransform(inside.astype(np.uint8),cv2.DIST_L2,5)
w=np.where(inside,np.clip(1-inner/26.0,0,1)*0.9,1.0)[...,None]
# ---- composição em 4x: fundo ampliado por IA (Real-ESRGAN) dentro da arte + extensão suave fora ----
FB=4
sr=np.asarray(Image.open('sr_fundo_x4.png').convert('RGB')).astype(np.float32)          # 2160x2880 = arte x4
sr4=np.zeros((CH*FB,CW*FB,3),np.float32); hh=min(sr.shape[0],CH*FB-OY*FB)
sr4[OY*FB:OY*FB+hh,OX*FB:OX*FB+sr.shape[1]]=sr[:hh]
up=lambda a_: cv2.resize(a_,(CW*FB,CH*FB),interpolation=cv2.INTER_CUBIC)
ext4=up(ext); w4=up(w[...,0])[...,None]; w4=np.clip(w4,0,1)
inside4=up(inside.astype(np.float32))[...,None]>0.5
comp4=np.where(inside4,sr4*(1-w4)+ext4*w4,ext4)
yy,xx=np.mgrid[0:CH*FB,0:CW*FB].astype(np.float32)
edge=np.minimum.reduce([xx,CW*FB-1-xx,yy,CH*FB-1-yy]); te=np.clip(1-edge/(28.0*FB),0,1)[...,None]*0.5
comp4=comp4*(1-te)+NAVY*te
comp4=comp4+np.random.default_rng(4).normal(0,0.7,comp4.shape[:2])[...,None]
Image.fromarray(np.clip(comp4,0,255).astype(np.uint8)).save('sublim_bg.jpg',quality=95,subsampling=0)

# ---- PDF: 52 cm de largura de frente (contorno amarelo 454 px) ----
CM_PER_PX=52/454.0; PW=SHEET_W*CM_PER_PX/2.54*72; PH=SHEET_H*CM_PER_PX/2.54*72; s_=PW/CW
c=canvas.Canvas(OUT,pagesize=(PW,PH)); c.drawImage('sublim_bg.jpg',0,0,PW,PH)
c.saveState(); c.translate(OX*s_,PH-OY*s_); c.scale(s_,-s_)     # coords da arte -> página
def path_of(curves):
    p=c.beginPath()
    for cv_ in curves:
        sp=cv_.start_point; p.moveTo(sp.x/F,sp.y/F)
        for sg in cv_.segments:
            if sg.is_corner: p.lineTo(sg.c.x/F,sg.c.y/F); p.lineTo(sg.end_point.x/F,sg.end_point.y/F)
            else: p.curveTo(sg.c1.x/F,sg.c1.y/F,sg.c2.x/F,sg.c2.y/F,sg.end_point.x/F,sg.end_point.y/F)
        p.close()
    return p
c.setLineJoin(1); c.setLineCap(1)
for curves,col,w_ in ((txt_c,col_txt,5.0),(bird_c,col_bird,0)):
    p=path_of(curves)
    if w_: c.setStrokeColorRGB(28/255,44/255,118/255); c.setLineWidth(w_); c.drawPath(p,stroke=1,fill=0)
    c.setFillColorRGB(*[v/255 for v in col]); c.drawPath(p,stroke=0,fill=1,fillMode=0)
c.restoreState(); c.showPage(); c.save()
print('PDF ok: %.1f x %.1f cm'%(SHEET_W*CM_PER_PX,SHEET_H*CM_PER_PX),'| canvas px',CW,CH)

# ---- prévia com o contorno do molde (guia, NÃO vai no PDF) ----
import subprocess; subprocess.run(['pdftocairo','-png','-r','60','-singlefile',OUT,'sublim_prev'])
pv=cv2.cvtColor(cv2.imread('sublim_prev.png'),cv2.COLOR_BGR2RGB); sc=pv.shape[1]/SHEET_W
L=np.load('molde_yel.npy').astype(np.uint8); cs,_=cv2.findContours(L,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE); cnt=max(cs,key=len)[:,0,:].astype(np.float32)
cnt=((cnt-[134,236])*sc).astype(np.int32); cv2.polylines(pv,[cnt],True,(255,230,0),2)
Image.fromarray(pv).save('sublim_prev_guia.png'); print(pv.shape)
