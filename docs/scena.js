// Scena 3D w nagłówku strony: nocne niebo, piramida z kamiennych warstw, unoszące się złote zwieńczenie,
// słup światła, pył i dryfujące w głębi zdjęcia z artykułów Leszka. Three.js, bez innych zależności.
// Gdy WebGL nie działa (albo nie wczyta się biblioteka), nagłówek dostaje statyczne tło z Bramą Słońca.

const hero = document.getElementById("hero");
const canvas = document.getElementById("scena");
const bez3d = () => {
  hero.classList.add("bez-3d");
  canvas.remove();
};

try {
  await start();
} catch (e) {
  console.warn("Scena 3D niedostępna:", e);
  bez3d();
}

async function start() {
  const THREE = await import("three");
  const { EffectComposer } = await import("three/addons/postprocessing/EffectComposer.js");
  const { RenderPass } = await import("three/addons/postprocessing/RenderPass.js");
  const { UnrealBloomPass } = await import("three/addons/postprocessing/UnrealBloomPass.js");
  const { OutputPass } = await import("three/addons/postprocessing/OutputPass.js");

  const spokojnie = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const telefon = matchMedia("(max-width: 720px)").matches;

  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false, powerPreference: "high-performance" });
  renderer.setPixelRatio(Math.min(devicePixelRatio, telefon ? 1.5 : 1.75));
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.05;
  renderer.setClearColor(0x05070c, 1);

  const scena = new THREE.Scene();
  scena.fog = new THREE.FogExp2(0x070a12, 0.032);
  const kamera = new THREE.PerspectiveCamera(42, 1, 0.1, 400);

  // ---------- światło ----------
  scena.add(new THREE.AmbientLight(0x3a4a6a, 0.9));
  const ksiezyc = new THREE.DirectionalLight(0x9fb4ff, 1.4);
  ksiezyc.position.set(-8, 10, 6);
  scena.add(ksiezyc);
  const zlote = new THREE.PointLight(0xffb347, 60, 14, 2);
  scena.add(zlote);

  // ---------- piramida ----------
  // tekstura kamiennych warstw (rzędy bloków) rysowana w canvasie
  const tex = (() => {
    const c = document.createElement("canvas");
    c.width = 512;
    c.height = 1024;
    const g = c.getContext("2d");
    g.fillStyle = "#3a3226";
    g.fillRect(0, 0, c.width, c.height);
    const rzedy = 40;
    const h = c.height / rzedy;
    for (let r = 0; r < rzedy; r++) {
      let x = -Math.random() * 60;
      while (x < c.width) {
        const w = 40 + Math.random() * 70;
        const jas = 44 + Math.random() * 26;
        g.fillStyle = `hsl(${32 + Math.random() * 8}, ${18 + Math.random() * 10}%, ${jas * 0.55}%)`;
        g.fillRect(x + 1.5, r * h + 1.5, w - 3, h - 3);
        x += w;
      }
      g.fillStyle = "rgba(0,0,0,.55)";
      g.fillRect(0, r * h, c.width, 2);
    }
    // ziarno
    const d = g.getImageData(0, 0, c.width, c.height);
    for (let i = 0; i < d.data.length; i += 4) {
      const n = (Math.random() - 0.5) * 22;
      d.data[i] += n;
      d.data[i + 1] += n;
      d.data[i + 2] += n;
    }
    g.putImageData(d, 0, 0);
    const t = new THREE.CanvasTexture(c);
    t.colorSpace = THREE.SRGBColorSpace;
    t.wrapS = t.wrapT = THREE.RepeatWrapping;
    t.repeat.set(3, 1);
    t.anisotropy = 4;
    return t;
  })();

  const piramida = new THREE.Group();
  scena.add(piramida);
  const R = 3.4; // „promień” podstawy (do narożnika)
  const H = 4.4; // wysokość pełnej piramidy
  const ciecie = 3.75; // na tej wysokości kończy się korpus, wyżej unosi się zwieńczenie
  const rGora = R * (1 - ciecie / H);
  const korpusGeo = new THREE.CylinderGeometry(rGora, R, ciecie, 4, 1, false);
  korpusGeo.rotateY(Math.PI / 4);
  korpusGeo.translate(0, ciecie / 2, 0);
  const korpus = new THREE.Mesh(
    korpusGeo,
    // polygonOffset odsuwa ściany o włos w głąb – świecące krawędzie nie migoczą (brak „z-fightingu”)
    new THREE.MeshStandardMaterial({ map: tex, color: 0xb9a582, roughness: 0.92, metalness: 0.05, flatShading: true, polygonOffset: true, polygonOffsetFactor: 2, polygonOffsetUnits: 4 }),
  );
  piramida.add(korpus);
  // świecące krawędzie
  // świecące krawędzie jako cienkie pręty (walce) – równa grubość i jednolity blask na całej długości
  // (zwykłe linie WebGL mają 1 piksel i przy efekcie blasku „koralikują”)
  const krawedzie = new THREE.Group();
  const materialKrawedzi = new THREE.MeshBasicMaterial({ color: new THREE.Color(0xffc56a).multiplyScalar(1.35), transparent: true, opacity: 0.75 });
  const pk = new THREE.EdgesGeometry(korpusGeo).attributes.position;
  for (let i = 0; i < pk.count; i += 2) {
    const a = new THREE.Vector3().fromBufferAttribute(pk, i);
    const b = new THREE.Vector3().fromBufferAttribute(pk, i + 1);
    const dl = a.distanceTo(b);
    const pret = new THREE.Mesh(new THREE.CylinderGeometry(0.011, 0.011, dl, 6, 1, true), materialKrawedzi);
    pret.position.copy(a).add(b).multiplyScalar(0.5);
    pret.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), b.clone().sub(a).normalize());
    krawedzie.add(pret);
  }
  piramida.add(krawedzie);

  // zwieńczenie (piramidion) – złote, unoszące się nad wierzchołkiem
  const czapkaGeo = new THREE.ConeGeometry(rGora, H - ciecie, 4, 1);
  czapkaGeo.rotateY(Math.PI / 4);
  const czapka = new THREE.Mesh(
    czapkaGeo,
    new THREE.MeshStandardMaterial({ color: 0xffc46b, emissive: 0xff9d2e, emissiveIntensity: 1.8, metalness: 0.9, roughness: 0.25, flatShading: true, polygonOffset: true, polygonOffsetFactor: 2, polygonOffsetUnits: 4 }),
  );
  const czapkaKrawedzie = new THREE.LineSegments(
    new THREE.EdgesGeometry(czapkaGeo),
    new THREE.LineBasicMaterial({ color: new THREE.Color(0xfff0c8).multiplyScalar(2.2) }),
  );
  czapka.add(czapkaKrawedzie);
  piramida.add(czapka);
  const yCzapki = ciecie + (H - ciecie) / 2 + 0.55;

  // słup światła w górę
  const slup = new THREE.Mesh(
    new THREE.CylinderGeometry(0.02, 0.2, 40, 32, 1, true),
    new THREE.ShaderMaterial({
      transparent: true,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
      side: THREE.DoubleSide,
      uniforms: { czas: { value: 0 } },
      vertexShader: `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
      fragmentShader: `uniform float czas; varying vec2 vUv;
        void main(){
          float fade = pow(1.0 - vUv.y, 2.2);
          float bok = pow(sin(vUv.x * 3.14159), 6.0);
          float migot = 0.85 + 0.15 * sin(czas * 2.3 + vUv.y * 14.0);
          gl_FragColor = vec4(vec3(1.0, 0.72, 0.35) * 0.9, fade * (0.05 + 0.16 * bok) * migot);
        }`,
    }),
  );
  slup.position.y = yCzapki + 20;
  piramida.add(slup);

  // poświata wokół zwieńczenia (sprite – zawsze zwrócony do kamery)
  const blask = (() => {
    const c = document.createElement("canvas");
    c.width = c.height = 256;
    const g = c.getContext("2d");
    const gr = g.createRadialGradient(128, 128, 0, 128, 128, 128);
    gr.addColorStop(0, "rgba(255,200,120,0.9)");
    gr.addColorStop(0.25, "rgba(255,160,60,0.35)");
    gr.addColorStop(1, "rgba(255,140,40,0)");
    g.fillStyle = gr;
    g.fillRect(0, 0, 256, 256);
    const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: new THREE.CanvasTexture(c), transparent: true, depthWrite: false, blending: THREE.AdditiveBlending }));
    s.scale.set(5, 5, 1);
    return s;
  })();
  piramida.add(blask);

  // ---------- teren: ciemny piasek i złota siatka znikająca w mgle ----------
  const teren = new THREE.Mesh(
    new THREE.PlaneGeometry(300, 300, 1, 1),
    new THREE.ShaderMaterial({
      transparent: true,
      depthWrite: false,
      uniforms: { czas: { value: 0 } },
      vertexShader: `varying vec3 vPoz; void main(){ vec4 w = modelMatrix * vec4(position,1.0); vPoz = w.xyz; gl_Position = projectionMatrix * viewMatrix * w; }`,
      fragmentShader: `uniform float czas; varying vec3 vPoz;
        float linia(float x, float grub){ float f = abs(fract(x) - 0.5); return smoothstep(grub, 0.0, 0.5 - f); }
        void main(){
          vec2 p = vPoz.xz / 2.0;
          float l = max(linia(p.x, 0.02), linia(p.y, 0.02));
          float d = length(vPoz.xz);
          float fala = 0.5 + 0.5 * sin(d * 0.6 - czas * 0.8);
          float zanik = exp(-d * 0.055);
          vec3 piasek = vec3(0.045, 0.04, 0.035);
          vec3 kolor = piasek + vec3(0.9, 0.6, 0.22) * l * (0.10 + 0.12 * fala) * zanik;
          gl_FragColor = vec4(kolor, zanik * 0.95 + 0.05);
        }`,
    }),
  );
  teren.rotation.x = -Math.PI / 2;
  scena.add(teren);

  // ---------- gwiazdy (z migotaniem) i pas Oriona ----------
  const gwiazdyGeo = new THREE.BufferGeometry();
  const N = telefon ? 1100 : 2200;
  const poz = new Float32Array(N * 3);
  const faza = new Float32Array(N);
  const rozm = new Float32Array(N);
  for (let i = 0; i < N; i++) {
    const r = 90 + Math.random() * 60;
    const th = Math.random() * Math.PI * 2;
    const ph = Math.acos(Math.random() * 0.92 + 0.06);
    poz.set([r * Math.sin(ph) * Math.cos(th), r * Math.cos(ph) - 6, r * Math.sin(ph) * Math.sin(th)], i * 3);
    faza[i] = Math.random() * 6.28;
    rozm[i] = Math.random() < 0.04 ? 3.2 + Math.random() * 2 : 1 + Math.random() * 1.6;
  }
  // trzy jasne gwiazdy pasa Oriona nad piramidą
  const orion = [
    [-14, 34, -110],
    [-9.5, 32.2, -110],
    [-5.4, 29.9, -110],
  ];
  orion.forEach((p, k) => {
    poz.set(p, k * 3);
    rozm[k] = 7;
  });
  gwiazdyGeo.setAttribute("position", new THREE.BufferAttribute(poz, 3));
  gwiazdyGeo.setAttribute("faza", new THREE.BufferAttribute(faza, 1));
  gwiazdyGeo.setAttribute("rozm", new THREE.BufferAttribute(rozm, 1));
  const gwiazdyMat = new THREE.ShaderMaterial({
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    uniforms: { czas: { value: 0 }, dpr: { value: renderer.getPixelRatio() } },
    vertexShader: `attribute float faza; attribute float rozm; uniform float czas; uniform float dpr; varying float vJas;
      void main(){ vJas = 0.55 + 0.45 * sin(czas * (0.8 + fract(faza) * 1.6) + faza);
        gl_PointSize = rozm * dpr * (0.8 + 0.4 * vJas);
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`,
    fragmentShader: `varying float vJas; void main(){ float d = length(gl_PointCoord - 0.5); float a = smoothstep(0.5, 0.0, d);
      gl_FragColor = vec4(mix(vec3(0.75,0.82,1.0), vec3(1.0,0.92,0.8), vJas) * (0.6 + vJas), a * vJas); }`,
  });
  const gwiazdy = new THREE.Points(gwiazdyGeo, gwiazdyMat);
  gwiazdy.frustumCulled = false;
  scena.add(gwiazdy);

  // ---------- pył unoszący się wokół piramidy ----------
  const M = telefon ? 260 : 520;
  const pylGeo = new THREE.BufferGeometry();
  const pylPoz = new Float32Array(M * 3);
  const pylPredk = new Float32Array(M);
  for (let i = 0; i < M; i++) {
    pylPoz.set([(Math.random() - 0.5) * 22, Math.random() * 12, (Math.random() - 0.5) * 18], i * 3);
    pylPredk[i] = 0.08 + Math.random() * 0.25;
  }
  pylGeo.setAttribute("position", new THREE.BufferAttribute(pylPoz, 3));
  const pyl = new THREE.Points(
    pylGeo,
    new THREE.PointsMaterial({ color: 0xffcf8a, size: 0.05, transparent: true, opacity: 0.55, depthWrite: false, blending: THREE.AdditiveBlending }),
  );
  scena.add(pyl);

  // ---------- zdjęcia Leszka dryfujące w głębi ----------
  const loader = new THREE.TextureLoader();
  const zdjecia = [];
  const fotoMat = (t) =>
    new THREE.ShaderMaterial({
      transparent: true,
      depthWrite: false,
      uniforms: { mapa: { value: t }, krycie: { value: 0 }, czas: { value: 0 } },
      vertexShader: `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
      fragmentShader: `uniform sampler2D mapa; uniform float krycie; uniform float czas; varying vec2 vUv;
        void main(){
          vec3 c = texture2D(mapa, vUv).rgb;
          float l = dot(c, vec3(0.299, 0.587, 0.114));
          vec3 duo = mix(vec3(0.03, 0.05, 0.12), vec3(0.85, 0.62, 0.34), smoothstep(0.05, 1.0, l));
          float skan = 0.92 + 0.08 * sin(vUv.y * 420.0 + czas * 3.0);
          vec2 k = smoothstep(0.0, 0.12, vUv) * smoothstep(0.0, 0.12, 1.0 - vUv);
          gl_FragColor = vec4(duo * skan, krycie * k.x * k.y);
        }`,
    });
  const lista = (window.ZDJECIA ?? []).filter((z) => z.img !== "brama.jpg").slice(0, telefon ? 8 : 12);
  lista.forEach((z, i) => {
    loader.load(`img/${z.img}`, (t) => {
      t.colorSpace = THREE.SRGBColorSpace;
      const proporcja = t.image.width / t.image.height;
      const h = 2.0 + (i % 3) * 0.35;
      const m = new THREE.Mesh(new THREE.PlaneGeometry(h * proporcja, h), fotoMat(t));
      // łuk za piramidą, na różnych głębokościach i wysokościach
      const kat = -1.25 + (i / Math.max(1, lista.length - 1)) * 2.5;
      const odl = 15 + (i % 4) * 3.5;
      m.position.set(Math.sin(kat) * odl, 2.4 + ((i * 37) % 5) * 0.9, -Math.cos(kat) * odl - 4);
      m.lookAt(0, m.position.y * 0.6, 14);
      m.userData = { baza: m.position.clone(), faza: i * 1.7, cel: 0.34 + (i % 3) * 0.06 };
      scena.add(m);
      zdjecia.push(m);
    });
  });
  // Brama Słońca – baner strony – daleko w tle, jak brama do przeszłości
  loader.load("img/brama.jpg", (t) => {
    t.colorSpace = THREE.SRGBColorSpace;
    const pr = t.image.width / t.image.height;
    const m = new THREE.Mesh(new THREE.PlaneGeometry(16 * pr, 16), fotoMat(t));
    m.position.set(0, 11, -55);
    m.userData = { baza: m.position.clone(), faza: 0, cel: 0.2 };
    scena.add(m);
    zdjecia.push(m);
  });

  // ---------- post-processing: blask ----------
  const composer = new EffectComposer(renderer);
  composer.addPass(new RenderPass(scena, kamera));
  const bloom = new UnrealBloomPass(new THREE.Vector2(1, 1), telefon ? 0.75 : 0.95, 0.65, 0.22);
  composer.addPass(bloom);
  composer.addPass(new OutputPass());

  // ---------- układ zależny od proporcji ekranu ----------
  const cel = new THREE.Vector3();
  let bazaKamery = new THREE.Vector3();
  const uklad = () => {
    const w = hero.clientWidth;
    const h = hero.clientHeight;
    renderer.setSize(w, h, false);
    composer.setSize(w, h);
    bloom.resolution.set(w, h);
    kamera.aspect = w / h;
    const szeroki = kamera.aspect > 1.15;
    const waski = kamera.aspect < 0.8;
    piramida.position.set(szeroki ? 5.4 : 0, 0, 0);
    piramida.scale.setScalar(waski ? 0.72 : szeroki ? 0.82 : 0.9);
    cel.set(szeroki ? 2.4 : 0, waski ? -3.4 : 2.0, 0);
    bazaKamery = new THREE.Vector3(szeroki ? 1.4 : 0, waski ? 1.8 : 2.5, waski ? 23 : 13.5);
    kamera.fov = waski ? 50 : 42;
    kamera.updateProjectionMatrix();
  };
  uklad();
  addEventListener("resize", uklad);

  // ---------- ruch ----------
  const mysz = { x: 0, y: 0, cx: 0, cy: 0 };
  addEventListener("pointermove", (e) => {
    mysz.x = (e.clientX / innerWidth - 0.5) * 2;
    mysz.y = (e.clientY / innerHeight - 0.5) * 2;
  });
  let widoczny = true;
  new IntersectionObserver(([w]) => (widoczny = w.isIntersecting)).observe(hero);

  const zegar = new THREE.Clock();
  const pos = pylGeo.attributes.position;
  const klatka = () => {
    const t = spokojnie ? 6 : zegar.getElapsedTime();
    const intro = spokojnie ? 1 : Math.min(1, t / 3.2);
    const ease = 1 - Math.pow(1 - intro, 3);
    const przewiniecie = Math.min(1, scrollY / Math.max(1, hero.clientHeight));

    mysz.cx += (mysz.x - mysz.cx) * 0.04;
    mysz.cy += (mysz.y - mysz.cy) * 0.04;
    kamera.position.set(
      bazaKamery.x + mysz.cx * 0.9,
      bazaKamery.y + (1 - ease) * 3.5 - mysz.cy * 0.45 + przewiniecie * 2.5,
      bazaKamery.z + (1 - ease) * 7 + przewiniecie * 3,
    );
    kamera.lookAt(cel.x, cel.y + przewiniecie * 1.5, cel.z);

    piramida.rotation.y = t * 0.06;
    czapka.position.y = yCzapki + Math.sin(t * 0.9) * 0.12;
    czapka.rotation.y = -t * 0.35;
    blask.position.set(0, czapka.position.y, 0);
    blask.material.opacity = ease;
    zlote.position.set(piramida.position.x, piramida.position.y + czapka.position.y * piramida.scale.y, 0);
    zlote.intensity = 60 * ease * (0.9 + 0.1 * Math.sin(t * 3.1));
    czapka.material.emissiveIntensity = 1.8 * ease;
    materialKrawedzi.opacity = 0.75 * ease;
    slup.material.uniforms.czas.value = t;
    teren.material.uniforms.czas.value = t;
    gwiazdyMat.uniforms.czas.value = t;

    if (!spokojnie) {
      for (let i = 0; i < M; i++) {
        let y = pos.getY(i) + pylPredk[i] * 0.012;
        if (y > 12) y = 0;
        pos.setY(i, y);
        pos.setX(i, pos.getX(i) + Math.sin(t * 0.3 + i) * 0.0025);
      }
      pos.needsUpdate = true;
    }

    for (const m of zdjecia) {
      const u = m.userData;
      m.material.uniforms.krycie.value += (u.cel * ease - m.material.uniforms.krycie.value) * 0.03;
      m.material.uniforms.czas.value = t;
      m.position.y = u.baza.y + Math.sin(t * 0.25 + u.faza) * 0.35;
      m.position.x = u.baza.x + Math.cos(t * 0.18 + u.faza) * 0.25;
    }

    composer.render();
  };

  let pierwsza = true;
  const petla = () => {
    requestAnimationFrame(petla);
    if (!widoczny || document.hidden) return;
    klatka();
    if (pierwsza) {
      pierwsza = false;
      canvas.classList.add("gotowa");
    }
  };
  if (spokojnie) {
    // bez animacji: kilka klatek, aż wczytają się zdjęcia, potem obraz stoi
    canvas.classList.add("gotowa");
    let ile = 0;
    const kilka = () => {
      klatka();
      if (++ile < 120) requestAnimationFrame(kilka);
    };
    kilka();
    addEventListener("resize", () => klatka());
  } else {
    petla();
  }
}
