import requests
import datetime
import time

shelly_plug_s_ip = '192.168.2.162'
country = 'de'
postal_code = '36037'

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
    while True:
        re_share_traffic_light_info = get_energy_charts_re_share_traffic_light()
        current_unix_time = get_unix_time_seconds()
        
        index = None
        for i, unix_time in enumerate(re_share_traffic_light_info['unix_seconds']):
            if unix_time > current_unix_time:
                index = i - 1
                break
        
        if index is not None and re_share_traffic_light_info['signal'][index] >= 2:
            print(current_unix_time, ": Green phase")
            switch_green_socket_on()
        else:
            print(current_unix_time, ": Not green phase")
            switch_green_socket_off()
        
        time.sleep(60)

if __name__ == "__main__":
    main()