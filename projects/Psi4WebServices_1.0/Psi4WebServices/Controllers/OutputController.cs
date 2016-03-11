using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Web.Http;

using System.Text;
using Psi4WebServices.Controllers.Data;

namespace Psi4WebServices.Controllers
{
    /// <summary>
    /// Records output from a psi4 job. Any file produced by the process may be uploaded.
    /// </summary>
    public class OutputController : BaseController
    {
        /// <summary>
        /// Adds a job result to the database for the job identified by {id}. The file contents are passed in the body of the message as text/plain.
        /// </summary>
        /// <param name="id">Job ID</param>
        /// <param name="fileContents">File contents</param>
        public void Post(int id, [FromBody]string fileContents)
        {
            HttpResponseMessage response;
            string machineID = null;
            string filename = null;
            string uuid = null;
            HttpRequestMessage msg = this.Request;
            IEnumerable<KeyValuePair<string, string>> list = msg.GetQueryNameValuePairs();
            foreach (KeyValuePair<string, string> item in list)
            {
                if (item.Key.ToLower() == "machineid")
                {
                    machineID = item.Value;
                }
                else if (item.Key.ToLower() == "filename")
                {
                    filename = item.Value;
                }
                else if (item.Key.ToLower() == "uuid")
                {
                    uuid = item.Value;
                }
            }
            if (machineID == null || machineID.Trim().Equals(""))
            {
                response = new HttpResponseMessage(HttpStatusCode.NotFound);
                response.Content = new StringContent("Error: Missing client machine ID");
                throw new HttpResponseException(response);
            }

            this.RequiredAuthorizationLevel = "None";
            OutputDataAccess db = new OutputDataAccess();
            db.Add(id, fileContents, Int16.Parse(machineID), filename, uuid);
        }
    }
}
