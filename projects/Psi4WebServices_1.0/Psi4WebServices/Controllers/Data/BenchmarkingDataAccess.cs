using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;

using MySql.Data.MySqlClient;
using Psi4WebServices.Models;

namespace Psi4WebServices.Controllers.Data
{
    public class BenchmarkingDataAccess : BaseDataAccess
    {
        public Job NextJob(int id, int machineID)
        {
            Job j = null;
            MySqlCommand cmd = this.getCommand("SELECT * FROM Jobs WHERE JobID IN (" +
                "SELECT JobID FROM JobSetJobs, JobSets " +
                    "WHERE JobSetJobs.JobSetID = JobSets.JobSetID " +
                    "AND JobSets.JobSetID = @jobsetid " +
                ") AND JobID NOT IN (" +
                    "SELECT JobID FROM JobResults " +
                    "WHERE MachineID = @machineID" +
                ") LIMIT 1");
            cmd.Parameters.AddWithValue("@jobsetid", id);
            cmd.Parameters.AddWithValue("@machineID", machineID);
            cmd.Prepare();
            MySqlDataReader reader = cmd.ExecuteReader();
            if (reader.Read())
            {
                id = reader.GetInt16("JobID");
                string name = reader.GetString("JobName");
                string inputfile = reader.GetString("Inputfile");
                DateTime created = reader.GetDateTime("Created");
                j = new Job(id, name, inputfile, created);
            }
            reader.Close();
            return j;
        }
    }
}