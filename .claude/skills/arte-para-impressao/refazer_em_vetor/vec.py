"""Ferramentas de vetorização limpa: formas ajustadas (círculo/retângulo), simetria, poucos nós."""
import cv2, numpy as np, potrace

def upscale_alpha(a, F, blur):
    big = cv2.resize(a.astype(np.float32), (a.shape[1]*F, a.shape[0]*F), interpolation=cv2.INTER_CUBIC)
    return cv2.GaussianBlur(big, (0, 0), F*blur) if blur else big

def symmetrize(big, F, search=3):
    """Média da imagem com seu espelho horizontal (eixo achado por correlação)."""
    fl = big[:, ::-1]; best = (-1, 0)
    for s in range(-search*F, search*F+1):
        sc = float((big*np.roll(fl, s, axis=1)).sum())
        if sc > best[0]: best = (sc, s)
    return (big + np.roll(fl, best[1], axis=1))/2

def trace(mask_big, alphamax=1.15, opttol=0.9, turd=40):
    """mask_big: bool (True=tinta). Devolve curvas potrace."""
    return potrace.Bitmap(~mask_big).trace(turdsize=turd, alphamax=alphamax, opticurve=True, opttolerance=opttol)

def curves_to_ops(curves, F, ox, oy):
    """-> lista de subpaths [('M',x,y),('L',..),('C',x1,y1,x2,y2,x,y)] em coords da arte original."""
    f = lambda p: (ox + p.x/F, oy + p.y/F)
    out = []
    for c in curves:
        ops = [('M',)+f(c.start_point)]
        for s in c.segments:
            if s.is_corner: ops += [('L',)+f(s.c), ('L',)+f(s.end_point)]
            else: ops.append(('C',)+f(s.c1)+f(s.c2)+f(s.end_point))
        out.append(ops)
    return out

def count_nodes(subpaths): return sum(len(p) for p in subpaths)

# ---- formas geométricas -> subpaths
K = 0.5522847498
def circle_ops(cx, cy, r): return ellipse_ops(cx, cy, r, r, 0)
def ellipse_ops(cx, cy, a, b, ang_deg):
    t = np.deg2rad(ang_deg); c, s = np.cos(t), np.sin(t)
    R = lambda x, y: (cx + x*c - y*s, cy + x*s + y*c)
    pts = [(a,0),(a,K*b),(K*a,b),(0,b),(-K*a,b),(-a,K*b),(-a,0),(-a,-K*b),(-K*a,-b),(0,-b),(K*a,-b),(a,-K*b),(a,0)]
    ops = [('M',)+R(*pts[0])]
    for i in range(1, 13, 3): ops.append(('C',)+R(*pts[i])+R(*pts[i+1])+R(*pts[i+2]))
    return ops
def rrect_ops(x0, y0, x1, y1, r):
    r = min(r, (x1-x0)/2, (y1-y0)/2); k = r*(1-K)
    return [('M',x0+r,y0),('L',x1-r,y0),('C',x1-k,y0,x1,y0+k,x1,y0+r),('L',x1,y1-r),('C',x1,y1-k,x1-k,y1,x1-r,y1),
            ('L',x0+r,y1),('C',x0+k,y1,x0,y1-k,x0,y1-r),('L',x0,y0+r),('C',x0,y0+k,x0+k,y0,x0+r,y0)]

def draw_ops(c, subpaths, fill_rgb, even_odd=True):
    p = c.beginPath()
    for ops in subpaths:
        for op in ops:
            if op[0]=='M': p.moveTo(*op[1:])
            elif op[0]=='L': p.lineTo(*op[1:])
            else: p.curveTo(*op[1:])
        p.close()
    c.setFillColorRGB(*[v/255 for v in fill_rgb]); c.drawPath(p, stroke=0, fill=1, fillMode=0 if even_odd else 1)

