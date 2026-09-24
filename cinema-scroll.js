/* Original moving storyboard. Three textured frames, no model or heavy lighting. */
const stage = document.querySelector('.film-stage');
const motion = matchMedia('(prefers-reduced-motion: reduce)');
let booted = false;
const trigger = new IntersectionObserver(entries => {
  if (entries[0].isIntersecting && !motion.matches && !navigator.connection?.saveData && !booted) {
    booted = true;
    import('./vendor/three/three.module.min.js').then(build).catch(() => stage.dataset.render = 'fallback');
  }
}, {rootMargin: '250px'});
if (stage) trigger.observe(stage);
motion.addEventListener('change', () => { if (!motion.matches && stage) { trigger.unobserve(stage); trigger.observe(stage); } });

async function build(T) {
  const host = stage.querySelector('.film-canvas');
  let renderer;
  try { renderer = new T.WebGLRenderer({alpha:true, antialias:true, powerPreference:'low-power'}); }
  catch { stage.dataset.render = 'fallback'; return; }
  const canvas = renderer.domElement;
  canvas.setAttribute('aria-hidden','true');host.append(canvas);
  renderer.setPixelRatio(Math.min(devicePixelRatio,1));
  const scene = new T.Scene();
  const camera = new T.PerspectiveCamera(34,1,.1,40);
  const rig=new T.Group();scene.add(rig);
  const textures=[];
  try {
    for(const file of ['realistic-signal.jpg','realistic-apex.jpg','realistic-tether.jpg']) {
      const texture=await new T.TextureLoader().loadAsync('/samples/'+file);
      texture.colorSpace=T.SRGBColorSpace;
      // Preserve the original image ratio within a cinematic frame.
      const aspect=texture.image.width/texture.image.height;
      if(aspect<16/9){texture.repeat.y=aspect/(16/9);texture.offset.y=(1-texture.repeat.y)/2;}
      else {texture.repeat.x=(16/9)/aspect;texture.offset.x=(1-texture.repeat.x)/2;}
      textures.push(texture);
    }
  } catch {
    textures.forEach(t=>t.dispose());renderer.dispose();canvas.remove();stage.dataset.render='fallback';return;
  }
  const edgeMaterial=new T.MeshBasicMaterial({color:0xc59443});
  const backingMaterial=new T.MeshBasicMaterial({color:0x141820});
  const cards=[];
  textures.forEach((texture,i)=>{
    const card=new T.Group();const x=(i-1)*3.16;
    card.position.set(x,i===1?.08:-.08,i===1?.45:-.5);
    card.rotation.y=(i-1)*-.16;
    const border=new T.Mesh(new T.PlaneGeometry(3.06,1.755),edgeMaterial);border.position.z=-.025;card.add(border);
    const backing=new T.Mesh(new T.PlaneGeometry(3.04,1.735),backingMaterial);backing.position.z=-.015;card.add(backing);
    const image=new T.Mesh(new T.PlaneGeometry(2.98,1.67625),new T.MeshBasicMaterial({map:texture}));card.add(image);
    rig.add(card);cards.push(card);
  });
  for(const y of [-1.13,1.13]) {
    const points=[];
    for(let i=0;i<=64;i++){const x=-6+i*12/64;points.push(new T.Vector3(x,y+Math.sin(x*.5)*.12,-.65-Math.abs(x)*.05));}
    const line=new T.Line(new T.BufferGeometry().setFromPoints(points),new T.LineBasicMaterial({color:0xf3b53f,transparent:true,opacity:.35}));rig.add(line);
  }
  let frame=0,visible=false,last=0,elapsed=0,progress=0,target=0,lost=false;
  const isPaused=()=>document.hidden||motion.matches||document.body.classList.contains('ambience-paused')||lost;
  function size(){
    const r=host.getBoundingClientRect();renderer.setSize(r.width,r.height,false);
    camera.aspect=r.width/r.height;
    const fieldWidth=innerWidth<600?4.4:10.8;
    camera.position.set(0,0,Math.max(3.3,fieldWidth/camera.aspect)/(2*Math.tan(17*Math.PI/180)));
    camera.updateProjectionMatrix();
    renderer.render(scene,camera);
  }
  function scroll(){
    const r=stage.getBoundingClientRect();target=T.MathUtils.clamp((innerHeight*.7-r.top)/(r.height+innerHeight*.15),0,1);
  }
  function paint(now){
    frame=0;if(!visible||isPaused())return;
    const dt=Math.min((now-last)/1000,.05);last=now;elapsed+=dt;
    // Time-based smoothing: identical speed on 60/120 Hz displays, no 30 fps throttle.
    progress+=(target-progress)*(1-Math.exp(-7*dt));
    // Reuse the rendered texture; compositor transforms avoid redrawing WebGL on every scroll frame.
    canvas.style.transform=`perspective(1000px) rotateY(${(progress-.5)*7}deg) rotateZ(${(progress-.5)*-.6}deg) translate3d(${(progress-.5)*18}px,${Math.sin(elapsed*.55)*2}px,0)`;
    stage.dataset.progress=progress.toFixed(3);
    frame=requestAnimationFrame(paint);
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
  new IntersectionObserver(entries=>{visible=entries[0].isIntersecting;scroll();update();},{threshold:0}).observe(host);
  new ResizeObserver(()=>{size();scroll();}).observe(host);
  window.addEventListener('scroll',scroll,{passive:true});
  document.addEventListener('visibilitychange',update);motion.addEventListener('change',update);
  new MutationObserver(update).observe(document.body,{attributes:true,attributeFilter:['class']});
  stage.querySelector('.film-motion').addEventListener('click',()=>document.body.classList.toggle('ambience-paused'));
  canvas.addEventListener('webglcontextlost',e=>{e.preventDefault();lost=true;stage.dataset.render='fallback';update();});
  canvas.addEventListener('webglcontextrestored',()=>{lost=false;renderer.render(scene,camera);stage.dataset.render='ready';update();});
  size();scroll();renderer.render(scene,camera);stage.dataset.render='ready';update();
}
