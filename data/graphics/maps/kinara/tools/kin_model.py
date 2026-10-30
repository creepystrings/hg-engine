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
# ---- ground: rebuilt from the DS-ready tileset (seamless HGSS-style tiles + autotiled path/shore edges)
import glob
TB={os.path.basename(f)[5:7]:np.asarray(Image.open(f).convert('RGB')).astype(np.int32) for f in sorted(glob.glob('out/ground/tile_*.png'))}
FAM={'G':['10','11','12'],'P':['00','01','02'],'S':['13','14','15'],'C':['20','21','22'],'F':['25','26','27'],'Y':['16','17'],'W':['70','71']}
gi=g.astype(np.int32)
pal={k:np.unique(np.concatenate([TB[t].reshape(-1,3) for t in v]),axis=0) for k,v in FAM.items() if k!='Y'}
ks=list(pal)
Dm=np.stack([np.abs(gi.reshape(-1,1,3)-pal[k][None]).sum(2).min(1) for k in ks],1)
plab=np.array(ks)[Dm.argmin(1)].reshape(512,512)
SEM=[]
for r in range(32):
    row=[]
    for c in range(32):
        cell=plab[r*16:r*16+16,c*16:c*16+16]; vals,cnt=np.unique(cell,return_counts=True); fr=dict(zip(vals,cnt/256))
        row.append('P' if fr.get('P',0)>=0.4 else max(fr,key=fr.get))
    SEM.append(row)
def setr(r0,r1,c0,c1,v):
    for r in range(r0,r1+1):
        for c in range(c0,c1+1): SEM[r][c]=v
setr(0,6,0,7,'F'); setr(25,31,0,6,'F')          # paddy-field plots (look like dry earth to the classifier)
setr(10,12,0,2,'Y'); setr(29,30,18,19,'Y')      # green paddy patches
setr(15,16,25,30,'J')                           # jetty
SEM[15][31]='W'; SEM[16][31]='W'
SEM[13][18]='P'; SEM[14][23]='S'
open('sem_grid.txt','w').write('\n'.join(''.join(r) for r in SEM))
def sem(r,c,default):
    if 0<=r<32 and 0<=c<32: return SEM[r][c]
    return default
PLAIN={k:v[0] for k,v in FAM.items()}
def mask_of(tid,mat): # pixels of an edge tile that are NOT the material
    return np.abs(TB[tid].reshape(-1,1,3)-pal[mat][None]).sum(2).min(1).reshape(16,16)>0
EDGE={'P':{'N':'03','E':'04','S':'05','W':'06','NW':'41','NE':'42','SE':'43','SW':'44'},
      'W':{'N':'50','E':'51','S':'52','W':'53','NW':'60','NE':'61','SE':'62','SW':'63'}}
EM={mt:{k:mask_of(t,mt) for k,t in d.items()} for mt,d in EDGE.items()}
JOIN={'P':{'P','J'},'W':{'W','J'}}
uniq={}; recon=np.zeros_like(g); GRID={}; SPECIAL={}
for r in range(32):
    for c in range(32):
        mt=SEM[r][c]
        if mt=='J':
            key=('J',r,c); SPECIAL[key]=gi[r*16:r*16+16,c*16:c*16+16]; GRID[(r,c)]=key; continue
        if mt in EDGE:
            nb={'N':sem(r-1,c,mt),'S':sem(r+1,c,mt),'W':sem(r,c-1,mt),'E':sem(r,c+1,mt),
                'NW':sem(r-1,c-1,mt),'NE':sem(r-1,c+1,mt),'SE':sem(r+1,c+1,mt),'SW':sem(r+1,c-1,mt)}
            if mt=='P' and c==0: nb['W']='P'; nb['NW']=nb['N'] if nb['N'] in JOIN[mt] else nb['NW']; nb['SW']=nb['S'] if nb['S'] in JOIN[mt] else nb['SW']
            out={d:v for d,v in nb.items() if v not in JOIN[mt]}
            # a diagonal only matters when both of its sides are open
            for d in ('NW','NE','SE','SW'):
                if d in out and (d[0] in out or d[1] in out): out.pop(d)
            if out:
                key=(mt,)+tuple(sorted((d,v) for d,v in out.items()))
                if key not in SPECIAL:
                    var=FAM[mt][0]; tile=TB[var].copy()
                    for d,v in out.items():
                        src=TB[PLAIN.get(v if v in PLAIN else 'C', '20')] if v!='J' else TB[var]
                        if v in ('F','Y','D'): src=TB[PLAIN['G']] if mt=='P' else TB['20']
                        mk=EM[mt][d]; tile[mk]=src[mk]
                    SPECIAL[key]=tile
                GRID[(r,c)]=key; continue
        GRID[(r,c)]=('F',mt)