def snap_instagram(a, box, F=12, blur=0.4):
    """Ícone Instagram: disco + anel quadrado arredondado + anel circular + ponto, tudo geométrico exato."""
    x0,y0,x1,y1 = box
    big = upscale_alpha(a[y0:y1,x0:x1], F, blur) > 0.5
    cs,h = cv2.findContours(big.astype(np.uint8), cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE); h=h[0]
    def depth(i):
        d=0
        while h[i][3]!=-1: i=h[i][3]; d+=1
        return d
    shapes=[]
    for i,c in enumerate(cs):
        if len(c)<20: continue
        pts=c[:,0,:].astype(np.float32)
        (cx,cy),r = cv2.minEnclosingCircle(pts)
        res_circle = np.abs(np.hypot(pts[:,0]-cx,pts[:,1]-cy)-r).mean()/r
        rect = cv2.minAreaRect(pts); (rx,ry),(rw,rh),ang = rect
        area = cv2.contourArea(c)
        shapes.append(dict(i=i,d=depth(i),cx=cx,cy=cy,r=r,res_c=res_circle,rect=rect,area=area,bbox=cv2.boundingRect(c)))
    return shapes, big

def build_instagram(a, box, F=12, blur=0.4):
    """Mede o ícone e devolve subpaths geométricos exatos (disco - anel quadrado - anel circular - ponto)."""
    x0,y0,x1,y1 = box; big = upscale_alpha(a[y0:y1,x0:x1], F, blur) > 0.5
    cs,h = cv2.findContours(big.astype(np.uint8), cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE); h=h[0]
    dep = lambda i: (lambda f: f(f,i))(lambda f,i: 0 if h[i][3]==-1 else 1+f(f,h[i][3]))
    L = {}
    for i,c in enumerate(cs):
        if len(c) > 40: L.setdefault(dep(i), []).append(c)
    top = lambda lst: max(lst, key=cv2.contourArea)
    d0, d1, d2 = top(L[0]), top(L[1]), top(L[2])
    bb = lambda c: cv2.boundingRect(c)
    X,Y,Wd,Ht = bb(d0); dcx,dcy,dr = X+Wd/2, Y+Ht/2, (Wd+Ht)/4
    def rr(c):
        x,y,w,h_ = bb(c); A = cv2.contourArea(c); r = np.sqrt(max(w*h_-A,0)/(4-np.pi)); return x,y,x+w,y+h_,r
    o = rr(d1); i_ = rr(d2)
    sc_x, sc_y = (o[0]+o[2]+i_[0]+i_[2])/4, (o[1]+o[3]+i_[1]+i_[3])/4
    so = (o[2]-o[0]+o[3]-o[1])/4; si = (i_[2]-i_[0]+i_[3]-i_[1])/4        # meios-lados
    ro_sq, ri_sq = o[4], i_[4]
    white = ~big; yy,xx = np.mgrid[0:big.shape[0],0:big.shape[1]]
    rad = np.hypot(xx-sc_x, yy-sc_y); inner = (np.abs(xx-sc_x) < si-2) & (np.abs(yy-sc_y) < si-2)
    # perfil radial (mediana angular) do anel circular
    prof=[]; rs=np.arange(5, int(si))
    for r in rs:
        sel = inner & (rad>=r) & (rad<r+1)
        prof.append(np.median(white[sel]) if sel.any() else 0)
    prof=np.array(prof); wr = np.where(prof>0.5)[0]
    r_in, r_out = rs[wr[0]], rs[wr[-1]]+1
    ring = inner & (rad>=r_in) & (rad<=r_out)
    dot = (inner & white & (rad>r_out+4)).astype(np.uint8)
    n_,lab_,st_,cen_ = cv2.connectedComponentsWithStats(dot,8); k_ = 1+int(np.argmax(st_[1:,4]))
    dxc,dyc = cen_[k_]; drr = np.sqrt(st_[k_,4]/np.pi)
    off = lambda ops: ops
    sp = [circle_ops(dcx,dcy,dr),
          rrect_ops(sc_x-so, sc_y-so, sc_x+so, sc_y+so, ro_sq),
          rrect_ops(sc_x-si, sc_y-si, sc_x+si, sc_y+si, ri_sq),
          circle_ops(sc_x,sc_y,r_out), circle_ops(sc_x,sc_y,r_in), circle_ops(dxc,dyc,drr)]
    # converte p/ coords da arte
    def tf(ops): return [(op[0],)+tuple(x0+v/F if k%2==0 else y0+v/F for k,v in enumerate(op[1:])) for op in ops]
    return [tf(s) for s in sp]


