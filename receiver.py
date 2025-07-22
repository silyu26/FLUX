from flask import Flask, request

app = Flask(__name__)

@app.route('/receive', methods=['POST'])
def receive_data():
    data = request.get_json()
    print("Received Data:", data)
    return {'status': 'success'}, 200
if __name__ == '__main__':
    app.run(host = '0.0.0.0', port = 5000)