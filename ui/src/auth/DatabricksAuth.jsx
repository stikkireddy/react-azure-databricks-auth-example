import React, {createContext, useEffect, useState} from 'react';
import startLogin, {checkValidSession} from "./auth.js";

const AuthContext = createContext(null);

const DatabricksAuthProvider = ({ children }) => {
    const [validSession, setValidSession] = useState(false);
    useEffect(() => {
        checkValidSession().then(async (valid) => {
            if (!valid) {
                await startLogin();
            } else {
                setValidSession(valid);
            }
        });
    }, []);

    return (
        <AuthContext.Provider value={validSession}>
            {validSession ? children : <p>Loading...</p>}
        </AuthContext.Provider>
    );
};


export default DatabricksAuthProvider;
