from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
  return render_template('index.html')

@app.route('/vid1', methods=['GET'])
def vid1():
  video = '2023-09-17-15-03-56.mp4'
  return render_template('vid1.html', video=video)

@app.route('/vid2', methods=['GET'])
def vid2():
  return render_template('vid2.html')

@app.route('/vid3', methods=['GET'])
def vid3():
  return render_template('vid3.html')

if __name__ == "__main__":
  app.run(debug=True)