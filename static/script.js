function fetchData() {
    fetch('/get_sensor_data')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            document.getElementById('temperature').innerText = data.temperature !== null ? `${data.temperature} °C` : 'N/A';
            document.getElementById('humidity').innerText = data.humidity !== null ? `${data.humidity} %` : 'N/A';
        })
        .catch(error => {
            console.error('Error fetching sensor data:', error);
        });
}

setInterval(fetchData, 5000); // Обновляем данные каждые 5 секунд для принятия данных о температуре и влажности

function toggleDevice(device) {
    fetch(`/toggle/${device}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            let button = document.getElementById(device.toLowerCase());
            button.classList.toggle('on', data[device]);
            button.classList.toggle('off', !data[device]);
            button.innerText = `${device} (${data[device] ? 'Включено' : 'Выключено'})`;
        })
        .catch(error => {
            console.error(`Error toggling device ${device}:`, error);
        });
}