# family textures: 2x2 arrangement of the tileset variants, mapped in world space
FAMTEX={}
for mt in set(v[1] for v in GRID.values() if v[0]=='F'):
    vs=FAM[mt]; order=[vs[0],vs[1%len(vs)],vs[2%len(vs)] if len(vs)>2 else vs[1%len(vs)],vs[0]]
    comp=np.zeros((32,32,3),np.int32)
    for j,t in enumerate(order): comp[(j//2)*16:(j//2)*16+16,(j%2)*16:(j%2)*16+16]=TB[t]
    nm='kf'+mt; FAMTEX[mt]=nm; quant(comp).save(f'{OUT}/{nm}.png'); uniq[nm]=1
for (r,c),v in GRID.items():
    if v[0]=='F': recon[r*16:r*16+16,c*16:c*16+16]=Image.open(f'{OUT}/kf{v[1]}.png').convert('RGB').crop(((c%2)*16,(r%2)*16,(c%2)*16+16,(r%2)*16+16))
    else: recon[r*16:r*16+16,c*16:c*16+16]=SPECIAL[v]
skeys=list(SPECIAL); SLOT={}
for n in range(0,len(skeys),16):
    grp=skeys[n:n+16]; atl=np.zeros((64,64,3),np.int32)
    for j in range(16):
        k=grp[j] if j<len(grp) else grp[0]; sx,sy=j%4,j//4; atl[sy*16:sy*16+16,sx*16:sx*16+16]=SPECIAL[k]
        if j<len(grp): SLOT[k]=(f'ka{n//16:02d}',sx,sy)
    nm=f'ka{n//16:02d}'; quant(atl).save(f'{OUT}/{nm}.png'); uniq[nm]=1
print('special tiles',len(SPECIAL),'atlases',(len(skeys)+15)//16)
def flush_ground():
    done=set()
    for r in range(32):
        for c in range(32):
            if (r,c) in done: continue
            v=GRID[(r,c)]
            if v[0]!='F':
                an,sx,sy=SLOT[v]; done.add((r,c)); x0=c-16; y0=(31-r)-16
                u0=sx/4; u1=(sx+1)/4; v1=1-sy/4; v0=1-(sy+1)/4
                face(an,an+'.png',[(x0,y0,0),(x0+1,y0,0),(x0+1,y0+1,0),(x0,y0+1,0)],[(u0,v0),(u1,v0),(u1,v1),(u0,v1)],NUP)
                continue
            w=1
            while c+w<32 and (r,c+w) not in done and GRID[(r,c+w)]==v: w+=1
            h=1
            while r+h<32 and all((r+h,c+k) not in done and GRID[(r+h,c+k)]==v for k in range(w)): h+=1
            for i in range(h):
                for k in range(w): done.add((r+i,c+k))
            x0=c-16; y0=(31-(r+h-1))-16; nm=FAMTEX[v[1]]
            u0=c/2; u1=(c+w)/2; v1=(64-r)/2; v0=(64-(r+h))/2
            face(nm,nm+'.png',[(x0,y0,0),(x0+w,y0,0),(x0+w,y0+h,0),(x0,y0+h,0)],[(u0,v0),(u1,v0),(u1,v1),(u0,v1)],NUP)
flush_ground()
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
