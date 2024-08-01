const BASE_URL = "http://localhost:5173"


export const getCurrentUser = async () => {
    const result = await fetch(`${BASE_URL}/test`, {
        method: 'GET',
        headers: {
            'accept': 'application/json',
            'Content-Type': 'application/json'
        }
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            return data
        })
        .catch(error => {
            console.error('Error:', error);
            return null
        });
    return result
}