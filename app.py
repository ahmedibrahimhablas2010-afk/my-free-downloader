from flask import Flask, request, Response, stream_with_context
import subprocess
import shutil

app = Flask(__name__)

# نحدد مسار yt-dlp (هيتم تثبيته تلقائي)
YTDLP_CMD = shutil.which("yt-dlp") or "yt-dlp"

@app.route('/download')
def download():
    url = request.args.get('url')
    if not url:
        return "No URL provided", 400

    print(f"Processing: {url}")

    # أمر yt-dlp السحري
    # بنخليه يخرج البيانات كـ Stream (Pipe) عشان منخزنش ملفات
    cmd = [
        YTDLP_CMD,
        url,
        "-f", "bestaudio[ext=m4a]/bestaudio/best", # أفضل جودة صوت
        "-o", "-",                 # الإخراج للـ Standard Output
        "--quiet",
        "--no-playlist",
        "--no-warnings",
        "--geo-bypass",
        "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    ]

    # تشغيل العملية
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # دالة لتقطيع البيانات وإرسالها
    def generate():
        try:
            while True:
                chunk = proc.stdout.read(4096) # نقرأ 4 كيلو بايت
                if not chunk:
                    break
                yield chunk
            proc.stdout.close()
            proc.wait()
        except GeneratorExit:
            proc.terminate()

    # الرد على فيركل بالملف الصوتي
    return Response(stream_with_context(generate()), mimetype="audio/mp4")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)