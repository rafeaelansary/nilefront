import re, pathlib, json, sys, collections
from py_mini_racer import MiniRacer
script=max(re.findall(r"<script>(.*?)</script>", pathlib.Path("/Users/rafea/src/blockfront/index.html").read_text(), re.S), key=len)
inner=script.rstrip()[:-len('})();')]
GROUP=sys.argv[1]
probe=inner+f"""
globalThis.__r=(function(){{
  var g={GROUP};
  var kept=globalThis.__worldBoxes(g).filter(function(b){{
    var mt=b.mesh.material; if(mt&&mt.polygonOffset) return false;
    var s=b.box.max.x-b.box.min.x,t=b.box.max.z-b.box.min.z,h=b.box.max.y-b.box.min.y;
    return (s<58&&t<58)||h>6; }});
  var AX=['x','y','z'], pat={{}};
  for(var i=0;i<kept.length;i++)for(var j=i+1;j<kept.length;j++){{
    var A0=kept[i].box,B0=kept[j].box;
    if(A0.min.x>B0.max.x+3||B0.min.x>A0.max.x+3||A0.min.z>B0.max.z+3||B0.min.z>A0.max.z+3) continue;
    var cmp=globalThis.__comparableBoxes(kept[i].mesh,A0,kept[j].mesh,B0); if(!cmp) continue;
    var A=cmp[0],B=cmp[1];
    for(var k=0;k<3;k++){{
      var ax=AX[k],u=AX[(k+1)%3],v=AX[(k+2)%3];
      if(Math.min(A.max[u],B.max[u])-Math.max(A.min[u],B.min[u])<0.12) continue;
      if(Math.min(A.max[v],B.max[v])-Math.max(A.min[v],B.min[v])<0.12) continue;
      if(Math.min(A.max[ax],B.max[ax])-Math.max(A.min[ax],B.min[ax])<=0) continue;
      [['min',A.min[ax],B.min[ax]],['max',A.max[ax],B.max[ax]]].forEach(function(pr){{
        if(Math.abs(pr[1]-pr[2])>=0.005) return;
        var key=ax+pr[0]+' | '+[(A.max.x-A.min.x).toFixed(2),(A.max.y-A.min.y).toFixed(2),(A.max.z-A.min.z).toFixed(2)].join('x')
                +' vs '+[(B.max.x-B.min.x).toFixed(2),(B.max.y-B.min.y).toFixed(2),(B.max.z-B.min.z).toFixed(2)].join('x');
        if(!pat[key]) pat[key]={{n:0, at:[+((A.min.x+A.max.x)/2).toFixed(1),+((A.min.y+A.max.y)/2).toFixed(2),+((A.min.z+A.max.z)/2).toFixed(1)], plane:+pr[1].toFixed(3)}};
        pat[key].n++;
      }});
    }}
  }}
  return pat;
}})();
}})();
"""
ctx=MiniRacer(); ctx.eval(pathlib.Path("/Users/rafea/src/blockfront/tools/audit/three_stub.js").read_text()); ctx.eval(probe)
r=json.loads(ctx.eval("JSON.stringify(globalThis.__r)"))
print(f"{GROUP}: {sum(v['n'] for v in r.values())} hits, {len(r)} distinct patterns")
for k,v in sorted(r.items(), key=lambda kv:-kv[1]['n'])[:18]:
    print(f"  {v['n']:4d}  {k}   at {v['at']} plane={v['plane']}")
