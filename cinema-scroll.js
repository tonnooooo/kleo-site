/* Original, decorative film camera. Local Three.js, no trackers or remote assets. */
const stage = document.querySelector('.film-stage');
const motion = matchMedia('(prefers-reduced-motion: reduce)');
const saveData = navigator.connection?.saveData;
let booted = false;
const trigger = new IntersectionObserver(entries => {
  if (entries[0].isIntersecting && !motion.matches && !saveData && !booted) {
    booted = true;
    import('./vendor/three/three.module.min.js').then(build).catch(() => stage.dataset.render = 'fallback');
  }
}, {rootMargin: '250px'});
if (stage) trigger.observe(stage);
motion.addEventListener('change', () => { if (!motion.matches && stage) { trigger.unobserve(stage); trigger.observe(stage); } });

function build(T) {
  const host = stage.querySelector('.film-canvas');
  let renderer;
  try { renderer = new T.WebGLRenderer({alpha:true, antialias:true, powerPreference:'low-power'}); }
  catch { stage.dataset.render = 'fallback'; return; }
  const canvas = renderer.domElement;
  canvas.setAttribute('aria-hidden','true');
  host.append(canvas);
  renderer.setPixelRatio(Math.min(devicePixelRatio, innerWidth < 600 ? 1.25 : 1.5));
  const scene = new T.Scene();
  const camera = new T.PerspectiveCamera(34, 1, .1, 60);
  camera.position.set(0,.35,10.7);
  scene.add(new T.HemisphereLight(0xffedcb, 0x3c4563, 3));
  const key = new T.DirectionalLight(0xffce80, 5); key.position.set(3,5,6); scene.add(key);
  const rim = new T.DirectionalLight(0xaaa5ff, 3); rim.position.set(-4,2,-2); scene.add(rim);
  const metal = new T.MeshStandardMaterial({color:0x414958,metalness:.35,roughness:.42});
  const dark = new T.MeshStandardMaterial({color:0x10141d,metalness:.4,roughness:.4});
  const gold = new T.MeshStandardMaterial({color:0xf3b53f,metalness:.65,roughness:.25});
  const glass = new T.MeshStandardMaterial({color:0x456777,metalness:.8,roughness:.13});
  const cameraRig = new T.Group(); scene.add(cameraRig);
  const add = (geometry, material, x,y,z, parent=cameraRig) => {
    const mesh = new T.Mesh(geometry, material); mesh.position.set(x,y,z); parent.add(mesh); return mesh;
  };
  add(new T.BoxGeometry(2.35,1.45,1),metal,0,0,0);
  add(new T.BoxGeometry(2.08,1.16,.04),dark,0,0,.53);
  add(new T.BoxGeometry(.68,.07,.05),gold,-.45,-.35,.57);
  // Pair of perforated film reels, modeled as rings and spokes.
  const reels=[];
  for (const x of [-.7,.7]) {
    const reel=new T.Group(); reel.position.set(x,1.18,0);cameraRig.add(reel);reels.push(reel);
    add(new T.TorusGeometry(.63,.075,8,40),gold,0,0,0,reel);
    add(new T.CylinderGeometry(.18,.18,.16,20),metal,0,0,0,reel).rotation.x=Math.PI/2;
    for(let i=0;i<6;i++) {
      const a=i*Math.PI/3;
      const spoke=add(new T.BoxGeometry(.43,.09,.07),metal,Math.cos(a)*.37,Math.sin(a)*.37,0,reel);
      spoke.rotation.z=a;
    }
  }
  // Lens points along the camera body's X axis.
  const lens=new T.Group(); lens.position.set(1.2,0,0);cameraRig.add(lens);
  for(let i=0;i<4;i++) {
    const ring=add(new T.CylinderGeometry(.43+i*.035,.43+i*.035,.17,40),i%2?metal:gold,i*.18,0,0,lens);
    ring.rotation.z=Math.PI/2;
  }
  const optic=add(new T.CylinderGeometry(.49,.49,.025,40),glass,.65,0,0,lens);optic.rotation.z=Math.PI/2;
  add(new T.BoxGeometry(.24,.4,.25),gold,0,-.9,0);
  add(new T.BoxGeometry(1.2,.1,.75),metal,0,-1.14,0);
  // A curved film ribbon with visible frames and sprocket holes, all geometry.
  const film=new T.Group();scene.add(film);
  const frameMaterial=new T.MeshStandardMaterial({color:0x99712e,metalness:.5,roughness:.42,side:T.DoubleSide});
  for(let i=0;i<25;i++) {
    const a=(i/24)*Math.PI*1.5-.7;
    const frame=new T.Group(); frame.position.set(Math.cos(a)*3.05,Math.sin(a*.9)*.65-.5,Math.sin(a)*1.7-1.1);
    frame.rotation.y=-a-Math.PI/2;
    add(new T.BoxGeometry(.42,.47,.018),frameMaterial,0,0,0,frame);
    for(const y of [-.31,.31]) {
      add(new T.BoxGeometry(.5,.09,.025),gold,0,y,0,frame);
      for(const x of [-.12,.12]) add(new T.BoxGeometry(.05,.045,.028),dark,x,y,.015,frame);
    }
    film.add(frame);
  }
  film.position.y=-.65;
  for (const edge of [-.31,.31]) {
    const points=[];
    for(let i=0;i<=80;i++) {
      const a=(i/80)*Math.PI*1.5-.7;
      points.push(new T.Vector3(Math.cos(a)*3.05,Math.sin(a*.9)*.65-.5+edge,Math.sin(a)*1.7-1.1));
    }
    film.add(new T.Mesh(new T.TubeGeometry(new T.CatmullRomCurve3(points),80,.018,4,false),gold));
  }
  const label=document.createElement('canvas');label.width=512;label.height=256;
  const ink=label.getContext('2d');ink.fillStyle='#10141d';ink.fillRect(0,0,512,256);
  ink.fillStyle='#f3b53f';ink.font='bold 90px sans-serif';ink.fillText('KLEO',48,135);
  ink.fillStyle='#b8bdc7';ink.font='20px monospace';ink.fillText('HUMAN DIRECTION',52,190);
  const labelTexture=new T.CanvasTexture(label);labelTexture.colorSpace=T.SRGBColorSpace;
  add(new T.PlaneGeometry(1.45,.72),new T.MeshBasicMaterial({map:labelTexture}),-.15,.1,.559);
  const floor = new T.Mesh(new T.RingGeometry(2.8,2.81,80),new T.MeshBasicMaterial({color:0xf3b53f,transparent:true,opacity:.25,side:T.DoubleSide}));
  floor.rotation.x=-Math.PI/2;floor.position.y=-1.5;scene.add(floor);
  let frame=0, visible=false, last=0, elapsed=0, progress=0, target=0, lost=false;
  const isPaused=()=>document.hidden||motion.matches||document.body.classList.contains('ambience-paused')||lost;
  function size(){
    const r=host.getBoundingClientRect(); renderer.setSize(r.width,r.height,false);
    camera.aspect=r.width/r.height; camera.position.z=camera.aspect<.9?15:10.7;camera.updateProjectionMatrix();
  }
  function scroll(){
    const r=stage.getBoundingClientRect();
    target=T.MathUtils.clamp((innerHeight*.7-r.top)/(r.height+innerHeight*.15),0,1);
  }
  function paint(now){
    frame=0;
    if(!visible||isPaused())return;
    frame=requestAnimationFrame(paint);
    if(now-last<1000/30)return;
    const dt=Math.min((now-last)/1000,.05);last=now;elapsed+=dt;
    progress+=(target-progress)*.09;
    cameraRig.rotation.set(.13+progress*.18,-.6+progress*1.65,Math.sin(elapsed*.45)*.035);
    cameraRig.position.y=Math.sin(elapsed*.6)*.07;
    lens.position.x=1.2+Math.sin(progress*Math.PI)*.42;
    reels.forEach((r,i)=>r.rotation.z=elapsed*(i?-.22:.18)+progress*2.5);
    film.rotation.y=-progress*.9;film.rotation.z=Math.sin(elapsed*.3)*.03;
    renderer.render(scene,camera);
    stage.dataset.progress=progress.toFixed(2);
  }
  function update(){
    stage.classList.toggle('motion-static',motion.matches);
    const paused=document.body.classList.contains('ambience-paused');
    document.querySelectorAll('.ambient-control,.film-motion').forEach(b=>{
      b.setAttribute('aria-pressed',String(paused));b.textContent=paused?'Resume ambience':'Pause ambience';
    });
    if(frame){cancelAnimationFrame(frame);frame=0;}
    if(visible&&!isPaused()){last=performance.now();frame=requestAnimationFrame(paint);}
  }
  const observer=new IntersectionObserver(entries=>{visible=entries[0].isIntersecting;scroll();update();},{threshold:0});observer.observe(host);
  new ResizeObserver(()=>{size();scroll();}).observe(host);
  window.addEventListener('scroll',scroll,{passive:true});
  document.addEventListener('visibilitychange',update);
  motion.addEventListener('change',update);
  new MutationObserver(update).observe(document.body,{attributes:true,attributeFilter:['class']});
  stage.querySelector('.film-motion').addEventListener('click',()=>document.body.classList.toggle('ambience-paused'));
  canvas.addEventListener('webglcontextlost',e=>{e.preventDefault();lost=true;stage.dataset.render='fallback';update();});
  canvas.addEventListener('webglcontextrestored',()=>{lost=false;stage.dataset.render='ready';update();});
  size();scroll();renderer.render(scene,camera);stage.dataset.render='ready';update();
}
