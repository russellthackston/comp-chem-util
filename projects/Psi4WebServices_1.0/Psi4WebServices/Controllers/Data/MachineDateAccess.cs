using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;

using Psi4WebServices.Models;
using MySql.Data.MySqlClient;

namespace Psi4WebServices.Controllers.Data
{
    public class MachineDateAccess : BaseDataAccess
    {
        public IList<Machine> Get()
        {
            IList<Machine> machines = new List<Machine>();
            MySqlCommand cmd = this.getCommand("SELECT * FROM Machines");
            MySqlDataReader reader = cmd.ExecuteReader();
            while (reader.Read())
            {
                int id = reader.GetInt16("MachineID");
                string mac = reader.GetString("MAC");
                string name = reader.GetString("Name");
                DateTime created = reader.GetDateTime("Created");
                Machine m = new Machine(id, name, created, mac);
                machines.Add(m);
            }
            reader.Close();
            return machines;
        }

        public Machine Get(int id)
        {
            Machine m = null;
            MySqlCommand cmd = this.getCommand("SELECT * FROM Machines WHERE MachineID = @id");
            cmd.Parameters.AddWithValue("@id", id);
            cmd.Prepare();
            MySqlDataReader reader = cmd.ExecuteReader();
            if (reader.Read())
            {
                id = reader.GetInt16("MachineID");
                string mac = reader.GetString("MAC");
                DateTime created = reader.GetDateTime("Created");
                string name = reader.GetString("Name");
                m = new Machine(id, name, created, mac);
            }
            reader.Close();
            return m;
        }

        public string GetMachineID(string mac, string name)
        {
            string machineID = null;
            MySqlCommand cmd = this.getCommand("SELECT * FROM Machines WHERE MAC = @id AND Name = @name");
            cmd.Parameters.AddWithValue("@id", mac);
            cmd.Parameters.AddWithValue("@name", name);
            cmd.Prepare();
            MySqlDataReader reader = cmd.ExecuteReader();
            if (reader.Read())
            {
                machineID = reader.GetString("MachineID");
            }
            reader.Close();
            return machineID;
        }

        public Machine Add(string mac, string name)
        {
            string machineID = null;
            Machine m = null;
            MySqlCommand cmdInsert = this.getCommand("INSERT INTO Machines (MAC, Created, Name) VALUES (@mac, now(), @name)");
            cmdInsert.Parameters.AddWithValue("@mac", mac);
            cmdInsert.Parameters.AddWithValue("@name", name);
            cmdInsert.Prepare();
            cmdInsert.ExecuteNonQuery();
            MySqlCommand cmdSelect = this.getCommand("SELECT * FROM Machines WHERE MAC = @mac AND Name = @name");
            cmdSelect.Parameters.AddWithValue("@mac", mac);
            cmdSelect.Parameters.AddWithValue("@name", name);
            cmdSelect.Prepare();
            MySqlDataReader reader = cmdSelect.ExecuteReader();
            if (reader.Read())
            {
                machineID = reader.GetString("MachineID");
            }
            reader.Close();
            if (machineID != null)
            {
                m = Get(Int16.Parse(machineID));
            }
            
            return m;
        }
    }
}