using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;

using MySql.Data.MySqlClient;

namespace Psi4WebServices.Controllers.Data
{
    public class ExecutionDataAccess : BaseDataAccess
    {
        public void Add(int id, string machineID)
        {
            MySqlCommand cmd = this.getCommand("INSERT INTO Executions (JobId, JobStarted, MachineID) VALUES (@jobID, NOW(), @machineID)");
            cmd.Parameters.AddWithValue("@jobID", id);
            cmd.Parameters.AddWithValue("@machineID", machineID);
            cmd.Prepare();
            cmd.ExecuteNonQuery();
        }
    }
}