/* Three.js computes each independent 3D film transform. The browser composites images;
   no WebGL redraw, model, shader, or video texture is needed during scroll. */
const stage=document.querySelector('.film-stage');
const motion=matchMedia('(prefers-reduced-motion: reduce)');
const cards=stage?[...stage.querySelectorAll('.film-frame')]:[];
let booted=false;
function staticState(){
  const quiet=motion.matches||navigator.connection?.saveData;
  stage?.classList.toggle('motion-static',!!quiet);
  if(quiet)cards.forEach(card=>card.tabIndex=0);
  return quiet;
}
const trigger=new IntersectionObserver(entries=>{
  if(entries[0].isIntersecting&&!staticState()&&!booted){
    booted=true;
    import('./vendor/three/three.core.min.js').then(build).catch(()=>stage.classList.add('motion-static'));
  }
},{rootMargin:'250px'});
if(stage){staticState();trigger.observe(stage);}
motion.addEventListener('change',()=>{if(stage&&!staticState()){trigger.unobserve(stage);trigger.observe(stage);}});
function build(T){
 const sticky=stage.querySelector('.film-sticky'),host=stage.querySelector('.film-frames');
 const label=stage.querySelector('.film-current');
 const matrix=new T.Matrix4(),position=new T.Vector3(),scale=new T.Vector3(1,1,1),quaternion=new T.Quaternion(),rotation=new T.Euler();
 let frame=0,visible=false,last=0,progress=0,target=0,width=640,selected=-1;
 const paused=()=>document.hidden||motion.matches||navigator.connection?.saveData||document.body.classList.contains('ambience-paused');
 function request(){if(!frame&&visible&&!paused()){last=performance.now();frame=requestAnimationFrame(paint);}}
 function measure(){
  if(staticState())return;
  const r=stage.getBoundingClientRect();
  const travel=Math.max(1,r.height-sticky.offsetHeight);
  target=T.MathUtils.clamp(-r.top/travel,0,1);
  width=cards[0].offsetWidth;request();
 }
 function paint(now){
  frame=0;if(!visible||paused())return;
  const dt=Math.min((now-last)/1000,.05);last=now;
  progress+=(target-progress)*(1-Math.exp(-12*dt));
  if(Math.abs(target-progress)<.0002)progress=target;
  const focus=progress*2;
  cards.forEach((card,i)=>{
   const d=i-focus,dist=Math.abs(d);
   position.set(d*width*.94,Math.min(dist,2)*22,-Math.min(dist,2)*180);
   rotation.set(0,T.MathUtils.degToRad(-T.MathUtils.clamp(d,-1.7,1.7)*26),T.MathUtils.degToRad(d*1.4));
   quaternion.setFromEuler(rotation);matrix.compose(position,quaternion,scale);
   card.style.transform='matrix3d('+matrix.elements.join(',')+')';
   card.style.opacity=String(Math.max(.4,1-dist*.23));
   card.tabIndex=i===Math.round(focus)?0:-1;
  });
  const active=Math.round(focus);
  if(active!==selected){selected=active;label.textContent='0'+(active+1)+' / 03 · '+cards[active].dataset.title;}
  stage.dataset.progress=progress.toFixed(3);
  if(progress!==target)frame=requestAnimationFrame(paint);
 }
 function update(){
  staticState();
  const stopped=document.body.classList.contains('ambience-paused');
  document.querySelectorAll('.ambient-control,.film-motion').forEach(b=>{b.setAttribute('aria-pressed',String(stopped));b.textContent=stopped?'Resume ambience':'Pause ambience';});
  if(frame){cancelAnimationFrame(frame);frame=0;}
  measure();request();
 }
 new IntersectionObserver(entries=>{visible=entries[0].isIntersecting;update();}).observe(sticky);
 new ResizeObserver(measure).observe(host);
 window.addEventListener('scroll',measure,{passive:true});
 window.addEventListener('resize',measure,{passive:true});
 document.addEventListener('visibilitychange',update);motion.addEventListener('change',update);
 new MutationObserver(update).observe(document.body,{attributes:true,attributeFilter:['class']});
 stage.querySelector('.film-motion').addEventListener('click',()=>document.body.classList.toggle('ambience-paused'));
 stage.dataset.render='ready';measure();update();
}
