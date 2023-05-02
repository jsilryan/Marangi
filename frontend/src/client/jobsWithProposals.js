import React from "react";
import SpecificProposal from "../components/specificProposal";
import DisplayJobs from "../components/displayJobs";
import AllProposals from "../components/allProposals";

export default function JobsWithProposals(props) {
    let left = props.sidebar ? "250px" : "auto"
    const styles = {
        marginLeft: left
    }

    const [showProposals, setShowProposals] = React.useState(false)

    const [jobShortCode, setJShortCode] = React.useState("")

    //Display all proposals
    function dispProposals(jsc) {
        setShowProposals(true)
        setJShortCode(jsc)
    }

    function hideProposals() {
        setShowProposals(false)        
    }
    const [openModal, setOpenModal] = React.useState(false)

    function showModal() {
        setOpenModal(true)
    }

    return (
        <div style={styles} >
        {
            !showProposals ?
            <div className="alljobs">
                <h2 className="component-heading">Jobs With Proposals</h2>  
                {
                    props.jobs && props.jobs.map((job) => {
                        return(
                            <DisplayJobs 
                                name={job.job_name} description={job.job_description} handleClick={() => dispProposals(job.job_short_code)} 
                                start={job.start_date} end ={job.end_date} created_at = {job.job_created_at}
                            />
                        )
                    })
                }
            </div>
            :
            <AllProposals jsc = {jobShortCode} user = {props.user} handleClick = {hideProposals}/>
        }
        </div>
    )
}