def build_traced(a, box, F=12, blur=0.55, sym=False, alphamax=1.2, opttol=1.0, turd=60, thr=0.5):
    """Vetorização suave (poucos nós). sym=True espelha para eliminar ruído/assimetria."""
    x0,y0,x1,y1 = box; big = upscale_alpha(a[y0:y1,x0:x1], F, blur)
    if sym: big = symmetrize(big, F)
    return curves_to_ops(trace(big>thr, alphamax, opttol, turd), F, x0, y0)

def arc_ops(cx, cy, r, a0, a1, move=True):
    """Arco de círculo (ângulos em rad, y para baixo) em Béziers de ≤90°."""
    n = max(1, int(np.ceil(abs(a1-a0)/(np.pi/2)-1e-9))); da = (a1-a0)/n; k = 4/3*np.tan(da/4)
    ops = []; a = a0
    p = lambda t: (cx+r*np.cos(t), cy+r*np.sin(t))
    if move: ops.append(('M',)+p(a))
    for _ in range(n):
        b = a+da; (x0_,y0_),(x1_,y1_) = p(a),p(b)
        ops.append(('C', x0_-k*r*np.sin(a), y0_+k*r*np.cos(a), x1_+k*r*np.sin(b), y1_-k*r*np.cos(b), x1_, y1_)); a = b
    return ops

def build_pin(a, box, F=12, blur=0.4):
    """Pino de localização exato: círculo + duas tangentes até a ponta, furo circular."""
    x0,y0,x1,y1 = box; big = symmetrize(upscale_alpha(a[y0:y1,x0:x1], F, blur), F) > 0.5
    cs,h = cv2.findContours(big.astype(np.uint8), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE); h=h[0]
    outer = max([c for i,c in enumerate(cs) if h[i][3]==-1], key=cv2.contourArea)
    hole = max([c for i,c in enumerate(cs) if h[i][3]!=-1], key=cv2.contourArea)
    X,Y,W_,H_ = cv2.boundingRect(outer); cx = X+W_/2; r = W_/2; cy = Y+r; ax, ay = cx, Y+H_
    d = ay-cy; th = np.arccos(r/d)
    # ponto de tangência (direita): ângulo medido a partir do eixo +x, y p/ baixo
    a_r = np.pi/2 - th          # tangente direita
    a_l = np.pi/2 + th          # tangente esquerda
    ops = arc_ops(cx, cy, r, a_l, a_r + 2*np.pi) # esquerda -> topo -> direita (sentido horário na tela)
    ops.append(('L', ax, ay)); 
    M = cv2.moments(hole); hx, hy = M['m10']/M['m00'], M['m01']/M['m00']; hr = np.sqrt(cv2.contourArea(hole)/np.pi)
    tf = lambda ops_: [(o[0],)+tuple(x0+v/F if k%2==0 else y0+v/F for k,v in enumerate(o[1:])) for o in ops_]
    return [tf(ops), tf(circle_ops(hx,hy,hr))]

def fit_circle(pts):
    x, y = pts[:,0].astype(float), pts[:,1].astype(float)
    A = np.c_[2*x, 2*y, np.ones(len(x))]; b = x*x+y*y
    cx, cy, c = np.linalg.lstsq(A, b, rcond=None)[0]; return cx, cy, np.sqrt(c+cx*cx+cy*cy)

