using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;

using MySql.Data.MySqlClient;
using Psi4WebServices.Models;

namespace Psi4WebServices.Controllers.Data
{
    public class OutputDataAccess : BaseDataAccess
    {
        public long GetCount()
        {
            MySqlCommand cmd = this.getCommand("SELECT COUNT(*) FROM JobResultsSummary");
            long count = (long)cmd.ExecuteScalar();
            return count;
        }

        public long GetCountSuccess()
        {
            MySqlCommand cmd = this.getCommand("SELECT COUNT(*) FROM JobResultsSummary WHERE Success = 1");
            long count = (long)cmd.ExecuteScalar();
            return count;
        }

        public void Add(int id, string fileContents, int machineID, string filename, string uuid)
        {
            MySqlCommand cmd = this.getCommand("INSERT INTO JobResults (JobID, OutputFile, ResultsCollected, MachineID, Filename, JobGUID) VALUES (@id, @output, NOW(), @machine, @filename, @uuid)");
            cmd.Parameters.AddWithValue("@id", id);
            cmd.Parameters.AddWithValue("@output", fileContents);
            cmd.Parameters.AddWithValue("@machine", machineID);
            cmd.Parameters.AddWithValue("@filename", filename);
            cmd.Parameters.AddWithValue("@uuid", uuid);
            cmd.Prepare();
            cmd.ExecuteNonQuery();
        }
    }
}