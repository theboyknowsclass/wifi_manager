# SPDX-FileCopyrightText: Copyright (c) 2022 Gautam Bhatnagar for n/a
#
# SPDX-License-Identifier: MIT
"""
`wifi_manager`
================================================================================

Circuit python helper library for managing wifi for iot devices


* Author(s): Gautam Bhatnagar

Implementation Notes
--------------------

**Hardware:**

.. todo:: Add links to any specific hardware product page(s), or category page(s).
  Use unordered list & hyperlink rST inline format: "* `Link Text <url>`_"

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://circuitpython.org/downloads

"""

# imports

__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/theboyknowsclass/CircuitPython_wifi_manager.git"

import time
import json
import ipaddress
import wifi
import socketpool
from adafruit_httpserver import HTTPServer, HTTPResponse, _HTTPRequest


class WifiManager:
    """The Wifi Manager class - needs to be initialised."""

    PING_POLL = 15
    PING_IP = "8.8.8.8"
    PING_FAIL_LIMIT = 4

    def __init__(self, ap_name):
        self.settings_filename = f"{ap_name}_wifi_settings"
        self.ip_address = None
        self.status = "ACCESS_POINT"
        self.selected_wifi = None
        self.ap_name = ap_name
        self.pool = None
        self.server = None
        self.last_poll_time = 0
        self.ping_status = None
        self.ping_fail_count = 0

    def initialise(self):
        """If a Wifi network has been previously set, connect to it, else inter AP mode."""
        self.selected_wifi = self.load_settings()
        if (
            self.selected_wifi is not None
            and "ssid" in self.selected_wifi
            and "password" in self.selected_wifi
            and self.connect_to_wifi(
                self.selected_wifi["ssid"], self.selected_wifi["password"]
            )
            is not None
        ):
            return

        self.create_ap()

    def poll(self):
        """Process any actions - this should be in the main loop (with no time.sleep)"""
        now = time.monotonic()
        if self.server is not None:
            self.server.poll()

        if self.status == "CLIENT" and now > self.last_poll_time + self.PING_POLL:
            ping_time = wifi.radio.ping(ipaddress.ip_address(self.PING_IP))
            self.ping_status = {
                "status": "Failed" if ping_time is None else "Success",
                "time": "None" if ping_time is None else ping_time,
            }
            if ping_time is None:
                self.ping_fail_count = self.ping_fail_count + 1
            else:
                self.ping_fail_count = 0
            self.last_poll_time = now
            print(self.ping_status)

            if self.ping_fail_count >= self.PING_FAIL_LIMIT:
                self.create_ap()
                self.connect_to_wifi(
                    self.selected_wifi["ssid"], self.selected_wifi["password"]
                )

    @staticmethod
    def get_wifi_networks():
        """Returns a list of the available SSIDs."""
        networks = []
        for network in wifi.radio.start_scanning_networks():
            networks.append(network.ssid)
        wifi.radio.stop_scanning_networks()
        networks.sort()
        return networks

    def connect_to_wifi(self, ssid, password):
        """Connect to a specified wifi network, and return the assigned IP address if successful"""
        try:
            if ssid in self.get_wifi_networks():
                self.server = None
                self.pool = None
                if self.status == "ACCESS_POINT":
                    self.stop_ap()
                wifi.radio.connect(ssid, password)
                self.ip_address = wifi.radio.ipv4_address
                print(f"Listening on http://{self.ip_address}:80/wifi_settings")
                self.status = "CLIENT"
                self.create_server()
                return self.ip_address
            else:
                print(f"{ssid} not available")
                return None
        except BaseException as err:
            print(f"Unexpected {err=}, {type(err)=} connecting to {ssid}")
            return None

    def create_ap(self):
        """Start the device in AP mode"""
        if self.status == "CLIENT":
            self.stop_ap()
        wifi.radio.start_ap(self.ap_name)
        wifi.radio.start_station()
        self.ip_address = wifi.radio.ipv4_gateway_ap
        print(f"Listening on http://{self.ip_address}/wifi_settings")
        self.status = "ACCESS_POINT"
        self.create_server()

    def stop_ap(self):
        """Stop AP mode"""
        self.ip_address = None
        wifi.radio.stop_ap()
        wifi.radio.stop_station()

    def save_settings(self, ssid, password):
        """Set the default SSID and password to connect to"""
        network_info = {
            "ssid": ssid,
            "password": password,
        }

        with open(self.settings_filename, "w") as jsonfile:
            jsonfile.write(json.dumps(network_info))
            jsonfile.close()

    def load_settings(self):
        """Returns the saved settings"""
        try:
            with open(self.settings_filename, "r") as jsonfile:
                data = json.load(jsonfile)
                jsonfile.close()
            return data
        except BaseException as err:
            print(
                f"Unexpected {err=}, {type(err)=} loading settings from to {self.settings_filename}"
            )
            return None

    def create_server(self):
        """Creates the server and adds the http routes"""
        self.pool = socketpool.SocketPool(wifi.radio)
        self.server = HTTPServer(self.pool)
        self.add_server_routes()
        if self.ip_address is not None:
            self.server.start(str(self.ip_address))

    def get_configuration_page(self, request):
        """Returns the html configuration page."""
        configPage = (
            '''<!DOCTYPE html>
<html>
    <head>
        <title>Wifi Manager</title>
        <style>
            body {
                font-family: Arial, Helvetica, sans-serif;
            }

            #content {
                margin: auto;
                padding: 10px;
                width: fit-content;
            }

            #loading {
                background-color: #cccccccc;
                position: absolute;
                top:0;
                left:0;
                width: 100%;
                height: 100%;
                text-align: center;
                visibility: visible;
            }

            #loading_content {
                background: #FFFFFF;
                border: #505050;
                border-style: solid;
                border-width: 0.2rem;
                position: absolute;
                padding: 15% 25%;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                border-radius: 1rem;
            }

            #wifi_settings {
                border: #505050;
                border-style: solid;
                border-width: 0.1rem;
                position: absolute;
                border-radius: 1rem;
                padding: 1rem;
                height: fit-content;
            }

            #wifi_settings_title {
                background-color: white;
                padding: 0px;
                margin: 0px;
                position: relative;
                top: -1.5rem;
                width: fit-content;
            }

            #wifi_networks {
                display: flex;
                flex-direction: row;
                margin-bottom: 0.2rem;
            }

            #wifi_password {
                display: flex;
                flex-direction: row;
            }

            #ssid_dropdown {
                height: 1.4rem;
                flex-grow: 1;
                margin-right: 0.2rem;
            }

            #refresh, #connect {
                height: 1.4rem;
                min-width: 4.1rem;
            }

            #password {
                height: 1.2rem;
                flex-grow: 1;
                padding: 0px;
            }

            h1 {
                color: #505050;
                font-size:1.4rem
            }

            h2 {
                color: #606060;
                font-size:1.2rem
            }

            h3 {
                color: #606060;
                font-size:1rem
            }


        </style>
        <script type="text/javascript">
            var ipAddress = "'''
            + self.ip_address
            + """"

            async function getNetworks() {
                var sel = document.getElementById('ssid_dropdown') // find the drop down
                const response = await fetch(`http://${ipAddress}/wifi_settings/networks`)
                const networks = await response.json()
                networks.forEach(ssid => 
                    {
                        var opt = document.createElement("option"); // Create the new element
                        opt.value = ssid; // set the value
                        opt.text = ssid; // set the text
                        sel.appendChild(opt)
                    }
                );
            }

            async function getMode() {
                var sel = document.getElementById('wifi_mode')
                const response = await fetch(`http://${ipAddress}/wifi_settings/mode`)
                const data = await response.json()
                console.log(data)
                sel.innerHTML = `Mode: ${data.mode}`
            }

            async function getSsid() {
                var sel = document.getElementById('wifi_ssid')
                var ssidDropdown = document.getElementById('ssid_dropdown')
                const response = await fetch(`http://${ipAddress}/wifi_settings/current`)
                const data = await response.json()
                sel.innerHTML = `SSID: ${data.ssid}`
                ssidDropdown.value = data.ssid
            }

            function refreshNetworks() {
                var sel = document.getElementById('ssid_dropdown')
                while (sel.options.length > 0) {                
                    sel.remove(0);
                }
                getNetworks()
            }

            function showLoading() {
                const element = document.getElementById("loading");
                element.style.visibility = "visible";
            }

            function hideLoading() {
                const element = document.getElementById("loading");	
                element.style.visibility = "hidden";
            }

            async function onLoad() {
                showLoading()
                await getMode()
                await getNetworks()
                await getSsid()
                hideLoading()
            }
        </script>
    </head>
    <body onLoad="onLoad()">
        <div id="loading">
            <h3 id="loading_content">
                Loading...
            </h3>
        </div>
        <div id="content">
            <h1 id="wifi_manager_title">Wifi Manager</h1>

            <h2 id="wifi_mode">Mode:</h2>
            <h2 id="wifi_ssid">SSID:</h2>
            <h3 id="wifi_status">Status</h3>

            <form action="/wifi_settings/connect" method="post">
                <div id="wifi_settings">
                    <div id="wifi_settings_title">Wifi Settings</div>
                    <div id="wifi_networks">
                        <select id="ssid_dropdown" name="ssid"></select>
                        <button id="refresh" onclick="refreshNetworks()">Refresh</button>
                    </div>
                    <div if="wifi_password">
                        <label id="password_label" for="password">Password: </label>
                        <input type="password" name="password" id="password" required>
                        <input id="connect" type="submit" value="Connect">
                    </div>
                </div>
            </form>
        </div>
    </body>
</html>"""
        )
        return HTTPResponse(body=configPage, content_type="text/html")

    def get_ssid(self):
        """Get the current SSID that the device is connected to or the AP Name"""
        if self.status == "ACCESS_POINT":
            return self.ap_name
        if self.selected_wifi is not None and "ssid" in self.selected_wifi:
            return self.selected_wifi["ssid"]

    def connect_to_wifi_network(self, request):
        """Get the current SSID that the device is connected to or the AP Name"""
        parameters = (
            request.raw_request.decode("utf-8").splitlines()[-1].split("&password=")
        )
        ssid = parameters[0].replace("ssid=", "")
        password = parameters[1]
        print(ssid)
        print(password)
        result = self.connect_to_wifi(ssid, password)
        return_status = json.dumps(
            {"status": "failure" if result is None else "success", "ip": f"{result}"}
        )

        return HTTPResponse(body=f"{str(return_status)}")

    def add_server_routes(self):
        """Add the server routes for the Wifi Manager"""
        self.add_server_route("/wifi_settings", "GET", self.get_configuration_page)
        self.add_server_route("/wifi_settings/mode", "GET", self.get_wifi_mode_response)
        self.add_server_route(
            "/wifi_settings/current", "GET", self.get_wifi_current_response
        )
        self.add_server_route(
            "/wifi_settings/networks", "GET", self.get_wifi_networks_response
        )
        self.add_server_route(
            "/wifi_settings/connect", "POST", self.connect_to_wifi_network
        )

    def add_server_route(self, path, method, func):
        """Add a server route for a path, method (GET, POST etc.), and function"""
        if self.server is not None:
            self.server.routes[_HTTPRequest(path, method)] = func

    def get_wifi_networks_response(self, request):
        """Wrapper function for get_wifi_networks"""
        networks = json.dumps(self.get_wifi_networks())
        return HTTPResponse(body=f"{str(networks)}")

    def get_wifi_mode_response(self, request):
        """Wrapper function for get_wifi_mode"""
        mode = json.dumps({"mode": self.status})
        return HTTPResponse(body=f"{str(mode)}")

    def get_wifi_current_response(self, request):
        """Wrapper function for get_wifi_current"""
        current_ssid = (
            self.selected_wifi["ssid"]
            if (self.selected_wifi is not None and "ssid" in self.selected_wifi)
            else "None"
        )
        current = json.dumps({"ssid": current_ssid})
        return HTTPResponse(body=f"{str(current)}")
