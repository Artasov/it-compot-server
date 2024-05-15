class Client {
    constructor() {
    }

    static getCookie(name) {
        const value = "; " + document.cookie;
        const parts = value.split("; " + name + "=");
        if (parts.length === 2) return parts.pop().split(";").shift();
    }

    static getProtocolAndDomain() {
        return `${window.location.protocol}//${window.location.host}`;
    }

    static getParamsFromCurrentURL() {
        const params = new URLSearchParams(window.location.search);
        const result = {};
        for (const [key, value] of params.entries()) {
            result[key] = value;
        }
        return result;
    }

    static sendPost(url, params) {
        return new Promise((resolve, reject) => {
            const formData = new FormData();
            for (const key in params) {
                // Если параметр является массивом, сериализуем его в JSON
                if (Array.isArray(params[key])) {
                    formData.append(key, JSON.stringify(params[key]));
                } else {
                    formData.append(key, params[key]);
                }
            }

            const xhr = new XMLHttpRequest();
            xhr.open('POST', url, true);
            xhr.setRequestHeader('X-CSRFToken', this.getCookie('csrftoken'));

            xhr.onload = () => {
                if (xhr.status === 200) {
                    try {
                        const response = JSON.parse(xhr.responseText);
                        resolve(response);
                    } catch (e) {
                        reject(e);
                    }
                } else {
                    reject(xhr.responseText);
                }
            };

            xhr.onerror = () => {
                reject('Request failed');
            };

            xhr.send(formData);
        });
    }

    static sendGet(url, params) {
        return new Promise((resolve, reject) => {
            const queryString = Object.keys(params).map(key => encodeURIComponent(key) + '=' + encodeURIComponent(params[key])).join('&');
            const xhr = new XMLHttpRequest();
            xhr.open('GET', `${url}?${queryString}`, true);

            xhr.onload = () => {
                if (xhr.status === 200) {
                    try {
                        const response = JSON.parse(xhr.responseText);
                        resolve(response);
                    } catch (e) {
                        reject(e);
                    }
                } else {
                    reject(xhr.responseText);
                }
            };

            xhr.onerror = () => {
                reject('Request failed');
            };

            xhr.send();
        });
    }

}

export default Client;

// Пример использования класса Client
// const client = new Client();
// const postParams = { name: 'John', age: 30 };
// const getParams = { query: 'info' };
//
// client.sendPost('https://example.com/api/post', postParams)
//     .then(response => console.log('POST Response:', response))
//     .catch(error => console.error('POST Error:', error));
//
// client.sendGet('https://example.com/api/get', getParams)
//     .then(response => console.log('GET Response:', response))
//     .catch(error => console.error('GET Error:', error));
