"""Redesenha as curvas da logo no padrão 'vetor limpo' (borda lisa, poucos pontos, degradê contínuo)."""
import sys, cv2, numpy as np
from PIL import Image
from scipy import ndimage as ndi
sys.path.insert(0,'.')
import vec
Image.MAX_IMAGE_PIXELS=None
SRC=sys.argv[1]; OUT=sys.argv[2]
im=np.asarray(Image.open(SRC)).astype(np.float32); H,W=im.shape[:2]; rgb=im[...,:3]; al=im[...,3]/255
n,lab,st,_=cv2.connectedComponentsWithStats((al>0.5).astype(np.uint8),8)
S=2
def redraw(i, split_lum=None, sig_face=14, sig_under=10, col_sigma=22, halo=25):
    global im
    x0,y0,x1,y1=max(st[i,0]-30,0),max(st[i,1]-30,0),min(st[i,0]+st[i,2]+30,W),min(st[i,1]+st[i,3]+30,H)
    me=(lab[y0:y1,x0:x1]==i); sub_rgb=rgb[y0:y1,x0:x1]; h,w=me.shape
    lum=cv2.GaussianBlur(sub_rgb@np.array([.299,.587,.114],np.float32),(0,0),3)
    arc=cv2.dilate(me.astype(np.uint8),np.ones((5,5),np.uint8))>0
    if split_lum:
        face0=arc&(lum>split_lum); under0=arc&~face0
        thick=cv2.morphologyEx(under0.astype(np.uint8),cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(21,21)))>0
        thin=under0&~thick; face0=face0|thin; under0=thick
        under0=(cv2.morphologyEx(under0.astype(np.uint8),cv2.MORPH_CLOSE,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(61,61)))>0)&arc   # liga as falhas do chanfro
        face0=face0&~under0       # riscos escuros finos viram parte da face (faixa única, sem listras)
    else: face0=arc; under0=np.zeros_like(arc)
    def clean(m,sig,min_island=1500,min_hole=800):
        mm=cv2.resize(cv2.GaussianBlur(m.astype(np.float32),(0,0),1.5),(w*S,h*S),interpolation=cv2.INTER_CUBIC)>0.5
        n_,l_,s_,_=cv2.connectedComponentsWithStats(mm.astype(np.uint8),8)
        for k in range(1,n_):
            if s_[k,4]<min_island*S*S: mm[l_==k]=False
        inv=(~mm).astype(np.uint8); n_,l_,s_,_=cv2.connectedComponentsWithStats(inv,4)
        for k in range(1,n_):
            if s_[k,4]<min_hole*S*S and not(s_[k,0]==0 or s_[k,1]==0): mm[l_==k]=True
        return vec.smooth_mask(mm,1,sig,corner_deg=70)
    face=clean(face0,sig_face); under=clean(under0,sig_under) if under0.any() else np.zeros_like(face)
    under=under&~face
    if under.any() and split_lum:                       # faixa de sombra ACIMA da face (metade esquerda do arco) não faz parte do desenho
        hh=face.shape[0]; cols=face.any(0); tops=np.where(cols,face.argmax(0),hh)
        yy=np.arange(hh)[:,None]; above=(yy<tops[None,:]-2)&(np.arange(face.shape[1])[None,:]<face.shape[1]*0.55)
        under&=~above
    if under.any(): under=(cv2.dilate(under.astype(np.uint8),np.ones((3,3),np.uint8))>0)&~face
    def color_field(mk,sigma):
        m=mk.astype(np.float32); num=np.stack([cv2.GaussianBlur(sub_rgb[...,c]*m,(0,0),sigma) for c in range(3)],-1); den=cv2.GaussianBlur(m,(0,0),sigma)[...,None]
        f=num/np.maximum(den,1e-3); far=den[...,0]<0.02
        if far.any(): _,(iy,ix)=ndi.distance_transform_edt(far,return_indices=True); f=f[iy,ix]
        return f
    cf_face=color_field((face0&(lum>split_lum)) if split_lum else face0,col_sigma); 
    a_f=cv2.resize(face.astype(np.float32),(w,h),interpolation=cv2.INTER_AREA)
    a_u=cv2.resize(under.astype(np.float32),(w,h),interpolation=cv2.INTER_AREA); cf_u=color_field(under0,26) if under.any() else cf_face
    reg=im[y0:y1,x0:x1].copy()
    # remove o antigo + toda a franja/sombra ao redor dele (sem tocar nos outros elementos)
    others=(al[y0:y1,x0:x1]>0.5)&~me; others=cv2.dilate(others.astype(np.uint8),np.ones((5,5),np.uint8))>0
    newm=cv2.dilate(((a_f+a_u)>0.05).astype(np.uint8),np.ones((5,5),np.uint8))>0
    old=cv2.dilate(me.astype(np.uint8),cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(2*halo+1,2*halo+1)))>0
    reg[old&~others&~newm,3]=0
    na=a_f+a_u*(1-a_f); C=(cf_face*a_f[...,None]+cf_u*(a_u*(1-a_f))[...,None])/np.maximum(na,1e-3)[...,None]
    oa=reg[...,3]/255; new_a=na+oa*(1-na)
    reg[...,:3]=np.where((na>0)[...,None],(C*na[...,None]+reg[...,:3]*(oa*(1-na))[...,None])/np.maximum(new_a,1e-3)[...,None],reg[...,:3])
    reg[...,3]=new_a*255; im[y0:y1,x0:x1]=reg
    print('curva',i,'bbox',x0,y0,x1,y1)
# arco (grande, topo) e curva branca (base)
arc_i=[k for k in range(1,n) if st[k,3]>1000 and st[k,2]>2500 and st[k,1]<50][0]
redraw(arc_i,split_lum=112)
sw=[k for k in range(1,n) if st[k,2]>1500 and st[k,1]>1700]
for k in sw: redraw(k,split_lum=None,sig_face=12,col_sigma=18,halo=12)
Image.fromarray(np.clip(im,0,255).astype(np.uint8),'RGBA').save(OUT,dpi=(300,300)); print('ok',OUT)
