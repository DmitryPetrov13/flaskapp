from flask import Flask, render_template, request, send_file, redirect, url_for
from pytube import YouTube
from io import BytesIO
import os
from moviepy.editor import AudioFileClip

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        video_url = request.form['url']
        try:
            yt = YouTube(video_url)
            return redirect(url_for('download', url=video_url))
        except:
            return render_template('index.html', error="Invalid URL or video unavailable")
    return render_template('index.html')

@app.route('/download', methods=['GET', 'POST'])
def download():
    if request.method == 'POST':
        video_url = request.form['url']
        format_choice = request.form['format']
        quality = request.form.get('quality', 'highest')
        
        try:
            yt = YouTube(video_url)
            if format_choice == 'mp3':
                # Get audio stream
                audio_stream = yt.streams.filter(only_audio=True).first()
                buffer = BytesIO()
                audio_stream.stream_to_buffer(buffer)
                buffer.seek(0)
                
                # Convert to MP3 using moviepy
                temp_audio_path = "temp_audio.mp4"
                with open(temp_audio_path, "wb") as f:
                    f.write(buffer.read())
                
                audio_clip = AudioFileClip(temp_audio_path)
                mp3_buffer = BytesIO()
                audio_clip.write_audiofile(mp3_buffer, codec='mp3')
                mp3_buffer.seek(0)
                
                os.remove(temp_audio_path)
                
                return send_file(
                    mp3_buffer,
                    as_attachment=True,
                    download_name=f"{yt.title}.mp3",
                    mimetype="audio/mpeg"
                )
            else:
                if quality == 'highest':
                    stream = yt.streams.get_highest_resolution()
                else:
                    stream = yt.streams.filter(res=quality, file_extension='mp4').first()
                    if not stream:
                        stream = yt.streams.get_highest_resolution()
                
                buffer = BytesIO()
                stream.stream_to_buffer(buffer)
                buffer.seek(0)
                
                return send_file(
                    buffer,
                    as_attachment=True,
                    download_name=f"{yt.title}.mp4",
                    mimetype="video/mp4"
                )
        except Exception as e:
            return render_template('download.html', error=str(e), url=video_url)
    
    video_url = request.args.get('url')
    try:
        yt = YouTube(video_url)
        video_streams = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc()
        resolutions = list(set([stream.resolution for stream in video_streams if stream.resolution]))
        return render_template('download.html', 
                             url=video_url,
                             title=yt.title,
                             thumbnail=yt.thumbnail_url,
                             resolutions=resolutions)
    except Exception as e:
        return render_template('index.html', error=str(e))

# HTML templates
@app.route('/favicon.ico')
def favicon():
    return '', 404

app.jinja_env.globals.update(zip=zip)

# Templates as strings
app.jinja_loader = type('CustomLoader', (object,), {
    'get_source': lambda self, *a, **k: (
        '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>YouTube Downloader</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
                .container { background: #f9f9f9; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                h1 { color: #ff0000; text-align: center; }
                .form-group { margin-bottom: 15px; }
                input[type="text"] { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; }
                button { background: #ff0000; color: white; border: none; padding: 10px 15px; border-radius: 4px; cursor: pointer; }
                button:hover { background: #cc0000; }
                .error { color: red; }
                .video-info { display: flex; margin: 20px 0; }
                .thumbnail { margin-right: 20px; }
                .thumbnail img { max-width: 200px; border-radius: 4px; }
                .download-options { margin-top: 20px; }
                .quality-options { margin: 10px 0; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>YouTube Downloader</h1>
                <form method="POST">
                    <div class="form-group">
                        <input type="text" name="url" placeholder="Enter YouTube URL" required value="{{ url if url else '' }}">
                    </div>
                    <button type="submit">Download</button>
                    {% if error %}
                        <p class="error">{{ error }}</p>
                    {% endif %}
                </form>
            </div>
        </body>
        </html>
        ''',
        'index.html',
        lambda: None
    ) if a[0] == 'index.html' else (
        '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Download {{ title }}</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
                .container { background: #f9f9f9; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                h1 { color: #ff0000; text-align: center; }
                .video-info { display: flex; margin: 20px 0; }
                .thumbnail { margin-right: 20px; }
                .thumbnail img { max-width: 200px; border-radius: 4px; }
                .download-options { margin-top: 20px; }
                .form-group { margin-bottom: 15px; }
                button { background: #ff0000; color: white; border: none; padding: 10px 15px; border-radius: 4px; cursor: pointer; }
                button:hover { background: #cc0000; }
                .error { color: red; }
                .quality-options { margin: 10px 0; }
                .quality-option { margin-right: 10px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Download Options</h1>
                
                <div class="video-info">
                    <div class="thumbnail">
                        <img src="{{ thumbnail }}" alt="Thumbnail">
                    </div>
                    <div>
                        <h3>{{ title }}</h3>
                    </div>
                </div>
                
                {% if error %}
                    <p class="error">{{ error }}</p>
                {% endif %}
                
                <div class="download-options">
                    <form method="POST">
                        <input type="hidden" name="url" value="{{ url }}">
                        
                        <div class="form-group">
                            <label>Format:</label><br>
                            <input type="radio" id="mp4" name="format" value="mp4" checked>
                            <label for="mp4">MP4 (Video)</label><br>
                            <input type="radio" id="mp3" name="format" value="mp3">
                            <label for="mp3">MP3 (Audio only)</label>
                        </div>
                        
                        <div class="form-group" id="quality-options">
                            <label>Quality (for MP4):</label><br>
                            <input type="radio" id="highest" name="quality" value="highest" checked>
                            <label for="highest">Highest available</label><br>
                            {% for res in resolutions %}
                                <input type="radio" id="{{ res }}" name="quality" value="{{ res }}" class="quality-option">
                                <label for="{{ res }}">{{ res }}</label><br>
                            {% endfor %}
                        </div>
                        
                        <button type="submit">Download Now</button>
                    </form>
                </div>
            </div>
            
            <script>
                document.getElementById('mp3').addEventListener('change', function() {
                    document.getElementById('quality-options').style.display = this.checked ? 'none' : 'block';
                });
                document.getElementById('mp4').addEventListener('change', function() {
                    document.getElementById('quality-options').style.display = this.checked ? 'block' : 'none';
                });
            </script>
        </body>
        </html>
        ''',
        'download.html',
        lambda: None
    ) if a[0] == 'download.html' else (None, None, None)
})

if __name__ == '__main__':
    app.run(debug=True)
