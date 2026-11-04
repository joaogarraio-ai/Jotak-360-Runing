"""Fachada TRB: reorganiza em 3 colunas (logo | serviços 2x2 | material+telefone) em 472x94 cm."""
import sys, cv2, numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS=None
SRC=sys.argv[1] if len(sys.argv)>1 else 'trb/board_sr_x4.png'      # board3000 ampliado 4x
OUT=sys.argv[2] if len(sys.argv)>2 else 'trb/layout.png'
SR=np.asarray(Image.open(SRC).convert('RGB')).astype(np.float32)
F_SRC=SR.shape[1]/2973.0                                           # 4.0 se for o x4
CWu,CHu=4358,868                                                  # canvas em "unidades board3000"
Q=4.0                                                              # px finais por unidade
CW,CH=int(CWu*Q),int(CHu*Q)

# ---------- fundo: azul liso do painel (a barra azul e as luminárias do mockup NÃO entram) ----------
def med_block(x0,x1,y0,y1): return np.median(SR[int(y0*F_SRC):int(y1*F_SRC), int(x0*F_SRC):int(x1*F_SRC)].reshape(-1,3),0)
c_top=med_block(40,200,160,420); c_bot=med_block(40,200,420,620)
ys=np.linspace(0,1,CH)[:,None]; bg=c_top[None,:]*(1-ys)+c_bot[None,:]*ys
canvas=np.repeat(bg[:,None,:],CW,1).astype(np.float32)
print('fundo azul',c_top.round(),c_bot.round())

def crop(x0,y0,x1,y1):                                            # coords em unidades board3000
    return SR[int(y0*F_SRC):int(y1*F_SRC), int(x0*F_SRC):int(x1*F_SRC)]
