const BASE_URL = import.meta.env.VITE_BACKEND_BASE_URL

export const getCurrentUser = async () => {
    return await fetch(`${BASE_URL}/test`, {
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
}