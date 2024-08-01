import React, {createContext, useEffect, useRef, useState} from 'react';
import startLogin, {checkValidSession} from "./auth.js";

const AuthContext = createContext(null);

const DatabricksAuthProvider = ({ children }) => {
    const [validSession, setValidSession] = useState(false);
    const intervalRef = useRef(null)

    const shouldRefreshToken = async () => {
        const validSession = await checkValidSession()
        if (validSession === false) {
            await startLogin()
            const validSession = await checkValidSession()
            setValidSession(validSession)
            return
        }
        setValidSession(validSession)
    }

    useEffect(() => {
        checkValidSession().then(async (valid) => {
            if (!valid) {
                await startLogin();
            } else {
                setValidSession(valid);
            }
        });
        if (intervalRef.current != null) {
            clearInterval(intervalRef.current)
        }
        intervalRef.current = setInterval(shouldRefreshToken, 10000)
    }, []);

    return (
        <AuthContext.Provider value={validSession}>
            {validSession ? children : <p>Loading...</p>}
        </AuthContext.Provider>
    );
};


export default DatabricksAuthProvider;
