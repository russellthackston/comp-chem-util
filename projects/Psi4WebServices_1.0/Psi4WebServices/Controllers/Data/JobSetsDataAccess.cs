using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;

using Psi4WebServices.Models;
using MySql.Data.MySqlClient;

namespace Psi4WebServices.Controllers.Data
{
    public class JobSetsDataAccess : BaseDataAccess
    {
        public JobSet Get(string name)
        {
            JobSet j = null;
            MySqlCommand cmd = this.getCommand("SELECT JobSetID FROM JobSets WHERE Name = @name");
            cmd.Parameters.AddWithValue("@name", name);
            cmd.Prepare();
            MySqlDataReader reader = cmd.ExecuteReader();
            if (reader.Read())
            {
                int id = reader.GetInt16("JobSetID");
                name = reader.GetString("Name");
                DateTime created = reader.GetDateTime("Created");
                j = new JobSet(id, name, created);
            }
            reader.Close();
            return j;
        }

        public IList<JobSet> Get()
        {
            IList<JobSet> jobs = new List<JobSet>();
            MySqlCommand cmd = this.getCommand("SELECT * FROM JobSets");
            MySqlDataReader reader = cmd.ExecuteReader();
            while (reader.Read())
            {
                int id = reader.GetInt16("JobSetID");
                string name = reader.GetString("Name");
                DateTime created = reader.GetDateTime("Created");
                JobSet j = new JobSet(id, name, created);
                jobs.Add(j);
            }
            return jobs;
        }

        public IList<JobSetJob> Get(int id)
        {
            IList<JobSetJob> jobs = new List<JobSetJob>();
            MySqlCommand cmd = this.getCommand("SELECT * FROM Jobs WHERE JobID IN (SELECT JobID FROM JobSetJobs WHERE JobSetID = @id)");
            cmd.Parameters.AddWithValue("@id", id);
            cmd.Prepare();
            MySqlDataReader reader = cmd.ExecuteReader();
            while (reader.Read())
            {
                int jobID = reader.GetInt16("JobSetID");
                string name = reader.GetString("Name");
                string inputFile = reader.GetString("InputFile");
                DateTime created = reader.GetDateTime("Created");
                JobSetJob j = new JobSetJob(jobID, name, inputFile, created, id);
                jobs.Add(j);
            }
            reader.Close();
            return jobs;
        }

        public JobSet Add(string name)
        {
            MySqlCommand cmd = this.getCommand("INSERT INTO JobSets (Name) VALUES (@name)");
            cmd.Parameters.AddWithValue("@name", name);
            cmd.Prepare();
            cmd.ExecuteNonQuery();
            return Get(name);
        }

        public JobSet Update(string id, string name)
        {
            MySqlCommand cmd = this.getCommand("UPDATE JobSets SET Name = @name WHERE JobSetID = @id");
            cmd.Parameters.AddWithValue("@name", name);
            cmd.Parameters.AddWithValue("@id", id);
            cmd.Prepare();
            cmd.ExecuteNonQuery();
            return Get(name);
        }

        public void Delete(int id)
        {
            MySqlCommand cmd = this.getCommand("INSERT INTO JobSets_Archived (SELECT * FROM JobSets WHERE JobSetID = @id)");
            cmd.Parameters.AddWithValue("@id", id);
            cmd.Prepare();
            try
            {
                cmd.ExecuteNonQuery();
                cmd = this.getCommand("DELETE FROM JobSets WHERE JobSetID = @id");
                cmd.Parameters.AddWithValue("@id", id);
                cmd.Prepare();
                cmd.ExecuteNonQuery();
            }
            catch (MySqlException)
            {
            }
        }
    }
}