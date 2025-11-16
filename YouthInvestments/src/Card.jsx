import pfp from "../200x200.png"


function Card() {  
    
    return(
        <div className="card">
            <img src={pfp} alt="Profile Pic" />
            <h2>Project Name</h2>
            <p>HTU - Computer Science</p>
        </div>
    );

}

export default Card;