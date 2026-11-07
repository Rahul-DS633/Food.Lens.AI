"""
FoodLens AI — 3D Interactive WebGL & JavaScript Elements
Embeds interactive Three.js 3D scenes, holographic food crystals,
and dynamic 3D card tilt effects that respond to mouse movements.
"""

import streamlit.components.v1 as components


def render_3d_hero(height: int = 240):
    """
    Renders an interactive Three.js 3D WebGL hero canvas.
    Displays a floating, glowing 3D Food Intelligence Crystal with orbital rings,
    nutrient satellites, a sweeping laser scanner beam, and particle dust.
    Interacts with user mouse position in real-time.
    """
    html_template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body, html { width: 100%; height: 100%; overflow: hidden; background: transparent; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        #canvas-container {
            width: 100%;
            height: __HEIGHT__px;
            position: relative;
            background: radial-gradient(circle at 65% 50%, #ECFCCB 0%, #F0FDF4 50%, #FFFDF9 100%);
            border-radius: 20px;
            overflow: hidden;
            border: 1.5px solid #86EFAC;
            box-shadow: 0 10px 30px -8px rgba(27, 94, 63, 0.15), inset 0 1px 2px rgba(255, 255, 255, 0.8);
        }
        #webgl-canvas { width: 100%; height: 100%; display: block; }
        .hud-overlay {
            position: absolute;
            top: 18px;
            left: 24px;
            pointer-events: none;
            z-index: 10;
        }
        .hud-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: rgba(27, 94, 63, 0.9);
            color: #FFFFFF;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.5px;
            padding: 4px 10px;
            border-radius: 8px;
            backdrop-filter: blur(8px);
            margin-bottom: 6px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        .hud-title {
            font-size: 20px;
            font-weight: 800;
            color: #144730;
            letter-spacing: -0.3px;
        }
        .hud-subtitle {
            font-size: 13px;
            color: #374151;
            margin-top: 3px;
            max-width: 440px;
            line-height: 1.4;
        }
        .hud-controls {
            position: absolute;
            bottom: 12px;
            right: 18px;
            pointer-events: auto;
            display: flex;
            gap: 8px;
            z-index: 10;
        }
        .hud-btn {
            background: rgba(255, 255, 255, 0.9);
            border: 1px solid #86EFAC;
            color: #166534;
            font-size: 11px;
            font-weight: 700;
            padding: 5px 12px;
            border-radius: 20px;
            cursor: pointer;
            backdrop-filter: blur(8px);
            transition: all 0.2s ease;
        }
        .hud-btn:hover {
            background: #1B5E3F;
            color: #FFFFFF;
            transform: translateY(-1px);
        }
        .pulse-dot {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: #A3E635;
            display: inline-block;
            box-shadow: 0 0 8px #A3E635;
            animation: pulse-glow 1.8s infinite;
        }
        @keyframes pulse-glow {
            0%, 100% { transform: scale(1); opacity: 1; }
            50% { transform: scale(1.4); opacity: 0.5; }
        }
      </style>
      <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    </head>
    <body>
      <div id="canvas-container">
        <div class="hud-overlay">
            <div class="hud-badge"><span class="pulse-dot"></span> LIVE 3D FOOD LENS ENGINE</div>
            <div class="hud-title">Real-Time Nutritional Molecular Matrix</div>
            <div class="hud-subtitle">Interactive 3D representation of verified nutritional bonds & spectral analysis. Move your cursor over the crystal to manipulate.</div>
        </div>
        <div class="hud-controls">
            <button class="hud-btn" id="btn-reset">Reset View</button>
            <button class="hud-btn" id="btn-spin">Turbo Spin</button>
        </div>
        <canvas id="webgl-canvas"></canvas>
      </div>

      <script>
        const container = document.getElementById('canvas-container');
        const canvas = document.getElementById('webgl-canvas');

        // Scene, Camera, Renderer
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 1000);
        camera.position.set(0, 0, 7);

        const renderer = new THREE.WebGLRenderer({ canvas: canvas, alpha: true, antialias: true });
        renderer.setSize(container.clientWidth, container.clientHeight);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

        // Center Object: 3D Crystal / Icosahedron
        const crystalGroup = new THREE.Group();
        scene.add(crystalGroup);
        crystalGroup.position.x = 2.4; // Position towards the right side of the banner

        // Inner Core (Glowing emerald octahedron)
        const coreGeo = new THREE.OctahedronGeometry(1.0, 0);
        const coreMat = new THREE.MeshPhongMaterial({
            color: 0x1B5E3F,
            emissive: 0x166534,
            specular: 0xA3E635,
            shininess: 90,
            flatShading: true,
            transparent: true,
            opacity: 0.92
        });
        const coreMesh = new THREE.Mesh(coreGeo, coreMat);
        crystalGroup.add(coreMesh);

        // Outer Wireframe Cage (Golden-Lime highlight)
        const wireGeo = new THREE.IcosahedronGeometry(1.45, 1);
        const wireMat = new THREE.MeshBasicMaterial({
            color: 0x10B981,
            wireframe: true,
            transparent: true,
            opacity: 0.45
        });
        const wireMesh = new THREE.Mesh(wireGeo, wireMat);
        crystalGroup.add(wireMesh);

        // Orbital Ring 1
        const ringGeo1 = new THREE.TorusGeometry(2.1, 0.02, 16, 100);
        const ringMat1 = new THREE.MeshBasicMaterial({ color: 0x86EFAC, transparent: true, opacity: 0.6 });
        const ring1 = new THREE.Mesh(ringGeo1, ringMat1);
        ring1.rotation.x = Math.PI / 3;
        crystalGroup.add(ring1);

        // Orbital Ring 2
        const ringGeo2 = new THREE.TorusGeometry(1.85, 0.015, 16, 100);
        const ringMat2 = new THREE.MeshBasicMaterial({ color: 0xF59E0B, transparent: true, opacity: 0.5 });
        const ring2 = new THREE.Mesh(ringGeo2, ringMat2);
        ring2.rotation.y = Math.PI / 4;
        crystalGroup.add(ring2);

        // Nutrient Satellites (Little spheres orbiting the core)
        const satelliteColors = [0xEF4444, 0x10B981, 0x3B82F6, 0xF59E0B]; // Red=Energy, Green=Fibre, Blue=Protein, Gold=Sugar
        const satellites = [];
        for (let i = 0; i < 4; i++) {
            const satGeo = new THREE.SphereGeometry(0.12, 16, 16);
            const satMat = new THREE.MeshPhongMaterial({
                color: satelliteColors[i],
                emissive: satelliteColors[i],
                emissiveIntensity: 0.5,
                shininess: 100
            });
            const satMesh = new THREE.Mesh(satGeo, satMat);
            crystalGroup.add(satMesh);
            satellites.push({
                mesh: satMesh,
                angle: (i * Math.PI) / 2,
                radius: 1.85 + (i * 0.15),
                speed: 0.015 + (i * 0.005)
            });
        }

        // 3D Laser Scanning Plane
        const scanGeo = new THREE.PlaneGeometry(3.6, 0.04);
        const scanMat = new THREE.MeshBasicMaterial({
            color: 0x34D399,
            side: THREE.DoubleSide,
            transparent: true,
            opacity: 0.8
        });
        const scanBeam = new THREE.Mesh(scanGeo, scanMat);
        scanBeam.rotation.x = Math.PI / 2;
        crystalGroup.add(scanBeam);

        // Ambient Floating Particles
        const partCount = 120;
        const partGeo = new THREE.BufferGeometry();
        const positions = new Float32Array(partCount * 3);
        for (let i = 0; i < partCount * 3; i += 3) {
            positions[i] = (Math.random() - 0.5) * 8;
            positions[i + 1] = (Math.random() - 0.5) * 4;
            positions[i + 2] = (Math.random() - 0.5) * 5;
        }
        partGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        const partMat = new THREE.PointsMaterial({
            color: 0x10B981,
            size: 0.05,
            transparent: true,
            opacity: 0.6
        });
        const particleSystem = new THREE.Points(partGeo, partMat);
        scene.add(particleSystem);

        // Lighting
        const ambientLight = new THREE.AmbientLight(0xFFFFFF, 0.9);
        scene.add(ambientLight);

        const pointLight = new THREE.PointLight(0xA3E635, 1.8, 50);
        pointLight.position.set(5, 5, 5);
        scene.add(pointLight);

        const fillLight = new THREE.PointLight(0x3B82F6, 1.2, 50);
        fillLight.position.set(-5, -3, 3);
        scene.add(fillLight);

        // Mouse Tracking & Interaction
        let mouseX = 0;
        let mouseY = 0;
        let targetRotX = 0;
        let targetRotY = 0;
        let turboSpeed = 1.0;

        container.addEventListener('mousemove', (e) => {
            const rect = container.getBoundingClientRect();
            mouseX = ((e.clientX - rect.left) / rect.width) * 2 - 1;
            mouseY = -(((e.clientY - rect.top) / rect.height) * 2 - 1);
            targetRotY = mouseX * 0.9;
            targetRotX = -mouseY * 0.7;
        });

        container.addEventListener('mouseleave', () => {
            targetRotX = 0;
            targetRotY = 0;
        });

        // Controls
        document.getElementById('btn-reset').addEventListener('click', () => {
            targetRotX = 0;
            targetRotY = 0;
            crystalGroup.rotation.set(0, 0, 0);
            turboSpeed = 1.0;
        });

        document.getElementById('btn-spin').addEventListener('click', () => {
            turboSpeed = turboSpeed === 1.0 ? 3.5 : 1.0;
        });

        // Responsive Resize
        window.addEventListener('resize', () => {
            camera.aspect = container.clientWidth / container.clientHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(container.clientWidth, container.clientHeight);
        });

        // Animation Loop
        let clock = new THREE.Clock();
        function animate() {
            requestAnimationFrame(animate);
            const delta = clock.getDelta();
            const elapsed = clock.getElapsedTime() * turboSpeed;

            // Smooth spring damping for mouse tilt
            crystalGroup.rotation.y += (targetRotY - crystalGroup.rotation.y) * 0.05 + (0.008 * turboSpeed);
            crystalGroup.rotation.x += (targetRotX - crystalGroup.rotation.x) * 0.05 + (0.004 * turboSpeed);

            // Rotate inner core opposite to outer cage
            coreMesh.rotation.y += 0.012 * turboSpeed;
            coreMesh.rotation.z += 0.008 * turboSpeed;
            wireMesh.rotation.y -= 0.006 * turboSpeed;
            ring1.rotation.z += 0.01 * turboSpeed;
            ring2.rotation.x += 0.008 * turboSpeed;

            // Animate 3D Laser Beam up and down
            scanBeam.position.y = Math.sin(elapsed * 2.2) * 1.5;

            // Animate Satellites
            satellites.forEach((sat) => {
                sat.angle += sat.speed * turboSpeed;
                sat.mesh.position.x = Math.cos(sat.angle) * sat.radius;
                sat.mesh.position.z = Math.sin(sat.angle) * sat.radius;
                sat.mesh.position.y = Math.sin(sat.angle * 2) * 0.4;
            });

            // Slowly drift particles
            particleSystem.rotation.y += 0.001 * turboSpeed;

            renderer.render(scene, camera);
        }

        animate();
      </script>
    </body>
    </html>
    """
    html_code = html_template.replace("__HEIGHT__", str(height))
    components.html(html_code, height=height + 10, scrolling=False)
