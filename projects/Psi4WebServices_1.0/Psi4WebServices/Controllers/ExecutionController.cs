using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Web.Http;

using System.Text;
using Psi4WebServices.Controllers.Data;

namespace Psi4WebServices.Controllers
{
    /// <summary>
    /// Manages list of executions and attempted executions for jobs.
    /// </summary>
    public class ExecutionController : BaseController
    {

        /// <summary>
        /// Notes a particular job in being executed by a particular machine.
        /// </summary>
        public void Post(int id)
        {
            this.RequiredAuthorizationLevel = "None";
            string machineID = GetParameter(this.Request, "machineID");
            if (machineID == null || machineID.Trim().Equals(""))
            {
                HttpResponseMessage response = new HttpResponseMessage(HttpStatusCode.NotFound);
                response.Content = new StringContent("Error: Missing client machine ID");
                throw new HttpResponseException(response);
            }

            ExecutionDataAccess db = new ExecutionDataAccess();
            db.Add(id, machineID);
        }
    }
}