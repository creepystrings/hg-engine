import numpy as np, json, os, math
from PIL import Image
OUT='/home/claude/kin/model'
for f in os.listdir(OUT): os.remove(os.path.join(OUT,f))
m=np.asarray(Image.open('mockup_1x.png').convert('RGB')).astype(np.int32)
g=np.asarray(Image.open('ground_clean.png').convert('RGB')).astype(np.uint8)
obj=np.load('obj_mask.npy'); pm=np.load('prop_mask.npy')
over=np.asarray(Image.open('overlay_layer.png').convert('RGB')).astype(np.int32)
ov=~((over[...,0]==248)&(over[...,1]==0)&(over[...,2]==248))
B=json.load(open('building_boxes.json'))
hits=json.load(open('prop_hits.json'))
def q555(a): return (a//8)*8
def quant(img_rgb,alpha=None,n=16):
    # returns RGBA PIL with <=n colours (incl transparent if alpha)
    im=Image.fromarray(q555(img_rgb.astype(np.int32)).astype(np.uint8))
    k=n-1 if alpha is not None else n
    cols=len(set(map(tuple,np.asarray(im).reshape(-1,3)[(alpha.reshape(-1) if alpha is not None else slice(None))])))
    if cols>k:
        im=im.quantize(k,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE).convert('RGB')
        im=Image.fromarray(q555(np.asarray(im).astype(np.int32)).astype(np.uint8))
    a=np.asarray(im)
    if alpha is None: return Image.fromarray(a,'RGB')
    rgba=np.dstack([a,np.where(alpha,255,0).astype(np.uint8)])
    rgba[~alpha,:3]=(248,0,248)
    return Image.fromarray(rgba,'RGBA')
def p2(v): return max(8,1<<math.ceil(math.log2(v)))
V=[];VT=[];VN=[];mats=[]  # mats: (name, png, [faces])
def addv(p): V.append(p); return len(V)
def addt(t): VT.append(t); return len(VT)
def addn(n): VN.append(n); return len(VN)
NUP=addn((0,0,1)); NSL=addn((0,-0.771,0.636))
matidx={}
def face(name,png,verts,uvs,n):
    if name not in matidx: matidx[name]=len(mats); mats.append((name,png,[]))
    vi=[addv(v) for v in verts]; ti=[addt(t) for t in uvs]
    mats[matidx[name]][2].append(' '.join(f'{a}/{b}/{n}' for a,b in zip(vi,ti)))
# ---- ground (fuzzy-deduped cells)
def dist(A,b):
    d=np.abs(A-b).reshape(len(A),256,3).sum(2)
    big=(d>45).sum(1)
    return np.where(big<=2, d.mean(1)/14.0, 10+d.mean(1))
cellk={}
for r in range(32):
  for c in range(32):
    cellk.setdefault(g[r*16:r*16+16,c*16:c*16+16].tobytes(),[]).append((r,c))
import glob
TB={os.path.basename(f)[5:7]:np.asarray(Image.open(f).convert('RGB')).astype(np.int32) for f in sorted(glob.glob('out/ground/tile_*.png'))}
TB={k:v for k,v in TB.items() if v.shape==(16,16,3)}
tn=list(TB); TA=np.array([TB[n] for n in tn])
uniq={}; recon=np.zeros_like(g); rest=[]
def put(nm,img,r,c):
    if nm not in uniq: uniq[nm]=1; quant(img).save(f'{OUT}/{nm}.png')
    recon[r*16:r*16+16,c*16:c*16+16]=img
    x0=c-16; y0=(31-r)-16
    face(nm,nm+'.png',[(x0,y0,0),(x0+1,y0,0),(x0+1,y0+1,0),(x0,y0+1,0)],[(0,0),(1,0),(1,1),(0,1)],NUP)
cand=[]
best={}
for r in range(32):
  for c in range(32):
    cell=g[r*16:r*16+16,c*16:c*16+16].astype(np.int32)
    d=np.abs(TA-cell).sum(3).mean((1,2)); j=int(d.argmin()); best[(r,c)]=j
    cand.append((d[j],r,c,cell))
cand.sort(key=lambda x:-x[0])
MAXU=int(os.environ.get('MAXU','40')); E=float(os.environ.get('ERR','14'))
uniqcells=[]; assign={}
for e,r,c,cell in cand:
    if e<E: break
    flat=cell.reshape(-1)
    hit=None
    for k,u in enumerate(uniqcells):
        if np.abs(u-flat).mean()<4: hit=k; break
    if hit is None and len(uniqcells)<MAXU: uniqcells.append(flat); hit=len(uniqcells)-1
    if hit is not None: assign[(r,c)]=hit
for r in range(32):
  for c in range(32):
    if (r,c) in assign: k=assign[(r,c)]; put(f'kg{k:03d}',uniqcells[k].reshape(16,16,3),r,c)
    else: j=best[(r,c)]; put('kt'+tn[j],TA[j],r,c)
Image.fromarray(recon).save('ground_final.png')
print('ground textures',len(uniq))
# ---- objects
def chunks(v):
    v=(v+7)//8*8; out=[]
    while v>0:
        b=8
        while b*2<=v: b*=2
        if v-b>0 and v-b<=b//4 and b*2-v< (v-b)*0: pass
        out.append(b); v-=b
    return out
emitted=set()
def emit(name,rgba,x0,y1,w,h,flat=False):
    a=np.asarray(rgba)
    xs=[0]
    for cw in chunks(w): xs.append(xs[-1]+cw)
    ys=[0]
    for ch in chunks(h): ys.append(ys[-1]+ch)
    for i in range(len(xs)-1):
        for j in range(len(ys)-1):
            px0,px1=xs[i],min(xs[i+1],w); py0,py1=ys[j],min(ys[j+1],h)   # py from top
            if px0>=w or py0>=h: continue
            sub=a[py0:py1,px0:px1]
            if sub[...,3].max()==0: continue
            TW,TH=xs[i+1]-xs[i],ys[j+1]-ys[j]
            nm=f'{name}{i}{j}' if (len(xs)>2 or len(ys)>2) else name
            if nm not in emitted:
                canvas=Image.new('RGBA',(TW,TH),(248,0,248,0)); canvas.paste(Image.fromarray(sub,'RGBA'),(0,0)); canvas.save(f'{OUT}/{nm}.png'); emitted.add(nm)
            sw,sh=px1-px0,py1-py0
            u1=sw/TW; v0=1-sh/TH
            X0=(x0+px0)/16-16; X1=(x0+px1)/16-16
            # vertical extent measured from art bottom: rows py0..py1 from top -> heights (h-py1)..(h-py0)
            hb=(h-py1)/16; ht=(h-py0)/16
            if flat:
                Yb=16-y1/16; z=0.02
                verts=[(X0,Yb+hb,z),(X1,Yb+hb,z),(X1,Yb+ht,z),(X0,Yb+ht,z)]; n=NUP
            else:
                Yb=16-y1/16+0.08
                verts=[(X0,Yb+0.636*hb,0.771*hb),(X1,Yb+0.636*hb,0.771*hb),(X1,Yb+0.636*ht,0.771*ht),(X0,Yb+0.636*ht,0.771*ht)]; n=NSL
            face(nm,nm+'.png',verts,[(0,v0),(u1,v0),(u1,1),(0,1)],n)
short={'bamboo_fence':'k_fence','bamboo_fence_corner':'k_fencec','banana_plant':'k_banana','banyan_shrine':'k_banyan','canoe':'k_canoe',
 'chinese_fishing_net':'k_fishnet','clothesline':'k_cloth','coconut_palm_drought':'k_palmdry','coconut_palm_healthy':'k_palm','helion_pump':'k_pump',
 'hibiscus_bush':'k_hibiscus','houseboat_stranded':'k_houseboat','jetty_post':'k_jpost','laterite_wall_corner':'k_wallc','marigold_pot':'k_marigold',
 'signpost':'k_sign','water_marker':'k_marker','well':'k_well'}
objs=[]
for p in hits:
    im=np.asarray(Image.open(f"out/props/{p['prop']}.png").convert('RGB')).astype(np.int32)
    mk=~((im[...,0]==248)&(im[...,1]==0)&(im[...,2]==248)); ys,xs=np.where(mk)
    im=im[ys.min():ys.max()+1,xs.min():xs.max()+1]; mk=mk[ys.min():ys.max()+1,xs.min():xs.max()+1]
    nm=short.get(p['prop'],'k_'+p['prop'][:14]); art=quant(im,mk)
    for x,y,_ in p['hits']: objs.append((y+mk.shape[0],nm,art,x,y+mk.shape[0],mk.shape[1],mk.shape[0],False))
bn={'player_house':'k_house_pl','kabir_house':'k_house_kb','lab':'k_lab','neighbor':'k_house_nb','wall_h':'k_wall','wall_v':'k_wallv','plant_x':'k_plant'}
for k,(x0,y0,x1,y1) in B.items():
    sub=m[y0:y1,x0:x1]; a=(ov&~pm)[y0:y1,x0:x1] if k!='plant_x' else ov[y0:y1,x0:x1]
    if k in('player_house','kabir_house','lab','neighbor'):
        # fill holes: everything inside the outline is opaque
        from scipy import ndimage
        a=ndimage.binary_fill_holes(ndimage.binary_closing(a,iterations=2))
    ys,xs=np.where(a); sub=sub[ys.min():ys.max()+1,xs.min():xs.max()+1]; a=a[ys.min():ys.max()+1,xs.min():xs.max()+1]
    if a.shape[0]>64: sub=sub[-64:]; a=a[-64:]
    X=x0+xs.min(); Yb=y0+ys.max()+1
    objs.append((Yb,bn[k],quant(sub,a),X,Yb,a.shape[1],a.shape[0],k=='wall_v'))
    print(k,X,Yb,a.shape[1],a.shape[0])
for o in sorted(objs,key=lambda o:o[0]): emit(*o[1:])
# ---- write obj/mtl (materials contiguous)
with open(f'{OUT}/kinara.mtl','w') as f:
    for nm,png,_ in mats: f.write(f'newmtl {nm}\nKd 1 1 1\nmap_Kd {png}\n\n')
with open(f'{OUT}/kinara.obj','w') as f:
    f.write('mtllib kinara.mtl\no kinara\n')
    for v in V: f.write('v %.4f %.4f %.4f\n'%(v[0],v[1],v[2]+1.0))
    for t in VT: f.write('vt %.5f %.5f\n'%t)
    for n in VN: f.write('vn %.4f %.4f %.4f\n'%n)
    for nm,png,fs in mats:
        f.write(f'usemtl {nm}\ns off\n'); [f.write('f '+x+'\n') for x in fs]
print('materials',len(mats),'faces',sum(len(x[2]) for x in mats))
tot=0
for fn in os.listdir(OUT):
    if fn.endswith('.png'):
        im=Image.open(f'{OUT}/{fn}'); tot+=im.width*im.height//2+32
print('est tex bytes',tot)
