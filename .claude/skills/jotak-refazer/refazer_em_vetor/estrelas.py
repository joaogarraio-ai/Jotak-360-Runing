import cv2, numpy as np
from PIL import Image
a=np.asarray(Image.open('fundo_limpo2_1x.png').convert('RGB')).astype(np.float32)/255; H,W=a.shape[:2]
d=np.load('cam_masks.npz'); txt=(d['sel']|d['birds'])
tm=cv2.dilate(txt.astype(np.uint8),cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(15,15)))>0
lua=np.load('lua_circ.npz')['moon']; moonz=cv2.dilate(lua.astype(np.uint8),np.ones((25,25),np.uint8))>0
fillz=tm&~moonz
lum=a@np.array([.299,.587,.114],np.float32)
dog=lum-cv2.GaussianBlur(lum,(0,0),3)
ring=cv2.dilate(fillz.astype(np.uint8),np.ones((61,61),np.uint8))>0; ring&=~tm&~moonz; ring[330:]=False
peaks=(dog>0.07)&(dog==cv2.dilate(dog,np.ones((5,5),np.float32)))&ring
dens=peaks.sum()/ring.sum(); amp=dog[peaks]
print('densidade de estrelas/px²: %.5f'%dens,'brilho médio %.2f'%amp.mean(), 'n alvo',int(dens*fillz.sum()))
rng=np.random.default_rng(11); ys,xs=np.nonzero(fillz); n=int(dens*fillz.sum())
canvas=np.zeros((H,W),np.float32)
for i in rng.choice(len(ys),n,replace=False):
    canvas[ys[i],xs[i]]+=rng.choice(amp)*rng.uniform(0.6,1.3)
st=cv2.GaussianBlur(canvas,(0,0),0.9)*3.2
# estrelas azuladas-brancas
add=np.stack([st*0.85,st*0.95,st*1.0],-1)
soft=cv2.GaussianBlur(fillz.astype(np.float32),(0,0),1.5)[...,None]
out=np.clip(a+add*soft,0,1)
Image.fromarray((out*255).astype(np.uint8)).save('fundo_limpo3_1x.png')
Image.fromarray((out*255).astype(np.uint8)[0:330]).resize((1080,660),Image.LANCZOS).save('fundo_view4.png')
