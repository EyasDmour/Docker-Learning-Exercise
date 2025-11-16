import LoginButton from "./LoginButton";
import LogoutButton from "./LogoutButton";
import { useAuth0 } from "@auth0/auth0-react";


function Header() {    

    const { user, isAuthenticated, isLoading } = useAuth0();


    return (
        <header>
            <h1>YouthInvest</h1>
            <nav>
                <button href="#/projects">Projects</button>
                {isLoading ? (
                    <div>Loading...</div>
                ) : (
                    <>
                        {!isAuthenticated ? <LoginButton /> : <>
                                <button>{user.name}</button>
                            </>}
                        {isAuthenticated ? <LogoutButton /> : null}
                    </>
                )}
            </nav>
        </header>
    );
}

export default Header;