def teardrop_ops(cx, cy, r, tx, ty, concave=0.0):
    """Círculo + ponta em tangente. concave>0 curva os lados da ponta para dentro (balão de fala)."""
    d = np.hypot(tx-cx, ty-cy); phi = np.arctan2(ty-cy, tx-cx); th = np.arccos(min(r/d, 0.999))
    ops = arc_ops(cx, cy, r, phi+th, phi-th+2*np.pi)
    T2 = np.array([cx+r*np.cos(phi-th), cy+r*np.sin(phi-th)]); T1 = np.array([cx+r*np.cos(phi+th), cy+r*np.sin(phi+th)])
    tip = np.array([tx, ty]); C = np.array([cx, cy])
    def side(P, Q):   # P (tangência) -> Q (ponta), curvando em direção ao centro perto da ponta
        v = Q-P; n = np.array([-v[1], v[0]]); n /= np.linalg.norm(n)
        if np.dot(n, C-(P+Q)/2) < 0: n = -n
        bend = concave*np.linalg.norm(v)
        return ('C',)+tuple(P+v/3)+tuple(P+2*v/3+n*bend)+tuple(Q)
    ops.append(side(T2, tip))
    ops.append(side(T1, tip)[:0] or ('C',)+tuple(tip+(T1-tip)/3 + 0)+tuple(0*tip))   # placeholder substituído abaixo
    # lado de volta: tip -> T1 (espelho do lado de ida)
    ops.pop()
    v = T1-tip; n = np.array([-v[1], v[0]]); n /= np.linalg.norm(n)
    if np.dot(n, C-(tip+T1)/2) < 0: n = -n
    bend = concave*np.linalg.norm(v)
    ops.append(('C',)+tuple(tip+v/3+n*bend)+tuple(tip+2*v/3)+tuple(T1))
    return ops

def build_whatsapp(a, box, F=12, blur=0.4, tail=(70, 200)):
    """WhatsApp: balão = círculo + ponta (tangentes), aro idem, fone traçado suave."""
    x0,y0,x1,y1 = box; big = upscale_alpha(a[y0:y1,x0:x1], F, blur) > 0.5
    cs,h = cv2.findContours(big.astype(np.uint8), cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE); h=h[0]
    dep = lambda i: (lambda f: f(f,i))(lambda f,i: 0 if h[i][3]==-1 else 1+f(f,h[i][3]))
    L = {}
    for i,c in enumerate(cs):
        if len(c) > 40: L.setdefault(dep(i), []).append(c)
    top = lambda lst: max(lst, key=cv2.contourArea)
    d0,d1,d2,d3 = top(L[0]),top(L[1]),top(L[2]),top(L[3])
    def shape(c):
        pts = c[:,0,:].astype(float); X,Y,W_,H_ = cv2.boundingRect(c); m = pts.mean(0)
        ang = np.degrees(np.arctan2(pts[:,1]-m[1], pts[:,0]-m[0])) % 360
        keep = ~((ang>tail[0])&(ang<tail[1]))
        cx,cy,r = fit_circle(pts[keep])
        dist = np.hypot(pts[:,0]-cx, pts[:,1]-cy); dist[keep] = 0; tip = pts[np.argmax(dist)]
        return cx,cy,r,tip[0],tip[1]
    s0,s1,s2 = shape(d0),shape(d1),shape(d2)
    # fone: máscara do componente d3, traço suave
    hm = np.zeros(big.shape, np.uint8); cv2.drawContours(hm, [d3], -1, 1, -1)
    hb = cv2.GaussianBlur(hm.astype(np.float32), (0,0), F*0.5) > 0.5
    hand = potrace.Bitmap(~hb).trace(turdsize=60, alphamax=1.3, opticurve=True, opttolerance=1.2)
    tf = lambda ops_: [(o[0],)+tuple(x0+v/F if k%2==0 else y0+v/F for k,v in enumerate(o[1:])) for o in ops_]
    sp = [tf(teardrop_ops(*s0, concave=0.14)), tf(teardrop_ops(*s1, concave=0.14)), tf(teardrop_ops(*s2, concave=0.14))]
    sp += [[(o[0],)+tuple(v for v in o[1:]) for o in ops] for ops in curves_to_ops(hand, F, x0, y0)]
    return sp

# ---------------- traços (linhas de espessura constante) ----------------
from collections import deque
from scipy.interpolate import splprep, splev
from skimage.morphology import skeletonize

def _longest_path(sk):
    pts = {tuple(p) for p in np.argwhere(sk)[:, ::-1]}   # (x,y)
    nb = lambda p: [(p[0]+dx,p[1]+dy) for dx in (-1,0,1) for dy in (-1,0,1) if (dx or dy) and (p[0]+dx,p[1]+dy) in pts]
    def bfs(s):
        par={s:None}; dq=deque([s]); last=s
        while dq:
            u=dq.popleft(); last=u
            for v in nb(u):
                if v not in par: par[v]=u; dq.append(v)
        return last,par
    a,_=bfs(next(iter(pts))); b,par=bfs(a); path=[b]
    while par[path[-1]] is not None: path.append(par[path[-1]])
    return np.array(path[::-1],float)

