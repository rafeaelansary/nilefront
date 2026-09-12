// Minimal THREE.js + DOM stub, sufficient to execute NILEFRONT's index.html script body
// headlessly and read back real world-space transforms. Throwaway verification tooling.
(function(global){

// ---------- tiny 4x4 matrix helpers (column-major, same convention as three.js) ----------
function matIdent(){ return [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1]; }
function matMul(a,b){
  const o = new Array(16);
  for(let c=0;c<4;c++) for(let r=0;r<4;r++){
    o[c*4+r] = a[0*4+r]*b[c*4+0] + a[1*4+r]*b[c*4+1] + a[2*4+r]*b[c*4+2] + a[3*4+r]*b[c*4+3];
  }
  return o;
}
// three.js Object3D default Euler order is XYZ
function composeTRS(p, e, s){
  const cx=Math.cos(e.x), sx=Math.sin(e.x);
  const cy=Math.cos(e.y), sy=Math.sin(e.y);
  const cz=Math.cos(e.z), sz=Math.sin(e.z);
  const ae=cx*cz, af=cx*sz, be=sx*cz, bf=sx*sz;
  const m = matIdent();
  m[0] = cy*cz;            m[4] = -cy*sz;           m[8]  = sy;
  m[1] = af + be*sy;       m[5] = ae - bf*sy;       m[9]  = -sx*cy;
  m[2] = bf - ae*sy;       m[6] = be + af*sy;       m[10] = cx*cy;
  m[0]*=s.x; m[1]*=s.x; m[2]*=s.x;
  m[4]*=s.y; m[5]*=s.y; m[6]*=s.y;
  m[8]*=s.z; m[9]*=s.z; m[10]*=s.z;
  m[12]=p.x; m[13]=p.y; m[14]=p.z;
  return m;
}
function applyMat(m, x, y, z){
  return {
    x: m[0]*x + m[4]*y + m[8]*z  + m[12],
    y: m[1]*x + m[5]*y + m[9]*z  + m[13],
    z: m[2]*x + m[6]*y + m[10]*z + m[14],
  };
}

// ---------- Vector3 ----------
class Vector3 {
  constructor(x=0,y=0,z=0){ this.x=x; this.y=y; this.z=z; }
  set(x,y,z){ this.x=x; this.y=y; this.z=z; return this; }
  copy(v){ this.x=v.x; this.y=v.y; this.z=v.z; return this; }
  clone(){ return new Vector3(this.x,this.y,this.z); }
  add(v){ this.x+=v.x; this.y+=v.y; this.z+=v.z; return this; }
  addVectors(a,b){ this.x=a.x+b.x; this.y=a.y+b.y; this.z=a.z+b.z; return this; }
  sub(v){ this.x-=v.x; this.y-=v.y; this.z-=v.z; return this; }
  subVectors(a,b){ this.x=a.x-b.x; this.y=a.y-b.y; this.z=a.z-b.z; return this; }
  multiplyScalar(s){ this.x*=s; this.y*=s; this.z*=s; return this; }
  divideScalar(s){ return this.multiplyScalar(1/s); }
  length(){ return Math.sqrt(this.x**2+this.y**2+this.z**2); }
  lengthSq(){ return this.x**2+this.y**2+this.z**2; }
  normalize(){ const l=this.length()||1; return this.divideScalar(l); }
  distanceTo(v){ return Math.sqrt((this.x-v.x)**2+(this.y-v.y)**2+(this.z-v.z)**2); }
  dot(v){ return this.x*v.x+this.y*v.y+this.z*v.z; }
  crossVectors(a,b){ this.x=a.y*b.z-a.z*b.y; this.y=a.z*b.x-a.x*b.z; this.z=a.x*b.y-a.y*b.x; return this; }
  applyQuaternion(){ return this; }
  setFromMatrixPosition(m){ this.x=m[12]; this.y=m[13]; this.z=m[14]; return this; }
  lerp(v,a){ this.x+=(v.x-this.x)*a; this.y+=(v.y-this.y)*a; this.z+=(v.z-this.z)*a; return this; }
  setScalar(s){ this.x=this.y=this.z=s; return this; }
  negate(){ this.x=-this.x; this.y=-this.y; this.z=-this.z; return this; }
  setX(v){ this.x=v; return this; } setY(v){ this.y=v; return this; } setZ(v){ this.z=v; return this; }
  addScalar(s){ this.x+=s; this.y+=s; this.z+=s; return this; }
  addScaledVector(v,s){ this.x+=v.x*s; this.y+=v.y*s; this.z+=v.z*s; return this; }
  multiply(v){ this.x*=v.x; this.y*=v.y; this.z*=v.z; return this; }
  divide(v){ this.x/=v.x; this.y/=v.y; this.z/=v.z; return this; }
  cross(v){ return this.crossVectors(this.clone(), v); }
  distanceToSquared(v){ return (this.x-v.x)**2+(this.y-v.y)**2+(this.z-v.z)**2; }
  manhattanLength(){ return Math.abs(this.x)+Math.abs(this.y)+Math.abs(this.z); }
  setLength(l){ return this.normalize().multiplyScalar(l); }
  angleTo(v){ const d=this.dot(v)/((this.length()*v.length())||1); return Math.acos(Math.max(-1,Math.min(1,d))); }
  min(v){ this.x=Math.min(this.x,v.x); this.y=Math.min(this.y,v.y); this.z=Math.min(this.z,v.z); return this; }
  max(v){ this.x=Math.max(this.x,v.x); this.y=Math.max(this.y,v.y); this.z=Math.max(this.z,v.z); return this; }
  clamp(a,b){ return this.max(a).min(b); }
  floor(){ this.x=Math.floor(this.x); this.y=Math.floor(this.y); this.z=Math.floor(this.z); return this; }
  round(){ this.x=Math.round(this.x); this.y=Math.round(this.y); this.z=Math.round(this.z); return this; }
  equals(v){ return this.x===v.x && this.y===v.y && this.z===v.z; }
  toArray(){ return [this.x,this.y,this.z]; }
  fromArray(a,o){ o=o||0; this.x=a[o]; this.y=a[o+1]; this.z=a[o+2]; return this; }
  applyMatrix4(m){ const e=m.elements||m; const p=applyMat(e,this.x,this.y,this.z); this.x=p.x; this.y=p.y; this.z=p.z; return this; }
  applyAxisAngle(){ return this; }
  applyEuler(){ return this; }
  transformDirection(){ return this.normalize(); }
  project(){ return this; } unproject(){ return this; }
  reflect(){ return this; }
  random(){ this.x=Math.random(); this.y=Math.random(); this.z=Math.random(); return this; }
}
class Euler { constructor(x=0,y=0,z=0){ this.x=x; this.y=y; this.z=z; } set(x,y,z){ this.x=x;this.y=y;this.z=z; return this; } copy(e){ this.x=e.x;this.y=e.y;this.z=e.z; return this; } }
class Quaternion {
  constructor(){ this._e = new Euler(); }
  // The models use setFromUnitVectors(UP, dir) to aim a Y-axis cylinder. Recover an equivalent
  // XYZ Euler so downstream bounding boxes are still approximately right.
  setFromUnitVectors(a,b){
    const ax=a.x, ay=a.y, az=a.z, bx=b.x, by=b.y, bz=b.z;
    const dot = ax*bx+ay*by+az*bz;
    if(dot > 0.999999){ this._e.set(0,0,0); return this; }
    if(dot < -0.999999){ this._e.set(Math.PI,0,0); return this; }
    // pitch/roll that carries +Y onto b
    this._e.set(Math.atan2(-bz, Math.hypot(bx,by)) , 0, Math.atan2(-bx, by));
    return this;
  }
  copy(q){ this._e.copy(q._e); return this; }
  setFromEuler(e){ this._e.copy(e); return this; }
}

// ---------- geometry ----------
// Each geometry records a local-space axis-aligned half-extent box. That is all the audit needs.
class BufferGeometry {
  constructor(){ this._half = {x:0,y:0,z:0}; this._offset={x:0,y:0,z:0}; this.parameters={}; }
  translate(x,y,z){ this._offset.x+=x; this._offset.y+=y; this._offset.z+=z; return this; }
  rotateX(){ return this; } rotateY(){ return this; } rotateZ(){ return this; }
  dispose(){}
  setAttribute(){ return this; }
  computeVertexNormals(){}
}
class BoxGeometry extends BufferGeometry {
  constructor(w=1,h=1,d=1){ super(); this._half={x:w/2,y:h/2,z:d/2}; this.parameters={width:w,height:h,depth:d}; this.type='BoxGeometry'; }
}
class CylinderGeometry extends BufferGeometry {
  constructor(rt=1,rb=1,h=1){ super(); const r=Math.max(rt,rb); this._half={x:r,y:h/2,z:r}; this.parameters={radiusTop:rt,radiusBottom:rb,height:h}; this.type='CylinderGeometry'; }
}
class ConeGeometry extends BufferGeometry {
  constructor(r=1,h=1){ super(); this._half={x:r,y:h/2,z:r}; this.parameters={radius:r,height:h}; this.type='ConeGeometry'; }
}
class SphereGeometry extends BufferGeometry {
  constructor(r=1){ super(); this._half={x:r,y:r,z:r}; this.parameters={radius:r}; this.type='SphereGeometry'; }
}
class PlaneGeometry extends BufferGeometry {
  constructor(w=1,h=1){ super(); this._half={x:w/2,y:h/2,z:0}; this.parameters={width:w,height:h}; this.type='PlaneGeometry'; }
}
class CircleGeometry extends BufferGeometry {
  constructor(r=1){ super(); this._half={x:r,y:r,z:0}; this.parameters={radius:r}; this.type='CircleGeometry'; }
}
class RingGeometry extends BufferGeometry {
  constructor(ri=0.5,ro=1){ super(); this._half={x:ro,y:ro,z:0}; this.parameters={innerRadius:ri,outerRadius:ro}; this.type='RingGeometry'; }
}
class TorusGeometry extends BufferGeometry {
  constructor(r=1,t=0.4){ super(); this._half={x:r+t,y:r+t,z:t}; this.type='TorusGeometry'; }
}
// A lathe spins a 2-D profile around the Y axis: radius is max|x| over the profile, and the
// Y extent comes straight from the profile's own y range (recentred, as three.js does not recentre).
class LatheGeometry extends BufferGeometry {
  constructor(points){
    super();
    const pts = points && points.length ? points : [{x:0,y:0}];
    let r=0, ymin=Infinity, ymax=-Infinity;
    for(const p of pts){ r=Math.max(r,Math.abs(p.x)); ymin=Math.min(ymin,p.y); ymax=Math.max(ymax,p.y); }
    this._half={x:r, y:(ymax-ymin)/2, z:r};
    this._offset={x:0, y:(ymax+ymin)/2, z:0};
    this.type='LatheGeometry';
  }
}
class PolyhedronGeometry extends BufferGeometry {
  constructor(r=1){ super(); this._half={x:r,y:r,z:r}; this.type='PolyhedronGeometry'; }
}
class TetrahedronGeometry extends PolyhedronGeometry {}
class OctahedronGeometry extends PolyhedronGeometry {}
class DodecahedronGeometry extends PolyhedronGeometry {}
class IcosahedronGeometry extends PolyhedronGeometry {}
class TubeGeometry extends BufferGeometry { constructor(path,seg,r=1){ super(); this._half={x:r,y:r,z:r}; this.type='TubeGeometry'; } }
class ExtrudeGeometry extends BufferGeometry { constructor(){ super(); this.type='ExtrudeGeometry'; } }
class ShapeGeometry extends BufferGeometry { constructor(){ super(); this.type='ShapeGeometry'; } }
class EdgesGeometry extends BufferGeometry { constructor(){ super(); this.type='EdgesGeometry'; } }
class WireframeGeometry extends BufferGeometry { constructor(){ super(); this.type='WireframeGeometry'; } }
class Shape { constructor(){ this.curves=[]; } moveTo(){return this;} lineTo(){return this;} quadraticCurveTo(){return this;} bezierCurveTo(){return this;} absarc(){return this;} closePath(){return this;} }
class Path extends Shape {}
class CatmullRomCurve3 { constructor(p){ this.points=p||[]; } getPoint(){ return new Vector3(); } getPoints(){ return this.points; } }
class BufferAttribute {
  constructor(array, itemSize){
    this.array = array || new Float32Array(0);
    this.itemSize = itemSize || 3;
    this.count = this.array.length / this.itemSize;
    this.needsUpdate = false;
  }
  setXYZ(){ return this; } setXY(){ return this; } getX(){ return 0; } getY(){ return 0; } getZ(){ return 0; }
  setUsage(){ return this; }
}
class Matrix4 {
  constructor(){ this.elements = matIdent(); }
  identity(){ this.elements = matIdent(); return this; }
  makeRotationX(){ return this; } makeRotationY(){ return this; } makeRotationZ(){ return this; }
  makeTranslation(x,y,z){ this.elements=matIdent(); this.elements[12]=x; this.elements[13]=y; this.elements[14]=z; return this; }
  makeScale(){ return this; } multiply(){ return this; } multiplyMatrices(){ return this; }
  compose(p){ this.elements=matIdent(); this.elements[12]=p.x; this.elements[13]=p.y; this.elements[14]=p.z; return this; }
  setPosition(p){ this.elements[12]=p.x; this.elements[13]=p.y; this.elements[14]=p.z; return this; }
  copy(m){ this.elements=m.elements.slice(); return this; }
  clone(){ const m=new Matrix4(); m.elements=this.elements.slice(); return m; }
  invert(){ return this; } transpose(){ return this; }
  extractRotation(){ return this; } lookAt(){ return this; }
}

// ---------- Object3D ----------
let _id = 0;
class Object3D {
  constructor(){
    this.id = _id++;
    this.position = new Vector3();
    this.rotation = new Euler();
    this.scale = new Vector3(1,1,1);
    this.quaternion = new Quaternion();
    this.children = [];
    this.parent = null;
    this.userData = {};
    this.visible = true;
    this.castShadow = false;
    this.receiveShadow = false;
    this.renderOrder = 0;
    this.name = '';
    this.matrixWorld = matIdent();
  }
  add(...objs){ for(const o of objs){ if(!o) continue; if(o.parent) o.parent.remove(o); o.parent=this; this.children.push(o); } return this; }
  remove(...objs){ for(const o of objs){ const i=this.children.indexOf(o); if(i>=0){ this.children.splice(i,1); o.parent=null; } } return this; }
  traverse(fn){ fn(this); for(const c of this.children.slice()) c.traverse(fn); }
  traverseVisible(fn){ this.traverse(fn); }
  lookAt(){ return this; }
  updateMatrixWorld(){
    // quaternion-driven objects (setFromUnitVectors) carry their orientation in quaternion._e
    const e = (this.quaternion && this.quaternion._e && (this.quaternion._e.x||this.quaternion._e.y||this.quaternion._e.z))
      ? this.quaternion._e : this.rotation;
    const local = composeTRS(this.position, e, this.scale);
    this.matrixWorld = this.parent ? matMul(this.parent.matrixWorld, local) : local;
    for(const c of this.children) c.updateMatrixWorld();
  }
  getWorldPosition(v){ v=v||new Vector3(); v.set(this.matrixWorld[12],this.matrixWorld[13],this.matrixWorld[14]); return v; }
  updateMatrix(){ this.matrix = composeTRS(this.position, this.rotation, this.scale); return this; }
  updateWorldMatrix(){ this.updateMatrixWorld(); return this; }
  applyMatrix4(){ return this; }
  localToWorld(v){ return v; }
  worldToLocal(v){ return v; }
  getWorldQuaternion(q){ return q||new Quaternion(); }
  getWorldScale(v){ v=v||new Vector3(); return v.copy(this.scale); }
  getWorldDirection(v){ v=v||new Vector3(); return v.set(0,0,-1); }
  attach(o){ return this.add(o); }
  translateX(d){ this.position.x+=d; return this; }
  translateY(d){ this.position.y+=d; return this; }
  translateZ(d){ this.position.z+=d; return this; }
  rotateX(a){ this.rotation.x+=a; return this; }
  rotateY(a){ this.rotation.y+=a; return this; }
  rotateZ(a){ this.rotation.z+=a; return this; }
  rotateOnAxis(){ return this; }
  setRotationFromAxisAngle(){ return this; }
  setRotationFromEuler(e){ this.rotation.copy(e); return this; }
  addEventListener(){} removeEventListener(){} dispatchEvent(){}
  clone(){
    const o = new this.constructor(this.geometry, this.material);
    o.position.copy(this.position); o.rotation.copy(this.rotation); o.scale.copy(this.scale);
    o.userData = Object.assign({}, this.userData);
    for(const c of this.children) o.add(c.clone());
    return o;
  }
}
class Scene extends Object3D { constructor(){ super(); this.fog=null; this.background=null; } }
class Group extends Object3D {}
class Mesh extends Object3D {
  constructor(geometry, material){ super(); this.geometry=geometry||new BufferGeometry(); this.material=material||{}; this.isMesh=true; }
  raycast(){}
}
class InstancedMesh extends Mesh {
  constructor(geometry, material, count){ super(geometry, material); this.count=count||0; this.instanceMatrix={needsUpdate:false}; this.isInstancedMesh=true; }
  setMatrixAt(){} getMatrixAt(){} setColorAt(){}
}
class Sprite extends Object3D { constructor(material){ super(); this.material=material||{}; this.isSprite=true; } raycast(){} }
class Points extends Object3D { constructor(g,m){ super(); this.geometry=g; this.material=m; } }
class Line extends Object3D { constructor(g,m){ super(); this.geometry=g; this.material=m; } }
class LineSegments extends Line {}

// ---------- materials / textures / lights ----------
class Material { constructor(p){ Object.assign(this, p||{}); this.color = new Color((p&&p.color)!==undefined?p.color:0xffffff); } dispose(){} clone(){ return new this.constructor(Object.assign({},this)); } }
class MeshBasicMaterial extends Material {}
class MeshLambertMaterial extends Material {}
class MeshPhongMaterial extends Material {}
class MeshStandardMaterial extends Material {}
class SpriteMaterial extends Material {}
class PointsMaterial extends Material {}
class LineBasicMaterial extends Material {}
class LineDashedMaterial extends Material {}
class MeshNormalMaterial extends Material {}
class MeshDepthMaterial extends Material {}
class MeshMatcapMaterial extends Material {}
class MeshToonMaterial extends Material {}
class MeshPhysicalMaterial extends Material {}
class ShaderMaterial extends Material {}
class RawShaderMaterial extends Material {}
class ShadowMaterial extends Material {}
class Color {
  constructor(c){ this.r=1; this.g=1; this.b=1; if(c!==undefined) this.set(c); }
  set(c){ if(typeof c==='number'){ this.r=((c>>16)&255)/255; this.g=((c>>8)&255)/255; this.b=(c&255)/255; } return this; }
  getHex(){
    const q = v => Math.max(0, Math.min(255, Math.round(v*255)));
    return (q(this.r)<<16) | (q(this.g)<<8) | q(this.b);
  }
  getHexString(){ return this.getHex().toString(16).padStart(6,'0'); }
  getStyle(){ return '#'+this.getHexString(); }
  multiplyScalar(s){ this.r*=s; this.g*=s; this.b*=s; return this; }
  multiply(c){ this.r*=c.r; this.g*=c.g; this.b*=c.b; return this; }
  addScalar(s){ this.r+=s; this.g+=s; this.b+=s; return this; }
  setRGB(r,g,b){ this.r=r; this.g=g; this.b=b; return this; }
  setHex(h){ return this.set(h); }
  offsetHSL(){ return this; }
  clone(){ const c=new Color(); c.r=this.r;c.g=this.g;c.b=this.b; return c; }
  copy(c){ this.r=c.r;this.g=c.g;this.b=c.b; return this; }
  lerp(){ return this; }
}
class Texture { constructor(){ this.wrapS=0; this.wrapT=0; this.repeat={set(){}}; this.offset={set(){}}; this.anisotropy=1; this.needsUpdate=false; } dispose(){} clone(){ return new Texture(); } }
class CanvasTexture extends Texture { constructor(c){ super(); this.image=c; } }
class Light extends Object3D { constructor(color,intensity){ super(); this.color=new Color(color); this.intensity=intensity; this.shadow={mapSize:{width:0,height:0,set(){}},camera:{}}; } }
class AmbientLight extends Light {}
class HemisphereLight extends Light {}
class PointLight extends Light { constructor(c,i,d){ super(c,i); this.distance=d; } }
class DirectionalLight extends Light {
  constructor(c,i){ super(c,i); this.target = new Object3D(); }   // real three.js exposes .target
}
class SpotLight extends Light {
  constructor(c,i){ super(c,i); this.target = new Object3D(); }
}
class Fog { constructor(c,n,f){ this.color=new Color(c); this.near=n; this.far=f; } }
class FogExp2 { constructor(c,d){ this.color=new Color(c); this.density=d; } }
class PerspectiveCamera extends Object3D {
  constructor(fov,aspect,near,far){ super(); this.fov=fov; this.aspect=aspect; this.near=near; this.far=far; }
  updateProjectionMatrix(){}
  getWorldDirection(v){ v=v||new Vector3(); return v.set(0,0,-1); }
}
class WebGLRenderer {
  constructor(){ this.domElement={ style:{}, addEventListener(){}, requestPointerLock(){}, getBoundingClientRect(){return{left:0,top:0,width:800,height:600};} };
    this.shadowMap={enabled:false,type:0};
    this.capabilities={ getMaxAnisotropy(){ return 16; } };
  }
  setSize(){} setPixelRatio(){} render(){} setClearColor(){} dispose(){}
}
class Raycaster {
  constructor(){ this.ray={origin:new Vector3(),direction:new Vector3()}; this.far=Infinity; this.near=0; }
  set(){} setFromCamera(){} intersectObject(){ return []; } intersectObjects(){ return []; }
}
class Clock { constructor(){ this._t=0; } getDelta(){ return 0.016; } getElapsedTime(){ return this._t+=0.016; } }
// Real enough for setFromObject(), which is what the game uses it for (measuring an actor's
// footprint in spawnBot). Leans on __meshWorldBox below so it agrees with the audit helpers.
class Box3 {
  constructor(min, max){
    this.min = min || new Vector3( Infinity,  Infinity,  Infinity);
    this.max = max || new Vector3(-Infinity, -Infinity, -Infinity);
  }
  makeEmpty(){ this.min.set(Infinity,Infinity,Infinity); this.max.set(-Infinity,-Infinity,-Infinity); return this; }
  isEmpty(){ return this.max.x < this.min.x || this.max.y < this.min.y || this.max.z < this.min.z; }
  expandByPoint(p){
    this.min.x=Math.min(this.min.x,p.x); this.min.y=Math.min(this.min.y,p.y); this.min.z=Math.min(this.min.z,p.z);
    this.max.x=Math.max(this.max.x,p.x); this.max.y=Math.max(this.max.y,p.y); this.max.z=Math.max(this.max.z,p.z);
    return this;
  }
  setFromObject(root){
    this.makeEmpty();
    root.updateMatrixWorld();
    root.traverse(o=>{
      if(o.isMesh){
        const b = global.__meshWorldBox(o);
        this.expandByPoint(b.min); this.expandByPoint(b.max);
      } else if(o.isSprite){
        // real three.js gives a Sprite a 1x1 plane geometry, so setFromObject() counts it. The audit
        // helpers (__modelBounds etc.) deliberately look at meshes only, but Box3 is what the GAME calls
        // to measure an enemy's collision radius -- if this ignored sprites, the harness would disagree
        // with the browser about how wide every enemy is.
        const m = o.matrixWorld, sx = o.scale.x/2, sy = o.scale.y/2;
        const p = applyMat(m, 0, 0, 0);
        this.expandByPoint({x:p.x-sx, y:p.y-sy, z:p.z-sx});
        this.expandByPoint({x:p.x+sx, y:p.y+sy, z:p.z+sx});
      }
    });
    return this;
  }
  getSize(t){ const v = t || new Vector3();
    v.set(this.max.x-this.min.x, this.max.y-this.min.y, this.max.z-this.min.z); return v; }
  getCenter(t){ const v = t || new Vector3();
    v.set((this.min.x+this.max.x)/2, (this.min.y+this.max.y)/2, (this.min.z+this.max.z)/2); return v; }
}

const THREE = {
  Scene, Group, Mesh, InstancedMesh, Sprite, Points, Line, LineSegments, Object3D,
  BufferGeometry, BoxGeometry, CylinderGeometry, ConeGeometry, SphereGeometry,
  PlaneGeometry, CircleGeometry, RingGeometry, TorusGeometry, LatheGeometry,
  PolyhedronGeometry, TetrahedronGeometry, OctahedronGeometry, DodecahedronGeometry,
  IcosahedronGeometry, TubeGeometry, ExtrudeGeometry, ShapeGeometry,
  EdgesGeometry, WireframeGeometry, Shape, Path, CatmullRomCurve3, Matrix4,
  Material, MeshBasicMaterial, MeshLambertMaterial, MeshPhongMaterial, MeshStandardMaterial,
  SpriteMaterial, PointsMaterial, LineBasicMaterial, LineDashedMaterial,
  MeshNormalMaterial, MeshDepthMaterial, MeshMatcapMaterial, MeshToonMaterial,
  MeshPhysicalMaterial, ShaderMaterial, RawShaderMaterial, ShadowMaterial,
  Color, Texture, CanvasTexture, Vector3, Vector2: Vector3, Euler, Quaternion,
  AmbientLight, HemisphereLight, PointLight, DirectionalLight, SpotLight,
  Fog, FogExp2, PerspectiveCamera, WebGLRenderer, Raycaster, Clock, Box3,
  BufferAttribute: BufferAttribute,
  Float32BufferAttribute: BufferAttribute,
  Uint16BufferAttribute: BufferAttribute,
  Uint32BufferAttribute: BufferAttribute,
  InstancedBufferAttribute: BufferAttribute,
  TextureLoader: function(){ return { load(){ return new Texture(); } }; },
  NearestFilter:1003, LinearFilter:1006,
  NearestMipmapNearestFilter:1004, NearestMipmapLinearFilter:1005,
  LinearMipmapNearestFilter:1007, LinearMipmapLinearFilter:1008,
  RepeatWrapping:1000, ClampToEdgeWrapping:1001, MirroredRepeatWrapping:1002,
  FrontSide:0, BackSide:1, DoubleSide:2,
  PCFSoftShadowMap:2, BasicShadowMap:0, PCFShadowMap:1,
  sRGBEncoding:3001, AdditiveBlending:2, NormalBlending:1,
  MathUtils:{ degToRad:d=>d*Math.PI/180, radToDeg:r=>r*180/Math.PI, clamp:(v,a,b)=>Math.max(a,Math.min(b,v)), lerp:(a,b,t)=>a+(b-a)*t },
};

// ---------- DOM stub ----------
function makeCtx(){
  const noop = ()=>{};
  return {
    canvas:null,
    fillStyle:'#000', strokeStyle:'#000', lineWidth:1, globalAlpha:1, font:'10px sans-serif',
    textAlign:'left', textBaseline:'alphabetic', shadowBlur:0, shadowColor:'#000',
    lineCap:'butt', lineJoin:'miter', globalCompositeOperation:'source-over',
    fillRect:noop, strokeRect:noop, clearRect:noop, beginPath:noop, closePath:noop,
    moveTo:noop, lineTo:noop, arc:noop, arcTo:noop, ellipse:noop, rect:noop,
    fill:noop, stroke:noop, save:noop, restore:noop, translate:noop, rotate:noop,
    scale:noop, transform:noop, setTransform:noop, clip:noop, drawImage:noop,
    fillText:noop, strokeText:noop, quadraticCurveTo:noop, bezierCurveTo:noop,
    measureText:()=>({width:10}),
    createLinearGradient:()=>({addColorStop:noop}),
    createRadialGradient:()=>({addColorStop:noop}),
    createPattern:()=>({}),
    getImageData:(x,y,w,h)=>({data:new Uint8ClampedArray(Math.max(1,w*h*4)),width:w,height:h}),
    putImageData:noop, createImageData:(w,h)=>({data:new Uint8ClampedArray(Math.max(1,w*h*4)),width:w,height:h}),
  };
}
function makeElement(tag){
  const el = {
    tagName:(tag||'div').toUpperCase(), style:{}, dataset:{}, children:[], width:0, height:0,
    textContent:'', innerHTML:'', value:'', checked:false, id:'',
    classList:{ _s:new Set(), add(...c){c.forEach(x=>this._s.add(x));}, remove(...c){c.forEach(x=>this._s.delete(x));},
                toggle(c){ this._s.has(c)?this._s.delete(c):this._s.add(c); }, contains(c){ return this._s.has(c); } },
    appendChild(c){ this.children.push(c); return c; },
    removeChild(c){ const i=this.children.indexOf(c); if(i>=0) this.children.splice(i,1); return c; },
    addEventListener(){}, removeEventListener(){}, dispatchEvent(){ return true; },
    setAttribute(){}, getAttribute(){ return null; }, removeAttribute(){},
    focus(){}, blur(){}, click(){}, remove(){},
    requestPointerLock(){}, getBoundingClientRect(){ return {left:0,top:0,right:800,bottom:600,width:800,height:600}; },
    querySelector(){ return makeElement('div'); }, querySelectorAll(){ return []; },
  };
  if((tag||'').toLowerCase()==='canvas'){
    const ctx = makeCtx(); ctx.canvas = el;
    el.getContext = ()=>ctx;
    el.toDataURL = ()=>'data:image/png;base64,';
  }
  return el;
}
const _byId = {};
const document = {
  createElement: makeElement,
  createElementNS: (ns,t)=>makeElement(t),
  getElementById(id){ if(!_byId[id]){ _byId[id]=makeElement('div'); _byId[id].id=id; } return _byId[id]; },
  querySelector(){ return makeElement('div'); },
  querySelectorAll(){ return []; },
  // Listeners are RECORDED, not dropped. A no-op addEventListener makes every keyboard-driven bug
  // untestable -- the [J] debug jump was one, and the only honest way to test it is to fire the real
  // keydown handler the game registered. __fire() below is how a harness does that.
  _listeners: {},
  addEventListener(type, fn){ (this._listeners[type] = this._listeners[type] || []).push(fn); },
  removeEventListener(type, fn){
    const a = this._listeners[type]; if(!a) return;
    const i = a.indexOf(fn); if(i >= 0) a.splice(i, 1);
  },
  dispatchEvent(ev){ (this._listeners[ev && ev.type] || []).forEach(fn=>fn(ev)); return true; },
  body: makeElement('body'),
  documentElement: makeElement('html'),
  head: makeElement('head'),
  exitPointerLock(){},
  pointerLockElement: null,
  hidden: false,
};
// Fire a real DOM-ish event at the document's registered handlers.
//   __fire('keydown', {code:'KeyJ'})
global.__fire = function(type, props){
  const ev = Object.assign({type:type, preventDefault(){}, stopPropagation(){},
                            repeat:false, shiftKey:false, ctrlKey:false, altKey:false, metaKey:false},
                           props||{});
  document.dispatchEvent(ev);
  return ev;
};
document.body.requestPointerLock = ()=>{};

class AudioParamStub { constructor(){ this.value=0; } setValueAtTime(){return this;} linearRampToValueAtTime(){return this;} exponentialRampToValueAtTime(){return this;} setTargetAtTime(){return this;} cancelScheduledValues(){return this;} }
function audioNode(extra){
  return Object.assign({
    connect(){ return this; }, disconnect(){}, start(){}, stop(){},
    frequency:new AudioParamStub(), detune:new AudioParamStub(), gain:new AudioParamStub(),
    Q:new AudioParamStub(), type:'sine', buffer:null, loop:false, playbackRate:new AudioParamStub(),
    onended:null,
  }, extra||{});
}
class AudioContextStub {
  constructor(){ this.currentTime=0; this.sampleRate=44100; this.state='running';
    this.destination=audioNode(); this.listener={ setPosition(){}, setOrientation(){} }; }
  createOscillator(){ return audioNode(); }
  createGain(){ return audioNode(); }
  createBiquadFilter(){ return audioNode(); }
  createBufferSource(){ return audioNode(); }
  createBuffer(ch,len,rate){ return { getChannelData:()=>new Float32Array(Math.max(1,len)), length:len, sampleRate:rate, numberOfChannels:ch }; }
  createDynamicsCompressor(){ return audioNode({threshold:new AudioParamStub(),knee:new AudioParamStub(),ratio:new AudioParamStub(),attack:new AudioParamStub(),release:new AudioParamStub()}); }
  createStereoPanner(){ return audioNode({pan:new AudioParamStub()}); }
  createWaveShaper(){ return audioNode({curve:null,oversample:'none'}); }
  createConvolver(){ return audioNode(); }
  // startGame() builds the audio graph, so a missing node type here makes the whole real start path
  // untestable -- which is how the campaign went unexercised end to end for so long.
  createDelay(){ return audioNode({delayTime:new AudioParamStub()}); }
  createChannelSplitter(){ return audioNode(); }
  createChannelMerger(){ return audioNode(); }
  createPanner(){ return audioNode({positionX:new AudioParamStub(),positionY:new AudioParamStub(),
                                    positionZ:new AudioParamStub(),setPosition(){},setOrientation(){}}); }
  createConstantSource(){ return audioNode({offset:new AudioParamStub()}); }
  decodeAudioData(){ return Promise.resolve(this.createBuffer(1,1,44100)); }
  createAnalyser(){ return audioNode({fftSize:2048,frequencyBinCount:1024,getByteFrequencyData(){},getByteTimeDomainData(){}}); }
  resume(){ return Promise.resolve(); }
  close(){ return Promise.resolve(); }
}

const windowStub = {
  innerWidth:1280, innerHeight:720, devicePixelRatio:1,
  addEventListener(){}, removeEventListener(){},
  requestAnimationFrame(){ return 0; },   // never fires: animate() runs at most once
  cancelAnimationFrame(){},
  setTimeout(){ return 0; }, clearTimeout(){}, setInterval(){ return 0; }, clearInterval(){},
  localStorage:{ _d:{}, getItem(k){ return this._d[k]!==undefined?this._d[k]:null; }, setItem(k,v){ this._d[k]=String(v); }, removeItem(k){ delete this._d[k]; }, clear(){ this._d={}; } },
  navigator:{ userAgent:'headless', maxTouchPoints:0, vibrate(){} },
  location:{ href:'http://localhost/', search:'', hash:'' },
  matchMedia(){ return { matches:false, addEventListener(){}, removeEventListener(){}, addListener(){}, removeListener(){} }; },
  performance:{ now(){ return 0; } },
  AudioContext: AudioContextStub,
  webkitAudioContext: AudioContextStub,
  document,
  THREE,
};
windowStub.window = windowStub;
windowStub.self = windowStub;
windowStub.globalThis = windowStub;

// export onto the V8 global
global.THREE = THREE;
global.document = document;
global.window = windowStub;
global.self = windowStub;
global.navigator = windowStub.navigator;
global.location = windowStub.location;
global.localStorage = windowStub.localStorage;
global.performance = windowStub.performance;
global.innerWidth = windowStub.innerWidth;
global.innerHeight = windowStub.innerHeight;
global.devicePixelRatio = 1;
global.AudioContext = AudioContextStub;
global.webkitAudioContext = AudioContextStub;
global.requestAnimationFrame = function(){ return 0; };
global.cancelAnimationFrame = function(){};
global.setTimeout = function(){ return 0; };
global.clearTimeout = function(){};
global.setInterval = function(){ return 0; };
global.clearInterval = function(){};
global.addEventListener = function(){};
global.removeEventListener = function(){};
global.matchMedia = windowStub.matchMedia;
global.alert = function(){};
global.confirm = function(){ return true; };

// ---------- audit helpers, used by the assertions ----------
// World-space AABB of a single mesh, accounting for its own rotation.
global.__meshWorldBox = function(mesh){
  const h = mesh.geometry && mesh.geometry._half ? mesh.geometry._half : {x:0,y:0,z:0};
  const off = mesh.geometry && mesh.geometry._offset ? mesh.geometry._offset : {x:0,y:0,z:0};
  const m = mesh.matrixWorld;
  let min={x:Infinity,y:Infinity,z:Infinity}, max={x:-Infinity,y:-Infinity,z:-Infinity};
  for(let i=0;i<8;i++){
    const p = applyMat(m,
      off.x + (i&1 ? h.x : -h.x),
      off.y + (i&2 ? h.y : -h.y),
      off.z + (i&4 ? h.z : -h.z));
    min.x=Math.min(min.x,p.x); min.y=Math.min(min.y,p.y); min.z=Math.min(min.z,p.z);
    max.x=Math.max(max.x,p.x); max.y=Math.max(max.y,p.y); max.z=Math.max(max.z,p.z);
  }
  return {min,max};
};

// Every mesh in a model, as world-space AABBs. `scale` mimics spawnBot()'s bot.scale.setScalar().
global.__modelBoxes = function(root, scale){
  root.scale.setScalar(scale===undefined?1:scale);
  root.updateMatrixWorld();
  const out=[];
  root.traverse(o=>{ if(o.isMesh) out.push({mesh:o, box:global.__meshWorldBox(o)}); });
  return out;
};

global.__modelBounds = function(root, scale){
  const boxes = global.__modelBoxes(root, scale);
  const min={x:Infinity,y:Infinity,z:Infinity}, max={x:-Infinity,y:-Infinity,z:-Infinity};
  for(const b of boxes){
    min.x=Math.min(min.x,b.box.min.x); min.y=Math.min(min.y,b.box.min.y); min.z=Math.min(min.z,b.box.min.z);
    max.x=Math.max(max.x,b.box.max.x); max.y=Math.max(max.y,b.box.max.y); max.z=Math.max(max.z,b.box.max.z);
  }
  return {min,max,count:boxes.length};
};


// ---------- oriented-box helpers (connectivity uses these, NOT the AABBs) ----------
// A rotated box's AABB is much larger than the box itself, so testing AABB overlap wrongly reports two
// rotated-and-separated pieces as touching. That is exactly the case that matters here: chained runs of
// rotated segments. These helpers test the real oriented boxes instead.
function matInvert(m){
  const inv = new Array(16);
  inv[0]  =  m[5]*m[10]*m[15] - m[5]*m[11]*m[14] - m[9]*m[6]*m[15] + m[9]*m[7]*m[14] + m[13]*m[6]*m[11] - m[13]*m[7]*m[10];
  inv[4]  = -m[4]*m[10]*m[15] + m[4]*m[11]*m[14] + m[8]*m[6]*m[15] - m[8]*m[7]*m[14] - m[12]*m[6]*m[11] + m[12]*m[7]*m[10];
  inv[8]  =  m[4]*m[9]*m[15]  - m[4]*m[11]*m[13] - m[8]*m[5]*m[15] + m[8]*m[7]*m[13] + m[12]*m[5]*m[11] - m[12]*m[7]*m[9];
  inv[12] = -m[4]*m[9]*m[14]  + m[4]*m[10]*m[13] + m[8]*m[5]*m[14] - m[8]*m[6]*m[13] - m[12]*m[5]*m[10] + m[12]*m[6]*m[9];
  inv[1]  = -m[1]*m[10]*m[15] + m[1]*m[11]*m[14] + m[9]*m[2]*m[15] - m[9]*m[3]*m[14] - m[13]*m[2]*m[11] + m[13]*m[3]*m[10];
  inv[5]  =  m[0]*m[10]*m[15] - m[0]*m[11]*m[14] - m[8]*m[2]*m[15] + m[8]*m[3]*m[14] + m[12]*m[2]*m[11] - m[12]*m[3]*m[10];
  inv[9]  = -m[0]*m[9]*m[15]  + m[0]*m[11]*m[13] + m[8]*m[1]*m[15] - m[8]*m[3]*m[13] - m[12]*m[1]*m[11] + m[12]*m[3]*m[9];
  inv[13] =  m[0]*m[9]*m[14]  - m[0]*m[10]*m[13] - m[8]*m[1]*m[14] + m[8]*m[2]*m[13] + m[12]*m[1]*m[10] - m[12]*m[2]*m[9];
  inv[2]  =  m[1]*m[6]*m[15]  - m[1]*m[7]*m[14]  - m[5]*m[2]*m[15] + m[5]*m[3]*m[14] + m[13]*m[2]*m[7]  - m[13]*m[3]*m[6];
  inv[6]  = -m[0]*m[6]*m[15]  + m[0]*m[7]*m[14]  + m[4]*m[2]*m[15] - m[4]*m[3]*m[14] - m[12]*m[2]*m[7]  + m[12]*m[3]*m[6];
  inv[10] =  m[0]*m[5]*m[15]  - m[0]*m[7]*m[13]  - m[4]*m[1]*m[15] + m[4]*m[3]*m[13] + m[12]*m[1]*m[7]  - m[12]*m[3]*m[5];
  inv[14] = -m[0]*m[5]*m[14]  + m[0]*m[6]*m[13]  + m[4]*m[1]*m[14] - m[4]*m[2]*m[13] - m[12]*m[1]*m[6]  + m[12]*m[2]*m[5];
  inv[3]  = -m[1]*m[6]*m[11]  + m[1]*m[7]*m[10]  + m[5]*m[2]*m[11] - m[5]*m[3]*m[10] - m[9]*m[2]*m[7]   + m[9]*m[3]*m[6];
  inv[7]  =  m[0]*m[6]*m[11]  - m[0]*m[7]*m[10]  - m[4]*m[2]*m[11] + m[4]*m[3]*m[10] + m[8]*m[2]*m[7]   - m[8]*m[3]*m[6];
  inv[11] = -m[0]*m[5]*m[11]  + m[0]*m[7]*m[9]   + m[4]*m[1]*m[11] - m[4]*m[3]*m[9]  - m[8]*m[1]*m[7]   + m[8]*m[3]*m[5];
  inv[15] =  m[0]*m[5]*m[10]  - m[0]*m[6]*m[9]   - m[4]*m[1]*m[10] + m[4]*m[2]*m[9]  + m[8]*m[1]*m[6]   - m[8]*m[2]*m[5];
  let det = m[0]*inv[0] + m[1]*inv[4] + m[2]*inv[8] + m[3]*inv[12];
  if(Math.abs(det) < 1e-12) return null;
  det = 1.0/det;
  for(let i=0;i<16;i++) inv[i] *= det;
  return inv;
}

// World-space sample points on a mesh's real (oriented) box: 8 corners, 6 face centres, 1 centre.
global.__meshSamples = function(mesh){
  const h = mesh.geometry && mesh.geometry._half ? mesh.geometry._half : {x:0,y:0,z:0};
  const o = mesh.geometry && mesh.geometry._offset ? mesh.geometry._offset : {x:0,y:0,z:0};
  const m = mesh.matrixWorld, pts = [];
  const push = (a,b,c)=>{ pts.push(applyMat(m, o.x+a*h.x, o.y+b*h.y, o.z+c*h.z)); };
  for(let i=-1;i<=1;i+=2) for(let j=-1;j<=1;j+=2) for(let k=-1;k<=1;k+=2) push(i,j,k);
  push(0,0,0); push(1,0,0); push(-1,0,0); push(0,1,0); push(0,-1,0); push(0,0,1); push(0,0,-1);
  return pts;
};

// Is a world point inside a mesh's real oriented box (with a small tolerance)?
global.__pointInMesh = function(mesh, p, eps){
  const inv = matInvert(mesh.matrixWorld);
  if(!inv) return false;
  const h = mesh.geometry && mesh.geometry._half ? mesh.geometry._half : {x:0,y:0,z:0};
  const o = mesh.geometry && mesh.geometry._offset ? mesh.geometry._offset : {x:0,y:0,z:0};
  const q = applyMat(inv, p.x, p.y, p.z);
  return Math.abs(q.x-o.x) <= h.x+eps && Math.abs(q.y-o.y) <= h.y+eps && Math.abs(q.z-o.z) <= h.z+eps;
};

// ---------- orientation gating for the coplanarity checks ----------
// Two boxes can only produce the coincident-plane flicker this check hunts for if their FACES are
// parallel — that is, if their world bases are the same up to permutation and sign. Where they are not,
// the faces meet at an angle and can never fight, no matter how close they come.
//
// This matters because the check compares AABBs, and a rotated box's AABB faces are not its own faces. A
// wing membrane sagging at one angle beside a finger bone at another would report as z-fighting purely
// because their bounding boxes happened to end at the same coordinate. Everything below either compares
// two genuinely world-axis-aligned boxes (where the AABB IS the box), or re-expresses a same-orientation
// pair in that shared frame first, where their faces are axis-aligned again.
function refFrame(mesh){
  const m=mesh.matrixWorld;
  const a=[m[0],m[1],m[2]], b=[m[4],m[5],m[6]], c=[m[8],m[9],m[10]];
  const na=Math.hypot(a[0],a[1],a[2])||1, nb=Math.hypot(b[0],b[1],b[2])||1, nc=Math.hypot(c[0],c[1],c[2])||1;
  return [[a[0]/na,a[1]/na,a[2]/na],[b[0]/nb,b[1]/nb,b[2]/nb],[c[0]/nc,c[1]/nc,c[2]/nc]];
}
function isAxisAligned(mesh){
  const F=refFrame(mesh);
  for(const v of F){
    let ok=false;
    for(let k=0;k<3;k++) if(Math.abs(Math.abs(v[k])-1) < 1e-4) ok=true;
    if(!ok) return false;
  }
  return true;
}
// permutation- and sign-invariant, so a box turned 90 degrees about Y still matches one that is not
function orientKey(mesh){
  return refFrame(mesh).map(v=>{
    let s=1;
    for(let k=0;k<3;k++){ if(Math.abs(v[k])>1e-6){ s = v[k]<0 ? -1 : 1; break; } }
    return v.map(x=>Math.round(x*s*1024)).join(',');
  }).sort().join('|');
}
// a mesh's box expressed in some reference frame's axes, in world-scale units
function frameBox(mesh, F){
  const h=(mesh.geometry&&mesh.geometry._half)||{x:0,y:0,z:0};
  const o=(mesh.geometry&&mesh.geometry._offset)||{x:0,y:0,z:0};
  const m=mesh.matrixWorld;
  const c=applyMat(m,o.x,o.y,o.z);
  const sx=Math.hypot(m[0],m[1],m[2]), sy=Math.hypot(m[4],m[5],m[6]), sz=Math.hypot(m[8],m[9],m[10]);
  const p={x:c.x*F[0][0]+c.y*F[0][1]+c.z*F[0][2],
           y:c.x*F[1][0]+c.y*F[1][1]+c.z*F[1][2],
           z:c.x*F[2][0]+c.y*F[2][1]+c.z*F[2][2]};
  const hx=h.x*sx, hy=h.y*sy, hz=h.z*sz;
  return {min:{x:p.x-hx,y:p.y-hy,z:p.z-hz}, max:{x:p.x+hx,y:p.y+hy,z:p.z+hz}};
}
// The comparable pair of boxes for a coplanarity test, or null when the two can never share a face plane.
// Geometries whose bounding-box faces are not surfaces of the mesh at all. A LatheGeometry ring is hollow,
// so its AABB is a solid block filling the whole arena and every object standing inside it reports as
// sharing that block's floor plane. A torus and a sphere touch their AABB at a point or a line, never over
// an area. Comparing AABB faces only says anything for shapes that actually HAVE a flat face there: boxes
// always do, and a cylinder or cone does on its cap axis.
const NON_PLANAR = {LatheGeometry:1, TorusGeometry:1, SphereGeometry:1};

global.__comparableBoxes = function(meshA, boxA, meshB, boxB){
  const ta = meshA.geometry && meshA.geometry.type, tb = meshB.geometry && meshB.geometry.type;
  if(NON_PLANAR[ta] || NON_PLANAR[tb]) return null;
  if(isAxisAligned(meshA) && isAxisAligned(meshB)) return [boxA, boxB];
  if(orientKey(meshA) !== orientKey(meshB)) return null;
  const F = refFrame(meshA);
  return [frameBox(meshA,F), frameBox(meshB,F)];
};

// Meshes that genuinely intersect: at least one of A's surface samples lies inside B, or vice versa.
global.__connectivity = function(root, scale, eps){
  const boxes = global.__modelBoxes(root, scale);
  const meshes = boxes.map(b=>b.mesh);
  const samples = meshes.map(m=>global.__meshSamples(m));
  const orphans = [];
  for(let i=0;i<meshes.length;i++){
    let hit=false;
    for(let j=0;j<meshes.length && !hit;j++){
      if(i===j) continue;
      // cheap AABB reject first, then the real oriented test
      const a=boxes[i].box, c=boxes[j].box;
      if(a.min.x>c.max.x+eps||c.min.x>a.max.x+eps||a.min.y>c.max.y+eps||
         c.min.y>a.max.y+eps||a.min.z>c.max.z+eps||c.min.z>a.max.z+eps) continue;
      for(const p of samples[i]) if(global.__pointInMesh(meshes[j], p, eps)){ hit=true; break; }
      if(!hit) for(const p of samples[j]) if(global.__pointInMesh(meshes[i], p, eps)){ hit=true; break; }
    }
    if(!hit) orphans.push({y:Math.round(boxes[i].box.min.y*1000)/1000, type:meshes[i].geometry.type});
  }
  return {orphans:orphans, total:meshes.length, detail:orphans.slice(0,6)};
};


// Near-coplanar face pairs: two boxes that overlap substantially in two axes and whose faces sit within
// eps on the third will fight for the same pixels in the depth buffer. This is the single most recurring
// visual bug in this project, so it is checked automatically.
global.__coplanar = function(root, scale, eps, omin){
  const boxes = global.__modelBoxes(root, scale);
  const AX = ['x','y','z'];
  const hits = [];
  for(let i=0;i<boxes.length;i++) for(let j=i+1;j<boxes.length;j++){
    const cmp = global.__comparableBoxes(boxes[i].mesh, boxes[i].box, boxes[j].mesh, boxes[j].box);
    if(!cmp) continue;              // faces meet at an angle — cannot fight, whatever the AABBs say
    const a = cmp[0], c = cmp[1];
    for(let k=0;k<3;k++){
      const ax=AX[k], u=AX[(k+1)%3], v=AX[(k+2)%3];
      const ou = Math.min(a.max[u],c.max[u]) - Math.max(a.min[u],c.min[u]);
      const ov = Math.min(a.max[v],c.max[v]) - Math.max(a.min[v],c.min[v]);
      if(ou < omin || ov < omin) continue;
      // the two boxes must actually interpenetrate on this axis, else they are merely stacked
      const oa = Math.min(a.max[ax],c.max[ax]) - Math.max(a.min[ax],c.min[ax]);
      if(oa <= 0) continue;
      const pairs = [[a.min[ax],c.min[ax]],[a.max[ax],c.max[ax]]];
      for(const [p,q] of pairs){
        const d = Math.abs(p-q);
        // d === 0 counts. Two faces at EXACTLY the same coordinate are the worst case there is — the depth
        // buffer has nothing at all to separate them and the flicker is total — and this check used to skip
        // them, requiring d > 1e-9. That hole is why a 14-cube mane ring sharing one front plane with the
        // mass behind it, and a crown circlet sharing its underside with a brow ridge, both passed.
        if(d < eps){
          hits.push({axis:ax, gap:Math.round(d*10000)/10000,
                     y:Math.round(a.min.y*1000)/1000,
                     ta:boxes[i].mesh.geometry.type, tb:boxes[j].mesh.geometry.type});
        }
      }
    }
  }
  return hits;
};


// ---- whole-world sweeps. These run over thousands of meshes, so both use a uniform grid hash to avoid
// the O(n^2) all-pairs comparison. ----
global.__worldBoxes = function(group){
  group.updateMatrixWorld();
  const out = [];
  group.traverse(o=>{ if(o.isMesh) out.push({mesh:o, box:global.__meshWorldBox(o)}); });
  return out;
};

// Near-coplanar face pairs across a whole map. Same rule as the per-model check: two boxes overlapping
// substantially in two axes whose faces sit within eps on the third will fight in the depth buffer.
global.__worldCoplanar = function(group, eps, omin, cell){
  const boxes = global.__worldBoxes(group);
  cell = cell || 4;
  const grid = new Map();
  const key = (i,j,k)=> i+','+j+','+k;
  boxes.forEach((b,idx)=>{
    // A material with polygonOffset set is DELIBERATELY coplanar with what it lies on — paths on roads,
    // plazas on ground. The depth bias is the fix, so flagging them is noise.
    const mt = b.mesh.material;
    if(mt && mt.polygonOffset) return;
    const i0=Math.floor(b.box.min.x/cell), i1=Math.floor(b.box.max.x/cell);
    const j0=Math.floor(b.box.min.y/cell), j1=Math.floor(b.box.max.y/cell);
    const k0=Math.floor(b.box.min.z/cell), k1=Math.floor(b.box.max.z/cell);
    // skip enormous meshes (ground slabs, backing planes): they touch every cell and everything is
    // legitimately coplanar with a floor
    if((i1-i0)>12 || (j1-j0)>12 || (k1-k0)>12) return;
    for(let i=i0;i<=i1;i++) for(let j=j0;j<=j1;j++) for(let k=k0;k<=k1;k++){
      const s=key(i,j,k); if(!grid.has(s)) grid.set(s,[]); grid.get(s).push(idx);
    }
  });
  const AX=['x','y','z'];
  const seen=new Set(); const hits=[];
  for(const bucket of grid.values()){
    for(let a=0;a<bucket.length;a++) for(let b=a+1;b<bucket.length;b++){
      const ia=bucket[a], ib=bucket[b];
      const pk = ia<ib ? ia+':'+ib : ib+':'+ia;
      if(seen.has(pk)) continue; seen.add(pk);
      const cmp = global.__comparableBoxes(boxes[ia].mesh, boxes[ia].box, boxes[ib].mesh, boxes[ib].box);
      if(!cmp) continue;
      const A=cmp[0], B=cmp[1];
      for(let k=0;k<3;k++){
        const ax=AX[k], u=AX[(k+1)%3], v=AX[(k+2)%3];
        const ou=Math.min(A.max[u],B.max[u])-Math.max(A.min[u],B.min[u]);
        const ov=Math.min(A.max[v],B.max[v])-Math.max(A.min[v],B.min[v]);
        if(ou<omin||ov<omin) continue;
        const oa=Math.min(A.max[ax],B.max[ax])-Math.max(A.min[ax],B.min[ax]);
        if(oa<=0) continue;
        for(const [pp,qq] of [[A.min[ax],B.min[ax]],[A.max[ax],B.max[ax]]]){
          const d=Math.abs(pp-qq);
          if(d<eps){                     // d === 0 counts — see the note in __coplanar
            hits.push({axis:ax, gap:Math.round(d*10000)/10000,
                       x:Math.round((A.min.x+A.max.x)/2*10)/10,
                       y:Math.round((A.min.y+A.max.y)/2*10)/10,
                       z:Math.round((A.min.z+A.max.z)/2*10)/10});
          }
        }
      }
    }
  }
  return hits;
};

// Scenery that floats: a mesh whose underside is well above the ground and which touches nothing else.
global.__worldFloaters = function(group, groundY, minGap, eps){
  // Exclude only the genuinely enormous: ground slabs (60-400 units) and the 1400-unit backing planes.
  // The threshold was 40, which also excluded things that legitimately hold other things up — a boss
  // chamber's 46-unit roof panels, for one — so everything hanging from them reported as floating.
  const boxes = global.__worldBoxes(group).filter(b=>{
    const s=b.box.max.x-b.box.min.x, t=b.box.max.z-b.box.min.z;
    return s<58 && t<58;
  });
  const out=[];
  for(let i=0;i<boxes.length;i++){
    const A=boxes[i].box;
    if(A.min.y < groundY + minGap) continue;   // sitting on or near the ground: fine
    let supported=false;
    for(let j=0;j<boxes.length && !supported;j++){
      if(i===j) continue;
      const B=boxes[j].box;
      if(A.min.x<=B.max.x+eps && B.min.x<=A.max.x+eps &&
         A.min.y<=B.max.y+eps && B.min.y<=A.max.y+eps &&
         A.min.z<=B.max.z+eps && B.min.z<=A.max.z+eps) supported=true;
    }
    if(!supported) out.push({x:Math.round((A.min.x+A.max.x)/2*10)/10,
                             y:Math.round(A.min.y*100)/100,
                             z:Math.round((A.min.z+A.max.z)/2*10)/10});
  }
  return out;
};

})(this);
