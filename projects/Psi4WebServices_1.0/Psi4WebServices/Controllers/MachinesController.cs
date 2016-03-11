using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Web.Http;

using System.Text;
using Psi4WebServices.Controllers.Data;
using Psi4WebServices.Models;

namespace Psi4WebServices.Controllers
{
    public class MachinesController : BaseController
    {
        // GET api/machines
        // Returns a list of the machines that are currently registered in the database.
        public HttpResponseMessage Get()
        {
            this.RequiredAuthorizationLevel = "None";
            StringBuilder jobNames = new StringBuilder();
            MachineDateAccess db = new MachineDateAccess();
            IList<Machine> machines = db.Get();
            foreach (Machine m in machines)
            {
                jobNames.Append(m.ID);
                jobNames.Append(", ");
                jobNames.Append(m.MAC);
                jobNames.Append(", ");
                jobNames.Append(m.Name);
                jobNames.Append(", ");
                jobNames.AppendLine(m.Created.ToString());
            }
            HttpResponseMessage response = new HttpResponseMessage(HttpStatusCode.OK);
            response.Content = new StringContent(jobNames.ToString());
            return response;
        }

        // POST api/jobs
        // Creates a new machine entry in the database for the specified {id}.
        // The machine name must be specified in the body of the message.
        // If the specified {id} already exists, it returns the existing machine details.
        public HttpResponseMessage Post(string id)
        {
            this.RequiredAuthorizationLevel = "None";
            HttpResponseMessage response;

            string name = null;
            HttpRequestMessage msg = this.Request;
            IEnumerable<KeyValuePair<string, string>> list = msg.GetQueryNameValuePairs();
            foreach (KeyValuePair<string, string> item in list)
            {
                if (item.Key.ToLower() == "name")
                {
                    name = item.Value;
                    break;
                }
            }
            if (name == null || name.Trim().Equals(""))
            {
                response = new HttpResponseMessage(HttpStatusCode.NotFound);
                response.Content = new StringContent("Error: Missing client name");
                throw new HttpResponseException(response);
            }

            string machineID = null;
            machineID = GetOrCreateMachineID(id, name);
            if (machineID == null)
            {
                response = new HttpResponseMessage(HttpStatusCode.ServiceUnavailable);
                response.Content = new StringContent("Service unavailable");
                throw new HttpResponseException(response);
            }
            response = new HttpResponseMessage(HttpStatusCode.OK);
            response.Content = new StringContent(machineID);
            return response;
        }

        protected string GetMachineID(string mac, string name)
        {
            string originalAuth = this.RequiredAuthorizationLevel;
            this.RequiredAuthorizationLevel = "None";
            string machineID = null;
            MachineDateAccess db = new MachineDateAccess();
            machineID = db.GetMachineID(mac, name);
            this.RequiredAuthorizationLevel = originalAuth;
            return machineID;
        }

        protected string GetOrCreateMachineID(string mac, string name)
        {
            string originalAuth = this.RequiredAuthorizationLevel;
            this.RequiredAuthorizationLevel = "None";
            string machineID = GetMachineID(mac, name);
            if (machineID == null)
            {
                MachineDateAccess db = new MachineDateAccess();
                db.Add(mac, name);
            }
            this.RequiredAuthorizationLevel = originalAuth;
            return machineID;
        }

    }
}
