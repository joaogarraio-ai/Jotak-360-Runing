import cv2, numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS=None
SR=np.asarray(Image.open('trb/board_sr_x4.png').convert('RGB')).astype(np.float32); F=SR.shape[1]/2973.0
X0,Y0,X1,Y1=215,15,1728,562
c=SR[int(Y0*F):int(Y1*F), int(X0*F):int(X1*F)]; h,w=c.shape[:2]; print(c.shape)
N=np.median(SR[int(160*F):int(420*F), int(40*F):int(200*F)].reshape(-1,3),0); print('azul',N)
u=N/np.linalg.norm(N); proj=np.clip((c@u)[...,None]/np.linalg.norm(N),0,1.15)*N       # reta 0..N (azul e suas sombras)
d=np.linalg.norm(c-proj,axis=2)
lo,hi=28,85; a=np.clip((d-lo)/(hi-lo),0,1)
# holofotes (só da ilustração): caixas exatas longe do logo + faixa de halo rente ao topo das letras T R B
X=lambda x:int((x-X0)*F); Y=lambda y:int((y-Y0)*F)
a[:, X(1695):X(1728)]=0                                  # fio da divisória
mx=c.max(2); mn=c.min(2); sat=(mx-mn)/np.maximum(mx,1)
lum=c@np.array([.299,.587,.114],np.float32)
def keep_near(solid,x0,x1,y0,y1,k=35):
    solid=solid.astype(np.uint8); n_,lab_,st_,_=cv2.connectedComponentsWithStats(solid,8)
    for i in range(1,n_):
        if st_[i,4]<1500: solid[lab_==i]=0
    near=cv2.GaussianBlur(cv2.dilate(solid,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(k,k))).astype(np.float32),(0,0),2.5)
    z=np.zeros((h,w),bool); z[max(Y(y0),0):Y(y1),max(X(x0),0):X(x1)]=True
    return np.where(z,near,1.0)
# holofote esquerdo (neblina bege/laranja, desbotada): fica só o que encosta no dourado sólido do logo
a=a*keep_near((sat>0.7)&(a>0.9),330,690,0,146)
a[:Y(62),X(380):X(700)]=0                                   # núcleo do holofote esquerdo (o arco só começa mais abaixo)
# holofote direito (acima do prédio): fica só o que encosta no branco sólido do prédio
a=a*keep_near((lum>200)&(sat<0.25)&(a>0.9),1330,1710,0,140,k=15)
# só o que está ligado ao logo (tira poeira)
bw=(a>0.2).astype(np.uint8); n,lab,st,_=cv2.connectedComponentsWithStats(bw,8)
for i in range(1,n):
    if st[i,4]<2500: a[lab==i]=0
a=cv2.GaussianBlur(a,(0,0),0.8)
gz=np.zeros((h,w),bool); gz[:Y(150),X(1330):X(1710)]=True
gray=(c@np.array([.299,.587,.114],np.float32))[...,None]*np.ones(3,np.float32)
c=np.where(gz[...,None], 0.2*c+0.8*gray, c)                  # branco do prédio sem tom laranja
lm=c@np.array([.299,.587,.114],np.float32)
a[470:660,5100:5420]*=np.clip((lm[470:660,5100:5420]-170)/30,0,1)   # neblina escura ao lado do prédio sai; o branco do prédio fica
# decontaminação do azul nas bordas: F=(p-(1-a)N)/a
aa=np.maximum(a,1e-3)[...,None]; Fg=np.clip((c-(1-a)[...,None]*N)/aa,0,255); Fg=np.where(a[...,None]>0.02,Fg,0)
rgba=np.dstack([Fg,a*255]).astype(np.uint8)
ys,xs=np.nonzero(a>0.03); rgba=rgba[ys.min():ys.max()+1,xs.min():xs.max()+1]
im=Image.fromarray(rgba,'RGBA'); im.save('TRB_logo_sem_fundo.png',dpi=(300,300)); print(im.size)
# prévias: fundo branco e xadrez
for name,bgc in (('prev_branco',(255,255,255)),('prev_escuro',(40,40,40))):
    b=Image.new('RGB',im.size,bgc); b.paste(im,(0,0),im); b.resize((1600,int(1600*im.height/im.width)),Image.LANCZOS).save(f'trb/{name}.png')
