function fetchData() {
    fetch('/update_sensor_data')
        .then(response => response.json())
        .then(data => {
            document.getElementById('temperature').innerText = data.temperature;
            document.getElementById('humidity').innerText = data.humidity;
        })
        .catch(error => console.error('Error:', error));
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
            // Обновляем кнопку после получения ответа
            let button = document.getElementById(device.toLowerCase());
            button.classList.toggle('on');
            button.classList.toggle('off');
            button.innerText = `${device} (${data.state ? 'Включено' : 'Выключено'})`;
        })
        .catch(error => {
            console.error('There has been a problem with your fetch operation:', error);
        });
}
