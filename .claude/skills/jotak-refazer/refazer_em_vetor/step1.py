import cv2, numpy as np
from PIL import Image
img = np.asarray(Image.open('orig.webp').convert('RGB')).astype(np.float32)
H, W = img.shape[:2]
bg = cv2.medianBlur(img.astype(np.uint8), 45).astype(np.float32)
# cores de tinta
def core(box, cond):
    x0,y0,x1,y1 = box; p = img[y0:y1,x0:x1].reshape(-1,3); b = bg[y0:y1,x0:x1].reshape(-1,3)
    d = np.abs(p-b).sum(1); sel = p[cond(p) & (d > np.percentile(d,92))]
    return np.median(sel,0)
BLUE = core((752,648,942,678), lambda p: p[:,2]>p[:,0])
GOLD = core((730,340,1100,490), lambda p: p[:,0]>p[:,2]+40)
print('BLUE',BLUE,'GOLD',GOLD)
REG = [(790,30,1290,232),(640,265,1140,530),(1160,270,1500,530),(695,565,1090,735),(1200,575,1455,722)]
def alpha(C):
    v = C-bg; n = (v*v).sum(-1)+1e-6
    return np.clip(((img-bg)*v).sum(-1)/n,0,1)
aB, aG = alpha(BLUE), alpha(GOLD)
reg = np.zeros((H,W),bool)
for x0,y0,x1,y1 in REG: reg[y0:y1,x0:x1]=True
# classe: azul ou dourado (o de maior cobertura); cobertura mínima 0.35
cls = np.where(aB>=aG,0,1); cov = np.maximum(aB,aG)
ink = (cov>0.30)&reg
np.savez('masks.npz', aB=aB*(reg&(cls==0)), aG=aG*(reg&(cls==1)), reg=reg, BLUE=BLUE, GOLD=GOLD)
m = cv2.dilate(ink.astype(np.uint8), np.ones((7,7),np.uint8)).astype(np.float32)
keep = 1-m
num = cv2.GaussianBlur(img*keep[...,None],(0,0),10); den = cv2.GaussianBlur(keep,(0,0),10)[...,None]+1e-4
fill = num/den
soft = cv2.GaussianBlur(m,(0,0),1.5)[...,None]
clean = np.clip(img*(1-soft)+fill*soft,0,255).astype(np.uint8)
Image.fromarray(clean).save('bg_clean.png')
Image.fromarray(clean).crop((630,20,1600,740)).save('bg_clean_view.png')
