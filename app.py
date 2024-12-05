from flask import Flask

app = Flask(__name__)


@app.route('/api/mentora/login')
def login():
    return 'Hello World!'


@app.route('/api/mentora/register')
def register():
    return 'Hello World!'


@app.route('/api/mentora/log-interests')
def register():
    return 'Hello World!'


@app.route('/api/mentora/student/get-my-classes')
def register():
    return 'Hello World!'


@app.route('/api/mentora/student/get-recommended-classes')
def register():
    return 'Hello World!'


@app.route('/api/mentora/student/register-class')
def register():
    return 'Hello World!'


@app.route('/api/mentora/teacher/get-my-classes')
def register():
    return 'Hello World!'


@app.route('/api/mentora/teacher/create-class')
def register():
    return 'Hello World!'


if __name__ == '__main__':
    app.run()
