import startLogin from "../auth/auth.js";

const BASE_URL = import.meta.env.VITE_BACKEND_BASE_URL

async function fetchWithAuth(url, options = {}) {
    try {
        const response = await fetch(url, options);

        if (response.status === 401) {
            // Handle 401 Unauthorized error by triggering the login flow
            await startLogin();
            return;
        }

        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        return response.json();
    } catch (error) {
        console.error('Fetch error:', error);
    }
}

export const getCurrentUser = async () => {
    return await fetchWithAuth(`${BASE_URL}/test`, {
        method: 'GET',
        headers: {
            'accept': 'application/json',
            'Content-Type': 'application/json'
        }
    })
        .then(data => {
            return data
        })
        .catch(error => {
            console.error('Error:', error);
            return null
        });
}