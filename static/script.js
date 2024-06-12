function fetchData() {
    fetch('/data')
        .then(response => response.json())
        .then(data => {
            document.getElementById('temperature').innerText = data.temperature;
            document.getElementById('humidity').innerText = data.humidity;
        })
        .catch(error => console.error('Error:', error));
}

setInterval(fetchData, 5000); // Обновляем данные каждые 5 секунд
