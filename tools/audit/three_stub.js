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
class DirectionalLight extends Light {}
class SpotLight extends Light {}
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
  Fog, FogExp2, PerspectiveCamera, WebGLRenderer, Raycaster, Clock,
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
  addEventListener(){}, removeEventListener(){},
  body: makeElement('body'),
  documentElement: makeElement('html'),
  head: makeElement('head'),
  exitPointerLock(){},
  pointerLockElement: null,
  hidden: false,
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

})(this);
