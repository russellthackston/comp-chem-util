using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Web.Http;

using System.Text;
using MySql.Data.MySqlClient;
using Psi4WebServices.Controllers.Data;
using Psi4WebServices.Models;

namespace Psi4WebServices.Controllers
{
    public class JobsetjobsController : BaseController
    {
        // GET api/jobssetjobs/42
        // Returns the list of jobs associated with the job set specified by {id} from the database.
        public HttpResponseMessage Get(int id)
        {
            this.RequiredAuthorizationLevel = "None";
            StringBuilder jobsString = new StringBuilder();
            JobSetsDataAccess db = new JobSetsDataAccess();
            IList<JobSetJob> jobs = db.Get(id);
            foreach (JobSetJob j in jobs)
            {
                jobsString.Append(j.ID);
                jobsString.Append(" [DELETE ID=");
                jobsString.Append(j.JobSetJobID);
                jobsString.AppendLine("]");
            }
            HttpResponseMessage response = new HttpResponseMessage(HttpStatusCode.OK);
            response.Content = new StringContent(jobs.ToString());
            return response;
        }

        // PUT api/jobssetjobs/42
        // Adds the specified JobID (from the message body) to the job set specified by {id}
        public HttpResponseMessage Put(int id, [FromBody]string value)
        {
            HttpResponseMessage response;
            this.RequiredAuthorizationLevel = "Admin";
            JobSetJobsDataAccess db = new JobSetJobsDataAccess();
            Boolean result = db.Add(Int16.Parse(value), id);
            if (result) {
                response = new HttpResponseMessage(HttpStatusCode.OK);
                return response;
            }
            else
            {
                response = new HttpResponseMessage(HttpStatusCode.BadRequest);
                throw new HttpResponseException(response);
            }
        }

        // DELETE api/jobssetjobs/42
        // Notifies the queue that this job set is no longer being run as part of this job set.
        public void Delete(int id)
        {
            this.RequiredAuthorizationLevel = "Admin";
            JobSetJobsDataAccess db = new JobSetJobsDataAccess();
            db.Remove(id);
        }
    }
}
