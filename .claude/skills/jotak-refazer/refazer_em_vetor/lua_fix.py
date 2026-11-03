import cv2, numpy as np
from PIL import Image
from skimage.restoration import inpaint_biharmonic
from scipy.optimize import least_squares
orig=np.asarray(Image.open('camisa.jpg').convert('RGB'))[410:1130,255:795].astype(np.float32)/255
H,W=orig.shape[:2]; lum=(orig*255)@np.array([.299,.587,.114],np.float32)
d=np.load('cam_masks.npz'); txt=(d['sel']|d['birds']); tm=cv2.dilate(txt.astype(np.uint8),cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(11,11)))>0
# --- máscara visível da lua: componentes claros grandes que NÃO são texto
m=((lum>150)&~cv2.dilate(txt.astype(np.uint8),np.ones((3,3),np.uint8)).astype(bool)).astype(np.uint8)
m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))
n,lab,st,_=cv2.connectedComponentsWithStats(m,8)
moon=np.zeros((H,W),bool)
for i in range(1,n):
    x,y,w,h=st[i,:4]
    if st[i,4]>1200 and x<300 and y<330: moon|=lab==i
print('moon px',moon.sum(), moon.any(0).nonzero()[0][[0,-1]], moon.any(1).nonzero()[0][[0,-1]])
cs,_=cv2.findContours(moon.astype(np.uint8),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE); c=max(cs,key=len)[:,0,:].astype(np.float32)
hull=cv2.convexHull(c.astype(np.int32)); hd=np.array([abs(cv2.pointPolygonTest(hull,(float(p[0]),float(p[1])),True)) for p in c])
outer=c[hd<1.6]; nt=cv2.dilate(tm.astype(np.uint8),np.ones((7,7),np.uint8))>0
inner=np.array([p for p,h_ in zip(c,hd) if h_>7 and not nt[int(p[1]),int(p[0])] and 3<p[0]<W-3 and 3<p[1]<H-3])
def fit(P):
    f=lambda q: np.hypot(P[:,0]-q[0],P[:,1]-q[1])-q[2]
    q0=[P[:,0].mean(),P[:,1].mean(),60]; return least_squares(f,q0,loss='soft_l1').x
co=fit(outer); ci=fit(inner); print('externo',co.round(1),'interno',ci.round(1),'pts',len(outer),len(inner))
np.savez('lua_circ.npz',co=co,ci=ci,moon=moon)
v=(orig*255).astype(np.uint8).copy()
cv2.circle(v,(int(co[0]),int(co[1])),int(co[2]),(255,60,60),1); cv2.circle(v,(int(ci[0]),int(ci[1])),int(ci[2]),(60,255,60),1)
Image.fromarray(v[0:330]).resize((1080,660)).save('lua_fit.png')

# ============ preenchimento da lua em coordenadas polares ============
tm=cv2.dilate(txt.astype(np.uint8),cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(21,21)))>0   # contorno escuro do texto ≈ 8 px
R=co[2]; cx,cy=co[:2]; ix,iy,ir=ci
base=np.asarray(Image.open('fundo_limpo_1x.png').convert('RGB')).astype(np.float32)/255   # céu já preenchido
def tfar(theta):
    u=np.stack([np.cos(theta),np.sin(theta)],-1); b=u@np.array([ix-cx,iy-cy]); c2=(ix-cx)**2+(iy-cy)**2-ir**2
    disc=b*b-c2; ok=disc>0; t=np.where(ok,b+np.sqrt(np.maximum(disc,0)),np.nan); return t,ok
