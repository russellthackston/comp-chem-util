using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;

using MySql.Data.MySqlClient;

namespace Psi4WebServices.Controllers.Data
{
    public class OutputDataAccess : BaseDataAccess
    {
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