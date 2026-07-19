(function(){
  const body = document.body;
  const btn2d = document.getElementById('btn-2d');
  const btn3d = document.getElementById('btn-3d');
  const engineLabel = document.getElementById('engine-label');
  const stageBody = document.getElementById('stage-body');
  const chatMessages = document.getElementById('chat-messages');

  let currentMode = '2d';
  let three = null; // lazy three.js scene handle

  function setMode(mode){
    currentMode = mode;
    body.classList.toggle('mode-2d', mode === '2d');
    body.classList.toggle('mode-3d', mode === '3d');
    btn2d.classList.toggle('active', mode === '2d');
    btn3d.classList.toggle('active', mode === '3d');
    btn2d.setAttribute('aria-selected', mode === '2d');
    btn3d.setAttribute('aria-selected', mode === '3d');
    engineLabel.textContent = mode === '2d' ? 'MANIM · 2D RENDER' : 'THREE.JS · 3D SCENE';
    renderEmptyState();
  }

  function renderEmptyState(){
    stageBody.innerHTML = `
      <div class="empty-state" id="empty-state">
        <div class="glyph">${currentMode === '2d' ? '✎' : '⬡'}</div>
        <h3>Nothing on the board yet</h3>
        <p>${currentMode === '2d'
          ? 'Type a topic above — like “give parabola” — and Chalkline will sketch it out here for the class to see.'
          : 'Type a topic above and Chalkline will build an interactive 3D scene you can orbit, pan and zoom.'}</p>
      </div>`;
  }

  function renderLoading(){
    stageBody.innerHTML = `
      <div class="loading-state">
        <div class="chalk-spinner">
          <svg viewBox="0 0 50 50">
            <circle cx="25" cy="25" r="20" fill="none" stroke="${currentMode==='2d' ? '#E7C948' : '#7FB4DE'}" stroke-width="3"
              stroke-linecap="round" stroke-dasharray="90 40" opacity="0.85"/>
          </svg>
        </div>
        <p>${currentMode === '2d' ? 'Sketching the animation…' : 'Building the 3D scene…'}</p>
        <p class="sub">sending prompt to model</p>
      </div>`;
  }

  function niceTopicLabel(raw){
    const t = raw.trim();
    if(!t) return currentMode === '2d' ? 'Parabola y = x²' : 'Paraboloid surface';
    return t.charAt(0).toUpperCase() + t.slice(1);
  }

  function renderResult2D(label){
    stageBody.innerHTML = `
      <div id="canvas2d-wrap"><canvas id="canvas2d" width="640" height="380"></canvas></div>
      <div class="playbar">
        <button class="play-btn" id="play-btn" aria-label="Play preview">
          <svg viewBox="0 0 24 24"><path d="M6 4l14 8-14 8V4z"/></svg>
        </button>
        <div class="track"><div class="track-fill"></div></div>
        <span class="time">00:04 / 00:12</span>
      </div>`;
    drawChalkGraph(document.getElementById('canvas2d'));
  }

  function renderResult2DFromJob(data){
    // data: { video_url, duration_seconds, status, job_id }
    if(data.video_url){
      stageBody.innerHTML = `
        <video id="manim-video" src="${data.video_url}" style="max-width:100%; max-height:100%; border-radius:8px;" controls autoplay loop></video>`;
    } else {
      // fallback while status is 'rendering' or if backend hasn't produced a file yet
      stageBody.innerHTML = `
        <div id="canvas2d-wrap"><canvas id="canvas2d" width="640" height="380"></canvas></div>
        <div class="playbar">
          <button class="play-btn" id="play-btn" aria-label="Play preview">
            <svg viewBox="0 0 24 24"><path d="M6 4l14 8-14 8V4z"/></svg>
          </button>
          <div class="track"><div class="track-fill"></div></div>
          <span class="time">preview unavailable — showing placeholder</span>
        </div>`;
      drawChalkGraph(document.getElementById('canvas2d'));
    }
  }

  function drawChalkGraph(canvas){
    const ctx = canvas.getContext('2d');
    const w = canvas.width, h = canvas.height;
    ctx.clearRect(0,0,w,h);
    // axes
    ctx.strokeStyle = 'rgba(242,239,228,0.35)';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(40, h/2); ctx.lineTo(w-30, h/2);
    ctx.moveTo(w/2, 20); ctx.lineTo(w/2, h-30);
    ctx.stroke();
    // parabola curve, chalky stroke
    ctx.strokeStyle = '#E7C948';
    ctx.lineWidth = 3;
    ctx.lineCap = 'round';
    ctx.beginPath();
    const scale = 0.012;
    for(let px=40; px<=w-30; px++){
      const x = px - w/2;
      const y = h/2 - (x*x*scale);
      if(px===40) ctx.moveTo(px,y); else ctx.lineTo(px,y);
    }
    ctx.stroke();
    ctx.fillStyle = 'rgba(242,239,228,0.55)';
    ctx.font = '13px IBM Plex Mono, monospace';
    ctx.fillText('y = x²', w-90, 40);
  }

  function renderResult3DFromScene(data){
    // data: { scene_spec, status, job_id } — scene_spec is JSON describing objects,
    // produced by the shared scene-spec service and turned into geometry here.
    stageBody.innerHTML = `
      <div id="canvas3d-wrap"></div>
      <div class="orbit-hint">
        <span>🖱 drag to orbit</span><span>⚲ scroll to zoom</span><span>⇧ + drag to pan</span>
      </div>`;
    initThree(document.getElementById('canvas3d-wrap'), data.scene_spec || null);
  }

  function initThree(container, sceneSpec){
    if(typeof THREE === 'undefined'){
      container.innerHTML = '<p style="color:#C9C6BA;font-family:IBM Plex Mono,monospace;font-size:12px;">Three.js failed to load.</p>';
      return;
    }
    const w = container.clientWidth, h = container.clientHeight;
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, w/h, 0.1, 100);
    camera.position.set(4.5, 3.2, 5.5);

    const renderer = new THREE.WebGLRenderer({ antialias:true, alpha:true });
    renderer.setSize(w, h);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.innerHTML = '';
    container.appendChild(renderer.domElement);

    // grid
    const grid = new THREE.GridHelper(10, 20, 0x3A4A40, 0x28382F);
    scene.add(grid);

    // paraboloid surface (mock 3D visual)
    const geo = new THREE.ParametricBufferGeometry ? null : null;
    const segs = 40, size = 3;
    const positions = [];
    const indices = [];
    for(let i=0;i<=segs;i++){
      for(let j=0;j<=segs;j++){
        const x = (i/segs - 0.5) * size * 2;
        const z = (j/segs - 0.5) * size * 2;
        const y = (x*x + z*z) * 0.28;
        positions.push(x, y, z);
      }
    }
    for(let i=0;i<segs;i++){
      for(let j=0;j<segs;j++){
        const a = i*(segs+1)+j, b = a+1, c = a+(segs+1), d = c+1;
        indices.push(a,c,b, b,c,d);
      }
    }
    const bufferGeo = new THREE.BufferGeometry();
    bufferGeo.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
    bufferGeo.setIndex(indices);
    bufferGeo.computeVertexNormals();
    const mat = new THREE.MeshStandardMaterial({ color: 0x7FB4DE, wireframe:false, opacity:0.85, transparent:true, side: THREE.DoubleSide });
    const mesh = new THREE.Mesh(bufferGeo, mat);
    scene.add(mesh);

    const wireMat = new THREE.MeshBasicMaterial({ color: 0xF2EFE4, wireframe:true, opacity:0.12, transparent:true });
    const wireMesh = new THREE.Mesh(bufferGeo, wireMat);
    scene.add(wireMesh);

    scene.add(new THREE.AmbientLight(0xffffff, 0.6));
    const dl = new THREE.DirectionalLight(0xffffff, 0.8);
    dl.position.set(5,8,4);
    scene.add(dl);

    // manual orbit controls (drag rotate, wheel zoom, shift+drag pan)
    let isDown=false, lastX=0, lastY=0, theta=0.7, phi=1.0, radius=7.5;
    let panX=0, panY=0;
    function updateCamera(){
      const px = radius * Math.sin(phi) * Math.sin(theta);
      const py = radius * Math.cos(phi);
      const pz = radius * Math.sin(phi) * Math.cos(theta);
      camera.position.set(px+panX, py+panY, pz);
      camera.lookAt(panX, panY, 0);
    }
    updateCamera();

    renderer.domElement.addEventListener('mousedown', (e)=>{ isDown=true; lastX=e.clientX; lastY=e.clientY; });
    window.addEventListener('mouseup', ()=> isDown=false);
    window.addEventListener('mousemove', (e)=>{
      if(!isDown) return;
      const dx = e.clientX-lastX, dy = e.clientY-lastY;
      lastX=e.clientX; lastY=e.clientY;
      if(e.shiftKey){ panX -= dx*0.01; panY += dy*0.01; }
      else{ theta -= dx*0.006; phi = Math.min(Math.max(phi - dy*0.006, 0.2), Math.PI-0.2); }
      updateCamera();
    });
    renderer.domElement.addEventListener('wheel', (e)=>{
      e.preventDefault();
      radius = Math.min(Math.max(radius + e.deltaY*0.01, 3), 16);
      updateCamera();
    }, { passive:false });

    let raf;
    function animate(){
      raf = requestAnimationFrame(animate);
      mesh.rotation.y += 0.0015;
      wireMesh.rotation.y = mesh.rotation.y;
      renderer.render(scene, camera);
    }
    animate();

    function onResize(){
      const nw = container.clientWidth, nh = container.clientHeight;
      if(nw===0||nh===0) return;
      camera.aspect = nw/nh; camera.updateProjectionMatrix();
      renderer.setSize(nw, nh);
    }
    window.addEventListener('resize', onResize);
  }

  const chatTextarea = document.getElementById('chat-textarea');
  const chatSendBtn = document.getElementById('chat-send-btn');
  const chatEngineTag = document.getElementById('chat-engine-tag');

  const API_BASE = window.CHALKLINE_API_BASE || 'http://localhost:8000';

  function addChatMessage(role, text){
    const wrap = document.createElement('div');
    wrap.className = 'chat-msg ' + (role === 'user' ? 'chat-msg-user' : 'chat-msg-assistant');
    wrap.innerHTML = `<div class="chat-msg-role">${role === 'user' ? 'you' : 'chalkline'}</div><div class="chat-msg-body"></div>`;
    wrap.querySelector('.chat-msg-body').textContent = text;
    chatMessages.appendChild(wrap);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return wrap;
  }

  function syncChatEngineTag(){
    chatEngineTag.textContent = currentMode === '2d' ? '2D · manim' : '3D · three.js';
  }

  async function generate(){
    const rawText = chatTextarea.value;
    if(!rawText.trim()) return;
    const label = niceTopicLabel(rawText);

    addChatMessage('user', rawText.trim());
    chatTextarea.value = '';
    renderLoading();

    try{
      const res = await fetch(`${API_BASE}/api/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: rawText.trim(), mode: currentMode })
      });
      if(!res.ok) throw new Error(`Server responded ${res.status}`);
      const data = await res.json();

      if(currentMode === '2d'){
        renderResult2DFromJob(data);
      } else {
        renderResult3DFromScene(data);
      }
      addChatMessage('assistant', `Done. "${label}" is on the board — let me know if you'd like a variation.`);
    } catch(err){
      renderEmptyState();
      addChatMessage('assistant', `Couldn't reach the render backend (${err.message}). Is the API running at ${API_BASE}?`);
    }
  }

  btn2d.addEventListener('click', ()=>{ setMode('2d'); syncChatEngineTag(); });
  btn3d.addEventListener('click', ()=>{ setMode('3d'); syncChatEngineTag(); });

  chatSendBtn.addEventListener('click', generate);
  chatTextarea.addEventListener('keydown', (e)=>{
    if(e.key === 'Enter' && !e.shiftKey){ e.preventDefault(); generate(); }
  });

  syncChatEngineTag();
  renderEmptyState();
})();