from flask import Flask, request, jsonify, make_response
from flask_restx import Namespace, Resource, fields
from models import Job, Client, Painter, Proposal
from flask_jwt_extended import (JWTManager, create_access_token, 
create_refresh_token, jwt_required, get_jwt_identity
)
from django.shortcuts import get_object_or_404
from datetime import datetime, time, timedelta, date
import random
import requests
import pytz

job_ns = Namespace("job", description = "Job Creation") 

job_model = job_ns.model(
    "Job Details",
    {
        "job_short_code" : fields.String(),
        "job_name" : fields.String(),
        "job_description" : fields.String(),
        "property_location" : fields.String(),
        "property_type" : fields.String(),
        "job_type" : fields.String(),
        "contract_type" : fields.String(),
        "total_floors" : fields.Integer(),
        "total_rooms" : fields.Integer(),
        "start_date" : fields.Date(),
        "end_date" : fields.Date(),
        "job_confirmed" : fields.Boolean(),
        "job_completed" : fields.Boolean(),
        "max_proposals" : fields.Integer(),
        "rated" : fields.Boolean(),
        "job_created_at" : fields.DateTime(),
        "client_id" : fields.Integer(),
        "bidded" : fields.Boolean()
    }
)

@job_ns.route("/client/jobs")
class Client_Jobs_Details(Resource):
    @job_ns.expect(job_model)
    @jwt_required()
    def post(self):
        """Create a job"""
        #Get current client
        email = get_jwt_identity()

        current_client = Client.query.filter_by(email=email).first()

        #Get a random alphanumeric code of length 4
        character = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        char_list = list(character)
        code = random.choices(char_list, k=4)
        code = "".join(code)
        db_job = Job.query.filter_by(job_short_code=code).first()
        while (db_job is not None):
            code = random.choices(char_list, k=4)
            code = "".join(code)
    
        data = request.get_json()

        start_date_str = data.get("start_date")
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')

        end_date_str = data.get("end_date")
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        #Get job created at
        # ip_address = request.remote_addr
        # latitude = data.get('lat')
        # longitude = data.get('long')

        # if latitude and longitude:
        #     # get the user's timezone based on their GPS coordinates
        #     timezone_response = requests.get(f'https://maps.googleapis.com/maps/api/timezone/json?location={latitude},{longitude}&timestamp={int(datetime.now().timestamp())}&key=AIzaSyCVgCH0d4vmVmtmRRD1PdTlkDYFBndKJcg')
        #     timezone_data = timezone_response.json()
        #     timezone_name = timezone_data['timeZoneId']
        # elif ip_address:
        #     # get the user's location based on their IP address
        #     response = requests.get(f'https://ipapi.co/{ip_address}/json/')
        #     location = response.json()
        #     try:
        #         timezone_name = location['timezone']
        #     except:
        #         timezone_name = 'Africa/Nairobi'
        # else:
        #     # use a default timezone if location information is not available
        #     timezone_name = 'Africa/Nairobi'
        # # set the timezone for the current datetime object
        timezone_name = 'Africa/Nairobi'
        local_tz = pytz.timezone(timezone_name)

        # set the client_created_at column with the current datetime object in the user's local timezone
        job_created_at=datetime.now(local_tz)
        new_job = Job (
            job_short_code = code,
            job_name = data.get("job_name"),
            job_description = data.get("job_description"),
            property_location = data.get("property_location"),
            property_type = data.get("property_type"),
            job_type = data.get("job_type"),
            contract_type = data.get("contract_type"),
            total_floors = data.get("total_floors"), 
            total_rooms = data.get("total_rooms"), 
            start_date = start_date,
            end_date = end_date,
            max_proposals = data.get("max_proposals"),
            job_created_at = job_created_at,
            client_id = current_client.id
        )

        new_job.save()
        response = make_response(jsonify({"message": "Job created successfully!"}))
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" 
        return response

    @job_ns.marshal_list_with(job_model)
    @job_ns.expect(job_model)
    @jwt_required()
    def get(self):
        """Get a client's jobs:"""
        #Get current client
        email = get_jwt_identity()

        current_client = Client.query.filter_by(email=email).first()
        jobs = Job.query.all()
        client_jobs = []
        #Check if Client ID is the same as the client ID in the job
        if (current_client):
            for x in range(0, len(jobs)):
                if (current_client.id == jobs[x].client_id):
                    client_jobs.append(jobs[x])

            return client_jobs


