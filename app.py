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
# DYNAMIC WATCH PAGE - AUTO-REFRESH PLAYER
# =====================================================================================
@app.get("/watch/{video_id}", response_class=HTMLResponse)
async def watch_page(request: Request, video_id: str):
    """Dynamic player — auto-updates link on every visit"""
    return HTMLResponse(content=f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>PlayFlx Player</title>
    <link href="https://vjs.zencdn.net/8.10.0/video-js.css" rel="stylesheet" />
    <style>
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{ background:#000; font-family:system-ui; }}
        #player-wrapper {{ width:100vw; height:100vh; display:flex; align-items:center; justify-content:center; position:relative; }}
        .video-js {{ width:100%; height:100%; }}
        
        .status-overlay {{ position:fixed; top:50%; left:50%; transform:translate(-50%,-50%); color:white; text-align:center; z-index:20; pointer-events:none; }}
        .spinner {{ width:40px; height:40px; border:3px solid rgba(255,255,255,0.2); border-top:3px solid #6366f1; border-radius:50%; animation:spin 0.8s linear infinite; margin:0 auto 15px; }}
        @keyframes spin {{ to {{ transform:rotate(360deg); }} }}
        
        .controls-bar {{ position:fixed; bottom:20px; right:20px; z-index:30; display:flex; gap:8px; opacity:0.5; transition:opacity 0.3s; }}
        .controls-bar:hover {{ opacity:1; }}
        .ctrl-btn {{ background:rgba(0,0,0,0.8); color:white; border:1px solid rgba(255,255,255,0.2); padding:10px 16px; border-radius:25px; cursor:pointer; font-size:12px; transition:all 0.2s; }}
        .ctrl-btn:hover {{ background:rgba(99,102,241,0.8); border-color:#6366f1; }}
        
        .toast {{ position:fixed; top:20px; left:50%; transform:translateX(-50%); background:#22c55e; color:white; padding:10px 25px; border-radius:25px; font-size:14px; z-index:50; display:none; animation:fadeInOut 2s; }}
        @keyframes fadeInOut {{ 0%{{opacity:0;top:0}} 20%{{opacity:1;top:20px}} 80%{{opacity:1;top:20px}} 100%{{opacity:0;top:0}} }}
    </style>
</head>
<body>
    <div id="player-wrapper">
        <div class="status-overlay" id="status">
            <div class="spinner"></div>
            <p id="statusText">Loading fresh stream...</p>
        </div>
        
        <video id="player" class="video-js vjs-big-play-centered" controls playsinline style="display:none;"></video>
        
        <div id="errorBox" style="display:none;color:white;text-align:center;position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);">
            <p style="font-size:18px;margin-bottom:15px;">⚠️ Stream expired</p>
            <button onclick="loadFreshStream()" style="padding:12px 30px;background:#6366f1;color:white;border:none;border-radius:25px;cursor:pointer;font-weight:600;">🔄 Get Fresh Link</button>
        </div>
    </div>
    
    <div class="controls-bar">
        <button class="ctrl-btn" onclick="copyCurrentLink()">📋 Copy Link</button>
        <button class="ctrl-btn" onclick="loadFreshStream()">🔄 Refresh</button>
    </div>
    
    <div class="toast" id="toast"></div>

    <script src="https://vjs.zencdn.net/8.10.0/video.min.js"></script>
    <script>
        const VIDEO_ID = '{video_id}';
        const API_URL = '/api/video/' + VIDEO_ID;
        let player = null;
        let currentMP4 = '';
        let refreshTimer = null;

        async function loadFreshStream() {{
            if (refreshTimer) clearTimeout(refreshTimer);
            
            document.getElementById('status').style.display = 'block';
            document.getElementById('statusText').textContent = 'Fetching fresh stream...';
            document.getElementById('player').style.display = 'none';
            document.getElementById('errorBox').style.display = 'none';
            
            try {{
                const response = await fetch(API_URL + '?t=' + Date.now());
                const data = await response.json();
                
                if (data.success && data.mp4_url) {{
                    currentMP4 = data.mp4_url;
                    document.title = data.title || 'PlayFlx Player';
                    
                    if (player) {{
                        player.dispose();
                        player = null;
                    }}
                    
                    document.getElementById('status').style.display = 'none';
                    document.getElementById('player').style.display = 'block';
                    
                    player = videojs('player', {{
                        controls: true,
                        autoplay: true,
                        preload: 'auto',
                        fluid: true,
                        playbackRates: [0.5, 0.75, 1, 1.25, 1.5, 2],
                        sources: [{{ src: currentMP4, type: 'video/mp4' }}]
                    }});
                    
                    player.ready(function() {{
                        player.play().catch(() => {{}});
                        
                        const savedTime = sessionStorage.getItem('time_' + VIDEO_ID);
                        if (savedTime) {{
                            player.currentTime(parseFloat(savedTime));
                            sessionStorage.removeItem('time_' + VIDEO_ID);
                        }}
                    }});
                    
                    player.on('error', function() {{
                        console.log('Stream expired, auto-refreshing...');
                        showToast('Stream expired. Getting new link...');
                        loadFreshStream();
                    }});
                    
                    player.on('timeupdate', function() {{
                        sessionStorage.setItem('time_' + VIDEO_ID, player.currentTime());
                    }});
                    
                    refreshTimer = setTimeout(function() {{
                        console.log('Auto-refreshing stream...');
                        showToast('Auto-refreshing stream...');
                        loadFreshStream();
                    }}, 5 * 60 * 60 * 1000);
                    
                    showToast('✅ Fresh stream loaded!');
                    
                }} else {{
                    throw new Error('No MP4 URL received');
                }}
            }} catch(e) {{
                console.error('Load error:', e);
                document.getElementById('status').style.display = 'none';
                document.getElementById('errorBox').style.display = 'block';
                
                setTimeout(loadFreshStream, 5000);
            }}
        }}

        function copyCurrentLink() {{
            if (currentMP4) {{
                navigator.clipboard.writeText(currentMP4).then(() => {{
                    showToast('📋 MP4 Link copied!');
                }});
            }} else {{
                showToast('⏳ Wait for stream to load...');
            }}
        }}

        function showToast(message) {{
            const toast = document.getElementById('toast');
            toast.textContent = message;
            toast.style.display = 'block';
            toast.style.animation = 'none';
            toast.offsetHeight;
            toast.style.animation = 'fadeInOut 2s';
            setTimeout(() => toast.style.display = 'none', 2000);
        }}

        document.addEventListener('keydown', function(e) {{
            switch(e.key.toLowerCase()) {{
                case 'r': e.preventDefault(); loadFreshStream(); break;
                case 'c': copyCurrentLink(); break;
                case 'f': if(player) {{ e.preventDefault(); player.requestFullscreen(); }} break;
                case ' ': e.preventDefault(); if(player) player.paused() ? player.play() : player.pause(); break;
                case 'arrowleft': if(player) player.currentTime(player.currentTime() - 10); break;
                case 'arrowright': if(player) player.currentTime(player.currentTime() + 10); break;
            }}
        }});

        loadFreshStream();
    </script>
</body>
</html>""")

# =====================================================================================
# HEALTH CHECK
# =====================================================================================
@app.api_route("/health", methods=["GET", "HEAD"])
async def health():
    return JSONResponse({"status": "ok", "message": "PlayFlx YT Server Running"})

# =====================================================================================
# START SERVER
# =====================================================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, log_level="info")