yy,xx=np.mgrid[0:H,0:W].astype(np.float32); r=np.hypot(xx-cx,yy-cy); th=np.arctan2(yy-cy,xx-cx)%(2*np.pi)
tf,ok=tfar(th); rho=(r-tf)/(R-tf)
inmoon=ok&(rho>=-0.02)&(rho<=1.02)&(r<=R+1.5)
gap=inmoon&tm
# faixa angular de interesse
tmoon=th[moon]
t0,t1=np.percentile(tmoon,[0.3,99.7])
t0,t1=max(t0,0.0),t1
print('ângulos da lua',np.degrees([t0,t1]).round(0))
Nr=64; Nt=int((t1-t0)*R*1.5); thg=np.linspace(t0,t1,Nt)
tg,okg=tfar(thg); rhog=np.linspace(0,1,Nr)
print('rays válidos',okg.mean().round(2))
rr=tg[:,None]+rhog[None,:]*(R-tg[:,None]); mx=(cx+rr*np.cos(thg)[:,None]).astype(np.float32); my=(cy+rr*np.sin(thg)[:,None]).astype(np.float32)
U=cv2.remap(orig,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)
gapU=cv2.remap(tm.astype(np.float32),mx,my,cv2.INTER_NEAREST)>0.5
gapU=cv2.dilate(gapU.astype(np.uint8),np.ones((7,5),np.uint8))>0
gapU|=~np.isfinite(rr)
fill_nan=~np.isfinite(mx)
mx=np.where(np.isfinite(mx),mx,0).astype(np.float32); my=np.where(np.isfinite(my),my,0).astype(np.float32)
def interp_theta(U,gap,k=4):
    out=U.copy(); Nt_,Nr_=gap.shape
    detail=U-cv2.GaussianBlur(U,(0,0),sigmaX=0.1,sigmaY=7.0)          # textura (crateras) sem o gradiente
    for j in range(Nr_):
        g=gap[:,j]; i=0
        while i<Nt_:
            if not g[i]: i+=1; continue
            a=i
            while i<Nt_ and g[i]: i+=1
            b=i; n=b-a
            if a==0 or b>=Nt_: continue
            L=U[max(a-k,0):a,j].mean(0); Rr=U[b:min(b+k,Nt_),j].mean(0)
            t=((np.arange(a,b)-a+0.5)/n)[:,None]; base=L*(1-t)+Rr*t
            # textura: trecho conhecido mais próximo do mesmo tamanho (depois do buraco, senão antes)
            for off in (b+4, a-4-n):
                if off>=0 and off+n<=Nt_ and not g[off:off+n].any(): base=base+detail[off:off+n,j]; break
            out[a:b,j]=base
    return out
Ufill=interp_theta(U,gapU)
# suaviza levemente entre colunas vizinhas só dentro do buraco (evita listras)
sm=cv2.GaussianBlur(Ufill,(0,0),sigmaX=1.0,sigmaY=0.0); Ufill=np.where(gapU[...,None],sm,Ufill)
ringU=cv2.dilate(gapU.astype(np.uint8),np.ones((9,9),np.uint8))>0; ringU&=~gapU
hp=U-cv2.GaussianBlur(U,(0,0),1.3); sg=hp[ringU].std(0)
nz=cv2.GaussianBlur(np.random.default_rng(9).normal(0,1,U.shape).astype(np.float32),(0,0),0.9); nz*=sg/nz.reshape(-1,3).std(0)
Ufill=np.clip(Ufill+nz,0,1)
# volta para a imagem
ti=((th-t0)/(t1-t0)*(Nt-1)).astype(np.float32); ri=(np.clip(rho,0,1)*(Nr-1)).astype(np.float32)
back=cv2.remap(Ufill,ri,ti,cv2.INTER_LINEAR)
w=cv2.GaussianBlur(gap.astype(np.float32),(0,0),1.2)[...,None]
w=np.clip(w,0,1)*((th>=t0)&(th<=t1))[...,None]
out=base*(1-w)+back*w
out8=(np.clip(out,0,1)*255).astype(np.uint8)
Image.fromarray(out8).save('fundo_limpo2_1x.png')
Image.fromarray(out8[0:330]).resize((1080,660),Image.LANCZOS).save('fundo_view2.png')

for (px,py) in [(75,165),(130,290),(110,300)]:
    print((px,py),'r=%.1f'%r[py,px],'th=%.0f'%np.degrees(th[py,px]),'tfar=%.1f'%tf[py,px],'rho=%.2f'%rho[py,px],'inmoon',inmoon[py,px],'tm',tm[py,px],'gap',gap[py,px],'w=%.2f'%w[py,px,0])
vis=np.hstack([U,np.repeat(gapU[...,None].astype(np.float32),3,2),Ufill]); vis=np.clip(vis,0,1)
Image.fromarray((vis*255).astype(np.uint8)).transpose(Image.ROTATE_90).save('U_dbg.png'); print(U.shape)
