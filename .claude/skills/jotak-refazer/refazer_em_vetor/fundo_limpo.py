import cv2, numpy as np
from PIL import Image
from skimage.restoration import inpaint_biharmonic
im=np.asarray(Image.open('camisa.jpg').convert('RGB'))
AX0,AY0,AX1,AY1=255,410,795,1130
art=im[AY0:AY1,AX0:AX1].astype(np.float32)/255; H,W=art.shape[:2]
d=np.load('cam_masks.npz'); m=(d['sel']|d['birds']).astype(np.uint8)
lum=(art*255)@np.array([.299,.587,.114],np.float32)
# máscara: texto + contorno escuro (≈4 px) ; pássaros com margem menor
m=cv2.dilate(m,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(11,11)))
ys,xs=np.nonzero(m); y0,y1,x0,x1=max(ys.min()-20,0),ys.max()+20,max(xs.min()-20,0),min(xs.max()+20,W)
sub=art[y0:y1,x0:x1]; ms=m[y0:y1,x0:x1]>0
# preenche suave (biharmônico, respeita a forma da lua) e reintroduz granulação do entorno
fill=inpaint_biharmonic(sub,ms,channel_axis=-1)
ring=cv2.dilate(ms.astype(np.uint8),np.ones((15,15),np.uint8))>0; ring&=~ms
hp=sub-cv2.GaussianBlur(sub,(0,0),1.6); sigma=hp[ring].std(0)
rng=np.random.default_rng(5); noise=cv2.GaussianBlur(rng.normal(0,1,sub.shape).astype(np.float32),(0,0),0.8)
noise*=0.45*sigma/noise.reshape(-1,3).std(0)
fill=np.clip(fill+noise,0,1)
soft=cv2.GaussianBlur(ms.astype(np.float32),(0,0),1.0)[...,None]
out=art.copy(); out[y0:y1,x0:x1]=sub*(1-soft)+fill*soft
out=(out*255).astype(np.uint8)
Image.fromarray(out).save('fundo_limpo_1x.png')
Image.fromarray(out[0:330]).resize((1080,660),Image.LANCZOS).save('fundo_view.png')
