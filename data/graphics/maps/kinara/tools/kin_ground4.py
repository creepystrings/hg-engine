import numpy as np
from PIL import Image
m=np.asarray(Image.open('mockup_1x.png').convert('RGB')).astype(np.int32)
obj=np.load('obj_mask.npy')
H=512; Y,X=np.mgrid[0:H,0:H]
R,G,B=m[...,0],m[...,1],m[...,2]
paddy=np.zeros((H,H),bool); paddy[160:208,0:48]=True; paddy[464:496,288:320]=True
green=(G>R+15)
zone=np.zeros((H,H),np.int8)  # 0 grass,1 paddy,2 sand,3 east(vertical),4 jetty
zone[paddy]=1
zone[:,330:385]=2; zone[:,385:]=3
zone[236:276,385:492]=4
zone[193:207,140:240]=5; zone[193:207,250:332]=5
zone[0:112,0:128]=6
src_ok={0:green&~paddy&(X<330),1:green&paddy}
g=m.copy()
def offs(kind):
    if kind=='v': o=[(d,0) for d in range(-12,13) if d]
    elif kind=='h': o=[(0,d) for d in range(-12,13) if d]
    else: o=[(dy,dx) for dy in range(-8,9) for dx in range(-8,9) if (dy,dx)!=(0,0)]
    return sorted(o,key=lambda t:t[0]**2+t[1]**2)
O={k:offs(k) for k in 'vha'}
ys,xs=np.where(obj); miss=0
for y,x in zip(ys,xs):
    z=zone[y,x]
    if z in(0,1): ok=src_ok[z]; oo=O['a']
    elif z==5: ok=(R>G+30)&~obj; oo=O['h']
    elif z==6: ok=~green&~obj&(X<128)&(Y<112); oo=O['a']
    elif z==4: ok=~obj&(zone==4); oo=O['h']
    else: ok=~obj&(zone==z); oo=O['v']
    for dy,dx in oo:
        yy,xx=y+16*dy,x+16*dx
        if 0<=yy<H and 0<=xx<H and ok[yy,xx] and not obj[yy,xx]:
            g[y,x]=m[yy,xx]; break
    else: miss+=1
print('miss',miss)
Image.fromarray(g.astype(np.uint8)).save('ground_clean.png')
Image.fromarray(g.astype(np.uint8)).resize((1024,1024),0).save('/tmp/claude-0/-home-claude/c3c0f279-ac4a-5260-b1d7-06029dc5dd91/scratchpad/gc.png')
