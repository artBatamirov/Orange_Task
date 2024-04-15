from flask import Flask, render_template

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('planer.html', planer_list=['1hhh', '2hhg', 'khg3', 'hh'])


if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1')