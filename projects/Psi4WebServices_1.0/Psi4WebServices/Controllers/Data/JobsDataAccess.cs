using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;

using MySql.Data.MySqlClient;
using Psi4WebServices.Models;

namespace Psi4WebServices.Controllers.Data
{
    public class JobsDataAccess : BaseDataAccess
    {
        public IList<Job> Get()
        {
            List<Job> jobs = new List<Job>();
            MySqlCommand cmd = this.getCommand("SELECT * FROM Jobs");
            MySqlDataReader reader = cmd.ExecuteReader();
            while (reader.Read())
            {
                int id = reader.GetInt16("JobID");
                string name = reader.GetString("JobName");
                string inputfile = reader.GetString("Inputfile");
                DateTime created = reader.GetDateTime("Created");
                Job j = new Job(id, name, inputfile, created);
                jobs.Add(j);
            }
            reader.Close();
            return jobs;
        }

        public Job Get(int id)
        {
            Job j = null;
            MySqlCommand cmd = this.getCommand("SELECT * FROM Jobs WHERE JobID = @id");
            cmd.Parameters.AddWithValue("@id", id);
            cmd.Prepare();
            MySqlDataReader reader = cmd.ExecuteReader();
            if (reader.Read())
            {
                id = reader.GetInt16("JobID");
                string inputFile = reader.GetString("InputFile");
                string name = reader.GetString("Name");
                DateTime created = reader.GetDateTime("Created");
                j = new Job(id, name, inputFile, created);
            }
            reader.Close();
            return j;
        }

        public Job Get(string name)
        {
            Job j = null;
            MySqlCommand cmd = this.getCommand("SELECT * FROM Jobs WHERE JobName = @name LIMIT 1");
            cmd.Parameters.AddWithValue("@name", name);
            cmd.Prepare();
            MySqlDataReader reader = cmd.ExecuteReader();
            if (reader.Read())
            {
                int id = reader.GetInt16("JobID");
                string inputFile = reader.GetString("InputFile");
                name = reader.GetString("Name");
                DateTime created = reader.GetDateTime("Created");
                j = new Job(id, name, inputFile, created);
            }
            reader.Close();
            return j;
        }

        public Job Add(string inputFile)
        {
            MySqlCommand cmd = this.getCommand("INSERT INTO Jobs (JobName, InputFile, Created) VALUES (@name, @input, NOW())");
            string name = inputFile.Split(Environment.NewLine.ToCharArray())[0];
            char[] trimMe = { '#', '!', ' ' };
            name = name.TrimStart(trimMe);
            cmd.Parameters.AddWithValue("@name", name);
            cmd.Parameters.AddWithValue("@input", inputFile);
            cmd.Prepare();
            cmd.ExecuteNonQuery();
            return Get(name);
        }

        public Job Update(int id, string inputFile)
        {
            MySqlCommand cmd = this.getCommand("UPDATE Jobs SET JobName = @name, InputFile = @input WHERE JobID = @idL");
            string name = inputFile.Split(Environment.NewLine.ToCharArray())[0];
            char[] trimMe = { '#', '!', ' ' };
            name = name.TrimStart(trimMe);
            cmd.Parameters.AddWithValue("@name", name);
            cmd.Parameters.AddWithValue("@input", inputFile);
            cmd.Parameters.AddWithValue("@id", id);
            cmd.Prepare();
            cmd.ExecuteNonQuery();
            return Get(id);
        }

        public void Delete(int id)
        {
            MySqlCommand cmd = this.getCommand("INSERT INTO Jobs_Archived (SELECT * FROM Jobs WHERE JobID = @id)");
            cmd.Parameters.AddWithValue("@id", id);
            cmd.Prepare();
            cmd.ExecuteNonQuery();
            cmd = this.getCommand("DELETE FROM Jobs WHERE JobID = @id");
            cmd.Parameters.AddWithValue("@id", id);
            cmd.Prepare();
            cmd.ExecuteNonQuery();
        }
    }
}