@job_ns.route("/painter/jobs")
class Painter_Jobs_Details(Resource):
    @job_ns.marshal_list_with(job_model)
    @job_ns.expect(job_model)
    @jwt_required()
    def get(self):
        """Get all jobs in your area:"""
        email = get_jwt_identity()

        current_painter = Painter.query.filter_by(email=email).first()

        jobs = Job.query.all()

        proposals = Proposal.query.all()

        close_jobs = []

        job_proposals = []

        painter_proposals = []

        for x in range(0, len(proposals)):
            if (current_painter.id == proposals[x].painter_id):
                painter_proposals.append(proposals[x])

        # if proposals:
        if proposals:
            for x in range(0, len(jobs)):
                individual_job_proposals = []
                for y in range(0, len(proposals)):
                    if(jobs[x].id == proposals[y].job_id):
                        individual_job_proposals.append(proposals[y])
                job_proposals.append(individual_job_proposals)

        # Get the current datetime
        now = datetime.now()

        MONTH_LIMIT = 30
        #Display only jobs whose maximum number of proposals have not been reached, those that are not confirmed, 
        #those whose end_date is less than or equal to today's date and the job is not more than 1 month of posting
        for x in range(0, len(jobs)):
            other_date = datetime.combine(jobs[x].start_date, datetime.min.time())
            time_difference = now - other_date
            if (job_proposals):
                if (len(job_proposals[x]) < jobs[x].max_proposals and jobs[x].job_confirmed != True 
                and time_difference < timedelta(days=MONTH_LIMIT) and jobs[x].end_date <= date.today()):
                    if (current_painter.area == jobs[x].property_location):
                        close_jobs.append(jobs[x]) 
            else:
                if (time_difference < timedelta(days=MONTH_LIMIT)):
                    if (current_painter.area == jobs[x].property_location):
                        close_jobs.append(jobs[x])    
        #Create some randomness in the order
        random.shuffle(close_jobs)
        far_jobs = []
        for x in range(0, len(jobs)):
            other_date = datetime.combine(jobs[x].start_date, datetime.min.time())
            time_difference = now - other_date
            if (job_proposals):
                if (len(job_proposals[x]) < jobs[x].max_proposals and jobs[x].job_confirmed != True and time_difference < timedelta(days=MONTH_LIMIT)):
                    if len(close_jobs) > 0:
                        if (jobs[x] not in close_jobs):
                            far_jobs.append(jobs[x])
                    else:
                        far_jobs.append(jobs[x])
            else:
                if (time_difference < timedelta(days=MONTH_LIMIT)):
                    if len(close_jobs) > 0:
                        if (jobs[x] not in close_jobs):
                            far_jobs.append(jobs[x])
                    else:
                        far_jobs.append(jobs[x])

        random.shuffle(far_jobs)
        for i in range(0, len(far_jobs)):
            close_jobs.append(far_jobs[i])

        if len(close_jobs) > 0:
            return close_jobs
        else:
            response = []
            return response

@job_ns.route('/job/<string:job_short_code>')
class Job_Details(Resource):
    @job_ns.marshal_with(job_model)
    @job_ns.expect(job_model)
    @jwt_required()
    def get(self, job_short_code):
        """Get details of a job via short code:"""
        email = get_jwt_identity()

        db_painter = Painter.query.filter_by(email = email).first()
        proposals = Proposal.query.all()
        job = Job.query.filter_by(job_short_code = job_short_code).first()
    
        if job:
            if db_painter:
                job_dict = job.__dict__
                bidded = False
                for x in range(0, len(proposals)):
                    if (db_painter.id == proposals[x].painter_id):
                        if (job.id == proposals[x].job_id): 
                            bidded =True                    
                job_dict["bidded"] = bidded
                return job_dict
            else:
                return job
        else:
            return []

@job_ns.route('/client/job/<string:job_short_code>')
class Update_Job(Resource):
    @jwt_required()
    def put(self, job_short_code):
        """Client updates job details:"""
        job_update = Job.query.filter_by(job_short_code = job_short_code).first()
        email = get_jwt_identity()
        db_client = Client.query.filter_by(email=email).first()
        if db_client is None:
            response = make_response(jsonify({
                "message" : "Only clients can edit jobs!"
            }))
            return response
        if job_update is None:
            response = make_response(jsonify({
                "message" : f"Job with job short code {job_short_code} does not exist!"
            }))
            return response
        elif job_update.job_confirmed == True:
            response = make_response(jsonify({
                "message" : f"Cannot edit a confirmed job."
            }))
            return response
        data = request.get_json()

        start_date_str = data.get("start_date")
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')

        end_date_str = data.get("end_date")
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')

        job_update.update (
            data.get("job_name"),
            data.get("job_description"),
            data.get("property_location"),
            data.get("property_type"),
            data.get("job_type"),
            data.get("contract_type"),
            data.get("total_floors"), 
            data.get("total_rooms"), 
            start_date,
            end_date,
            data.get("max_proposals")
        )
        response = make_response(jsonify({
            "message" : "Job updated."
        }))
        return response

    @jwt_required()
    def delete(self, job_short_code):
        """Delete Job by job_short_code"""
        delete_job = Job.query.filter_by(job_short_code = job_short_code).first()
        if delete_job is None:
            response = make_response(jsonify({
                "message" : f"No job with Short code {job_short_code}."
            }))
            return response
        if delete_job.job_completed != True: 
            delete_job.delete()
            response = make_response(jsonify({
                "message" : f"Job {job_short_code} deleted."
            }))
            return response
        else:
            response = make_response(jsonify({
                "message" : f"Cannot delete a completed job."
            }))
            return response

