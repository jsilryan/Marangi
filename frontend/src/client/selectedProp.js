import React from "react"

export default function SelectedProposals(props) {
    let left = props.sidebar ? "250px" : "auto"

    const styles = {
        marginLeft: left
    }

    return (
        <main className="empty-main" style={styles}>
            <h2 className="empty-h2">You have 0 Selected Proposals.</h2>
        </main>

        
    )

}
