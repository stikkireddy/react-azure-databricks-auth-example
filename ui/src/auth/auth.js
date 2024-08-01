const BASE_URL = "http://localhost:5173"

export const startLogin = async () => {
    const result = await fetch(`${BASE_URL}/authorize-url`, {
        method: 'GET',
        headers: {
            'accept': 'application/json',
            'Content-Type': 'application/json'
        },
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
    if (result) {
        // check if authorize url exists
        if (result.authorize_url !== undefined && result.authorize_url !== null) {
            window.location.href = result.authorize_url;
        }
    }
}

export const checkValidSession = async () => {
    try {
        const response = await fetch(`${BASE_URL}/validate-session`, {
            method: 'POST',
        });

        if (response.status === 200) {
            console.log('Token is valid');
            return true;
        } else if (response.status === 401) {
            console.log('Unauthorized');
            return false;
        } else {
            return false;
        }
    } catch (error) {
        return false;
    }
}

export default startLogin;
