using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;

using Psi4WebServices.Models;
using MySql.Data.MySqlClient;

namespace Psi4WebServices.Controllers.Data
{
    public class JobSetJobsDataAccess : BaseDataAccess
    {
        public IList<Job> Get(int jobSetID)
        {
            IList<Job> jobs = new List<Job>();
            MySqlCommand cmd = this.getCommand("SELECT JobID, JobSetJobID FROM JobSetJobs WHERE JobSetID = @id");
            cmd.Parameters.AddWithValue("@id", jobSetID);
            cmd.Prepare();
            MySqlDataReader reader = cmd.ExecuteReader();
            while (reader.Read())
            {
                int id = reader.GetInt16("JobID");
                string name = reader.GetString("Name");
                string inputFile = reader.GetString("InputFile");
                DateTime created = reader.GetDateTime("Created");
                Job j = new Job(id, name, inputFile, created);
                jobs.Add(j);
            }
            reader.Close();
            return jobs;
        }

        public Boolean Add(int jobID, int jobSetID)
        {
            MySqlCommand cmd = this.getCommand("INSERT INTO JobSetJobs (JobSetID, JobID) VALUES (@jobSetID, @jobID)");
            cmd.Parameters.AddWithValue("@jobSetID", jobSetID);
            cmd.Parameters.AddWithValue("@jobID", jobID);
            cmd.Prepare();
            try
            {
                cmd.ExecuteNonQuery();
                return true;
            }
            catch (MySqlException ex)
            {
                // already exists
                if (ex.Number == 1062)
                {
                    return true;
                }
                else
                {
                    return false;
                }
            }
        }

        public void Remove(int jobSetJobID)
        {
            MySqlCommand cmd = this.getCommand("DELETE FROM JobSetJobs WHERE JobSetJobID = @id");
            cmd.Parameters.AddWithValue("@id", jobSetJobID);
            cmd.Prepare();
            cmd.ExecuteNonQuery();
        }
    }
}