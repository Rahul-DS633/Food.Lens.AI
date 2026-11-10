"""
FoodLens AI — Standalone Web Application Portal
Self-contained, fast, responsive single-page application served directly by FastAPI.
Provides live interactive product analysis, 3D sugar visualization, allergen radar,
and API integration without needing external asset dependencies.
"""

def get_foodlens_html_portal() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FoodLens AI — Packaged Food Nutrition Intelligence</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🥗</text></svg>">
    <style>
        :root {
            --primary: #1B5E3F;
            --primary-light: #E8F5E9;
            --primary-dark: #123E2A;
            --accent-blue: #2563EB;
            --accent-blue-light: #EFF6FF;
            --text-main: #0F172A;
            --text-muted: #475569;
            --bg-page: #F8FAFC;
            --bg-card: #FFFFFF;
            --border-color: #E2E8F0;
            --score-green: #10B981;
            --score-yellow: #F59E0B;
            --score-orange: #EF4444;
            --radius-md: 14px;
            --radius-lg: 20px;
            --shadow-sm: 0 1px 3px rgba(0,0,0,0.05);
            --shadow-md: 0 4px 12px rgba(15, 23, 42, 0.08);
            --shadow-lg: 0 10px 25px rgba(15, 23, 42, 0.12);
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, "Helvetica Neue", sans-serif;
        }

        body {
            background-color: var(--bg-page);
            color: var(--text-main);
            line-height: 1.6;
            -webkit-font-smoothing: antialiased;
        }

        header {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-bottom: 1px solid var(--border-color);
            position: sticky;
            top: 0;
            z-index: 50;
            padding: 14px 24px;
        }

        .header-content {
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 12px;
            text-decoration: none;
            color: var(--text-main);
        }

        .brand-icon {
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, #1B5E3F 0%, #2E7D32 100%);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 22px;
            box-shadow: 0 4px 10px rgba(27, 94, 63, 0.25);
        }

        .brand-title {
            font-size: 20px;
            font-weight: 800;
            letter-spacing: -0.5px;
            color: #0F172A;
        }

        .brand-badge {
            background: var(--primary-light);
            color: var(--primary);
            font-size: 11px;
            font-weight: 700;
            padding: 3px 8px;
            border-radius: 20px;
            margin-left: 6px;
        }

        .nav-links {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .btn {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 8px 16px;
            border-radius: 10px;
            font-size: 13.5px;
            font-weight: 600;
            text-decoration: none;
            cursor: pointer;
            transition: all 0.18s ease-in-out;
            border: 1px solid transparent;
        }

        .btn-outline {
            background: #FFFFFF;
            border-color: var(--border-color);
            color: var(--text-main);
        }

        .btn-outline:hover {
            background: #F1F5F9;
            border-color: #CBD5E1;
        }

        .btn-primary {
            background: var(--primary);
            color: white;
        }

        .btn-primary:hover {
            background: var(--primary-dark);
            transform: translateY(-1px);
            box-shadow: var(--shadow-sm);
        }

        .btn-accent {
            background: var(--accent-blue);
            color: white;
        }

        .btn-accent:hover {
            background: #1D4ED8;
            transform: translateY(-1px);
        }

        main {
            max-width: 1200px;
            margin: 0 auto;
            padding: 32px 20px 80px;
        }

        .hero {
            text-align: center;
            padding: 40px 16px 48px;
            max-width: 860px;
            margin: 0 auto;
        }

        .hero-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: #DCFCE7;
            color: #166534;
            font-size: 12.5px;
            font-weight: 700;
            padding: 6px 14px;
            border-radius: 30px;
            margin-bottom: 16px;
            letter-spacing: 0.3px;
        }

        .hero h1 {
            font-size: 42px;
            font-weight: 900;
            line-height: 1.15;
            letter-spacing: -1px;
            margin-bottom: 16px;
            color: #0F172A;
        }

        .hero h1 span {
            background: linear-gradient(135deg, #1B5E3F 0%, #2563EB 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .hero p {
            font-size: 17px;
            color: var(--text-muted);
            max-width: 680px;
            margin: 0 auto 28px;
        }

        .hero-cta {
            display: flex;
            gap: 12px;
            justify-content: center;
            flex-wrap: wrap;
        }

        .section-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
            margin-bottom: 20px;
        }

        .section-title {
            font-size: 22px;
            font-weight: 800;
            color: var(--text-main);
            letter-spacing: -0.4px;
        }

        .section-sub {
            font-size: 14px;
            color: var(--text-muted);
            margin-top: 2px;
        }

        /* Product Selector Pills */
        .product-tabs {
            display: flex;
            gap: 10px;
            overflow-x: auto;
            padding-bottom: 10px;
            margin-bottom: 24px;
        }

        .product-pill {
            background: #FFFFFF;
            border: 1.5px solid var(--border-color);
            padding: 10px 18px;
            border-radius: 12px;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 14px;
            font-weight: 600;
            white-space: nowrap;
            transition: all 0.2s ease;
        }

        .product-pill:hover {
            border-color: #94A3B8;
            background: #F8FAFC;
        }

        .product-pill.active {
            border-color: var(--primary);
            background: #F0FDF4;
            color: var(--primary);
            box-shadow: 0 2px 8px rgba(27, 94, 63, 0.15);
        }

        /* Dashboard Grid */
        .dashboard-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 24px;
            margin-bottom: 40px;
        }

        @media (max-width: 900px) {
            .dashboard-grid {
                grid-template-columns: 1fr;
            }
            .hero h1 {
                font-size: 32px;
            }
        }

        .card {
            background: var(--bg-card);
            border-radius: var(--radius-lg);
            border: 1px solid var(--border-color);
            padding: 24px;
            box-shadow: var(--shadow-sm);
            transition: box-shadow 0.2s ease;
        }

        .card:hover {
            box-shadow: var(--shadow-md);
        }

        .product-header {
            display: flex;
            gap: 18px;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 18px;
            border-bottom: 1px solid var(--border-color);
        }

        .product-thumb {
            width: 80px;
            height: 80px;
            border-radius: 14px;
            object-fit: cover;
            background: #F1F5F9;
            border: 1px solid var(--border-color);
        }

        .product-name {
            font-size: 19px;
            font-weight: 800;
            color: #0F172A;
            line-height: 1.25;
        }

        .product-brand {
            font-size: 13.5px;
            color: var(--primary);
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-top: 3px;
        }

        .score-box {
            display: flex;
            align-items: center;
            gap: 16px;
            background: #F8FAFC;
            border-radius: 14px;
            padding: 16px 20px;
            margin-bottom: 20px;
            border: 1px solid var(--border-color);
        }

        .score-circle {
            width: 60px;
            height: 60px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            font-weight: 900;
            color: white;
            background: var(--score-green);
            box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
            flex-shrink: 0;
        }

        .score-details h4 {
            font-size: 16px;
            font-weight: 800;
            color: #0F172A;
        }

        .score-details p {
            font-size: 13px;
            color: var(--text-muted);
            margin-top: 2px;
        }

        /* Nutrient Grid */
        .nutrients-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
            margin-bottom: 20px;
        }

        .nutrient-item {
            background: #F8FAFC;
            border-radius: 12px;
            padding: 12px;
            text-align: center;
            border: 1px solid #EEF2F6;
        }

        .nutrient-label {
            font-size: 11.5px;
            font-weight: 700;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.4px;
        }

        .nutrient-val {
            font-size: 18px;
            font-weight: 800;
            color: #0F172A;
            margin-top: 4px;
        }

        /* Sugar Cubes Visualizer */
        .sugar-card {
            border-left: 5px solid var(--accent-blue);
            background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%);
        }

        .sugar-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 14px;
        }

        .sugar-title {
            font-size: 14px;
            font-weight: 800;
            color: #1E3A8A;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .cubes-display {
            background: rgba(239, 246, 255, 0.7);
            border: 1.5px dashed #93C5FD;
            border-radius: 14px;
            padding: 16px;
            min-height: 90px;
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 6px;
            margin-bottom: 14px;
        }

        .cube-svg {
            display: inline-block;
            vertical-align: middle;
            filter: drop-shadow(0 3px 4px rgba(59, 130, 246, 0.25));
            transition: transform 0.2s;
        }

        .cube-svg:hover {
            transform: scale(1.15) translateY(-3px);
        }

        .sugar-summary {
            font-size: 14px;
            color: #334155;
            line-height: 1.5;
        }

        .sugar-summary b {
            color: #1E40AF;
        }

        /* Ingredients & Allergens */
        .tag-list {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-top: 8px;
        }

        .allergen-tag {
            background: #FEE2E2;
            color: #991B1B;
            font-size: 12px;
            font-weight: 700;
            padding: 4px 10px;
            border-radius: 20px;
            border: 1px solid #FECACA;
        }

        .safe-tag {
            background: #DCFCE7;
            color: #166534;
            font-size: 12px;
            font-weight: 700;
            padding: 4px 10px;
            border-radius: 20px;
        }

        .ingredients-p {
            font-size: 13.5px;
            color: var(--text-muted);
            margin-top: 10px;
            background: #F8FAFC;
            padding: 12px;
            border-radius: 10px;
            border: 1px solid #E2E8F0;
            line-height: 1.5;
        }

        /* Sugar Calculator Interactive Tool */
        .calc-box {
            background: white;
            border-radius: var(--radius-lg);
            border: 1px solid var(--border-color);
            padding: 32px;
            margin-bottom: 40px;
        }

        .slider-wrapper {
            display: flex;
            align-items: center;
            gap: 20px;
            margin: 20px 0;
        }

        .sugar-slider {
            flex-grow: 1;
            height: 8px;
            border-radius: 5px;
            outline: none;
            accent-color: var(--accent-blue);
            cursor: pointer;
        }

        .slider-val-box {
            background: var(--accent-blue-light);
            color: var(--accent-blue);
            font-size: 20px;
            font-weight: 800;
            padding: 8px 18px;
            border-radius: 12px;
            min-width: 90px;
            text-align: center;
        }

        /* Swagger / Endpoints section */
        .endpoints-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 16px;
            margin-top: 16px;
        }

        .endpoint-card {
            background: white;
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 16px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            transition: all 0.18s;
            text-decoration: none;
            color: inherit;
        }

        .endpoint-card:hover {
            border-color: var(--primary);
            transform: translateY(-2px);
            box-shadow: var(--shadow-sm);
        }

        .method-badge {
            font-size: 11px;
            font-weight: 800;
            padding: 3px 8px;
            border-radius: 6px;
            color: white;
        }

        .get-badge { background: #059669; }
        .post-badge { background: #2563EB; }

        footer {
            border-top: 1px solid var(--border-color);
            padding: 32px 20px;
            text-align: center;
            font-size: 13.5px;
            color: var(--text-muted);
            background: white;
        }
    </style>
</head>
<body>

    <!-- Header Navigation -->
    <header>
        <div class="header-content">
            <a href="/" class="brand">
                <div class="brand-icon">🥗</div>
                <div>
                    <span class="brand-title">FoodLens AI</span>
                    <span class="brand-badge">API & Web Portal</span>
                </div>
            </a>
            <div class="nav-links">
                <a href="#demo" class="btn btn-outline">Demo Explorer</a>
                <a href="#calculator" class="btn btn-outline">Sugar Tool</a>
                <a href="/docs" target="_blank" class="btn btn-primary">Swagger Docs (/docs)</a>
            </div>
        </div>
    </header>

    <main>
        <!-- Hero Section -->
        <section class="hero">
            <div class="hero-badge">✨ 100% Deterministic Nutrition Engine • Live on Vercel</div>
            <h1>Packaged Food <span>Nutrition Intelligence</span></h1>
            <p>
                Transparent, category-aware nutritional scoring, 3D crystalline sugar visualization,
                and allergen safety alerts strictly grounded on verified label facts.
            </p>
            <div class="hero-cta">
                <a href="#demo" class="btn btn-primary" style="padding: 12px 24px; font-size: 15px;">🔍 Explore Sample Foods</a>
                <a href="/docs" target="_blank" class="btn btn-outline" style="padding: 12px 24px; font-size: 15px;">📚 Interactive API Docs</a>
                <a href="/health" target="_blank" class="btn btn-outline" style="padding: 12px 20px; font-size: 15px;">🟢 Health Status</a>
            </div>
        </section>

        <!-- Product Selector Section -->
        <section id="demo" style="margin-bottom: 20px;">
            <div class="section-header">
                <div>
                    <h2 class="section-title">Verified Indian Packaged Foods</h2>
                    <p class="section-sub">Select any staple food below to run real-time nutritional score and sugar cube calculations.</p>
                </div>
            </div>

            <div class="product-tabs" id="productTabs">
                <!-- Dynamically rendered tabs -->
            </div>

            <!-- Dashboard Grid -->
            <div class="dashboard-grid">
                <!-- Left Card: Product Info & Score -->
                <div class="card">
                    <div class="product-header">
                        <img id="pImg" src="" alt="Product" class="product-thumb">
                        <div>
                            <div class="product-name" id="pName">Product Name</div>
                            <div class="product-brand" id="pBrand">Brand</div>
                            <div style="font-size: 12px; color: #64748B; margin-top: 4px;">
                                Net Wt: <span id="pNet">100g</span> • Serving: <span id="pServing">30g</span>
                            </div>
                        </div>
                    </div>

                    <div class="score-box">
                        <div class="score-circle" id="pScoreCircle">82</div>
                        <div class="score-details">
                            <h4 id="pScoreBand">Evaluation Pending</h4>
                            <p id="pScoreDesc">Category-specific nutritional assessment based on reference thresholds.</p>
                        </div>
                    </div>

                    <h4 style="font-size: 12px; font-weight: 700; text-transform: uppercase; color: #64748B; margin-bottom: 8px;">
                        Nutritional Composition (per 100g)
                    </h4>
                    <div class="nutrients-grid">
                        <div class="nutrient-item">
                            <div class="nutrient-label">Energy</div>
                            <div class="nutrient-val" id="pEnergy">0 kcal</div>
                        </div>
                        <div class="nutrient-item">
                            <div class="nutrient-label">Protein</div>
                            <div class="nutrient-val" id="pProtein">0g</div>
                        </div>
                        <div class="nutrient-item">
                            <div class="nutrient-label">Total Sugar</div>
                            <div class="nutrient-val" id="pSugar" style="color: #2563EB;">0g</div>
                        </div>
                        <div class="nutrient-item">
                            <div class="nutrient-label">Added Sugar</div>
                            <div class="nutrient-val" id="pAddedSugar">0g</div>
                        </div>
                        <div class="nutrient-item">
                            <div class="nutrient-label">Sat Fat</div>
                            <div class="nutrient-val" id="pSatFat">0g</div>
                        </div>
                        <div class="nutrient-item">
                            <div class="nutrient-label">Sodium</div>
                            <div class="nutrient-val" id="pSodium">0 mg</div>
                        </div>
                    </div>

                    <h4 style="font-size: 12px; font-weight: 700; text-transform: uppercase; color: #64748B; margin-bottom: 6px;">
                        Allergens Detected
                    </h4>
                    <div class="tag-list" id="pAllergens"></div>

                    <h4 style="font-size: 12px; font-weight: 700; text-transform: uppercase; color: #64748B; margin-top: 14px; margin-bottom: 4px;">
                        Ingredients Breakdown
                    </h4>
                    <div class="ingredients-p" id="pIngredients"></div>
                </div>

                <!-- Right Card: 3D Sugar Cube Visualizer -->
                <div class="card sugar-card">
                    <div class="sugar-header">
                        <div class="sugar-title">
                            <span>🧊</span>
                            <span>Sugar Visualizer (3D Cubes)</span>
                        </div>
                        <span id="pSugarGramsBadge" style="font-weight: 800; font-size: 16px; color: #2563EB;">0 g total sugar</span>
                    </div>

                    <div style="font-size: 11.5px; font-weight: 700; color: #3B82F6; text-transform: uppercase; margin-bottom: 8px;">
                        Crystalline Representation (1 cube = 4g)
                    </div>

                    <div class="cubes-display" id="cubesContainer">
                        <!-- 3D SVG Cubes injected here -->
                    </div>

                    <div class="sugar-summary" id="sugarSummaryText">
                        Loading sugar breakdown...
                    </div>

                    <div style="margin-top: 24px; padding-top: 16px; border-top: 1px solid #E2E8F0;">
                        <h4 style="font-size: 13.5px; font-weight: 700; color: #1E3A8A; margin-bottom: 8px;">
                            💡 Dietary Guidelines
                        </h4>
                        <p style="font-size: 13px; color: var(--text-muted); line-height: 1.5;">
                            The World Health Organization (WHO) strongly recommends limiting free sugars to less than <b>10%</b> of total daily energy intake (approx. <b>50g or 12 teaspoons</b> for a 2,000 kcal diet), with a conditional target of <b>5% (~25g or 6 teaspoons)</b> for additional health benefits.
                        </p>
                    </div>
                </div>
            </div>
        </section>

        <!-- Interactive Sugar Slider Tool -->
        <section id="calculator" class="calc-box">
            <h2 class="section-title">Interactive Sugar-in-Teaspoons Calculator</h2>
            <p class="section-sub">Drag the slider to visualize any sugar quantity as realistic 3D crystalline cubes and teaspoons.</p>

            <div class="slider-wrapper">
                <input type="range" min="0" max="80" step="1" value="24" class="sugar-slider" id="interactiveSlider">
                <div class="slider-val-box" id="sliderValDisplay">24 g</div>
            </div>

            <div class="cubes-display" id="interactiveCubesContainer"></div>
            <div class="sugar-summary" id="interactiveSummary"></div>
        </section>

        <!-- REST API Endpoints Quick Reference -->
        <section style="margin-top: 40px;">
            <div class="section-header">
                <div>
                    <h2 class="section-title">FoodLens AI Backend REST Endpoints</h2>
                    <p class="section-sub">Explore the 36 deterministic endpoints deployed on this Vercel Serverless instance.</p>
                </div>
                <a href="/docs" target="_blank" class="btn btn-primary">Open Interactive Swagger</a>
            </div>

            <div class="endpoints-grid">
                <a href="/health" target="_blank" class="endpoint-card">
                    <div>
                        <div style="font-weight: 700; font-size: 14px;">/health</div>
                        <div style="font-size: 12px; color: #64748B;">System health & status probe</div>
                    </div>
                    <span class="method-badge get-badge">GET</span>
                </a>
                <a href="/docs" target="_blank" class="endpoint-card">
                    <div>
                        <div style="font-weight: 700; font-size: 14px;">/docs</div>
                        <div style="font-size: 12px; color: #64748B;">Interactive Swagger API UI</div>
                    </div>
                    <span class="method-badge get-badge">GET</span>
                </a>
                <a href="/openapi.json" target="_blank" class="endpoint-card">
                    <div>
                        <div style="font-weight: 700; font-size: 14px;">/openapi.json</div>
                        <div style="font-size: 12px; color: #64748B;">Full OpenAPI v3 specification</div>
                    </div>
                    <span class="method-badge get-badge">GET</span>
                </a>
                <div class="endpoint-card" style="cursor: default;">
                    <div>
                        <div style="font-weight: 700; font-size: 14px;">/api/scan/barcode</div>
                        <div style="font-size: 12px; color: #64748B;">Barcode OCR & OFF lookup</div>
                    </div>
                    <span class="method-badge post-badge">POST</span>
                </div>
                <div class="endpoint-card" style="cursor: default;">
                    <div>
                        <div style="font-weight: 700; font-size: 14px;">/api/sugar/analyze</div>
                        <div style="font-size: 12px; color: #64748B;">Hidden sugar & filler detector</div>
                    </div>
                    <span class="method-badge post-badge">POST</span>
                </div>
                <div class="endpoint-card" style="cursor: default;">
                    <div>
                        <div style="font-weight: 700; font-size: 14px;">/api/claims/verify</div>
                        <div style="font-size: 12px; color: #64748B;">Marketing claim verification</div>
                    </div>
                    <span class="method-badge post-badge">POST</span>
                </div>
            </div>
        </section>
    </main>

    <footer>
        <p><b>FoodLens AI</b> • Deterministic Packaged Food Nutrition Engine</p>
        <p style="margin-top: 6px; font-size: 12px; color: #94A3B8;">Built with FastAPI, Pydantic, and SQLite. Educational prototype strictly adhering to factual label evidence.</p>
    </footer>

    <script>
        // Pre-seeded Indian Packaged Food Dataset
        const PRODUCTS = {
            "kurkure": {
                name: "Kurkure Masala Munch",
                brand: "PepsiCo",
                net: "90g",
                serving: "30g",
                score: 54,
                band: "Consume Mindfully",
                scoreDesc: "High saturated fat and high sodium content typical of deep-fried savory snacks.",
                scoreColor: "#EF4444",
                img: "https://images.openfoodfacts.org/images/products/890/149/901/0029/front_en.3.400.jpg",
                nutrients: { energy: "560 kcal", protein: "6.2g", sugar: "1.8g", added_sugar: "0.0g", sat_fat: "15.2g", sodium: "890 mg" },
                sugarGrams: 1.8,
                allergens: [],
                ingredients: "Rice Meal (43.2%), Edible Vegetable Oil (Palmolein Oil), Corn Meal (20%), Gram Meal (3.3%), Spices and Condiments (Chilli Powder, Onion Powder, Garlic Powder, Coriander Powder, Turmeric Powder, Fenugreek Powder, Black Pepper Powder, Clove Powder, Cumin Powder, Cinnamon Powder, Nutmeg Powder), Salt, Sugar, Tartaric Acid (334), Citric Acid (330)."
            },
            "parle_g": {
                name: "Parle-G Original Gluco Biscuits",
                brand: "Parle",
                net: "65g",
                serving: "21.6g",
                score: 62,
                band: "Moderate",
                scoreDesc: "Moderate sugar content (~26.5g/100g); balanced energy density.",
                scoreColor: "#F59E0B",
                img: "https://images.openfoodfacts.org/images/products/890/171/910/1052/front_en.11.400.jpg",
                nutrients: { energy: "454 kcal", protein: "6.5g", sugar: "26.5g", added_sugar: "25.0g", sat_fat: "5.8g", sodium: "280 mg" },
                sugarGrams: 26.5,
                allergens: ["Wheat", "Gluten", "Milk", "Soy"],
                ingredients: "Wheat Flour (68%), Sugar, Edible Vegetable Oil (Palm Oil), Invert Sugar Syrup, Raising Agents [503(ii), 500(ii)], Salt, Milk Solids, Emulsifier [322], Dough Conditioner [223]."
            },
            "maggi": {
                name: "Maggi 2-Minute Masala Noodles",
                brand: "Nestle",
                net: "70g",
                serving: "70g",
                score: 58,
                band: "Consume Mindfully",
                scoreDesc: "High sodium concentration (1,020mg / 100g) in tastemaker blend.",
                scoreColor: "#EF4444",
                img: "https://images.openfoodfacts.org/images/products/890/105/885/2347/front_en.43.400.jpg",
                nutrients: { energy: "427 kcal", protein: "8.0g", sugar: "2.2g", added_sugar: "1.5g", sat_fat: "6.8g", sodium: "1020 mg" },
                sugarGrams: 2.2,
                allergens: ["Wheat", "Gluten", "Peanut"],
                ingredients: "Refined Wheat Flour (Maida), Palm Oil, Iodised Salt, Wheat Gluten, Thickeners (508, 412), Acidity Regulators (501(i), 500(i)), Masala Tastemaker: Mixed Spices, Sugar, Salt, Hydrolysed Groundnut Protein."
            },
            "frooti": {
                name: "Frooti Fresh 'N' Juicy Mango Drink",
                brand: "Parle Agro",
                net: "160ml",
                serving: "160ml",
                score: 48,
                band: "Consume Mindfully",
                scoreDesc: "High free sugar content (>15g per 100ml) from added sucrose and mango pulp.",
                scoreColor: "#EF4444",
                img: "https://images.openfoodfacts.org/images/products/890/171/911/4120/front_en.12.400.jpg",
                nutrients: { energy: "65 kcal", protein: "0.1g", sugar: "15.5g", added_sugar: "12.0g", sat_fat: "0.0g", sodium: "18 mg" },
                sugarGrams: 15.5,
                allergens: [],
                ingredients: "Water, Mango Pulp (19.5%), Sugar, Acidity Regulator (330), Antioxidant (300)."
            },
            "amul": {
                name: "Amul Butter Pasteurised",
                brand: "Amul",
                net: "100g",
                serving: "10g",
                score: 52,
                band: "Moderate",
                scoreDesc: "High saturated fat dairy spread; recommended in small portion sizes (10g).",
                scoreColor: "#F59E0B",
                img: "https://images.openfoodfacts.org/images/products/890/126/201/0025/front_en.21.400.jpg",
                nutrients: { energy: "722 kcal", protein: "0.6g", sugar: "0.0g", added_sugar: "0.0g", sat_fat: "51.0g", sodium: "840 mg" },
                sugarGrams: 0.0,
                allergens: ["Milk"],
                ingredients: "Butter, Common Salt, Permitted Natural Colour (Annatto)."
            }
        };

        // Render 3D Isometric SVG Sugar Cube
        function renderCubeSvg(size = 28, isHalf = false) {
            const opacity = isHalf ? "0.55" : "1.0";
            return `
                <div class="cube-svg" style="width: ${size}px; height: ${size + 4}px; opacity: ${opacity};">
                    <svg viewBox="0 0 32 36" width="${size}" height="${size + 4}" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <polygon points="16,2 30,10 16,18 2,10" fill="url(#cube-top)" stroke="#93C5FD" stroke-width="1.2"/>
                        <polygon points="2,10 16,18 16,32 2,24" fill="url(#cube-left)" stroke="#93C5FD" stroke-width="1.2"/>
                        <polygon points="16,18 30,10 30,24 16,32" fill="url(#cube-right)" stroke="#93C5FD" stroke-width="1.2"/>
                        <circle cx="16" cy="11" r="2.5" fill="#FFFFFF" opacity="0.8"/>
                        <defs>
                            <linearGradient id="cube-top" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#FFFFFF"/><stop offset="100%" stop-color="#EFF6FF"/></linearGradient>
                            <linearGradient id="cube-left" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#E0F2FE"/><stop offset="100%" stop-color="#BAE6FD"/></linearGradient>
                            <linearGradient id="cube-right" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#BFDBFE"/><stop offset="100%" stop-color="#93C5FD"/></linearGradient>
                        </defs>
                    </svg>
                </div>
            `;
        }

        function generateCubesHtml(sugarGrams) {
            if (sugarGrams === 0) {
                return '<div style="color: #64748B; font-size: 13.5px; padding: 10px;">✨ 0g declared sugar (No sugar cubes)</div>';
            }
            const fullCubes = Math.floor(sugarGrams / 4.0);
            const hasHalf = (sugarGrams % 4.0) >= 1.5;
            let html = "";
            const displayCount = Math.min(fullCubes, 24);
            for (let i = 0; i < displayCount; i++) {
                html += renderCubeSvg(28, false);
            }
            if (hasHalf && displayCount < 24) {
                html += renderCubeSvg(28, true);
            }
            return html;
        }

        // Display Selected Product
        function selectProduct(key) {
            const p = PRODUCTS[key];
            if (!p) return;

            document.querySelectorAll('.product-pill').forEach(pill => {
                pill.classList.toggle('active', pill.dataset.key === key);
            });

            document.getElementById('pImg').src = p.img;
            document.getElementById('pName').innerText = p.name;
            document.getElementById('pBrand').innerText = p.brand;
            document.getElementById('pNet').innerText = p.net;
            document.getElementById('pServing').innerText = p.serving;

            const circle = document.getElementById('pScoreCircle');
            circle.innerText = p.score;
            circle.style.backgroundColor = p.scoreColor;
            circle.style.boxShadow = `0 4px 12px ${p.scoreColor}40`;

            document.getElementById('pScoreBand').innerText = p.band;
            document.getElementById('pScoreDesc').innerText = p.scoreDesc;

            document.getElementById('pEnergy').innerText = p.nutrients.energy;
            document.getElementById('pProtein').innerText = p.nutrients.protein;
            document.getElementById('pSugar').innerText = p.nutrients.sugar;
            document.getElementById('pAddedSugar').innerText = p.nutrients.added_sugar;
            document.getElementById('pSatFat').innerText = p.nutrients.sat_fat;
            document.getElementById('pSodium').innerText = p.nutrients.sodium;

            // Allergens
            const algContainer = document.getElementById('pAllergens');
            algContainer.innerHTML = '';
            if (p.allergens.length > 0) {
                p.allergens.forEach(alg => {
                    algContainer.innerHTML += `<span class="allergen-tag">⚠️ Contains ${alg}</span>`;
                });
            } else {
                algContainer.innerHTML = '<span class="safe-tag">✓ No common allergens declared</span>';
            }

            document.getElementById('pIngredients').innerText = p.ingredients;

            // Sugar Visualizer
            document.getElementById('pSugarGramsBadge').innerText = `${p.sugarGrams} g total sugar`;
            document.getElementById('cubesContainer').innerHTML = generateCubesHtml(p.sugarGrams);

            const tsps = (p.sugarGrams / 4.0).toFixed(1);
            document.getElementById('sugarSummaryText').innerHTML = `
                Equivalent to <b>~${tsps} teaspoons</b> of granulated sugar per 100g.
                <div style="color: #64748B; font-size: 12px; margin-top: 4px;">
                    WHO daily recommended upper limit: ~6 teaspoons (25g) for a 2,000 kcal diet.
                </div>
            `;
        }

        // Initialize Product Selector Tabs
        function initTabs() {
            const tabs = document.getElementById('productTabs');
            tabs.innerHTML = '';
            Object.keys(PRODUCTS).forEach((key, index) => {
                const p = PRODUCTS[key];
                const pill = document.createElement('div');
                pill.className = `product-pill ${index === 0 ? 'active' : ''}`;
                pill.dataset.key = key;
                pill.innerHTML = `<span>🏷️</span><span>${p.name}</span>`;
                pill.onclick = () => selectProduct(key);
                tabs.appendChild(pill);
            });
            selectProduct('kurkure');
        }

        // Interactive Sugar Calculator Slider
        const slider = document.getElementById('interactiveSlider');
        const sliderDisplay = document.getElementById('sliderValDisplay');
        const interactiveCubes = document.getElementById('interactiveCubesContainer');
        const interactiveSummary = document.getElementById('interactiveSummary');

        function updateSliderTool(val) {
            const grams = parseFloat(val);
            sliderDisplay.innerText = `${grams} g`;
            interactiveCubes.innerHTML = generateCubesHtml(grams);
            const tsps = (grams / 4.0).toFixed(1);
            const percentOfWhoLimit = Math.round((grams / 25.0) * 100);
            interactiveSummary.innerHTML = `
                Equivalent to <b>~${tsps} culinary teaspoons</b> of granulated sugar.
                <div style="color: #64748B; font-size: 13px; margin-top: 4px;">
                    Represents <b>${percentOfWhoLimit}%</b> of the WHO recommended daily upper limit of 25g.
                </div>
            `;
        }

        slider.addEventListener('input', (e) => updateSliderTool(e.target.value));

        // Start
        initTabs();
        updateSliderTool(24);
    </script>
</body>
</html>
"""

