import os
import uvicorn
import yt_dlp
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

load_dotenv(".env")

BASE_URL = os.getenv("BASE_URL", "https://playflx-yt.onrender.com")

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# =====================================================================================
# HOME PAGE
# =====================================================================================
@app.get("/", response_class=HTMLResponse)
async def home():
    return HTMLResponse(content="""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PlayFlx - YouTube Direct Links</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background: #0a0a0a; color: white; font-family: system-ui; }
        .card { background: #1a1a1a; border-radius: 16px; padding: 30px; }
        input { background: #2a2a2a; border: 1px solid #444; color: white; padding: 14px 20px; border-radius: 10px; width: 100%; font-size: 16px; }
        input:focus { outline: none; border-color: #6366f1; }
        .btn { padding: 14px 30px; border-radius: 10px; font-weight: 600; cursor: pointer; border: none; transition: all 0.3s; }
        .btn-primary { background: #6366f1; color: white; }
        .btn-primary:hover { background: #4f46e5; transform: translateY(-2px); }
        .btn-success { background: #22c55e; color: white; }
        .btn-success:hover { background: #16a34a; }
        .result-box { background: #1a1a1a; border-radius: 12px; padding: 20px; margin-top: 20px; display: none; }
        .link-input { font-family: monospace; font-size: 13px; padding: 10px; }
    </style>
</head>
<body class="min-h-screen flex flex-col">
    <header class="p-6 text-center">
        <h1 class="text-3xl font-bold text-indigo-400">▶️ PlayFlx YouTube</h1>
        <p class="text-gray-400 mt-2">Get Direct MP4 Links — Use in Any Player!</p>
    </header>
    
    <main class="flex-grow flex items-center justify-center px-4">
        <div class="max-w-2xl w-full">
            <div class="card">
                <h2 class="text-xl font-semibold mb-4">🎬 Get Video Link</h2>
                <p class="text-gray-400 mb-3 text-sm">Enter YouTube URL or Video ID</p>
                
                <div class="flex gap-3 mb-3">
                    <input type="text" id="videoInput" placeholder="dQw4w9WgXcQ or paste full URL" value="dQw4w9WgXcQ">
                    <button class="btn btn-primary" onclick="getLink()">Get Link</button>
                </div>
                
                <div class="flex gap-2 text-xs text-gray-500">
                    <span>Examples:</span>
                    <button class="text-indigo-400 hover:underline" onclick="setInput('dQw4w9WgXcQ')">Rick Astley</button>
                    <button class="text-indigo-400 hover:underline" onclick="setInput('kJQP7kiw5Fk')">Despacito</button>
                    <button class="text-indigo-400 hover:underline" onclick="setInput('JGwWNGJdvx8')">Shape of You</button>
                </div>
            </div>
            
            <div id="loadingBox" class="text-center mt-4" style="display:none;">
                <div class="spinner-border text-indigo-400" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="text-gray-400 mt-2">Fetching video info...</p>
            </div>
            
            <div id="resultBox" class="result-box">
                <h3 id="videoTitle" class="text-lg font-semibold mb-2"></h3>
                <p id="videoInfo" class="text-gray-400 text-sm mb-4"></p>
                
                <div class="space-y-3">
                    <div>
                        <label class="text-xs text-gray-500">🔗 Direct MP4 Link (Expires ~6h):</label>
                        <div class="flex gap-2 mt-1">
                            <input type="text" id="mp4Link" class="link-input" readonly>
                            <button class="btn btn-success" onclick="copyText('mp4Link')">Copy</button>
                        </div>
                    </div>
                    
                    <div>
                        <label class="text-xs text-gray-500">📋 Permanent Watch Link:</label>
                        <div class="flex gap-2 mt-1">
                            <input type="text" id="watchLink" class="link-input" readonly>
                            <button class="btn btn-success" onclick="copyText('watchLink')">Copy</button>
                            <a id="watchBtn" href="#" target="_blank" class="btn btn-primary">Open</a>
                        </div>
                    </div>
                    
                    <div class="flex gap-2 mt-4">
                        <button class="btn btn-success flex-1" onclick="window.open(document.getElementById('mp4Link').value, '_blank')">▶ Stream Now</button>
                        <button class="btn btn-primary flex-1" onclick="window.open(document.getElementById('watchLink').value, '_blank')">📺 Watch Page</button>
                    </div>
                </div>
            </div>
        </div>
    </main>
    
    <footer class="p-4 text-center text-gray-500 text-sm">
        © 2025 PlayFlx • YouTube Direct Links
    </footer>
    
    <script>
        function setInput(id) { document.getElementById('videoInput').value = id; getLink(); }
        
        async function getLink() {
            const input = document.getElementById('videoInput').value.trim();
            let videoId = input;
            
            if (input.includes('youtube.com/watch?v=')) videoId = input.split('v=')[1].split('&')[0];
            else if (input.includes('youtu.be/')) videoId = input.split('/').pop().split('?')[0];
            else if (input.includes('youtube.com/shorts/')) videoId = input.split('/shorts/')[1].split('?')[0];
            
            if (!videoId || videoId.length < 5) return alert('Invalid video ID!');
            
            document.getElementById('loadingBox').style.display = 'block';
            document.getElementById('resultBox').style.display = 'none';
            
            try {
                const res = await fetch('/api/video/' + videoId);
                const data = await res.json();
                
                document.getElementById('loadingBox').style.display = 'none';
                
                if (data.success) {
                    document.getElementById('videoTitle').textContent = data.title;
                    document.getElementById('videoInfo').textContent = `⏱ ${data.duration}s | 🎬 ${data.quality || 'HD'}`;
                    document.getElementById('mp4Link').value = data.mp4_url;
                    document.getElementById('watchLink').value = data.watch_url;
                    document.getElementById('watchBtn').href = data.watch_url;
                    document.getElementById('resultBox').style.display = 'block';
                } else {
                    alert('Error: ' + (data.error || 'Failed to get video'));
                }
            } catch (e) {
                document.getElementById('loadingBox').style.display = 'none';
                alert('Network error: ' + e.message);
            }
        }
        
        function copyText(id) {
            const input = document.getElementById(id);
            input.select();
            document.execCommand('copy');
            alert('✅ Copied!');
        }
    </script>
</body>
</html>""")

