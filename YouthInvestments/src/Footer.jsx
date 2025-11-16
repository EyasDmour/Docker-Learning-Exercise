import { useAuth0 } from "@auth0/auth0-react";
import { useState } from "react";

function Footer(){    
    const { user, isAuthenticated, getAccessTokenSilently, isLoading } = useAuth0();
    const [token, setToken] = useState();
    
    if(isAuthenticated && !token){
        getAccessTokenSilently().then(tkn => setToken(tkn));
    }

    if (isLoading) {
        return <div>Loading...</div>;
    } else if (isAuthenticated){
        if (!token) {
            return <div>Loading...</div>;
        } else {
            console.log("User ID:", user.sub);
            console.log("Access Token:", token);
        }
    }



    return(
        <footer>
            <p>&copy;{new Date().getFullYear()} YouthInvestments</p>
            
            {isAuthenticated ? (<>
                <label htmlFor="userId">User ID: {user.sub} </label>
                <br></br>
                <label htmlFor="jwt">Access Token: </label>
                <input type="text" id="jwt" name="jwt" readOnly value={token || ""} title={token || ""} style={{
                        width: "420px",
                        display: "inline-block",
                        whiteSpace: "nowrap",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        verticalAlign: "middle"
                    }}
                />
            </>) : null}
        </footer>
    );
}

export default Footer