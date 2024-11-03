import numpy as np
import requests
import datetime
import time
from threading import Thread

from flask import Flask, render_template_string, request, jsonify


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
    <input type="range" min="-1" max="2" value="this.value" step="1" id="slider" onchange="updateSliderValue(this.value);">
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
		function getSliderValue() {
            $.ajax({
                url: "/get_slider",
                type: "get",
                success: function(data) {
                    document.getElementById('slider').value = data.slider_value;
                    document.getElementById('sliderValue').textContent = data.slider_value;
                }
            });
        }

        $(document).ready(function() {
            getSliderValue();
        });
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
  
@app.route('/get_slider', methods=['GET'])
def get_slider():
    global slider_value

    return jsonify({'slider_value': slider_value}), 200

def get_unix_time_seconds():
    return int(time.mktime(datetime.datetime.now().timetuple()))

def get_energy_charts_re_share_traffic_light():
  try:
    url = 'https://api.energy-charts.info/signal'
    params = {'country': country, 'postal_code': postal_code}
    headers = {'accept': 'application/json'}
    response = requests.get(url, params=params, headers=headers)
    return response.json()
  except Exception as e:
    return None
  
def get_energy_charts_price():
  try:
    url = 'https://api.energy-charts.info/price'
    params = {'country': country, 'postal_code': postal_code}
    headers = {'accept': 'application/json'}
    response = requests.get(url, params=params, headers=headers)
    return response.json()
  except Exception as e:
    return None

def add_price_traffic_light_to_price_info(data):
    prices = np.array(data['price'])

    
    upper_quantile = np.quantile(prices, 0.8)
    print("Today upper price quantile: ", upper_quantile)
    lower_quantile = np.quantile(prices, 0.2)
    print("Today lower price quantile: ", lower_quantile)
    
    signal = []
    for price in prices.astype(float):
        
        if price <= lower_quantile or price < 1:
            signal.append(2)
        elif price <= upper_quantile:
            signal.append(1)
        else:
            signal.append(0)
    
    data['signal'] = signal

    return data  
  
def switch_green_socket_on():
  try:
    url = 'http://' + shelly_plug_s_ip + '/relay/0?turn=on'
    headers = {'accept': 'application/json'}
    response = requests.get(url, headers=headers)
    return response.json()
  except Exception as e:
    print(f"An error when swiching on occurred: {e}")
    return None

def switch_green_socket_off():
  try:
    url = 'http://' + shelly_plug_s_ip + '/relay/0?turn=off'
    headers = {'accept': 'application/json'}
    response = requests.get(url, headers=headers)
    return response.json()
  except Exception as e:
    print(f"An error when swiching off occurred: {e}")
    return None

def main():
    global slider_value

    while True:
        re_share_traffic_light_info = get_energy_charts_re_share_traffic_light()
        price_info = get_energy_charts_price()
        current_unix_time = get_unix_time_seconds()
        
        if re_share_traffic_light_info == None or price_info == None:
          print(current_unix_time, ": No data, swiching off...")
          switch_green_socket_off()
        else:
          price_traffic_light_info = add_price_traffic_light_to_price_info(price_info)
          
          re_share_traffic_light_index = None
          for i, unix_time in enumerate(re_share_traffic_light_info['unix_seconds']):
              if unix_time > current_unix_time:
                  re_share_traffic_light_index = i - 1
                  break
          
          price_index = None
          for i, unix_time in enumerate(price_traffic_light_info['unix_seconds']):
              if unix_time > current_unix_time:
                  price_index = i - 1
                  break
          
          if re_share_traffic_light_index != None and price_index != None:
            
            print("Current slider value :", slider_value)
            print("Current price:", price_traffic_light_info['price'][price_index])
            print("Current RE share traffic light value :", re_share_traffic_light_info['signal'][re_share_traffic_light_index])
            print("Current price traffic light value :", price_traffic_light_info['signal'][price_index])
            
            
            combined_traffic_light_on = re_share_traffic_light_info['signal'][re_share_traffic_light_index] >= slider_value
            combined_traffic_light_on &= price_traffic_light_info['signal'][price_index] == 2

            if combined_traffic_light_on:
                print(current_unix_time, ": Green phase...")
                switch_green_socket_on()
            else:
                print(current_unix_time, ": Not green phase...")
                switch_green_socket_off()
          else:
            print(current_unix_time, ": Invalid index, swiching off...")
            switch_green_socket_off()
        
        time.sleep(60)

if __name__ == "__main__":

    flask_thread = Thread(target=lambda: app.run(debug=True, use_reloader=False, host='0.0.0.0'))
    flask_thread.start()

    main_thread = Thread(target=main)
    main_thread.start()