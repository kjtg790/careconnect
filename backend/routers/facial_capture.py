from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def face_capture_ui():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Multi-Angle Face Capture</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; }
            video { border: 1px solid black; }
            button, select, input { margin-top: 10px; }
        </style>
    </head>
    <body>
        <h2>Multi-Angle Face Capture</h2>
        <video id="video" width="400" height="300" autoplay></video><br>
        <input type="text" id="user_id" placeholder="Enter User ID" required><br>
        <select id="angle">
            <option value="front">Front</option>
            <option value="left">Left</option>
            <option value="right">Right</option>
            <option value="up">Up</option>
            <option value="down">Down</option>
        </select><br>
        <button onclick="capture()">Capture This Angle</button>
        <button onclick="submitAll()">Submit All Captures</button>
        <div id="status"></div>
        <ul id="capturesList"></ul>

        <script>
            const video = document.getElementById('video');
            const capturedImages = [];

            navigator.mediaDevices.getUserMedia({ video: true })
                .then(stream => video.srcObject = stream)
                .catch(err => console.error("Camera error", err));

            function capture() {
                const canvas = document.createElement('canvas');
                canvas.width = 400;
                canvas.height = 300;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

                const angle = document.getElementById('angle').value;

                canvas.toBlob(blob => {
                    capturedImages.push({ angle, blob });
                    const list = document.getElementById('capturesList');
                    const item = document.createElement('li');
                    item.textContent = `Captured angle ${angle}`;
                    list.appendChild(item);
                }, 'image/jpeg');
            }

            function submitAll() {
                const userId = document.getElementById('user_id').value.trim();
                if (!userId) {
                    alert("User ID is required.");
                    return;
                }
                if (capturedImages.length === 0) {
                    alert("No images to upload.");
                    return;
                }

                const formData = new FormData();
                formData.append("user_id", userId);
                capturedImages.forEach((entry, index) => {
                    formData.append("files", entry.blob, `${entry.angle}_${index}.jpg`);
                });

                fetch("/save-face-encodings", {
                    method: "POST",
                    body: formData
                })
                .then(res => res.json())
                .then(data => {
                    document.getElementById('status').textContent = JSON.stringify(data, null, 2);
                    alert("Upload complete.");
                })
                .catch(err => {
                    console.error(err);
                    alert("Upload failed.");
                });
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)
