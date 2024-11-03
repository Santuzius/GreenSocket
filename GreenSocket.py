import requests
import datetime
import time
from threading import Thread

from flask import Flask, render_template_string, request


shelly_plug_s_ip = '192.168.2.162'
country = 'de'
postal_code = '36037'

app = Flask(__name__)
slider_value = 2

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <title>GreenSocket</title>
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script>
</head>
<body>
    <h1>GreenSocket</h1>
    <input type="range" min="-1" max="2" value="2" step="1" id="slider" onchange="updateSliderValue(this.value);">
    <p>Value: <span id="sliderValue">2</span></p>
    <script>
        function updateSliderValue(value) {
            document.getElementById('sliderValue').textContent = value;
            $.ajax({
                url: "/set_slider",
                type: "post",
                data: { slider_value: value }
            });
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/set_slider', methods=['POST'])
def set_slider():
    global slider_value

    slider_value = int(request.form['slider_value'])
    return '', 204

def get_unix_time_seconds():
    return int(time.mktime(datetime.datetime.now().timetuple()))

def get_energy_charts_re_share_traffic_light():
    url = 'https://api.energy-charts.info/signal'
    params = {'country': country, 'postal_code': postal_code}
    headers = {'accept': 'application/json'}
    response = requests.get(url, params=params, headers=headers)
    return response.json()

def switch_green_socket_on():
    url = 'http://' + shelly_plug_s_ip + '/relay/0?turn=on'
    headers = {'accept': 'application/json'}
    response = requests.get(url, headers=headers)
    return response.json()

def switch_green_socket_off():
    url = 'http://' + shelly_plug_s_ip + '/relay/0?turn=off'
    headers = {'accept': 'application/json'}
    response = requests.get(url, headers=headers)
    return response.json()

def main():
    global slider_value

    while True:
        re_share_traffic_light_info = get_energy_charts_re_share_traffic_light()
        current_unix_time = get_unix_time_seconds()
        
        index = None
        for i, unix_time in enumerate(re_share_traffic_light_info['unix_seconds']):
            if unix_time > current_unix_time:
                index = i - 1
                break
        
        print("Current value :", slider_value)
        if index is not None and re_share_traffic_light_info['signal'][index] >= slider_value:
            print(current_unix_time, ": Green phase")
            switch_green_socket_on()
        else:
            print(current_unix_time, ": Not green phase")
            switch_green_socket_off()
        
        time.sleep(60)

if __name__ == "__main__":

    flask_thread = Thread(target=lambda: app.run(debug=True, use_reloader=False, host='0.0.0.0'))
    flask_thread.start()

    main_thread = Thread(target=main)
    main_thread.start()