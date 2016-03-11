using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;

using Psi4WebServices.Models;
using MySql.Data.MySqlClient;

namespace Psi4WebServices.Controllers.Data
{
    public class JobRunnerDataAccess : BaseDataAccess
    {
        public Job NextJob(int jobSetID)
        {
            Job j = null;
            MySqlCommand cmd = this.getCommand("SELECT Jobs.* FROM Jobs LEFT JOIN Executions " +
                "ON Jobs.JobID = Executions.JobID " +
                "WHERE Jobs.JobID IN (SELECT JobID FROM JobSetJobs, JobSets " + 
                "WHERE JobSetJobs.JobSetID = JobSets.JobSetID AND JobSets.JobSetID = @jobsetid)  " +
                "AND Jobs.JobID NOT IN (SELECT DISTINCT JobID FROM JobResults)  " +
                "GROUP BY Executions.JobID " +
                "ORDER BY COUNT(Executions.JobID) ASC " +
                "LIMIT 1");
            cmd.Parameters.AddWithValue("@jobsetid", jobSetID);
            cmd.Prepare();
            MySqlDataReader reader = cmd.ExecuteReader();
            if (reader.Read())
            {
                int id = reader.GetInt16("JobID");
                string name = reader.GetString("JobName");
                string inputfile = reader.GetString("Inputfile");
                DateTime created = reader.GetDateTime("Created");
                j = new Job(id, name, inputfile, created);
            }
            return j;
        }
    }
}