@job_ns.route('/client/complete-job/<string:job_short_code>')
class Update_Job(Resource):
    @jwt_required()
    def put(self, job_short_code):
        """Client updates job completion:"""
        job_update = Job.query.filter_by(job_short_code = job_short_code).first()
        if job_update is None:
            response = make_response(jsonify({
                "message" : f"Job with job short code {job_short_code} does not exist!"
            }))
            return response
        if job_update.job_confirmed == True:
            data = request.get_json()
            if job_update.job_completed != True:
                if data.get("job_completed") == True:
                    job_update.completed_update (
                        data.get("job_completed")
                    )
                    response = make_response(jsonify({
                        "message" : "Job completed."
                    }))
                else:
                    #To be changed
                    response = make_response(jsonify({
                        "message" : "Job is not completed."
                    }))
            else:
                response = make_response(jsonify({
                    "message" : "Job was already completed."
                }))
        else:
            response = make_response(jsonify({
                "message" : "Cannot complete a job that has not been confirmed!"
            }))
        return response

@job_ns.route("/client/job/job_proposals")
class Jobs_With_Proposals(Resource):
    @job_ns.marshal_list_with(job_model)
    @job_ns.expect(job_model)
    @jwt_required()
    def get(self):
        """Get all jobs with proposals for 1 client"""
        email = get_jwt_identity()
        current_client = Client.query.filter_by(email=email).first()
        jobs = Job.query.all()
        client_jobs = []
        for x in range(0, len(jobs)):
            if (current_client.id == jobs[x].client_id):
                client_jobs.append(jobs[x])
                
        proposals = Proposal.query.all()
        jobs_with_props = []

        for x in range(0, len(client_jobs)):
            for y in range(0, len(proposals)):
                if client_jobs[x].id == proposals[y].job_id:
                    if client_jobs[x] not in jobs_with_props:
                        jobs_with_props.append(client_jobs[x])

        
        return jobs_with_props

        

@job_ns.route("/job/confirmed")
class Confirmed_Jobs(Resource):
    @job_ns.marshal_list_with(job_model)
    @job_ns.expect(job_model)
    @jwt_required()
    def get(self):
        """Get all ongoing jobs for either client or painter"""
        email = get_jwt_identity()
        db_painter = Painter.query.filter_by(email=email).first()
        db_client = Client.query.filter_by(email=email).first()

        confirmed_jobs = []
        
        jobs = Job.query.all()
        proposals = Proposal.query.all()

        if db_client:
            client_jobs = []
            for x in range(0, len(jobs)):
                if (jobs[x].client_id == db_client.id):
                    client_jobs.append(jobs[x])
            for x in range(0, len(client_jobs)):
                if (client_jobs[x].job_confirmed == True):
                    if (client_jobs[x].job_completed != True):
                        confirmed_jobs.append(client_jobs[x])

        elif db_painter:
            painter_proposals = []
            selected_proposals = []
            for x in range(0, len(proposals)):
                if (db_painter.id == proposals[x].painter_id):
                    painter_proposals.append(proposals[x])
            for x in range(0, len(painter_proposals)):
                if (painter_proposals[x].proposal_selection == True):
                    selected_proposals.append(painter_proposals[x])
            for x in range(0, len(selected_proposals)):
                job_id = selected_proposals[x].job_id
                job = Job.query.filter_by(id = job_id).first()
                if (job.job_confirmed == True):
                    if (job.job_completed != True):
                        confirmed_jobs.append(job)

        if len(confirmed_jobs) > 0:
            return confirmed_jobs
        else:
            response = []
            return response

@job_ns.route("/job/completed")
class Completed_Jobs(Resource):
    @job_ns.marshal_list_with(job_model)
    @job_ns.expect(job_model)
    @jwt_required()
    def get(self):
        """Get all completed jobs for either client or painter"""
        email = get_jwt_identity()
        db_painter = Painter.query.filter_by(email=email).first()
        db_client = Client.query.filter_by(email=email).first()

        completed_jobs = []
        
        jobs = Job.query.all()
        proposals = Proposal.query.all()

        if db_client:
            client_jobs = []
            for x in range(0, len(jobs)):
                if (jobs[x].client_id == db_client.id):
                    client_jobs.append(jobs[x])
            for x in range(0, len(client_jobs)):
                if (client_jobs[x].job_completed == True):
                    completed_jobs.append(client_jobs[x])

        elif db_painter:
            painter_proposals = []
            selected_proposals = []
            for x in range(0, len(proposals)):
                if (db_painter.id == proposals[x].painter_id):
                    painter_proposals.append(proposals[x])
            for x in range(0, len(painter_proposals)):
                if (painter_proposals[x].proposal_selection == True):
                    selected_proposals.append(painter_proposals[x])
            for x in range(0, len(selected_proposals)):
                job_id = selected_proposals[x].job_id
                job = Job.query.filter_by(id = job_id).first()
                if job.job_completed == True:
                    completed_jobs.append(job)

        if len(completed_jobs) > 0:
            return completed_jobs
        else:
            return completed_jobs
