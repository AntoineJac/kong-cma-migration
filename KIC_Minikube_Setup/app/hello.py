from flask import Flask
app = Flask(__name__)
 
@app.route('/hello')
def hello():
    return '{"msg":"Hello Kong !!!"}'
 
if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')