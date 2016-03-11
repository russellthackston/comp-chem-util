using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Web.Http;

using System.Text;
using MySql.Data.MySqlClient;
using Psi4WebServices.Controllers.Data;
using Psi4WebServices.Models;

namespace Psi4WebServices.Controllers
{
    /// <summary>
    /// Manage jobs.
    /// </summary>
    public class JobsController : BaseController
    {

        /// <summary>
        /// Returns a list of the unarchived PSI4 jobs.
        /// </summary>
        /// <returns>List of job IDs and names</returns>
        public HttpResponseMessage Get()
        {
            this.RequiredAuthorizationLevel = "None";
            CheckAuth();
            StringBuilder jobNames = new StringBuilder();
            JobsDataAccess db = new JobsDataAccess();
            IList<Job> jobs = db.Get();
            foreach (Job j in jobs)
            {
                jobNames.Append(j.ID);
                jobNames.Append(": ");
                jobNames.Append(j.Name);
                jobNames.Append("\n");
            }
            HttpResponseMessage response = new HttpResponseMessage(HttpStatusCode.OK);
            response.Content = new StringContent(jobNames.ToString());
            return response;
        }

        /// <summary>
        /// Returns a PSI4 job from database specified by ID.
        /// </summary>
        /// <param name="id">ID of the desired job.</param>
        /// <returns>The input file (in the message body) of the specified job.</returns>
 
        public HttpResponseMessage Get(int id)
        {
            this.RequiredAuthorizationLevel = "None";
            string input_dat = "No data";
            JobsDataAccess db = new JobsDataAccess();
            Job j = db.Get(id);
            HttpResponseMessage response = new HttpResponseMessage(HttpStatusCode.OK);
            if (j != null)
            {
                input_dat = j.InputFile;
                StringBuilder sb = new StringBuilder();
                sb.Append("# JobID: ");
                sb.Append(id);
                sb.AppendLine();
                sb.Append(input_dat);
                response.Content = new StringContent(sb.ToString());
            }
            else
            {
                response = new HttpResponseMessage(HttpStatusCode.NotFound);
                response.Content = new StringContent("Job ID '" + id + "' not found");
                throw new HttpResponseException(response);
            }
            return response;
        }

        /// <summary>
        /// Adds a job to the database. The input.dat file contents are passed in the body of the message as text/plain.
        /// </summary>
        /// <param name="input_dat">the input.dat file contents as plain text.</param>
        /// <returns>The new job's ID in the message body</returns>
        public HttpResponseMessage Post([FromBody]string inputFile)
        {
            HttpResponseMessage response;
            this.RequiredAuthorizationLevel = "Admin";
            JobsDataAccess db = new JobsDataAccess();
            Job j = db.Add(inputFile);
            if (j == null)
            {
                response = new HttpResponseMessage(HttpStatusCode.BadRequest);
                throw new HttpResponseException(response);
            }
            else
            {
                response = new HttpResponseMessage(HttpStatusCode.OK);
                response.Content = new StringContent(j.ID.ToString());
                return response;
            }
        }

        /// <summary>
        /// Updates a job in the database. The input.dat file contents are passed in the body of the message as text/plain.
        /// </summary>
        /// <param name="id">The ID of the desired job.</param>
        /// <param name="input_dat">The new input.dat contents in the message body as plain text.</param>
        /// <returns>The job's ID in the message body</returns>
        public HttpResponseMessage Put(int id, [FromBody]string inputFile)
        {
            HttpResponseMessage response;
            this.RequiredAuthorizationLevel = "Admin";
            JobsDataAccess db = new JobsDataAccess();
            Job j = db.Update(id, inputFile);
            if (j == null)
            {
                response = new HttpResponseMessage(HttpStatusCode.BadRequest);
                throw new HttpResponseException(response);
            }
            else
            {
                response = new HttpResponseMessage(HttpStatusCode.OK);
                response.Content = new StringContent(j.ID.ToString());
                return response;
            }
        }

        /// <summary>
        /// Notifies the database that this job is no longer being run (archived). Job is moved to an archive table.
        /// </summary>
        /// <param name="id">The ID of the job to delete (archive).</param>
        public void Delete(int id)
        {
            this.RequiredAuthorizationLevel = "Admin";
            JobsDataAccess db = new JobsDataAccess();
            db.Delete(id);
        }
    }
}