def elem_alpha(src, lo=16, hi=52):
    """alpha do elemento = quão diferente o pixel é do fundo local estimado (anel + inpaint em baixa resolução)."""
    h,w=src.shape[:2]; k=max(1,int(max(h,w)/220)); small=cv2.resize(src,(w//k,h//k),interpolation=cv2.INTER_AREA).astype(np.float32)
    sh,sw=small.shape[:2]; ring=np.concatenate([small[:3].reshape(-1,3),small[-3:].reshape(-1,3),small[:,:3].reshape(-1,3),small[:,-3:].reshape(-1,3)])
    c0=np.median(ring,0); d0=np.linalg.norm(small-c0,axis=2); el=cv2.dilate((d0>40).astype(np.uint8),np.ones((5,5),np.uint8))
    est=cv2.inpaint(np.clip(small,0,255).astype(np.uint8),el*255,5,cv2.INPAINT_TELEA).astype(np.float32); est=cv2.GaussianBlur(est,(0,0),3)
    est=cv2.resize(est,(w,h),interpolation=cv2.INTER_CUBIC)
    d=np.linalg.norm(src-est,axis=2); a=np.clip((d-lo)/(hi-lo),0,1)
    lum=lambda x: x@np.array([.299,.587,.114],np.float32)
    ratio=np.clip(lum(src)/np.maximum(lum(est),1),0.35,1.0)      # sombra projetada (mais escuro que o fundo)
    return a,ratio
def place(src,cx,cy,scale,feather=0,anchor='c',alpha=None,shadow=True):
    h,w=src.shape[:2]; f=scale*Q/F_SRC
    a,ratio=(alpha if alpha is not None else elem_alpha(src))
    rs=lambda x,m: cv2.resize(x,(max(1,int(w*f)),max(1,int(h*f))),interpolation=m)
    im=rs(src,cv2.INTER_AREA if f<1 else cv2.INTER_CUBIC); al=rs(a,cv2.INTER_AREA if f<1 else cv2.INTER_CUBIC); rt=rs(ratio,cv2.INTER_AREA if f<1 else cv2.INTER_CUBIC)
    h2,w2=im.shape[:2]
    if anchor=='c': x0,y0=int(cx*Q-w2/2),int(cy*Q-h2/2)
    elif anchor=='l': x0,y0=int(cx*Q),int(cy*Q-h2/2)
    else: x0,y0=int(cx*Q-w2),int(cy*Q-h2/2)
    X0,Y0,X1,Y1=max(x0,0),max(y0,0),min(x0+w2,CW),min(y0+h2,CH)
    if X1<=X0 or Y1<=Y0: return
    sl=(slice(Y0-y0,Y1-y0),slice(X0-x0,X1-x0)); A=np.clip(al[sl],0,1)[...,None]
    base=canvas[Y0:Y1,X0:X1]
    if shadow: base=base*(rt[sl][...,None]**0.8)
    canvas[Y0:Y1,X0:X1]=base*(1-A)+im[sl]*A
def gold_alpha(src,x0,y0,excl=None):
    """alpha só do dourado (arcos dos cantos), sem texto/divisórias; excl = retângulos (unidades board) a ignorar."""
    r,g,b=src[...,0],src[...,1],src[...,2]; m=((r>140)&(g>80)&(b<110)&(r>b+70)).astype(np.float32)
    h,w=m.shape
    for (ex0,ey0,ex1,ey1) in (excl or []):
        m[int((ey0-y0)*F_SRC):int((ey1-y0)*F_SRC), int((ex0-x0)*F_SRC):int((ex1-x0)*F_SRC)]=0
    m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((31,31),np.uint8))
    n,lab,st,_=cv2.connectedComponentsWithStats((m>0.5).astype(np.uint8),8)
    for i in range(1,n):
        x,y,w_,h_,ar=st[i]; toca=(x<=2) or (y+h_>=h-2) or (x+w_>=w-2)
        if ar<4000 or not toca: m[lab==i]=0                            # só o arco que encosta na borda do recorte
    m=cv2.GaussianBlur(m,(0,0),1.5)
    return np.clip(m*1.3,0,1), np.ones_like(m)
if __name__=='__main__':
    # arcos dourados dos cantos (só o dourado)
    c1=crop(0,640,700,868); place(c1,350,868-114,1.0,alpha=gold_alpha(c1,0,640,[(285,640,700,778)]),shadow=False)
    ga=gold_alpha(c1,0,640,[(285,640,700,778)]); c2=c1[:,::-1].copy(); ga2=(ga[0][:,::-1].copy(),ga[1][:,::-1].copy())
    place(c2,4358-350,868-114,1.0,alpha=ga2,shadow=False)                  # canto direito = espelho do esquerdo
    # coluna 1: logo
    lc=crop(215,15,1700,560); la,lr=elem_alpha(lc,lo=30,hi=75)
    # halo dos holofotes (mockup): bege/laranja com azul médio-alto; o dourado do arco do logo tem azul baixo
    bch=lc[...,2]; X=lambda x: int((x-215)*F_SRC); Y=lambda y: int((y-15)*F_SRC)
    cut=np.zeros(la.shape,np.float32)
    for (x0,x1,y1) in ((360,700,128),(1500,1700,128)): cut[:Y(y1),X(x0):X(x1)]=1
    cut[:Y(56),X(1400):X(1520)]=1; cut=cv2.GaussianBlur(cut,(0,0),4)
    keep_gold=np.clip((70-bch)/18,0,1)
    la=la*(1-cut*(1-keep_gold))
    la[:, :int(8*F_SRC)]*=np.linspace(0,1,int(8*F_SRC))[None,:]
    la=cv2.GaussianBlur(la,(0,0),1.0)
    place(lc,980,395,1.2,alpha=(la,np.ones_like(lr)),shadow=False)
    # coluna 2: serviços 2x2
    S=1.4; items=[(295,565,615,785),(685,565,1000,785),(1068,565,1360,785),(1445,565,1735,785)]
    cells=[(2290,280),(2770,280),(2290,590),(2770,590)]          # centros (x,y) em unidades do canvas
    for (x0,y0,x1,y1),(cx,cy) in zip(items,cells): place(crop(x0,y0,x1,y1),cx,cy+60,S)
    # coluna 3: material + produtos + telefone
    mc=crop(1775,50,2870,305); ma,mr=elem_alpha(mc)
    gz=(slice(0,int(40*F_SRC)),slice(int((2300-1775)*F_SRC),int((2680-1775)*F_SRC))); ma[gz]=0     # brilho de holofote
    place(mc,3590,200,1.03,alpha=(ma,mr))
    place(crop(1775,305,2915,560),3590,455,1.03,feather=22)
    place(crop(1830,590,2780,790),3590,700,1.03,feather=20)
    Image.fromarray(np.clip(canvas,0,255).astype(np.uint8)).save(OUT)
    Image.fromarray(np.clip(canvas,0,255).astype(np.uint8)).resize((1800,int(1800*CH/CW)),Image.LANCZOS).save(OUT.replace('.png','_s.png'))
    print('canvas',CW,CH)
