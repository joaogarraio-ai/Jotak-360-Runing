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
# núcleo do holofote esquerdo: só o que está ACIMA da borda do arco (acompanha a curva, sem corte reto)
sat_=(c.max(2)-c.min(2))/np.maximum(c.max(2),1)
zone_h=np.zeros((h,w),bool); zone_h[:Y(70),X(380):X(700)]=True
arc_solid=((sat_>0.7)&(a>0.9)).astype(np.uint8); arc_solid=cv2.morphologyEx(arc_solid,cv2.MORPH_OPEN,np.ones((9,9),np.uint8))
nn,ll,ss,_=cv2.connectedComponentsWithStats(arc_solid,8)
big_=np.zeros((h,w),bool)
for i in range(1,nn):
    if ss[i,4]>30000: big_|=ll==i                                  # o arco + letras (massa grande e contínua)
protect=cv2.dilate(big_.astype(np.uint8),cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(25,25)))>0
a=np.where(zone_h&~protect,0,a)
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
# --- limpeza de borda (sem halo/sombra grudada): 1) aperta o alpha, 2) cor das bordas vem do miolo sólido mais próximo
from scipy import ndimage as ndi
warm=np.clip((c[...,0]-c[...,2]-4)/20,0,1)                    # marrom/laranja/dourado: a parede e a sombra dela são azuis (B>R)
a=np.where(a>0.01,np.maximum(a,warm),a)                        # o marrom escuro da letra não pode virar 'sombra'
a=np.clip((a-0.35)/0.5,0,1)                                   # tira a franja fraca (sombra/ringing); mantém serrilhado suave
a=cv2.GaussianBlur(a,(0,0),0.9)
# --- elementos BRANCOS (CONSTRUÇÕES, curva branca, prédio): descasca o fio escuro/fosco da sombra do mockup (não é saturado como o dourado)
lumc=c@np.array([.299,.587,.114],np.float32); satc=(c.max(2)-c.min(2))/np.maximum(c.max(2),1)
whiteZ=np.zeros((h,w),bool); whiteZ[Y(430):Y(562),X(430):X(1728)]=True; whiteZ[Y(15):Y(430),X(1200):X(1728)]=True
for _ in range(3):
    dist_=ndi.distance_transform_edt(a>0.5)
    rim=whiteZ&(a>0.0)&(dist_<=9)&(lumc<150)&(satc<0.78)
    a=np.where(rim,0,a)
a=cv2.GaussianBlur(a,(0,0),0.8)
# fibra solta no canto superior esquerdo do T
zT=np.zeros((h,w),bool); zT[Y(140):Y(235),X(255):X(335)]=True
opened=cv2.morphologyEx((a>0.5).astype(np.uint8),cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(9,9)))
keepT=cv2.dilate(opened,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(7,7)))>0
a=np.where(zT&~keepT,0,a)
solid=a>0.97
_,(iy,ix)=ndi.distance_transform_edt(~solid,return_indices=True)
near=c[iy,ix]                                                  # cor do pixel sólido mais próximo
w_=np.clip((a-0.55)/0.4,0,1)[...,None]                         # quanto confiar na cor original
Fg=np.clip(c*w_+near*(1-w_),0,255)
Fg=np.where(a[...,None]>0.01,Fg,0)
# fio escuro de 1-3 px na borda externa: pega a cor do miolo (>=5 px para dentro) quando o miolo é bem mais claro
dd=ndi.distance_transform_edt(a>0.5)
_,(jy,jx)=ndi.distance_transform_edt(dd<5,return_indices=True)
inner=Fg[jy,jx]; lum_in=inner@np.array([.299,.587,.114],np.float32); lum_me=Fg@np.array([.299,.587,.114],np.float32)
noB=np.ones((h,w),bool); noB[:,X(800):X(1130)]=False
a=np.where(noB,np.clip((a-0.45)/0.45,0,1),a)                   # +1 px de aperto fora do B: some o fio escuro pontilhado          # o B prateado tem chanfro escuro de verdade
fix=(dd<=3.5)&(a>0.02)&noB&((lum_in-lum_me)>35)
Fg=np.where(fix[...,None],inner,Fg)
rgba=np.dstack([Fg,a*255]).astype(np.uint8)
ys,xs=np.nonzero(a>0.03); rgba=rgba[ys.min():ys.max()+1,xs.min():xs.max()+1]
# fibra solta no canto do T (coordenadas da imagem final)
al=rgba[...,3].astype(np.float32)/255
op=cv2.morphologyEx((al>0.5).astype(np.uint8),cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(11,11)))
kp=cv2.dilate(op,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(3,3)))>0
zz=np.zeros(al.shape,bool); zz[480:600,230:320]=True
rgba[...,3]=np.where(zz&~kp,0,rgba[...,3])
im=Image.fromarray(rgba,"RGBA"); im.save('TRB_logo_sem_fundo.png',dpi=(300,300)); print(im.size)
# prévias: fundo branco e xadrez
for name,bgc in (('prev_branco',(255,255,255)),('prev_escuro',(40,40,40))):
    b=Image.new('RGB',im.size,bgc); b.paste(im,(0,0),im); b.resize((1600,int(1600*im.height/im.width)),Image.LANCZOS).save(f'trb/{name}.png')