# =====================================================================================
# API: GET VIDEO MP4 LINK
# =====================================================================================
@app.get("/api/video/{video_id}")
async def get_video(video_id: str):
    """Extract direct MP4 link using yt-dlp"""
    try:
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f'https://www.youtube.com/watch?v={video_id}', download=False)
            mp4_url = info.get('url', '')
        
        return JSONResponse({
            "success": True,
            "video_id": video_id,
            "title": info.get('title', 'Unknown'),
            "duration": info.get('duration', 0),
            "quality": f"{info.get('width', '')}p" if info.get('width') else 'HD',
            "thumbnail": info.get('thumbnail', ''),
            "mp4_url": mp4_url,
            "watch_url": f"{BASE_URL}/watch/{video_id}"
        })
        
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e),
            "watch_url": f"{BASE_URL}/watch/{video_id}"
        }, status_code=400)

# =====================================================================================
# WATCH PAGE (EMBED)
# =====================================================================================
@app.get("/watch/{video_id}", response_class=HTMLResponse)
async def watch_page(request: Request, video_id: str):
    return HTMLResponse(content=f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Watch - PlayFlx</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {{ background: #000; color: white; font-family: system-ui; }}
        .container {{ max-width: 1000px; margin: 0 auto; padding: 20px; }}
        .player-box {{ background: #111; border-radius: 16px; overflow: hidden; }}
        .info-box {{ background: #1a1a1a; border-radius: 12px; padding: 20px; margin-top: 20px; }}
        .btn {{ padding: 12px 25px; border-radius: 8px; font-weight: 600; cursor: pointer; border: none; }}
        .btn-primary {{ background: #6366f1; color: white; }}
    </style>
</head>
<body>
    <div class="container">
        <h1 class="text-2xl font-bold my-4">▶️ PlayFlx Player</h1>
        
        <div class="player-box">
            <iframe width="100%" height="500" 
                    src="https://www.youtube.com/embed/{video_id}?autoplay=0&rel=0&modestbranding=1"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowfullscreen style="border:none;">
            </iframe>
        </div>
        
        <div class="info-box">
            <h2 class="text-xl font-semibold mb-3">📋 Share Links</h2>
            
            <div class="mb-3">
                <label class="text-sm text-gray-400">Permanent Link:</label>
                <div class="flex gap-2 mt-1">
                    <input type="text" value="{BASE_URL}/watch/{video_id}" class="bg-gray-800 border border-gray-700 text-white p-2 rounded w-full font-mono text-sm" readonly>
                    <button class="btn btn-primary" onclick="navigator.clipboard.writeText('{BASE_URL}/watch/{video_id}')">Copy</button>
                </div>
            </div>
            
            <a href="/api/video/{video_id}" class="text-indigo-400 hover:underline text-sm">📡 Get Direct MP4 API</a>
        </div>
    </div>
</body>
</html>""")

# =====================================================================================
@app.api_route("/health", methods=["GET", "HEAD"])
async def health():
    return JSONResponse({"status": "ok"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, log_level="info")
