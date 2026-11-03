"""Real-ESRGAN x4plus (RRDBNet) em CPU, com tiles. Uso: sr_run.py entrada.png saida.png pesos.pth"""
import sys, time, numpy as np, torch, torch.nn as nn, torch.nn.functional as Fn
from PIL import Image
torch.set_num_threads(4)
class RDB(nn.Module):
    def __init__(s,nf=64,gc=32):
        super().__init__()
        s.conv1=nn.Conv2d(nf,gc,3,1,1); s.conv2=nn.Conv2d(nf+gc,gc,3,1,1); s.conv3=nn.Conv2d(nf+2*gc,gc,3,1,1)
        s.conv4=nn.Conv2d(nf+3*gc,gc,3,1,1); s.conv5=nn.Conv2d(nf+4*gc,nf,3,1,1); s.lrelu=nn.LeakyReLU(0.2,True)
    def forward(s,x):
        x1=s.lrelu(s.conv1(x)); x2=s.lrelu(s.conv2(torch.cat((x,x1),1))); x3=s.lrelu(s.conv3(torch.cat((x,x1,x2),1)))
        x4=s.lrelu(s.conv4(torch.cat((x,x1,x2,x3),1))); x5=s.conv5(torch.cat((x,x1,x2,x3,x4),1)); return x5*0.2+x
class RRDB(nn.Module):
    def __init__(s,nf,gc): super().__init__(); s.rdb1=RDB(nf,gc); s.rdb2=RDB(nf,gc); s.rdb3=RDB(nf,gc)
    def forward(s,x): return s.rdb3(s.rdb2(s.rdb1(x)))*0.2+x
class RRDBNet(nn.Module):
    def __init__(s,nf=64,nb=23,gc=32):
        super().__init__(); s.conv_first=nn.Conv2d(3,nf,3,1,1); s.body=nn.Sequential(*[RRDB(nf,gc) for _ in range(nb)])
        s.conv_body=nn.Conv2d(nf,nf,3,1,1); s.conv_up1=nn.Conv2d(nf,nf,3,1,1); s.conv_up2=nn.Conv2d(nf,nf,3,1,1)
        s.conv_hr=nn.Conv2d(nf,nf,3,1,1); s.conv_last=nn.Conv2d(nf,3,3,1,1); s.lrelu=nn.LeakyReLU(0.2,True)
    def forward(s,x):
        f=s.conv_first(x); f=f+s.conv_body(s.body(f))
        f=s.lrelu(s.conv_up1(Fn.interpolate(f,scale_factor=2,mode='nearest'))); f=s.lrelu(s.conv_up2(Fn.interpolate(f,scale_factor=2,mode='nearest')))
        return s.conv_last(s.lrelu(s.conv_hr(f)))
inp,outp,w=sys.argv[1:4]
net=RRDBNet(); sd=torch.load(w,map_location='cpu'); sd=sd.get('params_ema',sd.get('params',sd)); net.load_state_dict(sd,strict=True); net.eval()
img=np.asarray(Image.open(inp).convert('RGB')).astype(np.float32)/255; H,W=img.shape[:2]
T,P=128,16; S=4; out=np.zeros((H*S,W*S,3),np.float32); wt=np.zeros((H*S,W*S,1),np.float32)
ys=list(range(0,H,T)); xs=list(range(0,W,T)); t0=time.time(); n=0
for y in ys:
    for x in xs:
        y0,y1,x0,x1=max(y-P,0),min(y+T+P,H),max(x-P,0),min(x+T+P,W)
        t=torch.from_numpy(img[y0:y1,x0:x1]).permute(2,0,1)[None]
        with torch.no_grad(): o=net(t)[0].permute(1,2,0).numpy()
        # recorta a margem de contexto, mantém só o miolo do tile
        cy0,cx0=(y-y0)*S,(x-x0)*S; ch,cw=min(T,H-y)*S,min(T,W-x)*S
        out[y*S:y*S+ch,x*S:x*S+cw]=o[cy0:cy0+ch,cx0:cx0+cw]; n+=1
        print('tile',n,'/',len(ys)*len(xs),'%.0fs'%(time.time()-t0),flush=True)
Image.fromarray((np.clip(out,0,1)*255).round().astype(np.uint8)).save(outp); print('SR ok',out.shape)