def _bez_through(P):
    """Catmull-Rom -> Béziers passando pelos pontos P (n,2)."""
    P = np.vstack([P[0],P,P[-1]]); ops=[('M',)+tuple(P[1])]
    for i in range(1,len(P)-2):
        c1=P[i]+(P[i+1]-P[i-1])/6; c2=P[i+1]-(P[i+2]-P[i])/6
        ops.append(('C',)+tuple(c1)+tuple(c2)+tuple(P[i+1]))
    return ops

def fit_stroke(mask_alpha, box, F=4, tol=0.9, step=16, corner_deg=32, close_px=6, W=1600, H=800):
    """Linha de espessura constante: esqueleto -> spline suave -> poucos Béziers. Devolve (subpaths, largura)."""
    x0,y0,x1,y1 = box; a = mask_alpha[y0:y1,x0:x1].astype(np.float32)
    big = cv2.GaussianBlur(cv2.resize(a,(a.shape[1]*F,a.shape[0]*F),interpolation=cv2.INTER_CUBIC),(0,0),F*0.5)
    bw = (big>0.5).astype(np.uint8)
    if close_px>6:   # liga pontas separadas por uma falha de detecção: dilata, o esqueleto atravessa a emenda
        bw = cv2.dilate(bw, cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(int(F*close_px)|1,int(F*close_px)|1)))
    sk = skeletonize(bw>0)
    if not sk.any(): return [], 0.0
    P = _longest_path(sk)
    # largura = área de tinta / comprimento
    L = np.sum(np.hypot(*np.diff(P,axis=0).T))/F; width = float(a.sum()/max(L,1))
    # suaviza e detecta quina em janela larga (o esqueleto de traço grosso arredonda o vértice)
    k=9; Ps=np.vstack([np.convolve(np.pad(P[:,i],(k//2,k//2),mode='edge'),np.ones(k)/k,mode='valid') for i in (0,1)]).T
    w=int(9*F); ang=[]
    for i in range(w,len(Ps)-w):
        v1=Ps[i]-Ps[i-w]; v2=Ps[i+w]-Ps[i]; c=np.dot(v1,v2)/(np.linalg.norm(v1)*np.linalg.norm(v2)+1e-9)
        ang.append(np.degrees(np.arccos(np.clip(c,-1,1))))
    segs=[Ps]; corner=None
    if ang and max(ang)>corner_deg:
        i=int(np.argmax(ang))+w; q=int(3*F)
        def tang(pts):
            m=pts.mean(0); u,sv,vt=np.linalg.svd(pts-m); return m,vt[0]
        m1,d1=tang(Ps[i-w:i-q]); m2,d2=tang(Ps[i+q:i+w])
        A=np.array([d1,-d2]).T
        if abs(np.linalg.det(A))>0.2:
            t=np.linalg.solve(A,m2-m1); cp=m1+t[0]*d1
            corner=cp if np.hypot(*(cp-Ps[i]))<8*F else Ps[i]
        else: corner=Ps[i]
        segs=[np.vstack([Ps[:i-q],corner]), np.vstack([corner,Ps[i+q:]])]
    out=[]
    for sgm in segs:
        if len(sgm)<6: continue
        n=len(sgm); tck,_=splprep(sgm.T,s=n*(tol*F/ 4*1.0)**2,k=3); u=np.linspace(0,1,max(3,int(n/F/step)+2)*8); X=np.array(splev(u,tck)).T
        # amostra por comprimento de arco
        d=np.r_[0,np.cumsum(np.hypot(*np.diff(X,axis=0).T))]; m=max(2,int(round(d[-1]/F/step))+1)
        t=np.linspace(0,d[-1],m); S=np.c_[np.interp(t,d,X[:,0]),np.interp(t,d,X[:,1])]
        S=S/F+[x0,y0]
        if corner is not None:
            cc=corner/F+[x0,y0]
            for idx in (0,-1):
                if np.hypot(*(S[idx]-cc))<6: S[idx]=cc
        # prolonga pontas que tocam a borda da arte (sangria)
        for idx,nbr in ((0,1),(-1,-2)):
            p=S[idx]; 
            if p[0]<=12 or p[1]<=12 or p[0]>=W-13 or p[1]>=H-13:
                dv=S[idx]-S[nbr]; dv/=np.linalg.norm(dv)+1e-9; S[idx]=p+dv*30
        out.append(_bez_through(S))
    return out, L

def smooth_mask(m, F, sigma_px, corner_deg=55):
    """Suaviza o contorno (σ em px da arte) preservando cantos agudos (pontas de serifa); re-rasteriza."""
    cs,h = cv2.findContours(m.astype(np.uint8), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    out = np.zeros(m.shape, np.uint8); sg = sigma_px*F; k = int(4*sg)|1
    for pass_hole in (False, True):
        for i,c in enumerate(cs):
            is_hole = h[0][i][3] != -1
            if is_hole != pass_hole or len(c) < 12: continue
            P = c[:,0,:].astype(np.float32); n=len(P)
            # cantos: ângulo de giro numa janela de ~1.2 px da arte
            wv=max(2,int(1.2*F)); v1=P-np.roll(P,wv,0); v2=np.roll(P,-wv,0)-P
            cosang=(v1*v2).sum(1)/(np.linalg.norm(v1,axis=1)*np.linalg.norm(v2,axis=1)+1e-9)
            ang=np.degrees(np.arccos(np.clip(cosang,-1,1))); corner=ang>corner_deg
            # só o pico local de cada canto
            peaks=corner & (ang>=np.maximum(np.roll(ang,1),np.roll(ang,-1))) & (ang>=np.roll(ang,2)) & (ang>=np.roll(ang,-2))
            Q=P.copy()
            for ax in (0,1):
                pad=np.concatenate([P[-k:,ax],P[:,ax],P[:k,ax]]); ker=np.exp(-0.5*(np.arange(-k,k+1)/sg)**2); ker/=ker.sum()
                Q[:,ax]=np.convolve(pad,ker,mode='same')[k:-k]
            Q[peaks]=P[peaks]                      # mantém a ponta da serifa
            cv2.fillPoly(out,[np.round(Q).astype(np.int32)],0 if pass_hole else 1)
    return out>0

# ---------------- logomarca bicolor (separação de cores por pixel) ----------------
def unmix_two_inks(img, box, F=8, sigma=0.35, thr=0.5, alphamax=0.95, opttol=0.5, turd=20, return_maps=False, deconv=0.9, iters=25, close_b=2.0, close_g=2.5, smooth=0.45, norm=True, smooth_contour=0.9):
    """Separa tinta A (mais escura/azul) e tinta B (dourada) do fundo claro por mínimos quadrados em cada pixel.
    Devolve (subpaths_azul, subpaths_dourado, cor_azul, cor_dourada)."""
    x0,y0,x1,y1 = box; crop = img[y0:y1,x0:x1].astype(np.float32); h,w,_ = crop.shape
    border = np.concatenate([crop[0],crop[-1],crop[:,0],crop[:,-1]]); bgc = np.median(border,0)
    d = (crop-bgc).reshape(-1,3); mag = np.linalg.norm(d,axis=1)
    sel = d[mag>np.percentile(mag,80)]
    # agrupa em 2 cores de tinta por tom (R-B) e escolhe o núcleo (mais forte) de cada
    rb = sel[:,0]-sel[:,2]; blue = sel[rb<np.percentile(rb,40)]; gold = sel[rb>np.percentile(rb,85)]
    Bc = bgc+np.median(blue[np.linalg.norm(blue,axis=1)>np.percentile(np.linalg.norm(blue,axis=1),60)],0)
    Gc = bgc+np.median(gold[np.linalg.norm(gold,axis=1)>np.percentile(np.linalg.norm(gold,axis=1),50)],0)
    M = np.stack([Bc-bgc, Gc-bgc],1)                        # 3x2
    P = np.linalg.pinv(M)                                   # 2x3
    ab = (d@P.T).reshape(h,w,2); ab = np.clip(ab,0,1.0)
    if deconv:   # desfaz o desfoque do JPEG (Richardson-Lucy) -> recupera hastes finas e bordas nítidas
        from skimage.restoration import richardson_lucy
        r=int(np.ceil(3*deconv)); yy,xx=np.mgrid[-r:r+1,-r:r+1]; psf=np.exp(-(xx**2+yy**2)/(2*deconv**2)); psf/=psf.sum()
        for k in range(2):
            up=cv2.resize(ab[...,k],(w*4,h*4),interpolation=cv2.INTER_CUBIC); up=np.clip(up,1e-3,1)
            psf4=cv2.resize(psf,(psf.shape[1]*4,psf.shape[0]*4),interpolation=cv2.INTER_CUBIC); psf4/=psf4.sum()
            ab[...,k]=cv2.resize(np.clip(richardson_lucy(up,psf4,num_iter=iters,clip=False),0,1),(w,h),interpolation=cv2.INTER_AREA)
    out=[]
    for k in range(2):
        a = cv2.resize(ab[...,k],(w*F,h*F),interpolation=cv2.INTER_CUBIC)
        a = cv2.GaussianBlur(a,(0,0),F*sigma)
        out.append(a)
    def clean(m, close_px, min_island, min_hole, smooth):
        m = m.astype(np.uint8)
        if close_px: m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(int(close_px*F)|1,)*2))
        # remove ilhas pequenas (ruído) e tampa buracos pequenos (frestas)
        n,lab,st,_ = cv2.connectedComponentsWithStats(m,8)
        for i in range(1,n):
            if st[i,4] < min_island*F*F: m[lab==i]=0
        inv = (1-m).astype(np.uint8); n,lab,st,_ = cv2.connectedComponentsWithStats(inv,4)
        for i in range(1,n):
            if st[i,4] < min_hole*F*F and not (st[i,0]==0 or st[i,1]==0 or st[i,0]+st[i,2]==m.shape[1] or st[i,1]+st[i,3]==m.shape[0]): m[lab==i]=1
        return cv2.GaussianBlur(m.astype(np.float32),(0,0),F*smooth) > 0.5
    thr_b, thr_g = (thr, thr) if np.isscalar(thr) else thr
    def locnorm(a, floor, k=5):
        lm = cv2.dilate(a, cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(int(k*F)|1,)*2))
        return (a>floor) & (a>0.5*lm)
    mb = locnorm(out[0], thr_b*0.6) if norm else out[0]>thr_b
    mg = locnorm(out[1], thr_g*0.6) if norm else out[1]>thr_g
    blue_m = clean(mb, close_b, 12, 25, smooth)
    gold_m = clean(mg, close_g, 6, 10, smooth) & ~blue_m
    if smooth_contour:
        blue_m = smooth_mask(blue_m, F, smooth_contour); gold_m = smooth_mask(gold_m, F, smooth_contour) & ~blue_m
    sp=[curves_to_ops(trace(m,alphamax,opttol,turd),F,x0,y0) for m in (blue_m,gold_m)]
    res = (sp[0],sp[1],tuple(np.round(Bc).astype(int)),tuple(np.round(Gc).astype(int)))
    return (res+(out,)) if return_maps else res

# ---------------- monograma: S de fonte (curvas exatas) + haste do P e anel do original ----------------
def logo_with_font_S(img, box, font_path, F=8, thr=(0.45,0.33), stem_region=(275,372)):
    """S refeito com o desenho da fonte (ajustado ao S do logo por sobreposição); haste do P e anel dourado do original."""
    from PIL import ImageFont, ImageDraw, Image as _I
    from scipy.optimize import minimize
    x0,y0,x1,y1 = box
    b,g,cb,cg,maps = unmix_two_inks(img, box, thr=thr, return_maps=True)
    Mb = maps[0]>0.5; h,w = Mb.shape
    sx_,sy_ = stem_region
    valid = np.ones_like(Mb); valid[sy_:,:sx_] = False
    T = Mb & valid; ys,xs = np.nonzero(T); tb=(xs.min(),ys.min(),xs.max()+1,ys.max()+1)
    size=900; f=ImageFont.truetype(font_path,size); im=_I.new('L',(size*2,size*2),0); ImageDraw.Draw(im).text((size//2,size//4),'S',font=f,fill=255)
    a=np.asarray(im)>127; yy,xx=np.nonzero(a); G=a[yy.min():yy.max()+1,xx.min():xx.max()+1].astype(np.float32); gh,gw=G.shape
    def dice(p):
        sx,sy,sh,tx,ty=p; M=np.float32([[sx,sh,tx],[0,sy,ty]]); m=(cv2.warpAffine(G,M,(w,h),flags=cv2.INTER_AREA)>0.5)&valid
        return -2*(m&T).sum()/(m.sum()+T.sum()+1e-9)
    p0=[(tb[2]-tb[0])/gw,(tb[3]-tb[1])/gh,0,tb[0],tb[1]]
    r=minimize(dice,p0,method='Powell',options=dict(xtol=1e-3,ftol=1e-4,maxiter=4000)); sx,sy,sh,tx,ty=r.x
    # S em alta resolução; recortado onde o original não tem S (região da haste do P)
    K=2; M=np.float32([[sx*K,sh*K,tx*K],[0,sy*K,ty*K]]); S_hi=cv2.warpAffine(G,M,(w*K,h*K),flags=cv2.INTER_AREA)>0.5
    valid_hi = cv2.resize(valid.astype(np.uint8),(w*K,h*K),interpolation=cv2.INTER_NEAREST)>0
    S_hi = S_hi & valid_hi
    # haste do P: letra "I" da mesma fonte (haste + serifas), ajustada à haste do original
    stem_t = cv2.resize((Mb & ~valid).astype(np.uint8),(w,h),interpolation=cv2.INTER_NEAREST)>0
    colsum = stem_t[sy_:].sum(0); core = np.where(colsum > 0.5*colsum.max())[0]      # colunas da haste
    sxlo,sxhi = max(core.min()-40,0), core.max()+40
    stem_t = stem_t.copy(); stem_t[:, :max(sxlo-30,0)] = False
    imI=_I.new('L',(size*2,size*2),0); ImageDraw.Draw(imI).text((size//2,size//4),'I',font=f,fill=255)
    aI=np.asarray(imI)>127; yI,xI=np.nonzero(aI); GI=aI[yI.min():yI.max()+1,xI.min():xI.max()+1].astype(np.float32); ghI,gwI=GI.shape
    ysS,xsS=np.nonzero(stem_t); tbI=(xsS.min(),ysS.min(),xsS.max()+1,ysS.max()+1)
    def diceI(p):
        sxx,syy,txx,tyy=p; MI=np.float32([[sxx,0,txx],[0,syy,tyy]]); m=cv2.warpAffine(GI,MI,(w,h),flags=cv2.INTER_AREA)>0.5
        return -2*(m&stem_t).sum()/(m.sum()+stem_t.sum()+1e-9)
    rI=minimize(diceI,[(tbI[2]-tbI[0])/gwI,(tbI[3]-tbI[1])/ghI,tbI[0],tbI[1]],method='Powell',options=dict(xtol=1e-3,ftol=1e-4,maxiter=3000))
    sxx,syy,txx,tyy=rI.x; stem=cv2.warpAffine(GI,np.float32([[sxx*K,0,txx*K],[0,syy*K,tyy*K]]),(w*K,h*K),flags=cv2.INTER_AREA)>0.5
    print('haste: dice %.3f'%-rI.fun)
    stem = stem & ~S_hi
    blue_hi = S_hi | stem
    def to_art(ops_list):
        out=[]
        for ops in ops_list:
            o2=[]
            for op in ops:
                v=op[1:]; o2.append((op[0],)+tuple((x0+val/(K*F)) if k%2==0 else (y0+val/(K*F)) for k,val in enumerate(v)))
            out.append(o2)
        return out
    raw = curves_to_ops(trace(blue_hi,1.0,0.6,30),1,0,0)
    return to_art(raw), g, cb, cg, r
