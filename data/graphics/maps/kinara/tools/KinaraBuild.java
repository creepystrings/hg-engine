import formats.imd.ImdModel;
import formats.nsbtx2.*;
import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.io.File;
import java.util.*;
public class KinaraBuild { public static void main(String[] a) throws Exception {
  String dir=a[0], texset=a[1], outDir=a[2];
  ImdModel m=new ImdModel(dir+"/kinara.obj", outDir+"/kinara.imd", null);
  System.out.println("map imd: materials="+m.getNumMaterials()+" polys="+m.getNumPolygons()+" quads="+m.getNumQuads()+" verts="+m.getNumVertices());
  Nsbtx2 n=NsbtxLoader2.loadNsbtx(texset);
  int base=n.getTextures().size();
  File[] pngs=new File(dir).listFiles((d,f)->f.endsWith(".png")); Arrays.sort(pngs);
  for (File f: pngs){
    String name=f.getName().replace(".png","");
    if (n.isTextureNameUsed(name)) throw new RuntimeException("name clash "+name);
    BufferedImage img=ImageIO.read(f);
    boolean tr=false;
    for(int y=0;y<img.getHeight()&&!tr;y++)for(int x=0;x<img.getWidth();x++) if(((img.getRGB(x,y)>>>24)&0xFF)<128){tr=true;break;}
    n.addTextureAndPalette(n.getTextures().size()-1, n.getPalettes().size()-1, img, 3, tr, name, name+"_pl");
  }
  System.out.println("textures "+base+" -> "+n.getTextures().size()+", palettes "+n.getPalettes().size());
  NsbtxImd imd=new NsbtxImd(n); imd.saveToFile(outDir+"/texset_kinara.imd");
}}
