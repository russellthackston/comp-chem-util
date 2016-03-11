using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Web.Http;

using System.Diagnostics;
using System.Text;
using MySql.Data.MySqlClient;
using Psi4WebServices.Controllers.Data;
using Psi4WebServices.Models;

namespace Psi4WebServices.Controllers
{
    public class BenchmarkingController : BaseController
    {
        // GET api/benchmarking/42?machineID=XXXX
        // Gets the next benchmarking job in the job set identified by {id} for the machine specified by the MAC address in the url
        public HttpResponseMessage Get(int id)
        {
            string machineID = GetParameter(this.Request, "machineID");
            HttpResponseMessage response = new HttpResponseMessage(HttpStatusCode.OK);
            if (machineID == null || machineID.Trim().Equals(""))
            {
                response = new HttpResponseMessage(HttpStatusCode.NotFound);
                response.Content = new StringContent("Error: Missing client machine ID");
                throw new HttpResponseException(response);
            }
            this.RequiredAuthorizationLevel = "None";
            BenchmarkingDataAccess db = new BenchmarkingDataAccess();
            Job j = db.NextJob(id, Int16.Parse(machineID));
            if (j == null)
            {
                response = new HttpResponseMessage(HttpStatusCode.NotFound);
                response.Content = new StringContent("Job set '" + id + "' not found");
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
            }
            ExecutionDataAccess execDB = new ExecutionDataAccess();
            execDB.Add(id, machineID);
            return response;
        }

    }
}
