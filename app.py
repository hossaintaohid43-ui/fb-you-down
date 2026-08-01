import os
import tempfile
from flask import Flask, render_template, request, send_file, jsonify
import yt_dlp

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download_video():
    data = request.get_json()
    video_url = data.get('url')

    if not video_url:
        return jsonify({'error': 'মেহেরবানি করে একটি সঠিক URL দিন!'}), 400

    # অস্থায়ী ফোল্ডার তৈরি
    temp_dir = tempfile.mkdtemp()

    # FFmpeg ছাড়া সহজে ডাউনলোড হওয়ার জন্য ফ্লেক্সিবল ফরম্যাট কনফিগারেশন
    ydl_opts = {
        'format': 'best[ext=mp4]/best', # অডিও-ভিডিও যুক্ত সরাসরি সেরা mp4 ফাইল বেছে নেবে
        'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # ভিডিওর তথ্য ফেচ ও ডাউনলোড
            info = ydl.extract_info(video_url, download=True)
            filename = ydl.prepare_filename(info)

            # কোনো কারণে ফাইলের এক্সটেনশন ডিটেক্ট না হলে চেক করা
            if not os.path.exists(filename):
                files = os.listdir(temp_dir)
                if files:
                    filename = os.path.join(temp_dir, files[0])
                else:
                    return jsonify({'error': 'ভিডিও ফাইল প্রসেস করা সম্ভব হয়নি।'}), 500

            # ব্রাউজারে ফাইলটি পাঠানোর রেসপন্স
            response = send_file(
                filename,
                as_attachment=True,
                download_name=os.path.basename(filename)
            )

            # ডাউনলোড শেষ হলে অস্থায়ী ফাইল মুছে ফেলা
            @response.call_on_close
            def cleanup():
                try:
                    if os.path.exists(filename):
                        os.remove(filename)
                    if os.path.exists(temp_dir):
                        os.rmdir(temp_dir)
                except Exception as e:
                    app.logger.error(f"Cleanup error: {e}")

            return response

    except yt_dlp.utils.DownloadError as e:
        return jsonify({'error': 'অকার্যকর URL অথবা ভিডিওটি প্রাইভেট/ডিলিট করা হয়েছে।'}), 400
    except Exception as e:
        return jsonify({'error': f'ডাউনলোডে সমস্যা হয়েছে: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)