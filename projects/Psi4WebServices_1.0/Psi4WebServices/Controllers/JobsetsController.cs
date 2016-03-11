using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Web.Http;

using System.Text;
using Psi4WebServices.Models;
using Psi4WebServices.Controllers.Data;

namespace Psi4WebServices.Controllers
{
    public class JobsetsController : BaseController
    {
        /// <summary>
        /// Prepares a response containing the JobSetID in the body
        /// </summary>
        private HttpResponseMessage PrepareJobSetIDReponse(string name)
        {
            HttpResponseMessage response;
            JobSetsDataAccess db = new JobSetsDataAccess();
            JobSet j = db.Get(name);
            if (j != null)
            {
                response = new HttpResponseMessage(HttpStatusCode.OK);
                response.Content = new StringContent(j.ID.ToString());
            }
            else
            {
                response = new HttpResponseMessage(HttpStatusCode.ServiceUnavailable);
                response.Content = new StringContent("Wow. Something broke. Hard.");
            }
            return response;
        }

        /// <summary>
        /// Returns a list of the job sets from the database.
        /// </summary>
        public HttpResponseMessage Get()
        {
            this.RequiredAuthorizationLevel = "None";
            StringBuilder jobSetNames = new StringBuilder();
            JobSetsDataAccess db = new JobSetsDataAccess();
            IList<JobSet> jobs = db.Get();
            foreach (JobSet j in jobs)
            {
                jobSetNames.Append("[");
                jobSetNames.Append(j.ID);
                jobSetNames.Append("] ");
                jobSetNames.AppendLine(j.Name);
            }
            HttpResponseMessage response = new HttpResponseMessage(HttpStatusCode.OK);
            response.Content = new StringContent(jobSetNames.ToString());
            return response;
        }

        /// <summary>
        /// Returns the job set specified by job {id} from the database.
        /// </summary>
        public HttpResponseMessage Get(int id)
        {
            this.RequiredAuthorizationLevel = "None";
            StringBuilder jobstring = new StringBuilder();
            JobSetsDataAccess db = new JobSetsDataAccess();
            IList<JobSetJob> jobs = db.Get(id);
            foreach (JobSetJob j in jobs)
            {
                jobstring.AppendLine(j.ID.ToString());
            }
            HttpResponseMessage response = new HttpResponseMessage(HttpStatusCode.OK);
            response.Content = new StringContent(jobs.ToString());
            return response;
        }

        /// <summary>
        /// Creates a new job set in the database.
        /// </summary>
        public HttpResponseMessage Post([FromBody]string value)
        {
            this.RequiredAuthorizationLevel = "Admin";
            JobSetsDataAccess db = new JobSetsDataAccess();
            return PrepareJobSetIDReponse(db.Add(value).Name);
        }

        /// <summary>
        /// Updates the job set specified by {id} in the database.
        /// </summary>
        public HttpResponseMessage Put(int id, [FromBody]string value)
        {
            this.RequiredAuthorizationLevel = "Admin";
            JobSetsDataAccess db = new JobSetsDataAccess();
            return PrepareJobSetIDReponse(db.Add(value).Name);
        }

        /// <summary>
        /// Notifies the queue that this job set is no longer being run.
        /// </summary>
        public void Delete(int id)
        {
            this.RequiredAuthorizationLevel = "Admin";
            JobSetsDataAccess db = new JobSetsDataAccess();
            db.Delete(id);
        }
    }
}
