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
    /// <summary>
    /// Retrieves jobs for execution on a client machine.
    /// </summary>
    public class JobRunnerController : BaseController
    {

        /// <summary>
        /// Returns the next available job in the job set specified by {id} that does not have an associated completed job result.
        /// </summary>
        /// <param name="id">ID of the job set</param>
        /// <returns>An input.dat file in the body of the message.</returns>
        public HttpResponseMessage Get(int id)
        {
            HttpResponseMessage response= new HttpResponseMessage(HttpStatusCode.OK);
            string machineID = GetParameter(this.Request, "machineID");
            this.RequiredAuthorizationLevel = "None";
            JobRunnerDataAccess db = new JobRunnerDataAccess();
            Job j = db.NextJob(id);
            if (j == null)
            {
                response = new HttpResponseMessage(HttpStatusCode.NotFound);
                response.Content = new StringContent("Job ID '" + id + "' not found");
                throw new HttpResponseException(response);
            }
            else
            {
                StringBuilder sb = new StringBuilder();
                sb.Append("# JobID: ");
                sb.Append(j.ID.ToString());
                sb.AppendLine();
                sb.Append(j.InputFile);
                response.Content = new StringContent(sb.ToString());
                return response;
            }
        }
    }
}
