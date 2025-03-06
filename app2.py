import time
import threading
import serial
from flask import Flask, render_template
from flask_socketio import SocketIO

# Configurar la conexión con Arduino (ajusta COM5 si es necesario)
PORT = 'COM5'
baud_rate = 9600

arduino = serial.Serial(PORT, baud_rate, timeout=1)
time.sleep(2)  # Esperar a que la conexión con el Arduino se estabilice

# Configurar el servidor Flask y Socket.IO
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
def index():
    return render_template('index.html')

# Parámetros del filtro
alpha = 0.3  # Suavizado
last_temperature = None
last_humidity = None

def read_sensor():
    global last_temperature, last_humidity

    while True:
        try:
            line = arduino.readline().decode().strip()  # Leer línea del serial
            if line and "Error" not in line:
                temp, hum = map(float, line.split(","))  # Separar temperatura y humedad

                # Aplicar filtro exponencial
                if last_temperature is None:
                    last_temperature = temp
                    last_humidity = hum
                else:
                    temp = alpha * temp + (1 - alpha) * last_temperature
                    hum = alpha * hum + (1 - alpha) * last_humidity
                    last_temperature, last_humidity = temp, hum

                socketio.emit('update_data', {'temperature': round(temp, 2), 'humidity': round(hum, 2)})
                print(f"Temp: {round(temp, 2)}°C - Hum: {round(hum, 2)}%")

        except Exception as e:
            print(f"Error leyendo sensor: {e}")

        time.sleep(2)  # Esperar 2s entre lecturas

# Iniciar el hilo de lectura del sensor
sensor_thread = threading.Thread(target=read_sensor)
sensor_thread.daemon = True
sensor_thread.start()

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=False)
